"""Pruebas del diff genérico de candidatas (ie123kit.nucleo.validar.candidata) con B123 sintéticos."""
import hashlib
import struct
from pathlib import Path

import pytest

from ie123kit.nucleo.contenedores.fa import FaArchive
from ie123kit.nucleo.errores import ValidacionError
from ie123kit.nucleo.validar import candidata as V


def _fa_sintetico(ruta: Path, ficheros: dict[str, bytes]) -> Path:
    """Escribe un contenedor B123 mínimo que FaArchive sabe recorrer."""
    carpetas: dict[str, list[tuple[str, bytes]]] = {}
    for rel, datos in ficheros.items():
        carpeta, _, nombre = rel.rpartition("/")
        carpetas.setdefault(carpeta + "/" if carpeta else "", []).append((nombre, datos))
    nombres, datos_blob, de, fe = bytearray(), bytearray(), bytearray(), bytearray()
    primero = 0
    for carpeta, lista in carpetas.items():
        dir_name_off = len(nombres)
        nombres += carpeta.encode("ascii") + b"\0"
        name_base = len(nombres)
        for nombre, datos in lista:
            fe += struct.pack("<IIII", 0, len(nombres) - name_base, len(datos_blob), len(datos))
            nombres += nombre.encode("ascii") + b"\0"
            datos_blob += datos
        de += struct.pack("<IHHIIII", 0, len(lista), 0, name_base, primero, 0, dir_name_off)
        primero += len(lista)
    de_off = 32
    fe_off = de_off + len(de)
    name_off = fe_off + len(fe)
    data_off = name_off + len(nombres)
    cabecera = b"B123" + struct.pack("<5i", de_off, de_off, fe_off, name_off, data_off)
    cabecera += struct.pack("<HHI", len(carpetas), 0, primero)
    ruta.write_bytes(cabecera + de + fe + nombres + datos_blob)
    return ruta


BASE = {"a/uno.bin": b"uno", "font/F.bcfnt": b"fuente", "b/dos.bin": b"dos"}


def _par(tmp_path, cambios):
    base = FaArchive(str(_fa_sintetico(tmp_path / "base.fa", BASE)))
    cand = FaArchive(str(_fa_sintetico(tmp_path / "cand.fa", {**BASE, **cambios})))
    return base, cand


def _capa(dir_, ficheros):
    for rel, datos in ficheros.items():
        (dir_ / rel).parent.mkdir(parents=True, exist_ok=True)
        (dir_ / rel).write_bytes(datos)
    return dir_


def test_sha256_indice_y_payload(tmp_path):
    ruta = _fa_sintetico(tmp_path / "x.fa", BASE)
    assert V.sha256_fichero(ruta) == hashlib.sha256(ruta.read_bytes()).hexdigest()
    arc = FaArchive(str(ruta))
    idx = V.indice(arc)
    assert list(idx) == list(BASE)
    assert V.payload(arc, idx, "b/dos.bin") == b"dos"


def test_capa_correcta(tmp_path):
    base, cand = _par(tmp_path, {"a/uno.bin": b"UNO"})
    capas = V.cargar_capas([_capa(tmp_path / "capa", {"a/uno.bin": b"UNO"})])
    assert V.comprobar_entradas(base, cand, capas) == (1, 1)


def test_capas_posteriores_ganan(tmp_path):
    c1 = _capa(tmp_path / "c1", {"a/uno.bin": b"1"})
    c2 = _capa(tmp_path / "c2", {"a/uno.bin": b"2"})
    assert V.cargar_capas([c1, c2]) == {"a/uno.bin": b"2"}


def test_capa_distinta(tmp_path):
    base, cand = _par(tmp_path, {"a/uno.bin": b"UNO"})
    with pytest.raises(ValidacionError) as info:
        V.comprobar_entradas(base, cand, {"a/uno.bin": b"otro"})
    assert (info.value.codigo, info.value.detalle, info.value.ruta) == (
        "capa_distinta", "layer mismatch: a/uno.bin", "a/uno.bin")


def test_cambio_inesperado(tmp_path):
    base, cand = _par(tmp_path, {"b/dos.bin": b"DOS"})
    with pytest.raises(ValidacionError) as info:
        V.comprobar_entradas(base, cand, {})
    assert (info.value.codigo, info.value.detalle) == ("cambio_inesperado", "unexpected change: b/dos.bin")


def test_ignoradas(tmp_path):
    base, cand = _par(tmp_path, {"b/dos.bin": b"DOS"})
    assert V.comprobar_entradas(base, cand, {}, ignoradas=("b/dos.bin",)) == (0, 1)


def test_fuente_cambiada(tmp_path):
    base, cand = _par(tmp_path, {"font/F.bcfnt": b"FUENTE"})
    with pytest.raises(ValidacionError) as info:
        V.comprobar_entradas(base, cand, {"font/F.bcfnt": b"FUENTE"})
    assert (info.value.codigo, info.value.detalle) == ("fuente_cambiada", "font changed: font/F.bcfnt")


def test_lista_entradas(tmp_path):
    base = FaArchive(str(_fa_sintetico(tmp_path / "base.fa", BASE)))
    cand = FaArchive(str(_fa_sintetico(tmp_path / "cand.fa", {"a/uno.bin": b"uno"})))
    with pytest.raises(ValidacionError) as info:
        V.comprobar_entradas(base, cand, {})
    assert (info.value.codigo, info.value.detalle) == ("lista_entradas", "entry list changed")


def test_literales_cro():
    a = bytes(range(32))
    b = bytearray(a)
    b[4:8] = b"HOLA"
    V.comprobar_literales_cro(a, bytes(b), [{"offset": 4, "capacity": 4}])
    for lits, cro in (([], bytes(b)), ([{"offset": 4, "capacity": 4}], bytes(b) + b"x")):
        with pytest.raises(ValidacionError) as info:
            V.comprobar_literales_cro(a, cro, lits)
        assert (info.value.codigo, info.value.detalle) == (
            "cro_fuera_de_literales", "CRO changed outside declared literals")
