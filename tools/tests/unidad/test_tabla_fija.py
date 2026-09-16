"""RecordTable sobre los cuatro presets, con tablas sintéticas construidas en el propio test."""

from __future__ import annotations

import pytest

from ie123kit.nucleo.errores import ValidacionError
from ie123kit.nucleo.registros.tabla_fija import ITEM, RPGTITLE, TEAM, UNITBASE, RecordTable

PRESETS = [(UNITBASE, "name"), (TEAM, "name"), (ITEM, "name"), (RPGTITLE, "title")]


def cp932(texto: str) -> bytes:
    return texto.encode("cp932")


def tabla(spec, textos, campo):
    datos = bytearray(spec.header + spec.size * len(textos))
    for i, texto in enumerate(textos):
        rel, tam = spec.fields[campo]
        off = spec.header + i * spec.size + rel
        codificado = cp932(texto)
        datos[off:off + tam] = codificado + bytes(tam - len(codificado))
    return bytes(datos)


@pytest.mark.parametrize(("spec", "campo"), PRESETS)
def test_round_trip(spec, campo):
    original = tabla(spec, ["ab", "cd", "ef"], campo)
    t = RecordTable(original, spec)
    assert t.count == 3
    assert t.text(1, campo) == "cd"
    assert t.get(1, campo)[:2] == b"cd"
    assert t.to_bytes() == original

    t.set_text(1, campo, "zz", encoder=cp932)
    assert t.text(1, campo) == "zz"
    assert t.text(0, campo) == "ab"
    rel, tam = spec.fields[campo]
    inicio = spec.header + spec.size + rel
    assert t.rangos_cambiados() == [(inicio, inicio + tam)]


def test_capacidad_con_buffer_del_juego():
    # RPGTITLE tiene ranura de 32 B pero el juego solo lee 18: mandan los 18.
    assert RPGTITLE.capacidad("title") == 18
    t = RecordTable(tabla(RPGTITLE, ["a"], "title"), RPGTITLE)
    t.set_text(0, "title", "x" * 17, encoder=cp932)
    with pytest.raises(ValidacionError):
        t.set_text(0, "title", "x" * 18, encoder=cp932)


def test_falla_por_max_bytes():
    t = RecordTable(tabla(ITEM, ["a"], "name"), ITEM)
    t.set_text(0, "name", "hola", encoder=cp932, max_bytes=8)
    with pytest.raises(ValidacionError) as exc:
        t.set_text(0, "name", "demasiado", encoder=cp932, max_bytes=8)
    assert "no_cabe" in str(exc.value)


def test_falla_por_max_chars():
    t = RecordTable(tabla(UNITBASE, ["a"], "short"), UNITBASE)
    with pytest.raises(ValidacionError) as exc:
        t.set_text(0, "short", "12345678", encoder=cp932, max_chars=7)
    assert "texto_largo" in str(exc.value)


def test_campo_desconocido_y_registro_fuera():
    t = RecordTable(tabla(TEAM, ["a"], "name"), TEAM)
    with pytest.raises(ValidacionError):
        t.get(0, "inexistente")
    with pytest.raises(ValidacionError):
        t.get(5, "name")
