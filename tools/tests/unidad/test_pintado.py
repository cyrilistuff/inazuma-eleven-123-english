"""Pintado de rótulos: salida idéntica a translate_ui_textures del commit 0af2abd.

Los hashes de OPS se capturaron con Arial (`C:/Windows/Fonts/arial.ttf`), que no se puede
redistribuir, así que esos 5 tests solo corren en Windows (#59). La cobertura de conducta
de `paint`/`paint_condensed` que no depende de la fuente concreta está más abajo y corre en
los dos SO con cualquier TTF negrita del sistema.
"""
import hashlib
from pathlib import Path

import pytest
from PIL import Image

from ie123kit.nucleo.graficos.pintado import paint, paint_condensed

_ARIAL = Path("C:/Windows/Fonts/arial.ttf")
# Negrita de sistema (Arial en Windows, DejaVu en Linux): misma lista que
# tools/tests/unidad/graficos/test_formatos_ui.py.
_FUENTES_LIBRES = (
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)


def _fuente():
    if _ARIAL.is_file():
        return str(_ARIAL)
    pytest.skip("sin la fuente de referencia arial.ttf (los hashes se capturaron con ella)")


def _fuente_libre():
    """TTF negrita del sistema para comprobaciones que no dependen de los hashes de Arial."""
    for ruta in _FUENTES_LIBRES:
        if Path(ruta).is_file():
            return ruta
    pytest.skip("sin TTF de sistema: " + ", ".join(_FUENTES_LIBRES))


def _h(im):
    return hashlib.sha256(im.tobytes()).hexdigest()


def _lienzo():
    return Image.new("RGBA", (64, 32), (10, 20, 30, 255))


OPS = {
    "simple": ({"box": [2, 2, 62, 30], "text": "Hola", "size": 13, "stroke_width": 1,
                "shadow": [1, 1, [0, 0, 0, 255]]},
               13, "ef31c0d199ab2f094ef1a040e1faef3c32fe4afffdf3319d1d6db2799016b3d7"),
    "izq": ({"box": [0, 0, 64, 32], "text": "AB\ncd", "size": 12, "align": "left", "crisp": True},
            12, "5d444d1080cea842d8268f17457478619ea47e9ab03da8b946b98c4109ef3935"),
    "condensado": ({"box": [0, 4, 40, 24], "text": "PORTERO", "size": 13, "condense": True,
                    "crisp": True, "stroke_width": 1},
                   13, "d8a4c9d3f9bc8e4ddb1f9c6ac38234d9ea28988cef308dcfed7b0dac25cc5f52"),
    "rotado": ({"box": [4, 0, 24, 32], "text": "Hi", "size": 10, "rotate": 90},
               10, "76218374a5f3253e5aef573a63812c1fc776ce826ec8034ff1b3b485a2d4254f"),
}


@pytest.mark.parametrize("nombre", sorted(OPS))
def test_paint_igual_que_original(nombre):
    op, tam, esperado = OPS[nombre]
    im = _lienzo()
    assert paint(im, op, _fuente()) == tam
    assert _h(im) == esperado


def test_paint_condensed_igual_que_original():
    im = _lienzo()
    assert paint_condensed(im, {"box": [0, 0, 30, 20], "text": "Delantero", "size": 13}, _fuente()) == 13
    assert _h(im) == "ea0641f71f0fa6bd0716d25e4e601e2ab2af34bd2da1206d09b56116831df015"


@pytest.mark.parametrize("caja", [[10, 0, 5, 10], [0, 0, 65, 10], [-1, 0, 10, 10], [0, 5, 10, 5]])
def test_rectangulo_invalido(caja):
    with pytest.raises(ValueError, match="invalid text rectangle"):
        paint(_lienzo(), {"box": caja, "text": "x"}, "no-se-usa.ttf")


# --- Cobertura independiente de la fuente (corre también en Linux, #59) ---


def _transparente():
    return Image.new("RGBA", (64, 32))


def test_condensado_no_se_sale_de_la_caja():
    im = _transparente()
    assert paint_condensed(im, {"box": [0, 0, 30, 20], "text": "Delantero", "size": 13}, _fuente_libre()) == 13
    caja = im.getbbox()
    assert caja is not None
    assert caja[0] >= 0 and caja[1] >= 0 and caja[2] <= 30 and caja[3] <= 20


def test_rotado_no_se_sale_de_la_caja():
    im = _transparente()
    assert paint(im, {"box": [4, 0, 24, 32], "text": "Hi", "size": 10, "rotate": 90}, _fuente_libre()) == 10
    caja = im.getbbox()
    assert caja is not None
    assert caja[0] >= 4 and caja[1] >= 0 and caja[2] <= 24 and caja[3] <= 32


def test_rotacion_no_recta_falla():
    with pytest.raises(ValueError, match="only quarter-turn text rotation supported"):
        paint(_lienzo(), {"box": [0, 0, 20, 20], "text": "x", "rotate": 45}, "no-se-usa.ttf")


def test_texto_que_no_cabe_falla():
    with pytest.raises(ValueError, match="text does not fit"):
        paint(_transparente(), {"box": [0, 0, 10, 8], "text": "Delanteros", "size": 13}, _fuente_libre())


def test_padding_negativo_falla():
    with pytest.raises(ValueError, match="negative text padding"):
        paint(_transparente(), {"box": [0, 0, 40, 20], "text": "x", "padding": -1}, _fuente_libre())
