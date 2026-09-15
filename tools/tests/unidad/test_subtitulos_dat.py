"""Subtítulos .dat de películas DS sobre bytes sintéticos."""
import struct

import pytest

from ie123kit.nucleo.media.subtitulos_dat import SUBTITLE_TICK_RATE, Subtitle, read_subtitles


def _reg(inicio, fin, texto):
    return struct.pack("<III", inicio, fin, len(texto)) + texto


def _escribir(tmp_path, data):
    p = tmp_path / "op00.dat"
    p.write_bytes(data)
    return p


def test_lectura(tmp_path):
    data = _reg(0, 30, b" Hola\0\0\0") + _reg(40, 2675, b"\xd9vans \xb2\0basura") + b"\xff\xff\xff\xff"
    assert read_subtitles(_escribir(tmp_path, data)) == [Subtitle(0, 30, "Hola"), Subtitle(40, 2675, "Évans á")]
    assert SUBTITLE_TICK_RATE == 30


def test_sin_ruta():
    assert read_subtitles(None) == []


@pytest.mark.parametrize("data,mensaje", [
    (_reg(0, 1, b"a\0"), "falta el terminador"),
    (struct.pack("<II", 0, 1), "truncada"),
    (_reg(0, 1, b"a\0")[:-1], "inválido"),
    (_reg(5, 1, b"a\0") + b"\xff" * 4, "inválido"),
    (struct.pack("<III", 0, 1, 0) + b"\xff" * 4, "inválido"),
    (_reg(0, 1, b"a\0") + b"\xff" * 4 + b"\0", "después del terminador"),
])
def test_errores(tmp_path, data, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        read_subtitles(_escribir(tmp_path, data))
