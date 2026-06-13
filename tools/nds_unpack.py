#!/usr/bin/env python3
"""Extractor minimo del sistema de archivos de una ROM NDS (sin dependencias).

Lee las tablas FNT/FAT de la cabecera NDS y vuelca todos los archivos
respetando la jerarquia de carpetas. Pensado para inspeccionar las ROMs de
referencia oficiales en castellano (IE1 / IE2 DS).

Uso:
    python tools/nds_unpack.py "roms/Inazuma Eleven.nds" work/ie1_es
    python tools/nds_unpack.py --tree-only "roms/Inazuma Eleven.nds"

NOTA: el contenido extraido tiene copyright; queda en work/ (ignorado por git).
"""
import os
import struct
import sys


def u16(b, o): return struct.unpack_from("<H", b, o)[0]
def u32(b, o): return struct.unpack_from("<I", b, o)[0]


def read_dir(data, fnt_off, dir_id, fat, names_only, out_dir, files_log):
    """Procesa recursivamente el subtable de un directorio (dir_id >= 0xF000)."""
    idx = dir_id & 0x0FFF
    entry = fnt_off + idx * 8
    sub_off = fnt_off + u32(data, entry)
    file_id = u16(data, entry + 4)

    p = sub_off
    while True:
        t = data[p]; p += 1
        if t == 0x00:
            break
        length = t & 0x7F
        name = data[p:p + length].decode("shift_jis", errors="replace")
        p += length
        if t & 0x80:  # subdirectorio
            sub_id = u16(data, p); p += 2
            child = os.path.join(out_dir, name) if out_dir else None
            if child:
                os.makedirs(child, exist_ok=True)
            read_dir(data, fnt_off, sub_id, fat, names_only, child, files_log)
        else:  # archivo
            start, end = fat[file_id]
            rel = os.path.join(out_dir, name) if out_dir else name
            files_log.append((rel, end - start))
            if not names_only and out_dir:
                with open(os.path.join(out_dir, name), "wb") as f:
                    f.write(data[start:end])
            file_id += 1


def main():
    args = [a for a in sys.argv[1:]]
    tree_only = "--tree-only" in args
    args = [a for a in args if a != "--tree-only"]
    if not args:
        print(__doc__); sys.exit(1)
    rom = args[0]
    out = args[1] if len(args) > 1 else None

    with open(rom, "rb") as f:
        data = f.read()

    title = data[0:12].decode("ascii", "replace").rstrip("\x00")
    code = data[12:16].decode("ascii", "replace")
    fnt_off = u32(data, 0x40)
    fat_off = u32(data, 0x48)
    fat_size = u32(data, 0x4C)

    fat = []
    for i in range(fat_size // 8):
        s = u32(data, fat_off + i * 8)
        e = u32(data, fat_off + i * 8 + 4)
        fat.append((s, e))

    print(f"ROM: {os.path.basename(rom)}  title={title!r} code={code}")
    print(f"FNT@0x{fnt_off:X}  FAT@0x{fat_off:X}  archivos={len(fat)}")

    if out and not tree_only:
        os.makedirs(out, exist_ok=True)

    files_log = []
    read_dir(data, fnt_off, 0xF000, fat,
             names_only=(tree_only or not out), out_dir=out, files_log=files_log)

    total = sum(sz for _, sz in files_log)
    print(f"Total: {len(files_log)} archivos, {total/1024/1024:.1f} MB")
    # Resumen por extension (util para localizar contenedores de texto)
    by_ext = {}
    for name, sz in files_log:
        ext = os.path.splitext(name)[1].lower() or "(sin)"
        c, s = by_ext.get(ext, (0, 0))
        by_ext[ext] = (c + 1, s + sz)
    print("\nPor extension:")
    for ext, (c, s) in sorted(by_ext.items(), key=lambda x: -x[1][1]):
        print(f"  {ext:8} {c:5} archivos  {s/1024/1024:8.2f} MB")


if __name__ == "__main__":
    main()
