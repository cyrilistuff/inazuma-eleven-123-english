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
idx = parse_index(bytes(data[ho:ho + hs])); opkb = bytes(data[po:po + ps])
trans = R.load_translations("game1")
gexact = {}
for et in trans.values():
    gexact.update(et)

needles = ["そんなに急いで", "学校の生活を", "あいてるみたいだ", "ドコに行く", "記録すること"]
out = []
for eid, o, s in idx:
    dec = decompress(opkb[o:o + s])
    if dec[:4] != b"SSD\x00": continue
    ts = ssd_reinsert._text_start(dec)
    et = trans.get(eid, {})
    for c in dec[ts:].split(b"\x00"):
        if len(c) < 3 or c[0] not in (1, 2, 4): continue
        sj = _decode_string(c, "sjis")
        for nd in needles:
            if nd in sj:
                per = bool(et.get(sj))
                glob = sj in gexact
                out.append(f"eid={eid} {'SISTEMA' if eid>=90000000 else 'gameplay'} | por-evento={per} global={glob} | {sj[2:38]!r}")
# tambien: rango de eids de sistema con traduccion SOLO global (candidatos a activar)
sys_global_only = sorted({eid for eid, o, s in idx if eid >= 90000000
                          for c in [None]})  # placeholder
open(os.path.join(R.REPO, "work", "_diag_find.txt"), "w", encoding="utf-8").write("\n".join(out) if out else "NO ENCONTRADO")
print("escrito work/_diag_find.txt")
