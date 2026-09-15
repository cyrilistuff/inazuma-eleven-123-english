import sys,json,hashlib
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from fa_unpack import FaArchive
from pkb_unpack import parse_index
from lz10 import decompress
import ssd_records as S
from dialogue_typography import encode_fullwidth
from dialogue_lock import approved_layout
from build_ie1_probe import layout

def get(a,p):
 _,o,n=next(e for e in a.entries if e[0]==p); return bytes(a.d[o:o+n])
base='inazuma1/data_iz/script/'
orig=FaArchive('work/shared/base_3ds/romfs/archive.fa'); new=FaArchive('work/shared/candidatas/probe_ie1_v21/archive.fa')
idx0=parse_index(get(orig,base+'mch.pkh')); idx1=parse_index(get(new,base+'mch.pkh'))
assert len(idx0)==len(idx1)
for a,b in zip(idx0,idx1): assert a[0]==b[0]
eid=94001500
_,o,n=next(e for e in idx0 if e[0]==eid); _,o1,n1=next(e for e in idx1 if e[0]==eid)
xb=decompress(get(orig,base+'mch.pkb')[o:o+n]); yb=decompress(get(new,base+'mch.pkb')[o1:o1+n1])
end0,ins0,rows0=S.parse(xb); end1,ins1,rows1=S.parse(yb)
assert xb[32:end0]==yb[32:end1] and len(rows0)==len(rows1)
visible=[]; jp=[]
for i,(a,b) in enumerate(zip(rows0,rows1)):
 assert a.instruction==b.instruction and a.argument==b.argument
 if ins0.get(a.instruction)==0x301d and a.argument==1:
  visible.append(i); txt=b.body.decode('shift_jis','replace')
  if any('\u3040'<=c<='\u30ff' or '\u4e00'<=c<='\u9fff' for c in txt): jp.append((i,txt))
assert len(visible)==143 and not jp
mapping=json.loads(Path('translation/ie1/match_94001500.json').read_text(encoding='utf-8'))
assert rows1[24].body==encode_fullwidth(approved_layout(mapping['records']['24'], layout))
origpkb=get(orig,base+'mch.pkb'); newpkb=get(new,base+'mch.pkb'); unchanged=0
for (e,o,n),(ee,oo,nn) in zip(idx0,idx1):
 if e==eid: continue
 assert decompress(origpkb[o:o+n])==decompress(newpkb[oo:oo+nn]); unchanged+=1
font_hashes={
 'font/FONT12.bcfnt':'db74945637301e74d8d36248626b4cc3e88c794a33e3d439dbb7ab813e9ff2e3',
 'font/FONT12T.bcfnt':'71c37509f0eec6c092ea75f373667b0bf1f19389c45b1741a89a8f53270164ab',
 'font/FONT8.bcfnt':'b05e64c84cb564a98bea87cbdc94454f14f3df17e78252edf5a32be43ce454dd',
 'inazuma1/data_iz/font/FONT12.NFTR':'b43cfc73407c928272a001f04b85380976348e30da528b5938a3e45b87ea85c7',
 'inazuma1/data_iz/font/FONT8.NFTR':'6f683a8cef209d6e9eb9b31be5cadaad5eb90bf5ccd5e5c01c40afdf89984865',
}
for f,h in font_hashes.items():
 assert hashlib.sha256(get(new,f)).hexdigest()==h,f
sha=hashlib.sha256(Path('work/shared/candidatas/probe_ie1_v21/archive.fa').read_bytes()).hexdigest()
report={'archive_sha256':sha,'mch_event':eid,'mch_visible_records':len(visible),'mch_japanese_visible_records':len(jp),'mch_other_events_unchanged':unchanged,'instructions_unchanged_for_royal_event':True,'approved_fonts_hashes':True,'runtime_verified':False}
Path('work/shared/candidatas/probe_ie1_v21/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
