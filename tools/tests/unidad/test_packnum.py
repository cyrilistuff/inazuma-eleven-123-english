"""nucleo.eventos.packnum: índice PackNum sintético y equivalencia del LZ10 antiguo."""
import struct

import pytest

from ie123kit.nucleo.compresion import lz10
from ie123kit.nucleo.eventos import packnum


def _lz10_pkb_unpack_original(data):
    # Copia del cuerpo de tools/pkb_unpack.lz10_decompress en 0af2abd, como referencia.
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


def _pkh(entradas):
    cab = b"PackNum 20260101" + struct.pack("<I", 0x30 + 12 * len(entradas))
    cab += bytes(0x30 - len(cab))
    return cab + b"".join(struct.pack("<III", *e) for e in entradas)


def test_alias():
    assert packnum.lz10_decompress is lz10.decompress


def test_indice_y_entradas():
    a = b"hola hola hola hola \x00" * 5
    b = bytes(range(40))
    ca, cb = lz10.compress(a), lz10.compress_store(b)
    pkb = ca + b"sin" + cb
    idx = packnum.parse_index(_pkh([(10010001, 0, len(ca)), (10010002, len(ca), 3),
                                    (10010003, len(ca) + 3, len(cb))]))
    assert idx == [(10010001, 0, len(ca)), (10010002, len(ca), 3), (10010003, len(ca) + 3, len(cb))]
    assert [packnum.entry_data(pkb, o, s) for _, o, s in idx] == [a, b"sin", b]


def test_cabecera_invalida():
    with pytest.raises(AssertionError):
        packnum.parse_index(b"NoPack" + bytes(60))


@pytest.mark.parametrize("flujo", [
    lz10.compress(b"abcabcabcabcXYZ" * 20),
    lz10.compress_store(b"literal puro"),
    b"sin comprimir",
    b"",
    lz10.compress(b"abcabcabcabc" * 30)[:-7],
    b"\x10\x40\x00\x00\x00abc",
])
def test_equivalencia_lz10(flujo):
    def resultado(f):
        try:
            return f(flujo)
        except Exception as e:  # los datos truncados deben fallar igual
            return type(e)
    assert resultado(packnum.lz10_decompress) == resultado(_lz10_pkb_unpack_original)
