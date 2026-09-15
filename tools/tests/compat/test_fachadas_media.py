"""Fachadas F1.4 de gráficos y media: los shims de tools/ conservan la superficie v0."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from ie123kit.nucleo.compat.shims import MAPA
from ie123kit.nucleo.config.raiz import find_root

RAIZ = find_root()
TOOLS = RAIZ / "tools"
SUPERFICIE = json.loads((TOOLS / "tests" / "compat" / "superficie_v0.json").read_text(encoding="utf-8"))
MODULOS = ["translate_ui_textures", "mods_to_moflex", "ie1_keyboard"]


def _es_shim(nombre):
    ruta = TOOLS / f"{nombre}.py"
    return ruta.is_file() and "sys.modules[__name__]" in ruta.read_text(encoding="utf-8")


def _ejecutar(codigo):
    pre = "import sys; sys.path.insert(0, 'tools')\n"
    proc = subprocess.run([sys.executable, "-X", "utf8", "-c", pre + codigo], cwd=RAIZ,
                          capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


@pytest.mark.parametrize("nombre", MODULOS)
def test_destino_y_superficie(nombre):
    if not _es_shim(nombre):
        pytest.skip(f"{nombre} aún no es shim")
    nombres = sorted(SUPERFICIE[nombre])
    salida = _ejecutar(
        f"import {nombre} as m\n"
        "print(m.__name__)\n"
        f"print([n for n in {nombres!r} if getattr(m, n, None) is None])\n"
    )
    destino, faltan = salida.splitlines()
    assert destino == MAPA[nombre]
    assert faltan == "[]"


def test_identidades():
    if not all(_es_shim(n) for n in MODULOS):
        pytest.skip("faltan shims")
    salida = _ejecutar(
        "import translate_ui_textures, mods_to_moflex, ie1_keyboard\n"
        "import ie123kit.nucleo.graficos.pintado as p, ie123kit.nucleo.texto.nds_latin as n\n"
        "import ie123kit.ie1.graficos.teclado as t\n"
        "print(translate_ui_textures.paint is p.paint, mods_to_moflex.DS_TABLE is n.DS_TABLE,"
        " ie1_keyboard is t)\n"
        "print(mods_to_moflex.DEFAULT_MOBIPEG)\n"
        "print(mods_to_moflex.DEFAULT_FONT)\n"
    )
    ids, mobipeg, fuente = salida.splitlines()
    assert ids == "True True True"
    # Mismo valor que el original: REPO / work / shared / herramientas / media_tools / mobipeg-v2.1-x86.
    assert Path(mobipeg) == RAIZ / "work" / "shared" / "herramientas" / "media_tools" / "mobipeg-v2.1-x86"
    assert Path(fuente) == Path("C:/Windows/Fonts/arialbd.ttf")


def test_cli_sin_argumentos_sale_con_2():
    if not _es_shim("mods_to_moflex"):
        pytest.skip("mods_to_moflex aún no es shim")
    proc = subprocess.run([sys.executable, "-X", "utf8", "tools/mods_to_moflex.py"], cwd=RAIZ,
                          capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 2, proc.stderr
