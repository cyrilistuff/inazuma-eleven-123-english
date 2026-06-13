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
    """LZ10 greedy. Ventana 4096, longitud 3..18."""
    n = len(data)
    out = bytearray(b"\x10")
    out += struct.pack("<I", n)[:3]
    i = 0
    # indice simple por prefijo de 3 bytes para acelerar la busqueda
    from collections import defaultdict
    pos = defaultdict(list)
    tokens = []
    while i < n:
        best_len, best_disp = 0, 0
        if i + 3 <= n:
            key = data[i:i + 3]
            for j in reversed(pos.get(bytes(key), [])):
                disp = i - j
                if disp > 4096:
                    break
                length = 3
                maxlen = min(18, n - i)
                while length < maxlen and data[j + length] == data[i + length]:
                    length += 1
                if length > best_len:
                    best_len, best_disp = length, disp
                    if length == maxlen:
                        break
        if best_len >= 3:
            tokens.append((True, best_disp, best_len))
            for k in range(i, i + best_len):
                if k + 3 <= n:
                    pos[bytes(data[k:k + 3])].append(k)
            i += best_len
        else:
            tokens.append((False, data[i], 1))
            if i + 3 <= n:
                pos[bytes(data[i:i + 3])].append(i)
            i += 1
    # emitir en grupos de 8
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
