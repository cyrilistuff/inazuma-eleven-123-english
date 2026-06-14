#!/usr/bin/env python3
"""[Longitud VARIABLE] Reempaqueta archive.fa sustituyendo el/los eve.pkb + eve.pkh
por las versiones de tamano VARIABLE (work/eve_var/<game>.pkb/.pkh).

Estrategia eficiente: NO se reescribe 1,3 GB. Se **anaden** los archivos nuevos
(mas grandes) al FINAL del contenedor y se redirige su FileEntry (formato B123 tiene
dataOffset explicito por archivo). El dato viejo queda como hueco muerto. Solo se
parchean unos pocos FileEntry (off+size). El contenedor crece lo justo.

Uso: python tools/fa_repack.py <archive_in.fa> <archive_out.fa>
     (lee work/eve_var/game1.pkb/.pkh y game2.* si existen)
"""
import os, struct, sys
sys.path.insert(0, "tools")
from fa_unpack import FaArchive

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fe_offset_of(arc, suffix):
    """offset BYTE del FileEntry (16B) cuyo path acaba en `suffix`, y (data_off, size)."""
    d = arc.d
    for i in range(arc.de_cnt):
        o = arc.de_off + i * 24
        file_count = struct.unpack_from("<H", d, o + 4)[0]
        name_base = struct.unpack_from("<I", d, o + 8)[0]
        first_file = struct.unpack_from("<I", d, o + 12)[0]
        dir_name_off = struct.unpack_from("<I", d, o + 20)[0]
        dir_path = arc._name(dir_name_off)
        for j in range(file_count):
            fo = arc.fe_off + (first_file + j) * 16
            name_rel = struct.unpack_from("<I", d, fo + 4)[0]
            fname = arc._name(name_base + name_rel)
            if (dir_path + fname).endswith(suffix):
                return fo
    return None


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "work", "archive_es.fa")
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "work", "archive_var.fa")
    var = os.path.join(REPO, "work", "eve_var")
    arc = FaArchive(src)
    out = bytearray(arc.d)                       # copia del contenedor base (fuentes/UI ya parcheadas)
    data_off = arc.data_off

    replaced = []
    for game, folder in (("game1", "inazuma1"), ("game2", "inazuma2")):
        for ext in ("pkb", "pkh"):
            newpath = os.path.join(var, f"{game}.{ext}")
            if not os.path.exists(newpath):
                continue
            suffix = f"{folder}/data_iz/script/eve.{ext}"
            fo = fe_offset_of(arc, suffix)
            if fo is None:
                print(f"  AVISO: no encontrado {suffix}"); continue
            newdata = open(newpath, "rb").read()
            while len(out) % 16:                  # alineacion 16 (segura para Level-5)
                out += b"\x00"
            new_abs = len(out)
            out += newdata
            struct.pack_into("<I", out, fo + 8, new_abs - data_off)   # file_off (rel a data_off)
            struct.pack_into("<I", out, fo + 12, len(newdata))        # size
            replaced.append((suffix, len(newdata)))

    open(dst, "wb").write(out)
    print(f"archive base {len(arc.d)} -> {len(out)} (+{len(out)-len(arc.d)} bytes)")
    for s, n in replaced:
        print(f"  reemplazado {s}: {n} bytes (anadido al final, entrada redirigida)")
    print(f"-> {dst}")


if __name__ == "__main__":
    main()
