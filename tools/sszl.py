"""Compresor SSZL (LZSS con anillo de 4096 B que empieza en 0xFEE), inverso de ui_archive.unwrap.

Los .lzs/.arc del juego se cargan en búferes del tamaño aproximado del original comprimido: envolver
los datos solo con literales (12,5 % más grande que sin comprimir) hace que la textura no cargue.
"""
import struct
from collections import defaultdict

from ui_archive import unwrap


def compress(raw: bytes) -> bytes:
    n = len(raw)
    out = bytearray()
    cadenas = defaultdict(list)
    i = 0
    while i < n:
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= n:
                break
            mejor_len, mejor_j = 0, 0
            if i + 3 <= n:
                clave = raw[i:i + 3]
                lista = cadenas[clave]
                for j in reversed(lista[-64:]):
                    if i - j > 4078:
                        break
                    k = 3
                    while k < 18 and i + k < n and raw[j + k] == raw[i + k]:
                        k += 1
                    if k > mejor_len:
                        mejor_len, mejor_j = k, j
                        if k == 18:
                            break
            if mejor_len >= 3:
                off = (0xFEE + mejor_j) & 0xFFF
                out += bytes((off & 0xFF, ((off >> 4) & 0xF0) | (mejor_len - 3)))
                paso = mejor_len
            else:
                flags |= 1 << bit
                out.append(raw[i])
                paso = 1
            for p in range(i, min(i + paso, n - 2)):
                cadenas[raw[p:p + 3]].append(p)
            i += paso
        out[flag_pos] = flags
    data = b'SSZL' + bytes(4) + struct.pack('<II', len(out), n) + bytes(out)
    assert unwrap(data) == raw
    return data
