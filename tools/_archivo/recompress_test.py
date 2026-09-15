#!/usr/bin/env python3
"""[Diagnostico v9] eve.pkb del juego 1 RECOMPRIMIDO sin cambiar el texto + fuente.

Aisla si el cuelgue lo causa MI compresor LZ10 (vs el texto). Si v9 (igual que v7
pero con eve.pkb recomprimido sin tocar) tambien se cuelga -> el compresor produce
un stream que el juego no descomprime igual. Luego: ui_insert + build_3ds v9.
"""
import os
import shutil
import struct
import sys

sys.path.insert(0, "tools")
from fa_unpack import FaArchive
from lz10 import decompress, compress
from pkb_unpack import parse_index
from font_patch import patch_font_bytes

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "work", "shared", "base_3ds", "romfs", "archive.fa")
DST = os.path.join(REPO, "work", "archive_es.fa")
FONTS = ["font/FONT12T.bcfnt", "font/FONT12.bcfnt", "font/FONT8.bcfnt"]

shutil.copyfile(SRC, DST)
data = bytearray(open(DST, "rb").read())
arc = FaArchive(SRC)


def find(suf):
    for p, o, s in arc.entries:
        if p.endswith(suf):
            return o, s


po, ps = find("inazuma1/data_iz/script/eve.pkb")
ho, hs = find("inazuma1/data_iz/script/eve.pkh")
pkb = bytearray(data[po:po + ps])
ents = parse_index(bytes(data[ho:ho + hs]))
n = bad = 0
for eid, off, sz in ents:
    dec = decompress(bytes(pkb[off:off + sz]))
    comp = compress(dec)
    if decompress(comp) != dec:
        bad += 1
        continue
    if len(comp) <= sz:
        pkb[off:off + sz] = comp + b"\x00" * (sz - len(comp))
        n += 1
data[po:po + ps] = pkb
print(f"eventos recomprimidos sin cambiar: {n}  (roundtrip fallido: {bad})")

for fp in FONTS:
    o, s = find(fp)
    patched = patch_font_bytes(os.path.join(REPO, "work", "fa_extract", *fp.split("/")))
    data[o:o + s] = patched
open(DST, "wb").write(data)
print("archive_es.fa = original + fuente + eve.pkb(g1) recomprimido SIN cambios.")
