"""Build a local IE1-only LayeredFS diagnostic archive with proper SSD records.

Usage: python tools/build_ie1_probe.py --events 92010100 92010200
Only dialogue opcode 0x301d, argument 1 is translated. Code and ruby arguments
remain intact. This is a diagnostic candidate, not a release or stability claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct

from fa_unpack import FaArchive
from fa_repack import fe_offset_of
from font_patch import patch_font_bytes, Font
from lz10 import decompress, compress
from pkb_unpack import parse_index, _decode_string
import reinsert as R
import ssd_records as S
from dialogue_typography import encode_fullwidth
from dialogue_lock import validate as validate_dialogue_lock, approved_layout

ROOT = Path(__file__).resolve().parents[1]


def layout(text, advance=None, width=R.BOX_W):
    """Wrap at word boundaries using FONT12 pixel advances, three lines per page."""
    advance = advance or R._advance
    text = re.sub(r"%[1-9]F", "", text)
    pages = []
    for page in text.split(r"\f"):
        prose = " ".join(page.replace(r"\n", " ").split())
        lines, current, used = [], [], 0
        for word in prose.split():
            size = sum(advance(ch) for ch in word)
            if size > width:
                raise ValueError("unbreakable word exceeds pixel line width")
            space = advance(" ") if current else 0
            if current and used + space + size > width:
                lines.append(" ".join(current))
                current, used, space = [], 0, 0
            current.append(word)
            used += space + size
        if current:
            lines.append(" ".join(current))
        pages.extend(r"\n".join(lines[i:i+3]) for i in range(0,len(lines),3))
    return r"\f".join(pages)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--events', nargs='+', type=int, required=True)
    ap.add_argument('--fullwidth', action='store_true', help='Experimental NFTR-compatible Latin glyphs')
    ap.add_argument('--reviewed-json', type=Path, help='Local, source-hashed record overrides')
    ap.add_argument('--extra-files', type=Path, help='Local archive-relative verified replacement files')
    ap.add_argument('--output', type=Path, default=ROOT/'work/probe_ie1/archive.fa')
    opts = ap.parse_args()
    validate_dialogue_lock(opts.fullwidth, opts.extra_files, layout)
    reviewed = json.loads(opts.reviewed_json.read_text(encoding='utf-8')) if opts.reviewed_json else {}
    explicit = {(int(eid), row['index']): row for eid, rows in reviewed.get('records', {}).items() for row in rows}
    reviewed_only = set(reviewed.get('reviewed_only', []))
    seen_explicit = set()
    if any(eid not in opts.events for eid, _ in explicit):
        ap.error('reviewed event not selected')
    source = ROOT/'work/shared/base_3ds/romfs/archive.fa'
    if opts.output.resolve() == source.resolve():
        ap.error('output must not overwrite the original archive')
    arc = FaArchive(str(source))
    def get(suffix):
        p,o,n = next(e for e in arc.entries if e[0].endswith(suffix))
        return bytes(arc.d[o:o+n])
    suffix = 'inazuma1/data_iz/script/eve.'
    pkb, pkh = get(suffix+'pkb'), get(suffix+'pkh')
    index = parse_index(pkh)
    known = {eid for eid,_,_ in index}
    if set(opts.events)-known:
        ap.error('unknown event IDs')
    translations = R.load_translations('game1')
    report = {'events':opts.events,'translated':[], 'rejected':[], 'missing':[]}
    output = bytearray()
    new_index = []
    for eid,offset,size in index:
        compressed = pkb[offset:offset+size]
        if eid in opts.events:
            original = decompress(compressed)
            end, instructions, records = S.parse(original)
            replacements = {}
            for i,record in enumerate(records):
                override = explicit.get((eid, i))
                if not override and (eid in reviewed_only or record.argument != 1 or instructions[record.instruction] != 0x301d):
                    continue
                if override:
                    if hashlib.sha256(record.raw).hexdigest() != override['source_sha256']:
                        raise ValueError('reviewed source record mismatch')
                    seen_explicit.add((eid, i))
                # Old CSV keys mistakenly included the size byte. Match that exact
                # legacy extraction locally, without treating header bytes as text.
                legacy = _decode_string(record.raw[2:].split(b'\0',1)[0], 'sjis')
                jp = record.body.decode('shift_jis')
                es = override['text'] if override else translations.get(eid,{}).get(legacy) or translations.get(eid,{}).get(jp)
                if not es:
                    report['missing'].append([eid,i])
                    continue
                try:
                    formatted = approved_layout(es, layout)
                    if override and not override.get('wrap', True):
                        formatted = es
                    body = encode_fullwidth(formatted) if opts.fullwidth else R.es_encode(formatted,1<<20)
                    # An individual trial also enforces the actual one-byte limit.
                    S.replace(original,{i:body})
                except ValueError as exc:
                    report['rejected'].append([eid,i,str(exc)])
                    continue
                replacements[i] = body
                metric = (lambda ch: 11) if opts.fullwidth else R._advance
                report['translated'].append({'event':eid,'index':i,'old_bytes':len(record.body),'new_bytes':len(body), 'text':formatted, 'line_pixels':[[sum(metric(ch) for ch in line) for line in page.split(r'\n')] for page in formatted.split(r'\f')]})
            changed = S.replace(original,replacements)
            assert changed[32:end] == original[32:end]
            compressed = compress(changed)
            assert decompress(compressed) == changed
        new_index.append((eid,len(output),len(compressed)))
        output.extend(compressed)
        output.extend(bytes((-len(output))%4))
    if seen_explicit != set(explicit):
        raise ValueError('reviewed record index not found')
    new_header = bytearray(pkh[:0x30])
    for record in new_index:
        new_header.extend(struct.pack('<III',*record))
    struct.pack_into('<I',new_header,0x10,len(new_header))
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    if opts.output.exists():
        raise FileExistsError('Choose a new output path; preserve prior QA candidates')
    shutil.copyfile(source,opts.output)
    with opts.output.open('r+b') as f:
        for ext,payload in [('pkb',output),('pkh',new_header)]:
            field = fe_offset_of(arc,suffix+ext)
            if field is None:
                raise ValueError('missing archive entry')
            f.seek(0,2)
            f.write(bytes((-f.tell())%16))
            offset=f.tell()
            f.write(payload)
            f.seek(field+8)
            f.write(struct.pack('<II',offset-arc.data_off,len(payload)))
        for font in R.FONTS:
            p,offset,size = next(e for e in arc.entries if e[0].endswith(font))
            source_font = str(ROOT/'work/fa_extract'/font)
            # FONT12T is format 9 (one byte per pixel).  The glyph editor is
            # format-11-only; keep its raster intact and adjust only its CWDH
            # advances so dialogue spacing stays consistent.
            if not opts.fullwidth and font.endswith('FONT12T.bcfnt'):
                patched = patch_font_bytes(source_font, fullwidth=False,
                                           patch_glyphs=False, letter_spacing=1)
                assert len(patched)==size
                f.seek(offset)
                f.write(patched)
                continue
            if opts.fullwidth and Font(source_font).t['fmt'] != 11:
                report.setdefault('original_fonts_preserved', []).append(font)
                continue
            spacing = 1 if (not opts.fullwidth and font.endswith('FONT12.bcfnt')) else 0
            patched=patch_font_bytes(source_font, fullwidth=opts.fullwidth,
                                     letter_spacing=spacing)
            assert len(patched)==size
            f.seek(offset)
            f.write(patched)
        if opts.extra_files:
            known_paths = {p for p, _, _ in arc.entries}
            for extra in sorted(opts.extra_files.rglob('*')):
                if not extra.is_file():
                    continue
                rel = extra.relative_to(opts.extra_files).as_posix()
                if rel not in known_paths:
                    raise ValueError('extra file not in original archive: ' + rel)
                payload = extra.read_bytes()
                field = fe_offset_of(arc, rel)
                f.seek(0, 2)
                f.write(bytes((-f.tell()) % 16))
                offset = f.tell()
                f.write(payload)
                f.seek(field+8)
                f.write(struct.pack('<II', offset-arc.data_off, len(payload)))
                report.setdefault('extra_files', []).append({'path':rel, 'sha256':hashlib.sha256(payload).hexdigest()})
    with opts.output.open('rb') as f:
        report['archive_sha256']=hashlib.file_digest(f,'sha256').hexdigest()
    report['scope']='IE1 eve.pkb/pkh plus shared Spanish font glyphs; executable unchanged'
    report['typography']='fullwidth-20-columns-experimental' if opts.fullwidth else 'ascii-bcfnt-pixels'
    opts.output.with_suffix('.report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
