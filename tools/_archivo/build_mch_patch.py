from pathlib import Path
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from fa_unpack import FaArchive
from lz10 import compress, decompress
from pkb_unpack import parse_index
import ssd_records as S
from dialogue_typography import encode_fullwidth
from dialogue_lock import validate as validate_dialogue_lock, approved_layout
from build_ie1_probe import layout

EVENT_ID = 94001500
PACKAGE = 'inazuma1/data_iz/script/mch.'
MAPPING = ROOT / 'translation' / 'ie1' / 'match_94001500.json'


def _entry(arc, suffix):
    path, offset, size = next(e for e in arc.entries if e[0].endswith(suffix))
    return path, bytes(arc.d[offset:offset + size])


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Generate the IE1 Royal Academy match SSD patch.')
    ap.add_argument('--extra-files', type=Path, required=True,
                    help='LayeredFS extra root containing the approved fonts')
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    extra = args.extra_files.resolve()
    validate_dialogue_lock(True, extra, layout)
    mapping = json.loads(MAPPING.read_text(encoding='utf-8'))
    if int(mapping['event_id']) != EVENT_ID:
        raise ValueError('mapping event_id mismatch')
    translations = {int(k): v for k, v in mapping['records'].items()}

    arc = FaArchive(str(ROOT / 'work' / 'shared' / 'base_3ds' / 'romfs' / 'archive.fa'))
    _, pkh = _entry(arc, PACKAGE + 'pkh')
    _, pkb = _entry(arc, PACKAGE + 'pkb')
    index = parse_index(pkh)
    selected = next((e for e in index if e[0] == EVENT_ID), None)
    if selected is None:
        raise ValueError(f'event {EVENT_ID} not found in mch.pkh')
    _, offset, size = selected
    original = decompress(pkb[offset:offset + size])
    _, instructions, records = S.parse(original)
    visible = {i for i, record in enumerate(records)
               if instructions.get(record.instruction) == 0x301d and record.argument == 1}
    if visible != set(translations):
        missing = sorted(visible - set(translations))
        extra_indices = sorted(set(translations) - visible)
        raise ValueError(f'mapping mismatch: missing={missing}, extra={extra_indices}')

    replacements = {}
    line_pixels = {}
    for i, text in translations.items():
        formatted = approved_layout(text, layout)
        body = encode_fullwidth(formatted)
        S.replace(original, {i: body})
        replacements[i] = body
        line_pixels[i] = [[11 * len(line) for line in page.split(r'\n')]
                          for page in formatted.split(r'\f')]
    changed = S.replace(original, replacements)
    compressed_changed = compress(changed)
    assert decompress(compressed_changed) == changed

    output = bytearray()
    new_index = []
    for eid, off, n in index:
        payload = compressed_changed if eid == EVENT_ID else pkb[off:off + n]
        new_index.append((eid, len(output), len(payload)))
        output.extend(payload)
        output.extend(bytes((-len(output)) % 4))
    new_header = bytearray(pkh[:0x30])
    for record in new_index:
        new_header.extend(struct.pack('<III', *record))
    new_header.extend(pkh[0x30 + len(index) * 12:])
    if len(new_header) != len(pkh):
        raise AssertionError('mch.pkh size changed')

    pkh_out = extra / (PACKAGE + 'pkh')
    pkb_out = extra / (PACKAGE + 'pkb')
    pkh_out.parent.mkdir(parents=True, exist_ok=True)
    pkh_out.write_bytes(new_header)
    pkb_out.write_bytes(output)
    report = {
        'event_id': EVENT_ID,
        'records': len(translations),
        'source_event_sha256': hashlib.sha256(original).hexdigest(),
        'translated_event_sha256': hashlib.sha256(changed).hexdigest(),
        'mch_pkh_sha256': hashlib.sha256(new_header).hexdigest(),
        'mch_pkb_sha256': hashlib.sha256(output).hexdigest(),
        'line_pixels': line_pixels,
        'scope': 'IE1 mch.pkb/pkh: Royal Academy story match event only',
        'typography': 'approved-v20-fullwidth-20-columns',
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'event_id': EVENT_ID, 'records': len(translations),
                      'mch_pkb_bytes': len(output), 'mch_pkh_bytes': len(new_header)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
