"""Pintado de rótulos: salida idéntica a translate_ui_textures del commit 0af2abd."""
import hashlib
from pathlib import Path

import pytest
from PIL import Image

from ie123kit.nucleo.graficos.pintado import paint, paint_condensed

_ARIAL = Path("C:/Windows/Fonts/arial.ttf")


def _fuente():
    if _ARIAL.is_file():
        return str(_ARIAL)
    pytest.skip("sin la fuente de referencia arial.ttf (los hashes se capturaron con ella)")


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
