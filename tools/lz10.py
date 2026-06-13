#!/usr/bin/env python3
"""Compresor/descompresor LZ10 de Nintendo (cabecera 0x10 + tamaño 24-bit LE).

Es el formato de cada entrada de los .pkb (scripts de evento) de Inazuma Eleven.
`compress` produce un stream que `decompress` (y el juego) entienden. Greedy.
"""
import struct


def decompress(data):
    if not data or data[0] != 0x10:
        return data
    size = data[1] | (data[2] << 8) | (data[3] << 16)
    out = bytearray()
    p = 4
    while len(out) < size and p < len(data):
        flags = data[p]; p += 1
        for bit in range(8):
            if len(out) >= size or p >= len(data):
                break
            if flags & (0x80 >> bit):
                b1, b2 = data[p], data[p + 1]; p += 2
                length = (b1 >> 4) + 3
                disp = ((b1 & 0xF) << 8 | b2) + 1
                for _ in range(length):
                    out.append(out[-disp])
            else:
                out.append(data[p]); p += 1
    return bytes(out)


def compress(data):
    """LZ10 con lazy matching. Ventana 4096, longitud 3..18."""
    from collections import defaultdict
    n = len(data)
    out = bytearray(b"\x10")
    out += struct.pack("<I", n)[:3]
    pos = defaultdict(list)
    mv = memoryview(data)

    def best(i):
        if i + 3 > n:
            return 0, 0
        bl, bd = 0, 0
        maxlen = min(18, n - i)
        key = bytes(mv[i:i + 3])
        for j in reversed(pos.get(key, ())):
            disp = i - j
            if disp > 4096:
                break
            length = 3
            while length < maxlen and data[j + length] == data[i + length]:
                length += 1
            if length > bl:
                bl, bd = length, disp
                if length == maxlen:
                    break
        return bl, bd

    def addpos(i):
        if i + 3 <= n:
            pos[bytes(mv[i:i + 3])].append(i)

    tokens = []
    i = 0
    while i < n:
        bl, bd = best(i)
        if bl >= 3:
            addpos(i)
            nl, _ = best(i + 1) if i + 1 < n else (0, 0)
            if nl > bl:                       # lazy: mejor empezar match en i+1
                tokens.append((False, data[i], 1))
                i += 1
                continue
            for k in range(i + 1, i + bl):
                addpos(k)
            tokens.append((True, bd, bl))
            i += bl
        else:
            tokens.append((False, data[i], 1))
            addpos(i)
            i += 1

    k = 0
    while k < len(tokens):
        grp = tokens[k:k + 8]
        flag = 0
        for bit, (is_match, a, b) in enumerate(grp):
            if is_match:
                flag |= 0x80 >> bit
        out.append(flag)
        for is_match, a, b in grp:
            if is_match:
                disp, length = a - 1, b - 3
                out.append((length << 4) | (disp >> 8))
                out.append(disp & 0xFF)
            else:
                out.append(a)
        k += 8
    return bytes(out)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    # auto-test
    samples = [b"", b"A", b"ABABABABABAB", b"hola mundo " * 20,
               bytes(range(256)) * 4]
    ok = all(decompress(compress(s)) == s for s in samples)
    print("roundtrip auto-test:", "OK" if ok else "FALLO")
