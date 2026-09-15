"""Tests de arquitectura de ie123kit: reglas de importación por AST.

Ver docs/toolkit/ESPECIFICACION.md, «API de librería → REGLAS DE IMPORTACIÓN».
Solo se analiza tools/src/ie123kit; los scripts de tools/*.py quedan fuera.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

import ie123kit

SRC_PAQUETE = Path(ie123kit.__file__).resolve().parent

CAPAS = {"nucleo", "juego_principal", "ie1", "ie2", "ie3", "servicio", "cli", "_legado"}
VERSIONES = {
    "ie2": {"tormenta_de_fuego", "ventisca_eterna"},
    "ie3": {"rayo_celeste", "fuego_explosivo", "amenaza_del_ogro"},
}
RE_RUTA_MAQUINA = re.compile(r"(?i)([a-z]:[\\/]+users[\\/])|(/home/)|(/users/)|(\bdownloads\b)")


# --------------------------------------------------------------------------- utilidades puras


def nombre_modulo(ruta: Path, base: Path = SRC_PAQUETE) -> tuple[str, bool]:
    """Nombre punteado de un fichero bajo el paquete y si es un __init__.py."""
    partes = list(ruta.relative_to(base).with_suffix("").parts)
    es_paquete = partes[-1] == "__init__"
    if es_paquete:
        partes = partes[:-1]
    return ".".join(["ie123kit", *partes]), es_paquete


def modulos_reales() -> list[tuple[str, Path, bool]]:
    salida = []
    for ruta in sorted(SRC_PAQUETE.rglob("*.py")):
        if "__pycache__" in ruta.parts:
            continue
        nombre, es_paquete = nombre_modulo(ruta)
        salida.append((nombre, ruta, es_paquete))
    return salida


def capa(modulo: str) -> str:
    partes = modulo.split(".")
    return "raiz" if len(partes) == 1 else partes[1]


def _bajo(nombre: str, prefijo: str) -> bool:
    return nombre == prefijo or nombre.startswith(prefijo + ".")


def importaciones(arbol: ast.AST, modulo: str, es_paquete: bool) -> list[tuple[int, str]]:
    """(línea, nombre absoluto) de cada importación de ie123kit; resuelve relativas."""
    paquete = modulo if es_paquete else modulo.rpartition(".")[0]
    salida: list[tuple[int, str]] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            salida.extend((nodo.lineno, alias.name) for alias in nodo.names)
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
    return [(linea, n) for linea, n in salida if _bajo(n, "ie123kit")]


def violaciones_importacion(modulo: str, destino: str) -> str | None:
    if destino == "ie123kit":
        return None
    origen = capa(modulo)
    dcapa = capa(destino)

    if dcapa == "_legado" and origen != "_legado":
        return "(f) nadie salvo _legado importa ie123kit._legado"
    if origen == "raiz":
        return "(g) ie123kit/__init__.py no importa subpaquetes de ie123kit"
    if origen == "nucleo":
        if dcapa in CAPAS - {"nucleo"}:
            return f"(a) nucleo no importa ie123kit.{dcapa}"
        return None
    if origen == "juego_principal":
        ok = dcapa in ("nucleo", "juego_principal")
        return None if ok else "(b) juego_principal solo importa nucleo y juego_principal"
    if origen == "ie1":
        return None if dcapa in ("nucleo", "ie1") else "(c) ie1 solo importa nucleo e ie1"
    if origen in VERSIONES:
        if dcapa == "nucleo":
            return None
        if dcapa != origen:
            return f"(d) {origen} no importa ie123kit.{dcapa}"
        om, dm = modulo.split("."), destino.split(".")
        sub = om[2] if len(om) > 2 else None
        dsub = dm[2] if len(dm) > 2 else None
        if sub is None:
            return f"(d) {origen}/__init__ solo importa nucleo"
        if sub == "comun":
            return None if dsub == "comun" else f"(d) {origen}.comun solo importa nucleo y {origen}.comun"
        if dsub in ("comun", sub):
            return None
        return f"(d) {origen}.{sub} solo importa nucleo, {origen}.comun y su propia versión"
    if origen == "servicio":
        return None if dcapa in ("nucleo", "servicio") else "(e) servicio solo importa nucleo y servicio"
    if origen == "cli":
        return None if dcapa in ("servicio", "cli") else "(e) cli solo importa servicio y cli"
    return None


def usa_parents_indexado(texto: str) -> bool:
    return "parents[" in texto or "dirname(dirname" in texto


def _ids_docstrings(arbol: ast.AST) -> set[int]:
    ids = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            cuerpo = nodo.body
            if (
                cuerpo
                and isinstance(cuerpo[0], ast.Expr)
                and isinstance(cuerpo[0].value, ast.Constant)
                and isinstance(cuerpo[0].value.value, str)
            ):
                ids.add(id(cuerpo[0].value))
    return ids


def rutas_de_maquina(arbol: ast.AST) -> list[tuple[int, str]]:
    """Literales str (incluidas partes de f-strings), sin docstrings, con rutas de máquina."""
    docs = _ids_docstrings(arbol)
    salida = []
    for nodo in ast.walk(arbol):
        if (
            isinstance(nodo, ast.Constant)
            and isinstance(nodo.value, str)
            and id(nodo) not in docs
            and RE_RUTA_MAQUINA.search(nodo.value)
        ):
            salida.append((nodo.lineno, nodo.value))
    return salida


def _es_bloque_main(nodo: ast.AST) -> bool:
    if not isinstance(nodo, ast.If) or not isinstance(nodo.test, ast.Compare):
        return False
    t = nodo.test
    lados = [t.left, *t.comparators]
    return (
        len(t.ops) == 1
        and isinstance(t.ops[0], ast.Eq)
        and any(isinstance(x, ast.Name) and x.id == "__name__" for x in lados)
        and any(isinstance(x, ast.Constant) and x.value == "__main__" for x in lados)
    )


def print_o_exit_en_nucleo(arbol: ast.AST, modulo: str) -> list[tuple[int, str]]:
    if capa(modulo) != "nucleo" or _bajo(modulo, "ie123kit.nucleo.compat"):
        return []
    salida: list[tuple[int, str]] = []

    def visitar(nodo: ast.AST) -> None:
        if _es_bloque_main(nodo):
            for hijo in nodo.orelse:
                visitar(hijo)
            return
        if isinstance(nodo, ast.Call):
            f = nodo.func
            if isinstance(f, ast.Name) and f.id in ("print", "exit", "quit"):
                salida.append((nodo.lineno, f"{f.id}(...)"))
            elif (
                isinstance(f, ast.Attribute)
                and f.attr == "exit"
                and isinstance(f.value, ast.Name)
                and f.value.id == "sys"
            ):
                salida.append((nodo.lineno, "sys.exit(...)"))
        elif isinstance(nodo, ast.Raise) and nodo.exc is not None:
            exc = nodo.exc.func if isinstance(nodo.exc, ast.Call) else nodo.exc
            if isinstance(exc, ast.Name) and exc.id == "SystemExit":
                salida.append((nodo.lineno, "raise SystemExit"))
        for hijo in ast.iter_child_nodes(nodo):
            visitar(hijo)

    visitar(arbol)
    return salida


# --------------------------------------------------------------------------- tests sobre src

MODULOS = modulos_reales()


@pytest.mark.parametrize(("modulo", "ruta", "es_paquete"), MODULOS, ids=[m[0] for m in MODULOS])
def test_reglas_modulo(modulo: str, ruta: Path, es_paquete: bool) -> None:
    texto = ruta.read_text(encoding="utf-8")
    arbol = ast.parse(texto, filename=str(ruta))
    fallos = []
    for linea, destino in importaciones(arbol, modulo, es_paquete):
        regla = violaciones_importacion(modulo, destino)
        if regla:
            fallos.append(f"{ruta}:{linea}: importa {destino} -> {regla}")
    for n, contenido in enumerate(texto.splitlines(), 1):
        if usa_parents_indexado(contenido):
            fallos.append(f"{ruta}:{n}: prohibido parents[N] / dirname(dirname")
    for linea, valor in rutas_de_maquina(arbol):
        fallos.append(f"{ruta}:{linea}: ruta de máquina en literal {valor!r}")
    for linea, que in print_o_exit_en_nucleo(arbol, modulo):
        fallos.append(f"{ruta}:{linea}: {que} en nucleo fuera de compat y de __main__")
    assert not fallos, "\n".join(fallos)


def test_hay_modulos() -> None:
    assert len(MODULOS) >= 18, f"solo {len(MODULOS)} módulos en {SRC_PAQUETE}"


def test_esqueleto() -> None:
    paquetes = [
        "",
        "nucleo",
        "nucleo/config",
        "juego_principal",
        "ie1",
        "ie2",
        "ie2/comun",
        "ie2/tormenta_de_fuego",
        "ie2/ventisca_eterna",
        "ie3",
        "ie3/comun",
        "ie3/rayo_celeste",
        "ie3/fuego_explosivo",
        "ie3/amenaza_del_ogro",
        "_legado",
    ]
    faltan = [p or "ie123kit" for p in paquetes if not (SRC_PAQUETE / p / "__init__.py").is_file()]
    faltan += [f for f in ("nucleo/errores.py", "nucleo/config/raiz.py") if not (SRC_PAQUETE / f).is_file()]
    assert not faltan, f"faltan en el esqueleto: {faltan}"


# --------------------------------------------------------------------------- los detectores ven rojo


def _viol(codigo: str, modulo: str, es_paquete: bool = False) -> list[str]:
    arbol = ast.parse(codigo)
    return [r for _, d in importaciones(arbol, modulo, es_paquete) if (r := violaciones_importacion(modulo, d))]


def test_detectores_ven_rojo() -> None:
    assert _viol("import ie123kit.ie1.x", "ie123kit.nucleo.a")
    assert _viol("from ...ie1 import x", "ie123kit.nucleo.config.raiz")
    assert _viol("from ie123kit.ie2 import comun", "ie123kit.ie1.a")
    assert _viol("from ie123kit.ie2.ventisca_eterna import t", "ie123kit.ie2.tormenta_de_fuego.a")
    assert _viol("import ie123kit.ie2.comun", "ie123kit.ie3.rayo_celeste.a")
    assert _viol("from ..ventisca_eterna import t", "ie123kit.ie2.comun.a")
    assert _viol("from ie123kit._legado import viejo", "ie123kit.nucleo.a")
    assert _viol("from ie123kit import nucleo", "ie123kit", es_paquete=True)
    assert usa_parents_indexado("ROOT = Path(__file__).resolve().parents[2]")
    assert rutas_de_maquina(ast.parse("R = 'C:/Users/x'"))
    assert rutas_de_maquina(ast.parse("R = f'C:/Users/{x}'"))
    assert print_o_exit_en_nucleo(ast.parse("print('x')"), "ie123kit.nucleo.construir.algo")
    assert print_o_exit_en_nucleo(ast.parse("import sys\nsys.exit(1)"), "ie123kit.nucleo.a")
    assert print_o_exit_en_nucleo(ast.parse("raise SystemExit(2)"), "ie123kit.nucleo.a")

    # Casos permitidos: no deben dar violación.
    assert not _viol("from ie123kit.ie2.comun import x\nfrom ..comun import y", "ie123kit.ie2.ventisca_eterna.a")
    assert not _viol("from ie123kit.nucleo import errores\nimport ie123kit", "ie123kit.ie1.a")
    assert not usa_parents_indexado("for p in [r, *r.parents]: pass")
    assert not rutas_de_maquina(ast.parse('"""Ejemplo: C:/Users/x"""\nA = 1'))
    main = "def f():\n    return 1\nif __name__ == '__main__':\n    print('x')\n"
    assert not print_o_exit_en_nucleo(ast.parse(main), "ie123kit.nucleo.construir.algo")
    assert not print_o_exit_en_nucleo(ast.parse("print('x')"), "ie123kit.nucleo.compat.golden")
