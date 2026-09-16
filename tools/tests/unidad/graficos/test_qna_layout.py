"""QnaLayout sobre un maquetado QNA 051 mínimo construido con struct (sin ROM)."""

from __future__ import annotations

import struct

import pytest

from ie123kit.nucleo.graficos.qna import QnaLayout, qna_in_arc, regions

CABECERA = 64
NOMBRE = 32
PARTE = 128


def qna(nombres, partes):
    """``partes``: ``(caja_uv, x, y, indice_textura o None)``."""
    nombres_off = CABECERA
    partes_off = nombres_off + NOMBRE * len(nombres)
    datos = bytearray(partes_off + PARTE * len(partes))
    datos[:8] = b" QNA 051"
    struct.pack_into("<III", datos, 8, len(nombres), 0, len(partes))
    struct.pack_into("<III", datos, 36, nombres_off, 0, partes_off)
    for i, nombre in enumerate(nombres):
        crudo = nombre.encode("ascii")
        datos[nombres_off + i * NOMBRE:nombres_off + i * NOMBRE + len(crudo)] = crudo
    for i, (caja, x, y, tex) in enumerate(partes):
        o = partes_off + i * PARTE
        struct.pack_into("<4f", datos, o, *caja)
        for campo_x, campo_y in ((32, 36), (52, 56)):
            struct.pack_into("<f", datos, o + campo_x, x)
            struct.pack_into("<f", datos, o + campo_y, y)
        struct.pack_into("<I", datos, o + 88, 0xFFFFFFFF if tex is None else tex)
    return bytes(datos)


BLOB = qna(
    ["binder_t", "otra"],
    [((96.0, 32.0, 128.0, 64.0), 10.0, 20.0, 0),
     ((0.0, 0.0, 16.0, 16.0), 5.0, 5.0, 1),
     ((0.0, 0.0, 4.0, 4.0), 0.0, 0.0, None)],
)


def test_parse_y_regiones():
    layout = QnaLayout.parse(BLOB)
    assert layout.texturas == ["binder_t", "otra"]
    assert len(layout.partes) == 3
    assert layout.partes[0].caja == (96.0, 32.0, 128.0, 64.0)
    assert layout.partes[2].indice_textura is None
    assert layout.regions_for("binder_t") == [(96, 32, 128, 64)]
    assert layout.regions_for("binder_t.tga") == [(96, 32, 128, 64)]
    assert layout.regions_for("inexistente") == []


def test_regions_sigue_funcionando():
    assert regions(BLOB) == sorted({("binder_t", (96, 32, 128, 64)), ("otra", (0, 0, 16, 16))})


def test_move_escribe_los_dos_campos():
    layout = QnaLayout.parse(BLOB)
    layout.partes[0].move(-16.0, 4.0)
    assert (layout.partes[0].x, layout.partes[0].y) == (-6.0, 24.0)
    salida = layout.to_bytes()
    assert len(salida) == len(BLOB)
    base = 64 + 32 * 2
    for campo_x, campo_y in ((32, 36), (52, 56)):
        assert struct.unpack_from("<f", salida, base + campo_x)[0] == -6.0
        assert struct.unpack_from("<f", salida, base + campo_y)[0] == 24.0
    # Nada más cambia: el resto del blob es idéntico.
    assert salida[:base + 32] == BLOB[:base + 32]


def test_to_bytes_conserva_tamano():
    layout = QnaLayout.parse(BLOB)
    assert layout.to_bytes() == BLOB
    layout.datos += b"\0"
    with pytest.raises(ValueError, match="size"):
        layout.to_bytes()


def test_version_no_soportada():
    with pytest.raises(ValueError, match="QNA"):
        QnaLayout.parse(b" QNA 999" + bytes(120))


def test_qna_in_arc():
    otro = b"CTPK" + bytes(28)
    blobs = [otro, BLOB]
    tabla = 12 + 12 * len(blobs)
    cuerpo = bytearray()
    entradas = []
    for blob in blobs:
        entradas.append((tabla + len(cuerpo), len(blob)))
        cuerpo += blob
    datos = bytearray(b"ARCV" + struct.pack("<II", len(blobs), tabla + len(cuerpo)))
    for off, tam in entradas:
        datos += struct.pack("<III", off, tam, 0)
    datos += cuerpo
    encontrados = qna_in_arc(bytes(datos))
    assert [off for off, _ in encontrados] == [entradas[1][0]]
    assert encontrados[0][1].regions_for("binder_t") == [(96, 32, 128, 64)]
