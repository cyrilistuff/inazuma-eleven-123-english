"""Stage reviewed English IE1 dialogue as local SSD records for a later build.

This does not create an archive, change fonts, or certify a playable patch.
All staged game data stays under ignored work/.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

from ie123kit.nucleo.compresion.lz10 import decompress
from ie123kit.nucleo.contenedores.fa import FaArchive
from ie123kit.nucleo.eventos.packnum import parse_index
from ie123kit.nucleo.eventos import ssd
from ie123kit.nucleo.texto.nds_latin import decode_cadena
from ie123kit.nucleo.texto.ancho_completo import encode_fullwidth

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "tools"))
from build_ie1_probe import layout  # noqa: E402 - frozen, approved wrapping
from dialogue_lock import approved_layout  # noqa: E402

ARCHIVE = ROOT / "work/shared/base_3ds/romfs/archive.fa"
CSV = ROOT / "translation/en/ie1/dialogo.csv"
OUT = ROOT / "work/ie1/english_probe"


def translations(event_id: int, include_review: bool) -> dict[str, str]:
    accepted = {"approved", "review"} if include_review else {"approved"}
    with CSV.open(encoding="utf-8-sig", newline="") as stream:
        rows = [row for row in csv.DictReader(stream)
                if row["event_id"] == str(event_id) and row["estado"] in accepted
                and row["en_final"].strip()]
    return {row["japones"]: row["en_final"] for row in rows}


def stage(event_id: int, include_review: bool) -> dict:
    wanted = translations(event_id, include_review)
    if not wanted:
        raise ValueError(f"event {event_id}: no eligible English lines")
    archive = FaArchive(ARCHIVE)
    pkb = archive.read("inazuma1/data_iz/script/eve.pkb")
    pkh = archive.read("inazuma1/data_iz/script/eve.pkh")
    matches = [(offset, size) for eid, offset, size in parse_index(pkh) if eid == event_id]
    if len(matches) != 1:
        raise ValueError(f"event {event_id}: expected one archive entry, found {len(matches)}")
    offset, size = matches[0]
    original = decompress(pkb[offset:offset + size])
    code_end, instructions, records = ssd.parse(original)
    replacements = {}
    report = []
    matched = set()
    for index, record in enumerate(records):
        if record.argument != 1 or instructions[record.instruction] != 0x301d:
            continue
        japanese = record.body.decode("shift_jis")
        legacy = decode_cadena(record.raw[2:].split(b"\0", 1)[0], "sjis")
        key = legacy if legacy in wanted else japanese if japanese in wanted else None
        if key is None:
            continue
        matched.add(key)
        english = approved_layout(wanted[key], layout)
        try:
            body = encode_fullwidth(english)
            ssd.replace(original, {index: body})
        except (ValueError, UnicodeError) as exc:
            raise ValueError(f"event {event_id}, record {index}: {exc}") from exc
        replacements[index] = body
        report.append({"record": index, "source_sha256": hashlib.sha256(record.raw).hexdigest(),
                       "bytes": len(body), "text": english})
    missing = sorted(set(wanted) - matched)
    if missing:
        raise ValueError(f"event {event_id}: {len(missing)} English keys did not match dialogue records")
    changed = ssd.replace(original, replacements)
    if changed[32:code_end] != original[32:code_end]:
        raise ValueError("instruction bytecode changed")
    if changed == original:
        raise ValueError("no SSD records changed")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{event_id}.ssd").write_bytes(changed)
    summary = {"event": event_id, "records_changed": len(replacements),
               "original_bytes": len(original), "staged_bytes": len(changed),
               "includes_review": include_review, "records": report}
    (OUT / f"{event_id}.report.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", type=int, required=True)
    parser.add_argument("--include-review", action="store_true",
                        help="Stage review entries for a diagnostic candidate")
    args = parser.parse_args()
    try:
        result = stage(args.event, args.include_review)
    except (OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    print(f"IE1 event {result['event']}: {result['records_changed']} records staged in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
