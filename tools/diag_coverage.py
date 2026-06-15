#!/usr/bin/env python3
"""Diagnostico: del dialogo SIN traducir, cuanto es RECUPERABLE (el texto SI existe en los
datos de traduccion, solo no casa por eid/formato) vs GENUINAMENTE ausente (no esta).
Salida a un fichero para evitar el cp1252 de la consola."""
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

# mapa GLOBAL de todos los jp traducidos (en cualquier eid) y version NORMALIZADA
def norm(s):
    s = re.sub(r"%[0-9A-Fa-f]F", "", s)      # marcadores furigana
    s = re.sub(r"[\x00-\x1f]", "", s)         # control
    return s.replace("　", "").replace(" ", "").strip()

global_exact = set()
global_norm = {}
for eid, et in trans.items():
    for jp, es in et.items():
        global_exact.add(jp)
        global_norm[norm(jp)] = es

untr_total = 0
rec_same_eid_fmt = 0     # mismo eid existe pero formato distinto (normalizando casa)
rec_other_eid = 0        # el jp exacto existe en OTRO eid
rec_norm_global = 0      # normalizando casa en algun sitio
absent = 0
absent_ex = []
for eid, o, s in idx:
    if eid >= 90000000:   # sistema: SYS_ORIG lo deja jap aparte; lo contamos como gameplay-not
        pass
    dec = decompress(opkb[o:o + s])
    if dec[:4] != b"SSD\x00": continue
    ts = ssd_reinsert._text_start(dec)
    et = trans.get(eid, {})
    for c in dec[ts:].split(b"\x00"):
        if len(c) < 3 or c[0] not in (1, 2, 4): continue
        sj = _decode_string(c, "sjis")
        if not R.looks_like_dialogue(sj): continue
        if et.get(sj):    # ya traducida
            continue
        untr_total += 1
        nj = norm(sj)
        if any(norm(k) == nj for k in et):        # mismo eid, formato distinto
            rec_same_eid_fmt += 1
        elif sj in global_exact:                   # exacto en otro eid
            rec_other_eid += 1
        elif nj in global_norm and nj:             # normalizado en cualquier sitio
            rec_norm_global += 1
        else:
            absent += 1
            if len(absent_ex) < 25:
                absent_ex.append((eid, sj[2:50]))

out = []
out.append(f"Lineas de dialogo SIN traducir: {untr_total}")
out.append(f"  RECUPERABLE - mismo eid, solo formato distinto : {rec_same_eid_fmt}")
out.append(f"  RECUPERABLE - texto exacto existe en OTRO eid   : {rec_other_eid}")
out.append(f"  RECUPERABLE - normalizado casa en algun sitio   : {rec_norm_global}")
out.append(f"  GENUINAMENTE AUSENTE (no esta en los datos)     : {absent}")
rec = rec_same_eid_fmt + rec_other_eid + rec_norm_global
out.append(f"  => RECUPERABLE TOTAL: {rec}  ({100*rec//max(untr_total,1)}% de lo no traducido)")
out.append("")
out.append("Ejemplos GENUINAMENTE AUSENTES (eid, texto jp):")
for eid, ex in absent_ex:
    out.append(f"   {eid}  {ex!r}")
open(os.path.join(R.REPO, "work", "_diag_coverage.txt"), "w", encoding="utf-8").write("\n".join(out))
print("escrito work/_diag_coverage.txt")
