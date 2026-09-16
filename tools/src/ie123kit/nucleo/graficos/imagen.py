"""Ayudas puras sobre PIL.Image para las capas gráficas.

Consolidan los patrones ``before_after_previews`` y ``pixel_and_text_drawing_helpers`` del
catálogo de auditoría: cada capa de work/ redefinía o importaba de V37 su propio
``limpiar``/``pegar_centrado``/``recolorear``/``con_sombra``, y montaba a mano los pares
antes/después con ``Image.new`` + ``alpha_composite`` + ``resize(NEAREST)``.

Aquí no se resuelven rutas de fuentes ni se usa cv2: el pintado de texto vive en
``nucleo/graficos/pintado.py``. Todas las funciones son puras salvo las que reciben una
imagen destino (``clear``, ``paste_centered``, ``fit_into``, ``draw_boxes``), que la
modifican en sitio y además la devuelven para poder encadenar.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from PIL import Image, ImageDraw

__all__ = [
    "TRANSPARENTE",
    "binarize_alpha",
    "clear",
    "contact_sheet",
    "draw_boxes",
    "drop_shadow",
    "fit_into",
    "paste_centered",
    "preview_pair",
    "recolor",
    "zoom",
]

#: Píxel RGBA totalmente transparente.
TRANSPARENTE = (0, 0, 0, 0)

_FONDO = (40, 44, 70, 255)


def _rgba(im: Image.Image) -> Image.Image:
    return im if im.mode == "RGBA" else im.convert("RGBA")


def zoom(im: Image.Image, escala: int = 6, fondo: tuple[int, int, int, int] = _FONDO) -> Image.Image:
    """Amplía `im` por vecino más cercano sobre un fondo opaco (pixel art sin interpolar)."""
    if escala < 1:
        raise ValueError(f"escala debe ser >= 1, no {escala}")
    base = Image.new("RGBA", im.size, fondo)
    base.alpha_composite(_rgba(im))
    return base.resize((im.size[0] * escala, im.size[1] * escala), Image.NEAREST)


def preview_pair(
    antes: Image.Image,
    despues: Image.Image,
    escala: int = 6,
    fondo: tuple[int, int, int, int] = _FONDO,
    hueco: int = 20,
) -> Image.Image:
    """Par antes/después ampliado y en horizontal, separado por `hueco` píxeles."""
    izquierda = zoom(antes, escala, fondo)
    derecha = zoom(despues, escala, fondo)
    ancho = izquierda.width + hueco + derecha.width
    alto = max(izquierda.height, derecha.height)
    par = Image.new("RGBA", (ancho, alto), fondo)
    par.alpha_composite(izquierda, (0, 0))
    par.alpha_composite(derecha, (izquierda.width + hueco, 0))
    return par


def contact_sheet(
    tiles: Sequence[Image.Image],
    columnas: int = 2,
    etiquetas: Sequence[str] | None = None,
) -> Image.Image:
    """Mosaico de `tiles` en `columnas`, con una etiqueta opcional bajo cada casilla."""
    if columnas < 1:
        raise ValueError(f"columnas debe ser >= 1, no {columnas}")
    if not tiles:
        return Image.new("RGBA", (1, 1), _FONDO)
    if etiquetas is not None and len(etiquetas) != len(tiles):
        raise ValueError(f"{len(etiquetas)} etiquetas para {len(tiles)} casillas")
    pie = 12 if etiquetas is not None else 0
    celda_w = max(t.width for t in tiles)
    celda_h = max(t.height for t in tiles) + pie
    filas = (len(tiles) + columnas - 1) // columnas
    hoja = Image.new("RGBA", (celda_w * columnas, celda_h * filas), _FONDO)
    lapiz = ImageDraw.Draw(hoja)
    for i, tile in enumerate(tiles):
        x = (i % columnas) * celda_w
        y = (i // columnas) * celda_h
        hoja.alpha_composite(_rgba(tile), (x, y))
        if etiquetas is not None:
            lapiz.text((x + 1, y + celda_h - pie), etiquetas[i], fill=(255, 255, 255, 255))
    return hoja


def draw_boxes(
    im: Image.Image,
    cajas: Iterable[tuple[int, int, int, int]],
    escala: int = 1,
    color: tuple[int, int, int] = (255, 60, 60),
    numerar: bool = True,
) -> Image.Image:
    """Dibuja los rectángulos `cajas` (x0, y0, x1, y1) sobre una copia ampliada de `im`."""
    salida = zoom(im, escala) if escala != 1 else _rgba(im).copy()
    lapiz = ImageDraw.Draw(salida)
    for i, (x0, y0, x1, y1) in enumerate(cajas):
        lapiz.rectangle(
            (x0 * escala, y0 * escala, x1 * escala - 1, y1 * escala - 1),
            outline=(*color, 255),
        )
        if numerar:
            lapiz.text((x0 * escala + 1, y0 * escala + 1), str(i), fill=(*color, 255))
    return salida


def clear(im: Image.Image, caja: tuple[int, int, int, int]) -> Image.Image:
    """Vacía (deja transparente) el rectángulo semiabierto `caja` de `im`, en sitio."""
    x0, y0, x1, y1 = caja
    ImageDraw.Draw(im).rectangle((x0, y0, x1 - 1, y1 - 1), fill=TRANSPARENTE)
    return im


def paste_centered(
    im: Image.Image,
    pieza: Image.Image,
    caja: tuple[int, int, int, int],
    escala: int = 1,
) -> Image.Image:
    """Compone `pieza` centrada dentro de `caja`; ValueError si no cabe (V37.pegar_centrado)."""
    pieza = _rgba(pieza)
    if escala != 1:
        pieza = pieza.resize((pieza.size[0] * escala, pieza.size[1] * escala), Image.NEAREST)
    x0, y0, x1, y1 = caja
    w, h = pieza.size
    if w > x1 - x0 or h > y1 - y0:
        raise ValueError(f"pieza {w}x{h} no cabe en {caja}")
    im.alpha_composite(pieza, (x0 + (x1 - x0 - w) // 2, y0 + (y1 - y0 - h) // 2))
    return im


def fit_into(
    im: Image.Image,
    pieza: Image.Image,
    caja: tuple[int, int, int, int],
    centrar: bool = True,
) -> Image.Image:
    """Escala `pieza` con LANCZOS para que quepa en `caja` con 1 px de margen por lado (v67)."""
    pieza = _rgba(pieza)
    x0, y0, x1, y1 = caja
    ancho, alto = x1 - x0 - 2, y1 - y0 - 2
    if ancho <= 0 or alto <= 0:
        raise ValueError(f"caja demasiado pequeña para un margen de 1 px: {caja}")
    f = min(ancho / pieza.width, alto / pieza.height)
    escalada = pieza.resize((round(pieza.width * f), round(pieza.height * f)), Image.LANCZOS)
    if centrar:
        destino = (x0 + (x1 - x0 - escalada.width) // 2, y0 + (y1 - y0 - escalada.height) // 2)
    else:
        destino = (x0 + 1, y0 + 1)
    im.alpha_composite(escalada, destino)
    return im


def recolor(im: Image.Image, mapa_rgb: dict[tuple[int, int, int], tuple[int, int, int]]) -> Image.Image:
    """Copia de `im` con los colores de `mapa_rgb` sustituidos (solo píxeles con alfa)."""
    salida = _rgba(im).copy()
    px = salida.load()
    for y in range(salida.size[1]):
        for x in range(salida.size[0]):
            c = px[x, y]
            if c[3] and c[:3] in mapa_rgb:
                px[x, y] = (*mapa_rgb[c[:3]], c[3])
    return salida


def drop_shadow(
    pieza: Image.Image,
    color: tuple[int, int, int] = (16, 32, 72),
    desplazamiento: tuple[int, int] = (1, 1),
) -> Image.Image:
    """Añade una sombra sólida del alfa de `pieza`, desplazada (V37.con_sombra)."""
    pieza = _rgba(pieza)
    dx, dy = desplazamiento
    if dx < 0 or dy < 0:
        raise ValueError(f"desplazamiento debe ser >= 0 en ambos ejes, no {desplazamiento}")
    salida = Image.new("RGBA", (pieza.width + dx, pieza.height + dy), TRANSPARENTE)
    sombra = Image.new("RGBA", pieza.size, (*color, 255))
    sombra.putalpha(pieza.split()[3])
    salida.alpha_composite(sombra, (dx, dy))
    salida.alpha_composite(pieza, (0, 0))
    return salida


def binarize_alpha(im: Image.Image, umbral: int = 110) -> Image.Image:
    """Copia de `im` con el alfa llevado a 0 o 255 según `umbral` (antialias fuera)."""
    salida = _rgba(im).copy()
    alfa = salida.split()[3].point(lambda v: 255 if v >= umbral else 0)
    salida.putalpha(alfa)
    return salida
