"""Cuarentena de los módulos obsolete_dangerous y fachada de reinsert (F1.4, T2)."""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys

import pytest

from ie123kit.nucleo.compat import shims
from ie123kit.nucleo.config.raiz import find_root

RAIZ = find_root()
TOOLS = RAIZ / "tools"
CUARENTENA = ("ds_roster", "reinsert_var", "ssd_reinsert", "validate")
SUPERFICIE = json.loads((TOOLS / "tests/compat/superficie_v0.json").read_text(encoding="utf-8"))


def _es_shim(nombre: str) -> bool:
    return "Shim generado por ie123kit" in (TOOLS / f"{nombre}.py").read_text(encoding="utf-8")


def _importar(nombre: str):
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    return importlib.import_module(nombre)


@pytest.mark.parametrize("nombre", CUARENTENA)
def test_cli_se_niega_sin_bandera(nombre):
    if not _es_shim(nombre):
        pytest.skip("aún no es shim")
    entorno = {k: v for k, v in os.environ.items() if not k.startswith("IE123_")}
    r = subprocess.run([sys.executable, "-X", "utf8", f"tools/{nombre}.py"], cwd=RAIZ, env=entorno,
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 2
    assert r.stdout == ""
    assert "--legado-lo-se" in r.stderr and "cuarentena" in r.stderr


@pytest.mark.parametrize("nombre", CUARENTENA + ("reinsert",))
def test_superficie(nombre):
    if not _es_shim(nombre):
        pytest.skip("aún no es shim")
    assert shims.MAPA[nombre] == f"ie123kit._legado.{nombre}"
    mod = _importar(nombre)
    assert mod is importlib.import_module(f"ie123kit._legado.{nombre}")
    for atributo in SUPERFICIE[nombre]:
        getattr(mod, atributo)


def test_funciones_de_libreria():
    if not all(_es_shim(n) for n in CUARENTENA):
        pytest.skip("aún no son shims")
    assert _importar("reinsert_var").DONT_TOUCH == {81000040}
    assert callable(_importar("validate").run)
    assert callable(_importar("ds_roster").patch_unitbase)
    from ie123kit import _legado
    assert _legado.CUARENTENA == frozenset(CUARENTENA)
    assert _legado.EXCLUIDOS_DEL_REGISTRO == _legado.CUARENTENA | {"ds_official"}
    assert _legado.BANDERA_LEGADO == "--legado-lo-se"
