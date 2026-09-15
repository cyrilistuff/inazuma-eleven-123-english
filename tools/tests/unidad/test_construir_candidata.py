"""Equivalencia de ie123kit.nucleo.construir.candidata con tools/build_ui_revision.py (congelado)."""
import ast
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

import pytest

from ie123kit.nucleo.config.raiz import find_root
from ie123kit.nucleo.construir import candidata as C

RAIZ = find_root()
CONGELADO = RAIZ / "tools" / "build_ui_revision.py"
FUNCIONES = ("digest", "archive_payload", "replace_entry", "rebuild_events")


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


def _preparar(tmp_path):
    base = _fa_sintetico(tmp_path / "base.fa", {"a/uno.bin": b"uno" * 5, "b/dos.bin": b"dos", "c/tres.bin": b"t"})
    ui = tmp_path / "ui"
    (ui / "romfs/cro").mkdir(parents=True)
    (ui / "romfs/cro/ina_main1.cro").write_bytes(b"CRO sintetica" * 3)
    extra = tmp_path / "extra"
    (extra / "b").mkdir(parents=True)
    (extra / "b/dos.bin").write_bytes(b"DOS nuevo y mas largo")
    return base, ui, extra


def test_equivalencia_con_congelado(tmp_path):
    base, ui, extra = _preparar(tmp_path)
    o1 = tmp_path / "o1" / "archive.fa"
    o2 = tmp_path / "o2" / "archive.fa"
    env = dict(os.environ)
    env.pop("IE123_ROOT", None)
    r = subprocess.run([sys.executable, "-X", "utf8", "tools/build_ui_revision.py", "--base", str(base),
                        "--ui", str(ui), "--output", str(o1), "--extra", str(extra)],
                       cwd=RAIZ, env=env, capture_output=True, text=True, encoding="utf-8", check=False)
    assert r.returncode == 0, r.stderr
    report = C.construir(base, o2, ui=ui, capas=[extra])
    assert o1.read_bytes() == o2.read_bytes()
    cro = "romfs/cro/ina_main1.cro"
    assert (o1.parent / cro).read_bytes() == (o2.parent / cro).read_bytes()
    j1 = json.loads(o1.with_suffix(".build.json").read_text(encoding="utf-8"))
    j2 = json.loads(o2.with_suffix(".build.json").read_text(encoding="utf-8"))

    def normalizar(informe, salida):
        texto = json.dumps(informe, indent=2)
        return texto.replace(json.dumps(str(salida.parent.resolve()))[1:-1], "<SALIDA>")

    assert normalizar(j1, o1) == normalizar(j2, o2)
    assert j2 == report
    with pytest.raises(FileExistsError):
        C.construir(base, o2, ui=ui, capas=[extra])


def test_errores(tmp_path):
    base, ui, _ = _preparar(tmp_path)
    with pytest.raises(FileNotFoundError):
        C.construir(tmp_path / "no.fa", tmp_path / "o" / "archive.fa", ui=ui)
    malo = tmp_path / "malo" / "z"
    malo.mkdir(parents=True)
    (malo / "x.bin").write_bytes(b"x")
    with pytest.raises(ValueError):
        C.construir(base, tmp_path / "o3" / "archive.fa", ui=ui, capas=[tmp_path / "malo"])


def _funciones(texto):
    return {n.name: ast.dump(n) for n in ast.parse(texto).body
            if isinstance(n, ast.FunctionDef) and n.name in FUNCIONES}


def test_literalidad():
    a = _funciones(CONGELADO.read_text(encoding="utf-8"))
    b = _funciones(Path(C.__file__).read_text(encoding="utf-8"))
    assert set(a) == set(FUNCIONES)
    assert a == b


def test_congelado_conserva_rutas_de_eventos():
    texto = CONGELADO.read_text(encoding="utf-8")
    assert "inazuma1/data_iz/script/eve.pkh" in texto
    assert "inazuma1/data_iz/script/eve.pkb" in texto
