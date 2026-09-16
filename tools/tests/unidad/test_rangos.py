"""Rangos cambiados y comprobación enmascarada (datos sintéticos)."""

from __future__ import annotations

import pytest

from ie123kit.nucleo.errores import ValidacionError
from ie123kit.nucleo.registros.rangos import assert_only_changed, diff_ranges, fusionar, same_size


def test_sin_cambios():
    base = bytes(range(32))
    assert diff_ranges(base, base) == []


def test_contiguos_se_fusionan():
    base = bytearray(16)
    nuevo = bytearray(base)
    nuevo[4:7] = b"\x01\x02\x03"
    assert diff_ranges(bytes(base), bytes(nuevo)) == [(4, 7)]


def test_rangos_separados():
    base = bytearray(16)
    nuevo = bytearray(base)
    nuevo[2] = 1
    nuevo[9:11] = b"\x05\x06"
    nuevo[15] = 7
    assert diff_ranges(bytes(base), bytes(nuevo)) == [(2, 3), (9, 11), (15, 16)]


def test_same_size():
    assert same_size(b"abc", b"xyz") == 3
    with pytest.raises(ValidacionError):
        same_size(b"abc", b"ab")


def test_fusionar_solapes():
    assert fusionar([(5, 8), (0, 3), (3, 4), (7, 12)]) == [(0, 4), (5, 12)]


def test_assert_only_changed_verde():
    base = bytearray(32)
    nuevo = bytearray(base)
    nuevo[10:12] = b"\x01\x02"
    assert assert_only_changed(bytes(base), bytes(nuevo), [(8, 16)]) == [(10, 12)]


def test_assert_only_changed_rojo():
    base = bytearray(32)
    nuevo = bytearray(base)
    nuevo[10] = 1
    nuevo[20] = 2
    with pytest.raises(ValidacionError) as exc:
        assert_only_changed(bytes(base), bytes(nuevo), [(8, 16)])
    assert "0x14" in str(exc.value)
