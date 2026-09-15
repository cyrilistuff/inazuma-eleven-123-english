"""Read-only comparison of NDS voiced events with candidate SSD records.

Full text stays in ignored work/. Matching owner IDs is diagnostic, not proof
that the corresponding opcodes and audio calls have the same semantics.
"""
import json
import re
import struct
import unicodedata
from pathlib import Path
from ds_official import load_ds_events, decode_ds
from fa_unpack import FaArchive
from pkb_unpack import parse_index
from lz10 import decompress
from ssd_records import parse
from dialogue_typography import ACCENTS

ROOT = Path(__file__).resolve().parents[1]


def nds_records(data):
    if struct.unpack_from('<I', data)[0] != len(data) - 4:
        raise ValueError('unexpected evet length')
    pos, result = 4, {}
    while pos < len(data):
        owner, argument, length = struct.unpack_from('<HHI', data, pos)
        if length < 12 or pos + length > len(data):
            raise ValueError('invalid evet record')
        result[owner, argument] = decode_ds(data[pos+8:pos+length].split(b'\0', 1)[0])
        pos += length
    return result


def normalize(text):
    for original, transported in ACCENTS.items():
        text = text.replace(transported, original)
    text = unicodedata.normalize('NFKC', text)
    return re.sub(r'\s+', '', text.replace('\\n', '').replace('\\f', ''))


def voice_name(text):
    return re.fullmatch(r'\d{2}_\d+\.SAD', text, re.I) is not None


def main():
    archive = FaArchive(str(ROOT / 'work/probe_ie1_v35/archive.fa'))
    files = {p: bytes(archive.d[o:o+s]) for p,o,s in archive.entries
             if p in ('inazuma1/data_iz/script/eve.pkb', 'inazuma1/data_iz/script/eve.pkh')}
    stem = 'inazuma1/data_iz/script/eve'
    nds = load_ds_events('game1')
    report = []
    for eid, offset, size in parse_index(files[stem+'.pkh']):
        chunk = files[stem+'.pkb'][offset:offset+size]
        data = decompress(chunk) if chunk[:1] == b'\x10' else chunk
        _, ops, records = parse(data)
        voices = [r.body.decode('ascii') for r in records
                  if voice_name(r.body.decode('ascii', errors='replace'))]
        if not voices:
            continue
        ds = nds_records(nds[eid]) if eid in nds else {}
        pairs = []
        for voice in voices:
            ds_calls = [owner for (owner,arg),text in ds.items() if text.upper()==voice.upper()]
            ctr_calls = [r.instruction for r in records if r.body.decode('ascii',errors='replace').upper()==voice.upper()]
            if len(ds_calls)!=1 or len(ctr_calls)!=1:
                raise ValueError(f'ambiguous voice call {eid} {voice}')
            candidates = [(i,r) for i,r in enumerate(records) if r.instruction>ctr_calls[0]
                          and ops.get(r.instruction)==0x301d and r.argument==1]
            i,r = min(candidates,key=lambda item:item[1].instruction)
            ds_dialogue = [(owner,text) for (owner,arg),text in ds.items()
                           if owner>ds_calls[0] and arg==1]
            ds_owner,source = min(ds_dialogue)
            # A later movie or another voice call is not this voice's subtitle.
            boundary = min((owner for (owner,arg),text in ds.items()
                            if owner>ds_calls[0] and
                            (voice_name(text) or re.fullmatch(r'am\d+|op\d+',text))), default=10**9)
            if ds_owner >= boundary:
                source = None
            current = r.body.decode('shift_jis', errors='replace')
            pairs.append({'voice':voice,'record':i,'instruction':r.instruction,
                          'nds_instruction':ds_owner,'current':current,
                          'nds':source,'same_normalized':source is not None and normalize(source)==normalize(current)})
        report.append({'event':eid,'voices':voices,'dialogue':pairs})
    target = ROOT/'work/volumen_1/ie1_media_mod/voiced_text_audit.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    pairs=[p for e in report for p in e['dialogue']]
    print(json.dumps({'events_with_SAD':len(report),'dialogue_records':len(pairs),
                      'same_owner_found':sum(p['nds'] is not None for p in pairs),
                      'same_normalized':sum(p['same_normalized'] for p in pairs),
                      'report':str(target)}))


if __name__ == '__main__':
    main()
