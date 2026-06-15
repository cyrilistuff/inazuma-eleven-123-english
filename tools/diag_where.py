#!/usr/bin/env python3
import sys, os, re
sys.path.insert(0, "tools")
import ssd_reinsert
import reinsert as R
from fa_unpack import FaArchive
from pkb_unpack import parse_index, _decode_string
from lz10 import decompress

arc = FaArchive(os.path.join(R.REPO, "work", "romfs", "archive.fa")); data = arc.d
def find(s):
    for p, o, sz in arc.entries:
        if p.endswith(s): return o, sz
po, ps = find("inazuma1/data_iz/script/eve.pkb"); ho, hs = find("inazuma1/data_iz/script/eve.pkh")
idx = parse_index(bytes(data[ho:ho + hs])); opkb = bytes(data[po:po + ps])
trans = R.load_translations("game1")
gexact = set()
for et in trans.values():
    gexact.update(et)

# 1) split sistema/gameplay de las RECUPERABLES (untrad cuyo jp existe en otro evento)
rec_sys = rec_gpl = 0
# 2) localizar las frases de las capturas
needles = ["やろうぜ", "このままじゃダメ", "野球場", "練習を始め"]
found = []
for eid, o, s in idx:
    dec = decompress(opkb[o:o + s])
    if dec[:4] != b"SSD\x00": continue
    ts = ssd_reinsert._text_start(dec)
    et = trans.get(eid, {})
    for c in dec[ts:].split(b"\x00"):
        if len(c) < 3 or c[0] not in (1, 2, 4): continue
        sj = _decode_string(c, "sjis")
        if not R.looks_like_dialogue(sj): continue
        for nd in needles:
            if nd in sj:
                has_tr = bool(et.get(sj)) or (sj in gexact)
                found.append((eid, nd, has_tr, eid >= 90000000))
        if not et.get(sj) and sj in gexact:
            if eid >= 90000000: rec_sys += 1
            else: rec_gpl += 1

out = []
out.append(f"RECUPERABLES (jp traducido en otro evento) por zona:")
out.append(f"   en eventos de SISTEMA (>=9000, SYS_ORIG=jap): {rec_sys}")
out.append(f"   en eventos de GAMEPLAY (<9000, si se aplican): {rec_gpl}")
out.append("")
out.append("Frases de las capturas -> en que evento y si hay traduccion:")
for eid, nd, has_tr, is_sys in found:
    out.append(f"   {nd!r}: eid={eid}  {'SISTEMA' if is_sys else 'gameplay'}  traduccion_disponible={has_tr}")
open(os.path.join(R.REPO, "work", "_diag_where.txt"), "w", encoding="utf-8").write("\n".join(out))
print("escrito work/_diag_where.txt")
