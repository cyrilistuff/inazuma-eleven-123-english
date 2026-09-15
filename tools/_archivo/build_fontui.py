#!/usr/bin/env python3
"""[Diagnostico] archive_es.fa = original + SOLO fuentes (sin tocar eve.pkb).

Para aislar si el cuelgue viene de la reinsercion del dialogo. Despues correr
ui_insert.py (UI) y build_3ds.py. NO modifica los scripts de evento.
"""
import os
import shutil
import sys

sys.path.insert(0, "tools")
from fa_unpack import FaArchive
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


for fp in FONTS:
    o, s = find(fp)
    patched = patch_font_bytes(os.path.join(REPO, "work", "fa_extract", *fp.split("/")))
    assert len(patched) == s
    data[o:o + s] = patched
open(DST, "wb").write(data)
print("archive_es.fa = original + solo fuentes (sin dialogo). Ahora: ui_insert + build.")
