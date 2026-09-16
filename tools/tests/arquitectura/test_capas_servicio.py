"""La capa `servicio` no conoce los juegos, y los juegos no conocen `servicio` ni `cli`.

Punto (4) del gate de F2.1. Autocontenido a propósito: pytest usa `--import-mode=importlib`
y no se comparten ayudas con test_importaciones.py.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import ie123kit

SRC_PAQUETE = Path(ie123kit.__file__).resolve().parent

PROHIBIDO_EN_JUEGOS = ("servicio", "cli")
PROHIBIDO_EN_SERVICIO = ("juego_principal", "ie1", "ie2", "ie3", "_legado")
CAPAS_JUEGO = ("nucleo", "juego_principal", "ie1", "ie2", "ie3")


def _modulos() -> list[tuple[str, Path, bool]]:
    salida = []
    for ruta in sorted(SRC_PAQUETE.rglob("*.py")):
        if "__pycache__" in ruta.parts:
            continue
        partes = list(ruta.relative_to(SRC_PAQUETE).with_suffix("").parts)
        es_paquete = partes[-1] == "__init__"
        if es_paquete:
            partes = partes[:-1]
        salida.append((".".join(["ie123kit", *partes]), ruta, es_paquete))
    return salida


def _destinos(arbol: ast.AST, modulo: str, es_paquete: bool) -> list[tuple[int, str]]:
    """(línea, módulo absoluto) de cada importación de ie123kit, resolviendo las relativas."""
    paquete = modulo if es_paquete else modulo.rpartition(".")[0]
    salida: list[tuple[int, str]] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            salida += [(nodo.lineno, alias.name) for alias in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level:
                partes = paquete.split(".") if paquete else []
                subir = nodo.level - 1
                if subir:
                    partes = partes[: max(len(partes) - subir, 0)]
                base = ".".join(partes + ([nodo.module] if nodo.module else []))
            else:
                base = nodo.module or ""
            if base:
                salida.append((nodo.lineno, base))
            for alias in nodo.names:
                if alias.name != "*":
                    salida.append((nodo.lineno, f"{base}.{alias.name}" if base else alias.name))
    return [(n, d) for n, d in salida if d == "ie123kit" or d.startswith("ie123kit.")]


def _capa(modulo: str) -> str:
    partes = modulo.split(".")
    return "raiz" if len(partes) == 1 else partes[1]


MODULOS = _modulos()


def test_hay_modulos() -> None:
    assert MODULOS, f"no hay módulos bajo {SRC_PAQUETE}"


@pytest.mark.parametrize(("modulo", "ruta", "es_paquete"), MODULOS, ids=[m[0] for m in MODULOS])
def test_capas_servicio(modulo: str, ruta: Path, es_paquete: bool) -> None:
    origen = _capa(modulo)
    arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    fallos = []
    for linea, destino in _destinos(arbol, modulo, es_paquete):
        destino_capa = _capa(destino)
        if origen in CAPAS_JUEGO and destino_capa in PROHIBIDO_EN_JUEGOS:
            fallos.append(
                f"{ruta}:{linea}: {origen} importa {destino}; "
                f"nucleo/juego_principal/ie1/ie2/ie3 nunca importan ie123kit.servicio ni ie123kit.cli"
            )
        if origen == "servicio" and destino_capa in PROHIBIDO_EN_SERVICIO:
            fallos.append(
                f"{ruta}:{linea}: servicio importa {destino}; "
                f"servicio solo habla con nucleo y servicio (los juegos se cargan por registro)"
            )
    assert not fallos, "\n".join(fallos)


def test_detectores_ven_rojo() -> None:
    """Los detectores marcan los dos casos prohibidos y respetan los permitidos."""
    def capas(codigo: str, modulo: str, es_paquete: bool = False) -> list[str]:
        return [_capa(d) for _, d in _destinos(ast.parse(codigo), modulo, es_paquete)]

    assert "servicio" in capas("from ie123kit.servicio import api", "ie123kit.ie1.graficos")
    assert "cli" in capas("from ...cli import main", "ie123kit.ie2.comun.textos")
    assert "ie1" in capas("import ie123kit.ie1", "ie123kit.servicio.api")
    assert "_legado" in capas("from ie123kit._legado import viejo", "ie123kit.servicio.api")
    assert capas("from ie123kit.nucleo import tipos", "ie123kit.servicio.api") == ["nucleo", "nucleo"]
