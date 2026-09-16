"""Cro y CroPatcher sobre una CRO sintética mínima (sin ROM ni datos extraídos)."""

from __future__ import annotations

import json
import struct

import pytest

from ie123kit.nucleo.ejecutable.cro import Cro, CroPatcher
from ie123kit.nucleo.errores import ValidacionError

TAM = 0x400
SEG_TABLA, REL_TABLA = 0x200, 0x240
CODIGO, DATOS = 0x300, 0x340
LIT_A, LIT_B = 0x340, 0x350


def cro_sintetica() -> bytes:
    datos = bytearray(TAM)
    struct.pack_into("<I", datos, 0xC8, SEG_TABLA)
    struct.pack_into("<I", datos, 0xCC, 2)
    struct.pack_into("<III", datos, SEG_TABLA, CODIGO, 0x40, 0)
    struct.pack_into("<III", datos, SEG_TABLA + 12, DATOS, 0x40, 2)
    struct.pack_into("<I", datos, 0x128, REL_TABLA)
    struct.pack_into("<I", datos, 0x12C, 2)
    # Relocación 0: destino 0x310 (segmento 0), valor 0x350 (segmento 1 + 0x10).
    struct.pack_into("<IBBBBI", datos, REL_TABLA, ((0x310 - CODIGO) << 4) | 0, 2, 1, 0, 0, 0x10)
    # Relocación 1: destino 0x318, valor 0x340.
    struct.pack_into("<IBBBBI", datos, REL_TABLA + 12, ((0x318 - CODIGO) << 4) | 0, 2, 1, 0, 0, 0x00)
    # ADD rX, pc, #0x40 en 0x300 -> referencia a 0x348.
    struct.pack_into("<I", datos, CODIGO, 0xE28F0040)
    for offset in (LIT_A, LIT_B):
        datos[offset:offset + 2] = "ab".encode("cp932")
    return bytes(datos)


def cp932(texto: str) -> bytes:
    return texto.encode("cp932")


@pytest.fixture
def base(tmp_path):
    ruta = tmp_path / "ina_main2.cro"
    ruta.write_bytes(cro_sintetica())
    return ruta


def test_segmentos_y_relocaciones():
    cro = Cro(cro_sintetica())
    assert [(s.offset, s.size, s.id) for s in cro.segments] == [(CODIGO, 0x40, 0), (DATOS, 0x40, 2)]
    relocs = cro.relocations
    assert [(r.target, r.value) for r in relocs] == [(0x310, 0x350), (0x318, 0x340)]
    assert cro.imports() == {}


def test_referencias_adr():
    cro = Cro(cro_sintetica())
    assert ("adr", CODIGO) in cro.references(0x348)
    assert cro.references(0x344) == []


def test_retarget_correcto_e_incorrecto():
    cro = Cro(cro_sintetica())
    nuevo = cro.retarget(0x310, 0x360, expect_old=0x350)
    assert (nuevo.seg_index, nuevo.addend, nuevo.value) == (1, 0x20, 0x360)
    assert cro.relocations[1].value == 0x340

    otra = Cro(cro_sintetica())
    with pytest.raises(ValidacionError, match="relocacion_inesperada"):
        otra.retarget(0x310, 0x360, expect_old=0x344)
    with pytest.raises(ValidacionError, match="relocacion_ambigua"):
        otra.retarget(0x999, 0x360)
    with pytest.raises(ValidacionError, match="valor_fuera_de_segmento"):
        otra.retarget(0x310, 0x10)


def test_find_literal(base):
    p = CroPatcher(base)
    assert p.find_literal("ab") == [LIT_A, LIT_B]
    assert p.find_literal("zz") == []


def test_literal_que_cabe_y_que_no(base):
    p = CroPatcher(base)
    assert p.literal(LIT_A, "ab", "x", encoder=cp932) == (LIT_A, LIT_A + 3)
    assert bytes(p.datos[LIT_A:LIT_A + 3]) == b"x\0\0"
    with pytest.raises(ValidacionError, match="literal_no_cabe"):
        p.literal(LIT_B, "ab", "xyz", encoder=cp932)
    with pytest.raises(ValidacionError, match="literal_inesperado"):
        p.literal(LIT_B + 1, "ab", "x", encoder=cp932)
    # El hueco de relleno solo se usa si se pide explícitamente.
    p.literal(LIT_B, "ab", "xyz", encoder=cp932, allow_growth_into_padding=True)
    assert bytes(p.datos[LIT_B:LIT_B + 4]) == b"xyz\0"


def test_literal_vacio_usa_el_blanco(base):
    p = CroPatcher(base)
    p.literal(LIT_A, "ab", "", encoder=cp932)
    assert bytes(p.datos[LIT_A:LIT_A + 3]) == "　".encode("cp932") + b"\0"


def test_raw(base):
    p = CroPatcher(base)
    p.raw(LIT_A, b"ab", b"cd")
    with pytest.raises(ValidacionError, match="raw_inesperado"):
        p.raw(LIT_A, b"ab", b"cd")
    with pytest.raises(ValidacionError, match="raw_tamano_distinto"):
        p.raw(LIT_B, b"ab", b"c")


def test_save_escribe_y_comprueba_rangos(base, tmp_path):
    capa = tmp_path / "capa"
    p = CroPatcher(base)
    p.literal(LIT_A, "ab", "x", encoder=cp932)
    destino = p.save(capa)
    assert destino == capa / "romfs" / "cro" / "ina_main2.cro"
    assert destino.read_bytes()[LIT_A:LIT_A + 3] == b"x\0\0"
    informe = json.loads((capa / "cro_literales.json").read_text(encoding="utf-8"))
    assert informe["cro"] == "ina_main2.cro"
    assert informe["rangos"] == [[LIT_A, LIT_A + 3]]

    otro = CroPatcher(base)
    otro.literal(LIT_A, "ab", "x", encoder=cp932)
    otro.datos[CODIGO + 8] = 0x42  # cambio no declarado
    with pytest.raises(ValidacionError, match="cambio_fuera_de_rango"):
        otro.save(capa)
