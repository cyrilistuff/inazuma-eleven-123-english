"""sszl.reenvolver_como: las tres políticas y el tope de crecimiento (F2.2, #48)."""

from __future__ import annotations

import pytest

from ie123kit.nucleo.compresion import sszl
from ie123kit.nucleo.errores import ValidacionError

RAW = b"ARCV" + b"\x00\x01\x02\x03" * 64 + b"texto repetido texto repetido " * 8
NUEVO = b"ARCV" + b"\x04\x05\x06\x07" * 64 + b"otro texto repetido otro texto repetido " * 8


def test_raw_devuelve_los_bytes_tal_cual() -> None:
    assert sszl.reenvolver_como(sszl.compress(RAW), NUEVO, "raw") == NUEVO
    assert sszl.reenvolver_como(RAW, NUEVO, "raw") == NUEVO


def test_sszl_comprime_siempre() -> None:
    resultado = sszl.reenvolver_como(RAW, NUEVO, "sszl")
    assert resultado[:4] == b"SSZL"
    assert sszl.unwrap(resultado) == NUEVO


def test_keep_comprime_solo_si_el_original_venia_envuelto() -> None:
    envuelto = sszl.reenvolver_como(sszl.compress(RAW), NUEVO, "keep")
    assert envuelto[:4] == b"SSZL"
    assert sszl.unwrap(envuelto) == NUEVO
    assert sszl.reenvolver_como(RAW, NUEVO, "keep") == NUEVO


def test_keep_es_el_valor_por_defecto() -> None:
    assert sszl.reenvolver_como(RAW, NUEVO) == NUEVO


def test_politica_desconocida() -> None:
    with pytest.raises(ValueError, match="política de reenvoltura desconocida"):
        sszl.reenvolver_como(RAW, NUEVO, "literal")


def test_crecimiento_maximo_rechaza_una_salida_mayor() -> None:
    original = sszl.compress(RAW)
    with pytest.raises(ValidacionError) as exc:
        sszl.reenvolver_como(original, NUEVO * 4, "sszl", crecimiento_max=1.0)
    assert exc.value.codigo == "sszl_crecimiento"


def test_crecimiento_maximo_holgado_pasa() -> None:
    original = sszl.compress(RAW)
    resultado = sszl.reenvolver_como(original, NUEVO, "sszl", crecimiento_max=4.0)
    assert sszl.unwrap(resultado) == NUEVO


def test_crecimiento_maximo_tambien_aplica_en_raw() -> None:
    with pytest.raises(ValidacionError):
        sszl.reenvolver_como(b"x" * 8, b"y" * 200, "raw", crecimiento_max=2.0)
