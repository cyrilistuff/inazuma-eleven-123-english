#!/usr/bin/env python3
"""Reconstruye el exefs con code.bin PARCHEADO y PLANO (descomprimido), y limpia el flag
compress-code del exheader. Necesario para meter los bounds-checks de patch_code.py.

El loader carga el .code SIN descomprimir si el flag compress-code (exheader @0xD bit0)
esta a 0 -> asi evitamos recomprimir BLZ. El exefs es: header 0x200 (8 entradas de
name[8]+offset[4]+size[4], + hashes SHA256 en orden INVERSO: entry i -> 0x200-(i+1)*0x20)
seguido de los ficheros, cada uno padded a 0x200."""
import os, struct, hashlib, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import patch_code

EXEFS_FILES = [(".code", "code.bin"), ("banner", "banner.bnr"),
               ("icon", "icon.icn"), ("logo", "logo.darc.lz")]


def build_exefs(exefs_dir, out_path):
    """Parchea el .code (descomprime + bounds-checks, lo deja plano) y construye el exefs
    completo. Devuelve (n_parches, tam_plano)."""
    comp = open(os.path.join(exefs_dir, "code.bin"), "rb").read()
    plain, npatch = patch_code.patch_code_bin(comp)
    contents = [plain] + [open(os.path.join(exefs_dir, fn), "rb").read()
                          for _, fn in EXEFS_FILES[1:]]
    header = bytearray(0x200)
    data = bytearray()
    offset = 0
    for i, ((name, _fn), content) in enumerate(zip(EXEFS_FILES, contents)):
        struct.pack_into("<8sII", header, i * 0x10, name.encode(), offset, len(content))
        header[0x200 - (i + 1) * 0x20: 0x200 - i * 0x20] = hashlib.sha256(content).digest()
        data += content
        data += b"\x00" * ((-len(content)) % 0x200)            # padding a 0x200
        offset = len(data)
    open(out_path, "wb").write(bytes(header) + bytes(data))
    return npatch, len(plain)


def patch_exheader(exh_in, exh_out, text_size=None):
    """Pone a 0 el bit0 (compress-code) del exheader @0xD. Si text_size != None, ademas
    actualiza el code_size del .text @0x18 (necesario cuando se inserta el cave en el slack
    de pagina -> el .text crece para incluir el hook). num_pages @0x14 no cambia."""
    exh = bytearray(open(exh_in, "rb").read())
    exh[0xD] &= ~0x01
    if text_size is not None:
        struct.pack_into("<I", exh, 0x18, text_size)
    open(exh_out, "wb").write(bytes(exh))


if __name__ == "__main__":
    n, sz = build_exefs("work/exefs_out", "work/exefs_patched.bin")
    print(f"exefs reconstruido: {n} parches en code.bin (plano {sz} bytes)")
