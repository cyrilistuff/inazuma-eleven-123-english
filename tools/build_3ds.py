#!/usr/bin/env python3
"""[Etapa 8] Construye el .3ds parcheado (parche in-place de archive.fa) + xdelta.

archive.fa parcheado (work/archive_es.fa) tiene el MISMO tamano que el original, asi
que se sobrescribe in-place en una copia del .3ds, sin tocar offsets/estructura. Los
hashes IVFC/NCCH quedan desactualizados; Citra/Lime3DS/Azahar suelen ignorarlos
(si no, ver README: rebuild con 3dstool).

Salida: work/build/inazuma123_es.3ds + patch/inazuma123-es.xdelta (este SI se versiona).
"""
import os
import shutil
import struct
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM = os.path.join(REPO, "roms", "Inazuma Eleven 1-2-3 - Endou Mamoru Densetsu.3ds")
FA_ES = os.path.join(REPO, "work", "archive_es.fa")
_VER = sys.argv[1] if len(sys.argv) > 1 else ""
_SUF = f"_{_VER}" if _VER else ""
OUT = os.path.join(REPO, "work", "build", f"inazuma123_es{_SUF}.3ds")
PATCH = os.path.join(REPO, "patch", f"inazuma123-es{('-' + _VER) if _VER else ''}.xdelta")
XDELTA = os.path.join(REPO, "tools", "bin", "xdelta3.exe")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    # localizar offset de archive.fa en el .3ds
    head = open(FA_ES, "rb").read(32)
    fa_size = os.path.getsize(FA_ES)
    import mmap
    with open(ROM, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        off = mm.find(head)
        mm.close()
    if off < 0:
        raise SystemExit("no se encontro archive.fa en el .3ds")
    print(f"archive.fa @0x{off:X} en el .3ds; tamano {fa_size}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    print("copiando ROM base...")
    shutil.copyfile(ROM, OUT)
    print("sobrescribiendo archive.fa parcheado in-place...")
    with open(OUT, "r+b") as out, open(FA_ES, "rb") as fa:
        out.seek(off)
        while True:
            chunk = fa.read(8 << 20)
            if not chunk:
                break
            out.write(chunk)
    print(f"-> {OUT}")

    os.makedirs(os.path.dirname(PATCH), exist_ok=True)
    print("generando xdelta...")
    r = subprocess.run([XDELTA, "-e", "-f", "-s", ROM, OUT, PATCH],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("xdelta fallo: " + r.stderr)
    print(f"-> {PATCH}  ({os.path.getsize(PATCH)} bytes)")


if __name__ == "__main__":
    main()
