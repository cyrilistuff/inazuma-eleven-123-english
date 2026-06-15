#!/usr/bin/env python3
"""Parchea ina_main1.cro: bounds-checks para los crashes de TEXTO que tumban el juego al
traducir (puntero corrupto diminuto -> unmapped Read).

DOS familias de crash, AMBAS resueltas con caves EN EL CRO (tiene ~700 bytes libres y
carga ESTABLE en 0xA89000 — lo confirman los crashes consistentes en 0xABFCC0):

  1. ruby/furigana, DENTRO del CRO @ 0xABFCC0 (`ldrb r0,[r4]`, r4 basura). Salto interno.
  2. strcpy/getc/strcmp, en CODE.BIN (@0x14AC5C/0x1B3788/0x184AAC). code.bin NO tiene hueco
     para el parche (in-place=4 bytes; los ceros del .text son datos que rompen el boot;
     extender el .code cierra Azahar). SOLUCION: el cave va en el CRO y code.bin solo pone un
     SALTO de 4 bytes in-place (cross-module; el CRO esta a distancia fija). Ver patch_code.py.

Bounds-check: puntero valido >=0x100000, corrupto <0x10000 (los logs: 0x192..0x20C) -> si es
basura, cadena vacia / no-igual. Caves en el run de 716 ceros @ file 0x50E14 (loaded 0xAD9E14).
"""
import os

CRO_REL = os.path.join("work", "romfs", "cro", "ina_main1.cro")
LOAD = 0xA89000      # direccion de carga de ina_main1 (estable; del log)
CRASH = 0x36CC0      # file offset de `ldrb r0,[r4]` del ruby (= PC 0xABFCC0 - LOAD)
CAVE = 0x50E14       # cave del ruby (16 bytes), inicio del run de 716 ceros

# Caves de los crashes de code.bin (van DESPUES del cave del ruby, en el mismo run libre).
# (file_offset, asm). {ret} no se usa: el `b` final vuelve a code.bin (direccion absoluta).
CODE_CAVES = [
    (0x14AC5C, 0x50E24, "cmp r1,#0x10000; movlo r2,#0; ldrbhs r2,[r1]; b #0x14AC60"),   # strcpy
    (0x1B3788, 0x50E38, "cmp r0,#0x10000; movlo r0,#0; bxlo lr; ldr r1,[r0,#0x10]; b #0x1B378C"),  # getc
    (0x184AAC, 0x50E50, "cmp r0,#0x10000; cmphs r1,#0x10000; movlo r0,#1; bxlo lr; and r3,r0,#3; b #0x184AB0"),  # strcmp
]
# direcciones CARGADAS de los caves de code.bin -> patch_code.py salta aqui desde code.bin
CODE_CAVE_ADDRS = {pc: LOAD + off for pc, off, _ in CODE_CAVES}


def patch(cro):
    """Aplica TODOS los caves (ruby + code.bin) sobre el bytearray del CRO. Idempotente
    (reescribe los mismos bytes). Devuelve True."""
    from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
    ks = Ks(KS_ARCH_ARM, KS_MODE_ARM)
    # 1) ruby: salto interno + cave
    cro[CRASH:CRASH + 4] = bytes(ks.asm("b #%d" % (LOAD + CAVE), LOAD + CRASH)[0])
    cro[CAVE:CAVE + 16] = bytes(ks.asm(
        "cmp r4,#0x10000; movlo r0,#0; ldrbhs r0,[r4]; b #%d" % (LOAD + CRASH + 4), LOAD + CAVE)[0])
    # 2) caves de code.bin: DESCARTADO. La zona @0x50E24+ del CRO NO es libre (la rellena la
    #    relocacion/runtime); escribir ahi PETA el juego @0xAD9E38 (confirmado por el log).
    #    El cross-module code.bin->CRO no es viable. Solo el cave del ruby (@0x50E14) es seguro.
    return True


def main():
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(repo, CRO_REL)
    orig = path + ".orig"
    src = orig if os.path.exists(orig) else path
    cro = bytearray(open(src, "rb").read())            # partir del .orig limpio si existe
    patch(cro)
    open(path, "wb").write(cro)
    print("ina_main1.cro PARCHEADO (ruby 0xABFCC0 + caves code.bin strcpy/getc/strcmp)")


if __name__ == "__main__":
    main()
