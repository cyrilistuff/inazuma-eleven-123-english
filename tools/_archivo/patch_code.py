#!/usr/bin/env python3
"""Parchea code.bin (ARM11) para los crashes de las funciones de texto strcpy/getc/strcmp
(@0x14AC5C/0x1B3788/0x184AAC) que petan con puntero corrupto (logs: unmapped Read @ 0x192..
0x20C, todos <0x10000).

CLAVE: code.bin NO tiene hueco seguro para meter el bounds-check:
  - in-place = solo 4 bytes (no caben las ~5 instrucciones del check),
  - los runs de ceros del .text son DATOS que el juego lee -> los machacas y NO ARRANCA,
  - extender el .code (slack de pagina / code_size) -> Azahar CIERRA al cargar.
SOLUCION: el bounds-check va en un CAVE DEL CRO (ina_main1.cro, ~700 bytes libres, carga
estable en 0xA89000). Aqui SOLO se pone un SALTO de 4 bytes IN-PLACE a ese cave (cross-module).
Sin insertar, sin cambiar code_size -> misma estructura que arranca, no rompe boot ni carga.
Los caves (y el retorno a code.bin) los escribe patch_cro.py. Ver CODE_CAVE_ADDRS alli.

code.bin va comprimido (BLZ) -> blz.py descomprime; se deja PLANO (patch_exefs pone el flag
compress-code a 0). NO_CODE_PATCH=1 -> no parchea (diagnostico)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blz
import patch_cro

LOAD = 0x100000
NEW_TEXT_SIZE = None          # NO se cambia code_size (solo saltos in-place de 4 bytes)


def patch_code_bin(compressed):
    """Descomprime el code.bin BLZ y pone un salto in-place (4 bytes) en cada crash site
    hacia su cave del CRO. Devuelve (code_plano, n_parches). Sin insertar nada."""
    dec = bytearray(blz.decompress(compressed))
    if os.environ.get("NO_CODE_PATCH"):
        return bytes(dec), 0
    from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
    ks = Ks(KS_ARCH_ARM, KS_MODE_ARM)
    n = 0
    for pc, cave_addr in patch_cro.CODE_CAVE_ADDRS.items():
        off = pc - LOAD
        dec[off:off + 4] = bytes(ks.asm("b #%d" % cave_addr, pc)[0])   # salto al cave del CRO
        n += 1
    return bytes(dec), n


if __name__ == "__main__":
    comp = open(sys.argv[1], "rb").read()
    plain, n = patch_code_bin(comp)
    open(sys.argv[2], "wb").write(plain)
    print(f"code.bin: {len(comp)} -> {len(plain)} plano, {n} saltos a caves del CRO")
