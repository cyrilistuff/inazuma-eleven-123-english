"""Static verification of a layered IE1 candidate against its base candidate.

Every entry provided by a layer must match that layer (later layers win); every
other archive entry, including fonts, must be byte-identical to the base. Only
staged SSD events may differ after decompression, and the CRO may differ only in
the declared literal slots. The v20 typography lock must pass.

Example:
  python tools/verify_candidate.py --base work/probe_ie1_v29 --candidate work/probe_ie1_v30 \
      --layer work/menu_revision/extra --layer work/submenu_revision/extra
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from fa_unpack import FaArchive  # noqa: E402
from pkb_unpack import parse_index  # noqa: E402
from lz10 import decompress  # noqa: E402
from dialogue_lock import validate  # noqa: E402
from build_ie1_probe import layout  # noqa: E402

EVE = ('inazuma1/data_iz/script/eve.pkh', 'inazuma1/data_iz/script/eve.pkb')


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--layer', type=Path, action='append', default=[])
    ap.add_argument('--events', type=Path, help='directory of staged <event>.ssd files')
    ap.add_argument('--literals', type=Path, help='JSON with entries[offset,capacity] allowed to differ in the CRO')
    args = ap.parse_args()

    validate(True, ROOT / 'work/probe_ie1_v14_inputs/extra_ascii', layout)
    base = FaArchive(str(args.base / 'archive.fa'))
    cand = FaArchive(str(args.candidate / 'archive.fa'))
    a = {p: (o, n) for p, o, n in base.entries}
    b = {p: (o, n) for p, o, n in cand.entries}
    if list(a) != list(b):
        raise SystemExit('entry list changed')
    get = lambda arc, idx, p: bytes(arc.d[idx[p][0]:idx[p][0] + idx[p][1]])

    expected = {}
    for layer in args.layer:
        for f in sorted(layer.rglob('*')):
            if f.is_file():
                expected[f.relative_to(layer).as_posix()] = f.read_bytes()
    replaced = fonts = 0
    for p in a:
        old, new = get(base, a, p), get(cand, b, p)
        if p in expected:
            if new != expected[p]:
                raise SystemExit('layer mismatch: ' + p)
            replaced += 1
        elif p in EVE:
            continue
        elif old != new:
            raise SystemExit('unexpected change: ' + p)
        if '/font/' in p or p.startswith('font/'):
            if old != new:
                raise SystemExit('font changed: ' + p)
            fonts += 1

    staged = {int(f.stem): f.read_bytes() for f in args.events.glob('*.ssd')} if args.events else {}
    ia = {e: (o, n) for e, o, n in parse_index(get(base, a, EVE[0]))}
    ib = {e: (o, n) for e, o, n in parse_index(get(cand, b, EVE[0]))}
    if list(ia) != list(ib):
        raise SystemExit('event index changed')
    pa, pb = get(base, a, EVE[1]), get(cand, b, EVE[1])
    changed_events = []
    if pa != pb or get(base, a, EVE[0]) != get(cand, b, EVE[0]):
        for eid, (o, n) in ia.items():
            o2, n2 = ib[eid]
            old, new = decompress(pa[o:o + n]), decompress(pb[o2:o2 + n2])
            if eid in staged:
                if new != staged[eid]:
                    raise SystemExit(f'staged event mismatch: {eid}')
                changed_events.append(eid)
            elif old != new:
                raise SystemExit(f'event {eid} changed')

    cro_a = (args.base / 'romfs/cro/ina_main1.cro').read_bytes()
    cro_b = (args.candidate / 'romfs/cro/ina_main1.cro').read_bytes()
    masked = bytearray(cro_b)
    literals = json.loads(args.literals.read_text(encoding='utf-8'))['entries'] if args.literals else []
    for e in literals:
        masked[e['offset']:e['offset'] + e['capacity']] = cro_a[e['offset']:e['offset'] + e['capacity']]
    if len(cro_a) != len(cro_b) or masked != cro_a:
        raise SystemExit('CRO changed outside declared literals')

    report = dict(candidate=str(args.candidate), archive_sha256=digest(args.candidate / 'archive.fa'),
                  cro_sha256=hashlib.sha256(cro_b).hexdigest(), base_sha256=digest(args.base / 'archive.fa'),
                  replaced_entries=replaced, fonts_identical_to_base=fonts, events_changed=sorted(changed_events),
                  cro_literals_changed=len(literals) if cro_a != cro_b else 0, dialogue_lock='PASS',
                  runtime_verified=False)
    (args.candidate / 'verify.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
