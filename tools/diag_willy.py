#!/usr/bin/env python3
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
idx = {e: (o, s) for e, o, s in parse_index(bytes(data[find("inazuma1/data_iz/script/eve.pkh")[0]:find("inazuma1/data_iz/script/eve.pkh")[0]+find("inazuma1/data_iz/script/eve.pkh")[1]]))}
opkb = bytes(data[po:po + ps])
trans = R.load_translations("game1")
gexact = {}
for et in trans.values():
    gexact.update(et)

out = []
# dump del evento Willy (92010250) y vecinos del area escolar inicial
for eid in (92010250, 92010240, 92010260, 92010200, 92010100):
    if eid not in idx:
        out.append(f"--- {eid}: NO EXISTE ---"); continue
    o, s = idx[eid]; dec = decompress(opkb[o:o + s])
    if dec[:4] != b"SSD\x00": continue
    ts = ssd_reinsert._text_start(dec); et = trans.get(eid, {})
    out.append(f"--- {eid} ({'SISTEMA' if eid>=90000000 else 'gameplay'}) ---")
    for c in dec[ts:].split(b"\x00"):
        if len(c) < 3 or c[0] not in (1, 2, 4): continue
        sj = _decode_string(c, "sjis")
        if not R.looks_like_dialogue(sj): continue
        per = bool(et.get(sj)); glob = sj in gexact
        mark = "ES-perEvento" if per else ("ES-global" if glob else "SIN-TRADUCCION")
        out.append(f"   [{mark}] {sj[2:46]!r}")

open(os.path.join(R.REPO, "work", "_diag_willy.txt"), "w", encoding="utf-8").write("\n".join(out))
print("escrito work/_diag_willy.txt")
