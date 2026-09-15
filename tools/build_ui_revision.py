"""Build the approved UI revision on top of the current v27 candidate.

The revision contains archive replacements in ``work/ie1/legacy/ui_revision/extra`` and
decompressed SSD event blobs in ``work/ie1/legacy/ui_revision/events``.  This tool keeps
the v27 archive as the base, validates that event instructions and record
identity are unchanged, then writes a new LayeredFS archive and CRO copy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

from fa_unpack import FaArchive
from fa_repack import fe_offset_of
from lz10 import compress, decompress
from pkb_unpack import parse_index
import ssd_records as S

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def archive_payload(arc: FaArchive, path: str) -> bytes:
    for p, off, size in arc.entries:
        if p == path:
            return bytes(arc.d[off:off + size])
    raise ValueError(f"missing archive entry: {path}")


def replace_entry(handle, arc: FaArchive, path: str, payload: bytes) -> None:
    field = fe_offset_of(arc, path)
    if field is None:
        raise ValueError(f"missing archive entry: {path}")
    handle.seek(0, 2)
    handle.write(bytes((-handle.tell()) % 16))
    offset = handle.tell()
    handle.write(payload)
    handle.seek(field + 8)
    handle.write(struct.pack("<II", offset - arc.data_off, len(payload)))


def rebuild_events(arc: FaArchive, events_dir: Path):
    pkh_path = "inazuma1/data_iz/script/eve.pkh"
    pkb_path = "inazuma1/data_iz/script/eve.pkb"
    pkh = archive_payload(arc, pkh_path)
    pkb = archive_payload(arc, pkb_path)
    index = parse_index(pkh)
    by_id = {eid: (off, size) for eid, off, size in index}
    staged = {int(p.stem): p for p in events_dir.glob("*.ssd")}
    unknown = sorted(set(staged) - set(by_id))
    if unknown:
        raise ValueError(f"unknown staged event ids: {unknown}")

    output = bytearray()
    new_index = []
    report = []
    for eid, off, size in index:
        original_compressed = pkb[off:off + size]
        original = decompress(original_compressed)
        payload = original
        changed = 0
        if eid in staged:
            payload = staged[eid].read_bytes()
            old_end, old_instructions, old_records = S.parse(original)
            new_end, new_instructions, new_records = S.parse(payload)
            if old_instructions != new_instructions:
                raise ValueError(f"event {eid}: instruction table changed")
            if len(old_records) != len(new_records):
                raise ValueError(f"event {eid}: record count changed")
            for i, (old, new) in enumerate(zip(old_records, new_records)):
                if (old.instruction, old.argument) != (new.instruction, new.argument):
                    raise ValueError(f"event {eid}: record identity changed at {i}")
                if old.body != new.body:
                    changed += 1
            if new_end != 32 + struct.unpack_from("<I", payload, 16)[0]:
                raise ValueError(f"event {eid}: malformed SSD payload")
        compressed = compress(payload)
        if decompress(compressed) != payload:
            raise ValueError(f"event {eid}: LZ10 round-trip failed")
        new_index.append((eid, len(output), len(compressed)))
        output.extend(compressed)
        output.extend(bytes((-len(output)) % 4))
        if eid in staged:
            report.append({"event": eid, "records_changed": changed,
                           "old_compressed": len(original_compressed),
                           "new_compressed": len(compressed),
                           "source_sha256": digest(staged[eid])})

    new_pkh = bytearray(pkh[:0x30])
    for record in new_index:
        new_pkh.extend(struct.pack("<III", *record))
    struct.pack_into("<I", new_pkh, 0x10, len(new_pkh))
    return bytes(new_pkh), bytes(output), report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=ROOT / "work/shared/candidatas/probe_ie1_v27/archive.fa")
    parser.add_argument("--ui", type=Path, default=ROOT / "work/ie1/legacy/ui_revision")
    parser.add_argument("--output", type=Path, default=ROOT / "work/shared/candidatas/probe_ie1_v28/archive.fa")
    parser.add_argument("--extra", type=Path, action="append",
                        help="Overlay directory of archive-relative files (repeatable, "
                             "later overlays win); defaults to <ui>/extra")
    parser.add_argument("--cro", type=Path,
                        help="CRO to ship with the candidate; defaults to <ui>/romfs/cro/ina_main1.cro")
    args = parser.parse_args()
    base = args.base.resolve()
    ui = args.ui.resolve()
    output = args.output.resolve()
    if not base.is_file():
        raise FileNotFoundError(base)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite candidate: {output}")
    arc = FaArchive(str(base))
    events_dir = ui / "events"
    staged_events = events_dir.is_dir() and any(events_dir.glob("*.ssd"))
    event_report = []
    if staged_events:
        new_pkh, new_pkb, event_report = rebuild_events(arc, events_dir)
    known = {p for p, _, _ in arc.entries}
    overlays = [p.resolve() for p in args.extra] if args.extra else [ui / "extra"]
    extra_files = {}
    overridden = []
    for extra in overlays:
        for src in sorted(extra.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(extra).as_posix()
            if rel not in known:
                raise ValueError(f"extra file is not an archive entry: {rel}")
            if rel in extra_files:
                overridden.append({"entry": rel, "overlay": str(extra)})
            extra_files[rel] = src.read_bytes()

    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(base, output)
    with output.open("r+b") as handle:
        if staged_events:
            replace_entry(handle, arc, "inazuma1/data_iz/script/eve.pkh", new_pkh)
            replace_entry(handle, arc, "inazuma1/data_iz/script/eve.pkb", new_pkb)
        for rel, payload in sorted(extra_files.items()):
            replace_entry(handle, arc, rel, payload)

    cro_src = args.cro.resolve() if args.cro else ui / "romfs/cro/ina_main1.cro"
    cro_dst = output.parent / "romfs/cro/ina_main1.cro"
    if cro_src.is_file():
        cro_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cro_src, cro_dst)
    report = {
        "base": str(base),
        "base_sha256": digest(base),
        "archive": str(output),
        "archive_sha256": digest(output),
        "events": event_report,
        "events_staged": len(event_report),
        "archive_replacements": len(extra_files),
        "overridden_by_later_overlay": overridden,
        "cro": str(cro_dst) if cro_dst.is_file() else None,
        "typography": "v20 lock preserved",
        "runtime_verified": False,
    }
    output.with_suffix(".build.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
