#!/usr/bin/env python3
"""Align a user's IE1 English NDS text with the Japanese 3DS event scripts.

The output contains copyrighted game text and is written only under ignored
work/. It is a review reference, never an input that silently fills the
committed English translation CSV.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "src"))

from ie123kit.nucleo.compresion.lz10 import decompress  # noqa: E402
from ie123kit.nucleo.contenedores.fa import FaArchive  # noqa: E402
from ie123kit.nucleo.eventos.alineado_ids import emparejar, tabla_3ds, tabla_nds  # noqa: E402
from ie123kit.nucleo.eventos.packnum import parse_index  # noqa: E402
from ie123kit.nucleo.texto.nds_latin import decode_ds  # noqa: E402
from ie123kit._legado.reinsert import looks_like_dialogue  # noqa: E402

ARCHIVE = ROOT / "work/shared/base_3ds/romfs/archive.fa"
FIELDS = ("event_id", "string_id", "japones", "english_ds", "status")


def events(pkh: bytes, pkb: bytes) -> dict[int, bytes]:
    result = {}
    for eid, offset, size in parse_index(pkh):
        chunk = pkb[offset:offset + size]
        if chunk:
            result[eid] = decompress(chunk) if chunk[0] == 0x10 else chunk
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=("ie1",), default="ie1")
    args = parser.parse_args()
    game = args.game
    reference = ROOT / "work" / game / "english_references/data_iz/script/en"
    out = ROOT / "work" / game / "english_references/alignment"
    workspace = ROOT / "translation/en" / game / "dialogo.csv"
    for path in (ARCHIVE, reference / "evet.pkh", reference / "evet.pkb", workspace):
        if not path.is_file():
            print(f"Missing input: {path}", file=sys.stderr)
            return 2

    arc = FaArchive(ARCHIVE)
    files = {path: (offset, size) for path, offset, size in arc.entries}

    def archive_file(name: str) -> bytes:
        matches = [pair for path, pair in files.items() if path.endswith(name)]
        if len(matches) != 1:
            raise ValueError(f"Expected one {name} in archive.fa, found {len(matches)}")
        offset, size = matches[0]
        return arc.d[offset:offset + size]

    archive_game = "inazuma1"
    jp_events = events(
        archive_file(f"{archive_game}/data_iz/script/eve.pkh"),
        archive_file(f"{archive_game}/data_iz/script/eve.pkb"),
    )
    del arc
    en_events = events((reference / "evet.pkh").read_bytes(), (reference / "evet.pkb").read_bytes())
    with workspace.open(encoding="utf-8-sig", newline="") as stream:
        workspace_keys = {(row["event_id"], row["japones"]) for row in csv.DictReader(stream)}
    # The inherited Japanese CSV sometimes has a one-byte SSD prefix rendered
    # as an ASCII character. Resolve it only when the event has one exact suffix.
    keys_by_suffix = defaultdict(list)
    for eid, japanese in workspace_keys:
        keys_by_suffix[(eid, japanese)].append(japanese)
        if len(japanese) > 1 and japanese[0].isascii():
            keys_by_suffix[(eid, japanese[1:])].append(japanese)

    pairs = []
    counts = Counter()
    by_key = defaultdict(set)
    for eid in sorted(jp_events.keys() & en_events.keys()):
        jp = tabla_3ds(jp_events[eid])
        if jp is None:
            counts["unparsed_events"] += 1
            continue
        en = tabla_nds(en_events[eid])
        mapping, anchors_ok, anchors_bad = emparejar(jp, en)
        counts["common_events"] += 1
        counts["ascii_anchors_ok"] += anchors_ok
        counts["ascii_anchors_different"] += anchors_bad
        if anchors_bad:
            counts["events_with_anchor_differences"] += 1
        for sid, (typ, raw, old_key) in jp.items():
            if typ != 1:
                continue
            japanese = raw.decode("cp932", "replace")
            if not looks_like_dialogue(japanese):
                continue
            en_sid = mapping.get(sid)
            if en_sid is None or en[en_sid][0] != 1:
                counts["dialogue_without_ds_match"] += 1
                continue
            english = decode_ds(en[en_sid][1])
            if not english:
                counts["empty_ds_lines"] += 1
                continue
            candidates = set(keys_by_suffix.get((str(eid), japanese), ()))
            if old_key and (str(eid), old_key) in workspace_keys:
                candidates.add(old_key)
            key = (str(eid), next(iter(candidates))) if len(candidates) == 1 else (str(eid), japanese)
            status = "review" if not anchors_bad else "check_event_alignment"
            if len(candidates) > 1:
                status = "ambiguous_workspace_key"
            elif key not in workspace_keys:
                status = "outside_workspace"
            if (japanese.count("%s"), japanese.count("%d")) != (english.count("%s"), english.count("%d")):
                status = "placeholder_mismatch"
            pairs.append([eid, sid, key[1], english, status])
            by_key[key].add(english)

    ambiguous = {key for key, values in by_key.items() if len(values) > 1}
    for row in pairs:
        if (str(row[0]), row[2]) in ambiguous:
            row[4] = "ambiguous_same_japanese"
        counts[row[4]] += 1
    counts["ambiguous_keys"] = len(ambiguous)
    counts["matched_rows"] = len(pairs)
    counts["matched_unique_workspace_keys"] = len({(str(r[0]), r[2]) for r in pairs if (str(r[0]), r[2]) in workspace_keys})
    counts["workspace_keys"] = len(workspace_keys)

    out.mkdir(parents=True, exist_ok=True)
    pairs_path = out / f"{game}_ds_pairs.csv"
    with pairs_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(FIELDS)
        writer.writerows(pairs)
    (out / "summary.json").write_text(json.dumps(counts, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(counts, indent=2))
    print(f"Review reference: {pairs_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
