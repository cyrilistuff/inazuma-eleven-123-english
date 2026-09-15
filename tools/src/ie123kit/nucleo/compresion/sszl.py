"""Compresor SSZL (LZSS con anillo de 4096 B que empieza en 0xFEE), inverso de ui_archive.unwrap.

Los .lzs/.arc del juego se cargan en búferes del tamaño aproximado del original comprimido: envolver
los datos solo con literales (12,5 % más grande que sin comprimir) hace que la textura no cargue.
"""
import struct
from collections import defaultdict


def unwrap(data):
    if data[:4] != b'SSZL':
        return data
    packed, expected = struct.unpack_from('<II', data, 8)
    if packed + 16 != len(data):
        raise ValueError('SSZL size mismatch')
    ring = bytearray(4096)
    cursor, pos, out = 0xfee, 16, bytearray()
    while len(out) < expected:
        flags = data[pos]
        pos += 1
        for bit in range(8):
            if len(out) == expected:
                break
            if flags & (1 << bit):
                values = [data[pos]]
                pos += 1
                for value in values:
                    out.append(value);ring[cursor] = value;cursor = (cursor+1)&4095
            else:
                lo, hi = data[pos:pos+2]
                pos += 2
                offset = lo | ((hi & 0xf0) << 4)
                length = (hi & 15)+3
                for k in range(length):
                    if len(out) >= expected:
                        raise ValueError('SSZL output overflow')
                    value = ring[(offset+k)&4095]
                    out.append(value);ring[cursor] = value;cursor = (cursor+1)&4095
    return bytes(out)


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
