#!/usr/bin/env python3
"""Lista los eventos de SISTEMA (eid>=90000000) a los que el fallback GLOBAL AÑADE traduccion
(per-evento no la tiene). Son los que cambian entre INTRO_ES (global off sistema) y MAX_ES (on,
que congelaba). Ordenados por eid -> ver el cluster de apertura/crear-partida a proteger."""
import sys, os
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
gexact = {}
for et in trans.values():
    gexact.update(et)

rows = []
for eid, o, s in idx:
    if eid < 90000000:
        continue
    dec = decompress(opkb[o:o + s])
    if dec[:4] != b"SSD\x00": continue
    ts = ssd_reinsert._text_start(dec)
    et = trans.get(eid, {})
    added = 0; sample = ""
    for c in dec[ts:].split(b"\x00"):
        if len(c) < 3 or c[0] not in (1, 2, 4): continue
        sj = _decode_string(c, "sjis")
        if not R.looks_like_dialogue(sj): continue
        if not et.get(sj) and sj in gexact:    # global AÑADE
            added += 1
            if not sample: sample = sj[2:30]
    if added:
        rows.append((eid, added, sample))

rows.sort()
out = [f"Eventos de SISTEMA donde el GLOBAL añade traduccion ({len(rows)} eventos):"]
for eid, n, s in rows:
    out.append(f"   {eid}  +{n} lineas  {s!r}")
open(os.path.join(R.REPO, "work", "_diag_sysglobal.txt"), "w", encoding="utf-8").write("\n".join(out))
print(f"escrito work/_diag_sysglobal.txt ({len(rows)} eventos)")
