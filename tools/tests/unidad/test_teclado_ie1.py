"""Teclado IE1: patch_map y texture_operations idénticos al ie1_keyboard de 0af2abd."""
import hashlib
import json

import pytest

from ie123kit.ie1.graficos.teclado import ROWS, patch_map, texture_operations


def _mapa():
    base = bytearray(b"xy" * 156) + b"\r\n"
    base[52 + 48:52 + 52] = b"BBBB"
    base[104 + 48:104 + 52] = b"CCCC"
    base[0:4] = b"    "
    base[208 + 10:208 + 14] = b"    "
    assert len(base) == 314
    return bytes(base)


ESPERADO = {
    0: ("a9ed778c5ee21425d267d15e8aea9d369522b6e65b48f1ee0b98e7e2c66c3f05",
        "62de5dcbc01c4862ac2e5d25804c4f361d5166cb7501623521819a7fdef703e3"),
    1: ("963f998cdd4995d176ff1b5264cbe8b5e2e5f5c5f89e15470469100d22ee5ed3",
        "185c78dc88e3ff94bff04e0d904112a9f97c9c680756df87de02eed272bb4840"),
    2: ("ea3eeaa0b9f3d35b3adb59c970da48549c1ea3c2849da18baa85017958369f30",
        "da73db2780ed8cafb65a77dc48d7e06306892999fea5916b6de83c3c388f8ddd"),
}


@pytest.mark.parametrize("modo", [0, 1, 2])
def test_patch_map_y_operaciones(modo):
    mapa, ops = ESPERADO[modo]
    salida = patch_map(_mapa(), modo)
    assert len(salida) == 314 and salida.endswith(b"\r\n")
    assert hashlib.sha256(salida).hexdigest() == mapa
    texto = json.dumps(texture_operations(modo), ensure_ascii=False).encode()
    assert hashlib.sha256(texto).hexdigest() == ops


def test_rejilla_20px():
    assert len(ROWS) == 6 and all(len(r) == 10 for r in ROWS)
    assert texture_operations(0)[11]["box"] == [20, 22, 40, 38]


def test_mapa_inesperado():
    with pytest.raises(ValueError):
        patch_map(_mapa()[:-2] + b"\n\n", 0)
    with pytest.raises(ValueError):
        patch_map(_mapa() + b"x", 0)
    roto = bytearray(_mapa())
    roto[52 + 48:52 + 52] = b"xyxy"
    with pytest.raises(ValueError, match="diacritic"):
        patch_map(bytes(roto), 0)
