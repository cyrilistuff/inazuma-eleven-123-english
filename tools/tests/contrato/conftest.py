"""Fixtures de la suite de contrato: proyecto sintético en tmp_path y servicio con el JuegoFalso."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

from fa_sintetico import escribir_fa
from juego_falso import FICHEROS, OBJETIVO, JuegoFalso

IE123_TOML = """\
[proyecto]
idioma = "es-ES"
nombres_europeos = true

[candidatas]
patron = "probe_ie1_v{n}"
conservar = 2
golden = []

[objetivos]
habilitados = ["ie1"]

[golden]
manifiestos = "tools/tests/compat/golden"
"""


@pytest.fixture
def proyecto_sintetico(tmp_path: Path):
    """Repo falso mínimo (AGENTS.md + tools/pyproject.toml + ie123.toml + archive.fa sintético)."""
    from ie123kit.servicio.proyecto import Workspace

    raiz = tmp_path / "repo"
    (raiz / "tools").mkdir(parents=True)
    (raiz / "AGENTS.md").write_text("# repo sintético de pruebas\n", encoding="utf-8")
    (raiz / "tools" / "pyproject.toml").write_text('[project]\nname = "ie123kit"\n', encoding="utf-8")
    (raiz / "ie123.toml").write_text(IE123_TOML, encoding="utf-8")
    escribir_fa(raiz / "work" / "shared" / "base_3ds" / "romfs" / "archive.fa", FICHEROS)
    return Workspace.abrir(raiz, entorno={})


@pytest.fixture
def juego_falso() -> JuegoFalso:
    return JuegoFalso()


@pytest.fixture
def servicio(proyecto_sintetico, juego_falso):
    """ServicioToolkit sobre el proyecto sintético, con el JuegoFalso inyectado."""
    from ie123kit.servicio.api import ServicioToolkit, descubrir_juegos

    juegos = descubrir_juegos(extra={OBJETIVO: juego_falso})
    return ServicioToolkit(proyecto_sintetico, juegos=juegos)
