"""Ayudas de imagen de nucleo/graficos/imagen.py (F2.2, #48)."""

from __future__ import annotations

import pytest
from PIL import Image

from ie123kit.nucleo.graficos import imagen as I

ROJO = (255, 0, 0, 255)
VERDE = (0, 255, 0, 255)


def lienzo(w: int = 8, h: int = 8, color: tuple[int, int, int, int] = I.TRANSPARENTE) -> Image.Image:
    return Image.new("RGBA", (w, h), color)


def test_zoom_multiplica_el_tamano_y_opaca_el_fondo() -> None:
    im = lienzo(4, 3)
    im.putpixel((0, 0), ROJO)
    z = I.zoom(im, 5, fondo=(1, 2, 3, 255))
    assert z.size == (20, 15)
    assert z.getpixel((4, 4)) == ROJO
    assert z.getpixel((5, 0)) == (1, 2, 3, 255)


def test_zoom_rechaza_escala_cero() -> None:
    with pytest.raises(ValueError, match="escala"):
        I.zoom(lienzo(), 0)


def test_preview_pair_pone_las_dos_a_los_lados() -> None:
    antes, despues = lienzo(4, 4, ROJO), lienzo(4, 4, VERDE)
    par = I.preview_pair(antes, despues, escala=2, hueco=6)
    assert par.size == (8 + 6 + 8, 8)
    assert par.getpixel((0, 0)) == ROJO
    assert par.getpixel((14, 0)) == VERDE


def test_contact_sheet_tamano_y_etiquetas() -> None:
    tiles = [lienzo(4, 4, ROJO) for _ in range(3)]
    hoja = I.contact_sheet(tiles, columnas=2)
    assert hoja.size == (8, 8)
    con_pie = I.contact_sheet(tiles, columnas=2, etiquetas=["a", "b", "c"])
    assert con_pie.size == (8, 32)


def test_contact_sheet_valida_las_etiquetas() -> None:
    with pytest.raises(ValueError, match="etiquetas"):
        I.contact_sheet([lienzo()], columnas=1, etiquetas=["a", "b"])


def test_draw_boxes_pinta_el_contorno() -> None:
    salida = I.draw_boxes(lienzo(8, 8), [(2, 2, 6, 6)], numerar=False)
    assert salida.getpixel((2, 2))[:3] == (255, 60, 60)
    assert salida.getpixel((5, 5))[:3] == (255, 60, 60)
    assert salida.getpixel((4, 4)) == I.TRANSPARENTE


def test_clear_vacia_solo_la_caja() -> None:
    im = lienzo(6, 6, ROJO)
    I.clear(im, (1, 1, 3, 3))
    assert im.getpixel((1, 1)) == I.TRANSPARENTE
    assert im.getpixel((2, 2)) == I.TRANSPARENTE
    assert im.getpixel((3, 3)) == ROJO
    assert im.getpixel((0, 0)) == ROJO


def test_paste_centered() -> None:
    im = lienzo(8, 8)
    I.paste_centered(im, lienzo(2, 2, ROJO), (0, 0, 8, 8))
    assert im.getpixel((3, 3)) == ROJO
    assert im.getpixel((2, 2)) == I.TRANSPARENTE


def test_paste_centered_con_escala() -> None:
    im = lienzo(8, 8)
    I.paste_centered(im, lienzo(2, 2, ROJO), (0, 0, 8, 8), escala=2)
    assert im.getpixel((2, 2)) == ROJO
    assert im.getpixel((5, 5)) == ROJO


def test_paste_centered_falla_si_no_cabe() -> None:
    with pytest.raises(ValueError, match="no cabe"):
        I.paste_centered(lienzo(8, 8), lienzo(9, 2, ROJO), (0, 0, 8, 8))


def test_fit_into_deja_margen_y_centra() -> None:
    im = lienzo(20, 20)
    I.fit_into(im, lienzo(40, 40, ROJO), (0, 0, 20, 20))
    assert im.getpixel((10, 10)) == ROJO
    assert im.getpixel((0, 0)) == I.TRANSPARENTE
    assert im.getpixel((19, 19)) == I.TRANSPARENTE


def test_fit_into_sin_centrar_va_a_la_esquina() -> None:
    im = lienzo(20, 12)
    I.fit_into(im, lienzo(40, 40, ROJO), (0, 0, 20, 12), centrar=False)
    assert im.getpixel((1, 1)) == ROJO


def test_fit_into_caja_minuscula() -> None:
    with pytest.raises(ValueError, match="margen"):
        I.fit_into(lienzo(), lienzo(2, 2, ROJO), (0, 0, 2, 2))


def test_recolor_respeta_los_transparentes() -> None:
    im = lienzo(2, 1, ROJO)
    im.putpixel((1, 0), (255, 0, 0, 0))
    salida = I.recolor(im, {(255, 0, 0): (0, 0, 255)})
    assert salida.getpixel((0, 0)) == (0, 0, 255, 255)
    assert salida.getpixel((1, 0)) == (255, 0, 0, 0)
    assert im.getpixel((0, 0)) == ROJO  # no muta el original


def test_drop_shadow_crece_un_pixel() -> None:
    pieza = lienzo(3, 3, ROJO)
    salida = I.drop_shadow(pieza, (0, 0, 16))
    assert salida.size == (4, 4)
    assert salida.getpixel((0, 0)) == ROJO
    assert salida.getpixel((3, 3)) == (0, 0, 16, 255)


def test_drop_shadow_rechaza_desplazamiento_negativo() -> None:
    with pytest.raises(ValueError, match="desplazamiento"):
        I.drop_shadow(lienzo(2, 2, ROJO), (0, 0, 0), (-1, 0))


def test_binarize_alpha() -> None:
    im = lienzo(3, 1)
    im.putpixel((0, 0), (255, 255, 255, 109))
    im.putpixel((1, 0), (255, 255, 255, 110))
    im.putpixel((2, 0), (255, 255, 255, 255))
    salida = I.binarize_alpha(im)
    assert [salida.getpixel((x, 0))[3] for x in range(3)] == [0, 255, 255]
