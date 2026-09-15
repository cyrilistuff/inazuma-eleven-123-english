"""Pruebas de ie123kit.ie1.verificar con candidatas IE1 sintéticas (sin datos del juego)."""
import hashlib
import json
import struct
from pathlib import Path

import pytest

from ie123kit.ie1 import verificar
from ie123kit.nucleo.compresion.lz10 import compress
from ie123kit.nucleo.errores import ValidacionError


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


EVENTOS = {5: b"evento cinco" * 4, 9: b"evento nueve" * 3}
CRO_BASE = b"CRO" * 16


def _packnum(eventos):
    pkb, idx = bytearray(), []
    for eid, datos in eventos.items():
        comp = compress(datos)
        idx.append((eid, len(pkb), len(comp)))
        pkb += comp + bytes((-len(comp)) % 4)
    pkh = bytearray(b"PackNum" + bytes(0x30 - 7))
    for rec in idx:
        pkh += struct.pack("<III", *rec)
    return bytes(pkh), bytes(pkb)


def _candidata(dir_, eventos, extra=None, cro=CRO_BASE):
    pkh, pkb = _packnum(eventos)
    ficheros = {"a/uno.bin": b"uno", "font/F.bcfnt": b"fuente",
                verificar.EVE[0]: pkh, verificar.EVE[1]: pkb, **(extra or {})}
    dir_.mkdir(parents=True)
    _fa_sintetico(dir_ / "archive.fa", ficheros)
    (dir_ / verificar.CRO).parent.mkdir(parents=True)
    (dir_ / verificar.CRO).write_bytes(cro)
    return dir_


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def test_report_con_capa_evento_y_literal(tmp_path):
    base = _candidata(tmp_path / "base", EVENTOS)
    cro_b = bytearray(CRO_BASE)
    cro_b[3:6] = b"xyz"
    cand = _candidata(tmp_path / "cand", {5: b"otro evento", 9: EVENTOS[9]}, {"a/uno.bin": b"UNO"}, bytes(cro_b))
    capa = tmp_path / "capa"
    (capa / "a").mkdir(parents=True)
    (capa / "a/uno.bin").write_bytes(b"UNO")
    ev = tmp_path / "ev"
    ev.mkdir()
    (ev / "5.ssd").write_bytes(b"otro evento")
    lit = tmp_path / "lit.json"
    lit.write_text(json.dumps({"entries": [{"offset": 3, "capacity": 3}]}), encoding="utf-8")
    report = verificar.verificar_candidata(base, cand, [capa], ev, lit)
    assert list(report) == ["candidate", "archive_sha256", "cro_sha256", "base_sha256", "replaced_entries",
                            "fonts_identical_to_base", "events_changed", "cro_literals_changed",
                            "dialogue_lock", "runtime_verified"]
    assert report == dict(candidate=str(cand), archive_sha256=_sha(cand / "archive.fa"),
                          cro_sha256=hashlib.sha256(cro_b).hexdigest(), base_sha256=_sha(base / "archive.fa"),
                          replaced_entries=1, fonts_identical_to_base=1, events_changed=[5],
                          cro_literals_changed=1, dialogue_lock="PASS", runtime_verified=False)


def test_candidatas_identicas(tmp_path):
    base = _candidata(tmp_path / "base", EVENTOS)
    cand = _candidata(tmp_path / "cand", EVENTOS)
    report = verificar.verificar_candidata(base, cand)
    assert (report["replaced_entries"], report["events_changed"], report["cro_literals_changed"]) == (0, [], 0)


def test_evento_no_preparado(tmp_path):
    base = _candidata(tmp_path / "base", EVENTOS)
    cand = _candidata(tmp_path / "cand", {5: EVENTOS[5], 9: b"cambiado"})
    with pytest.raises(ValidacionError) as info:
        verificar.verificar_candidata(base, cand)
    assert (info.value.codigo, info.value.detalle) == ("evento_cambiado", "event 9 changed")


def test_media_raiz_vacia(tmp_path):
    with pytest.raises(FileNotFoundError):
        verificar.verificar_media(tmp_path, tmp_path / "instalado")


def test_media_valida_y_escritura(tmp_path):
    report = {"failures": [], "movie_failures": [], "movies": [{}] * 21}
    assert verificar.media_valida(report)
    assert not verificar.media_valida({**report, "movies": []})
    destino = verificar.escribir_informe_media(report, tmp_path / "x" / "m.json")
    assert json.loads(destino.read_text(encoding="utf-8")) == report
