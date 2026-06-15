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
idx = {e: (o, s) for e, o, s in parse_index(bytes(data[ho:ho + hs]))}
opkb = bytes(data[po:po + ps])
trans = R.load_translations("game1")

out = []
eid = 92010250; o, s = idx[eid]; dec = decompress(opkb[o:o + s])
ts = ssd_reinsert._text_start(dec); et = trans.get(eid, {})
for c in dec[ts:].split(b"\x00"):
    if len(c) < 3 or c[0] not in (1, 2, 4): continue
    sj = _decode_string(c, "sjis")
    if not R.looks_like_dialogue(sj): continue
    es = et.get(sj)
    if not es: continue
    if not R._MK.search(c):
        out.append(f"[PLANA, ok] {sj[2:30]!r}"); continue
    # furigana: ver si _furigana_body_bytes la acepta o la rechaza
    orig_body = c[2:]
    budget = len(c) - 2
    res = R._furigana_body_bytes(orig_body, es, budget)
    jp_pages = orig_body.split(b"\\f"); es_pages = es.split("\\f")
    status = "RECHAZADA->japones" if res is None else f"OK ({len(res)}/{budget}B)"
    fit = "" if res is not None else (" (paginas jp=%d es=%d)" % (len(jp_pages), len(es_pages)))
    out.append(f"[{status}{fit}]")
    out.append(f"     jp: {sj[2:50]!r}")
    out.append(f"     es: {es[:50]!r}")

open(os.path.join(R.REPO, "work", "_diag_inplace.txt"), "w", encoding="utf-8").write("\n".join(out))
print("escrito work/_diag_inplace.txt")
