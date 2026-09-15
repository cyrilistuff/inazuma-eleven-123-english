"""Índice del paquete de scripts de evento Level-5 "PackNum" (eve.pkb + eve.pkh).

FORMATO RESUELTO del indice (.pkh):
  - 16 bytes: cabecera ASCII "PackNum YYYYMMDD"
  - +0x10 u32: tamaño total del .pkh
  - +0x30 en adelante: tabla de entradas de 12 bytes c/u:
        u32 event_id   (p.ej. 10010001 = mapa/capitulo 1001, evento 0001)
        u32 offset      (en el .pkb)
        u32 size
  Los offsets cubren el .pkb completo (verificado).

Cada entrada del .pkb es un SCRIPT DE EVENTO COMPILADO (bytecode) con el texto del
dialogo EMBEBIDO como operandos, comprimido en LZ10 de Nintendo.

``lz10_decompress`` es un alias de ``nucleo.compresion.lz10.decompress`` (cuerpo
idéntico al de la antigua ``pkb_unpack.lz10_decompress``). La reconstrucción del
paquete queda para F2.2.
"""
import struct

from ie123kit.nucleo.compresion.lz10 import decompress as lz10_decompress


def parse_index(pkh):
    assert pkh[:7] == b"PackNum", "no es un .pkh PackNum"
    n = (len(pkh) - 0x30) // 12
    out = []
    for i in range(n):
        eid, off, size = struct.unpack_from("<III", pkh, 0x30 + i * 12)
        out.append((eid, off, size))
    return out


def entry_data(pkb, off, size):
    """Devuelve el contenido descomprimido de una entrada del .pkb."""
    return lz10_decompress(pkb[off:off + size])
