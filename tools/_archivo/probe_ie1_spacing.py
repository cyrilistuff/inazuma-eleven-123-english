"""Local regression candidate for the 81000090/287 classroom dialogue."""
import hashlib
import json
from pathlib import Path
import shutil
import struct

from fa_unpack import FaArchive
from fa_repack import fe_offset_of
from font_patch import Font, PLAN, patch_font_bytes
from nftr_metrics import read_metrics
from dialogue_typography import encode_fullwidth
from build_ie1_probe import layout
from pkb_unpack import parse_index
from lz10 import compress, decompress
import ssd_records as S


def main():
    root = Path(__file__).resolve().parents[1]
    output = root/'work/probe_ie1_spacing_v18'
    output.mkdir(exist_ok=True)
    target = output/'archive.fa'
    if target.exists():
        raise FileExistsError(target)
    arc = FaArchive(str(root/'work/shared/candidatas/probe_ie1_v17/archive.fa'))
    def get(path):
        _, offset, size = next(e for e in arc.entries if e[0] == path)
        return arc.d[offset:offset+size]
    font_path = root/'work/fa_extract/font/FONT12.bcfnt'
    font = Font(font_path)
    font.data[:] = patch_font_bytes(font_path, letter_spacing=1)
    nftr = bytearray(get('inazuma1/data_iz/font/FONT12.NFTR'))
    metrics, offsets = read_metrics(nftr, with_offsets=True)
    aliases=[]
    for ch, base, _, carrier in PLAN:
        code=int.from_bytes(chr(carrier).encode('shift_jis'),'big')
        if code in offsets:
            continue
        base_code=int.from_bytes(chr(ord(base)+0xfee0).encode('shift_jis'),'big')
        width_offset=offsets[base_code]
        pointer=struct.unpack_from('<I',nftr,36)[0]
        while pointer:
            pos=pointer-8
            begin,end=struct.unpack_from('<HH',nftr,pos+8)
            if pos+16 <= width_offset < pos+16+3*(end-begin+1):
                aliases.append((code,begin+(width_offset-pos-16)//3)); break
            pointer=struct.unpack_from('<I',nftr,pos+12)[0]
    if aliases:
        aliases.sort()
        old=struct.unpack_from('<I',nftr,40)[0]
        pos=len(nftr)
        block=bytearray(struct.pack('<4sIHHHHIH',b'PAMC',0,aliases[0][0],aliases[-1][0],2,0,old,len(aliases)))
        for code,gi in aliases: block.extend(struct.pack('<HH',code,gi))
        block.extend(bytes((-len(block))%4))
        struct.pack_into('<I',block,4,len(block)); nftr.extend(block)
        struct.pack_into('<I',nftr,40,pos+8); struct.pack_into('<I',nftr,8,len(nftr))
        struct.pack_into('<H',nftr,14,struct.unpack_from('<H',nftr,14)[0]+1)
        metrics,offsets=read_metrics(nftr,with_offsets=True)
    advances = {}
    # Copy the drawing as well as the bearing: the original fullwidth glyph
    # is centred in its cell, unlike the ordinary Latin drawing.
    mappings = [(chr(cp), cp, cp+0xfee0) for cp in range(33,127)]
    mappings += [(ch, carrier, carrier) for ch, _, _, carrier in PLAN]
    for ch, base, dest in mappings:
        try:
            code = int.from_bytes(chr(dest).encode('shift_jis'), 'big')
        except UnicodeEncodeError:
            continue
        if code not in offsets or dest not in font.cmap:
            continue
        source_gi, dest_gi = font.cmap[base], font.cmap[dest]
        font.write_cell(dest_gi, font.read_cell(source_gi))
        font.copy_width(source_gi, dest_gi)
        bo = font.cwdh_entry_off(source_gi)
        left, width, advance = struct.unpack_from('<bBB',font.data,bo)
        # NFTR coordinates use the original 11-pixel cells; BCFNT uses 14.
        triple = (round(left*11/14), max(1,round(width*11/14)), max(1,round(advance*11/14)))
        struct.pack_into('<bBB',nftr,offsets[code],*triple)
        advances[ch] = max(advance, triple[2]*14/11)
    space_code = 0x8140
    struct.pack_into('<bBB',nftr,offsets[space_code],0,0,4)
    space_gi=font.cmap[0x3000]
    struct.pack_into('<bBB',font.data,font.cwdh_entry_off(space_gi),0,0,5)
    advances[' '] = 4*14/11
    reviewed=json.loads((root/'work/probe_ie1_v14_inputs/reviewed.json').read_text(encoding='utf-8'))
    row=next(r for r in reviewed['records']['81000090'] if r['index']==287)
    def advance(c):
        if c in advances:
            return advances[c]
        off=font.cwdh_entry_off(font.cmap[ord(c)])
        return font.data[off+2]
    text=layout(row['text'],advance=advance,width=184)
    body=encode_fullwidth(text)
    prefix='inazuma1/data_iz/script/eve.'
    pkb=bytearray(get(prefix+'pkb')); pkh=bytearray(get(prefix+'pkh'))
    for i,(eid,off,size) in enumerate(parse_index(pkh)):
        if eid != 81000090:
            continue
        original=decompress(pkb[off:off+size])
        changed=S.replace(original,{287:body})
        end,_,before=S.parse(original); _,_,after=S.parse(changed)
        assert original[32:end] == changed[32:end]
        assert all(a.raw==b.raw for n,(a,b) in enumerate(zip(before,after)) if n!=287)
        packed=compress(changed)
        assert decompress(packed)==changed
        struct.pack_into('<III',pkh,0x30+i*12,eid,len(pkb),len(packed))
        pkb.extend(packed)
        break
    replacements={prefix+'pkb':pkb,prefix+'pkh':pkh,'font/FONT12.bcfnt':font.data,'inazuma1/data_iz/font/FONT12.NFTR':nftr}
    shutil.copyfile(root/'work/shared/candidatas/probe_ie1_v17/archive.fa',target)
    with target.open('r+b') as f:
        for path,data in replacements.items():
            f.seek(0,2); f.write(bytes((-f.tell())%16)); off=f.tell(); f.write(data)
            f.seek(fe_offset_of(arc,path)+8); f.write(struct.pack('<II',off-arc.data_off,len(data)))
    with target.open('rb') as f:
        digest=hashlib.file_digest(f,'sha256').hexdigest()
    report={'event':81000090,'record':287,'text':text,'payload_bytes':len(body),'archive_sha256':digest,'runtime_verified':False,'scope':'Single classroom dialogue; paired FONT12 Latin transport, glyphs and advances. Other dialogue records unchanged.'}
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True,indent=2))


if __name__=='__main__':
    main()
