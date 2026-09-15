"""Importar cualquier módulo de ie123kit no tiene efectos: sin salida, sin ficheros y sin IE123_ROOT."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

import ie123kit

SRC_PAQUETE = Path(ie123kit.__file__).resolve().parent


def _modulos() -> list[str]:
    nombres = []
    for ruta in sorted(SRC_PAQUETE.rglob("*.py")):
        if "__pycache__" in ruta.parts:
            continue
        partes = list(ruta.relative_to(SRC_PAQUETE).with_suffix("").parts)
        if partes[-1] == "__init__":
            partes = partes[:-1]
        nombres.append(".".join(["ie123kit", *partes]))
    return nombres


MODULOS = _modulos()


def test_hay_modulos_parametrizados() -> None:
    assert MODULOS, f"no hay módulos bajo {SRC_PAQUETE}"


@pytest.mark.parametrize("mod", MODULOS)
def test_importar_sin_efectos(mod: str, tmp_path: Path) -> None:
    env = os.environ.copy()
    previo = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(SRC_PAQUETE.parent) + (os.pathsep + previo if previo else "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("IE123_ROOT", None)
    res = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", f"import {mod}"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert res.returncode == 0, f"import {mod} falló:\n{res.stderr}"
    assert res.stdout == "", f"import {mod} escribe en stdout: {res.stdout!r}"
    assert res.stderr == "", f"import {mod} escribe en stderr: {res.stderr!r}"
    creados = list(tmp_path.iterdir())
    assert creados == [], f"import {mod} crea ficheros: {creados}"
