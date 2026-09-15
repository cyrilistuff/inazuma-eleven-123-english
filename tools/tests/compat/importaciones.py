"""Comprueba por AST que los imports de módulos de tools/ en los scripts de work/ se resuelven.

Uso: python tools/tests/compat/importaciones.py [--work work] [--baseline B.json] [--capturar B.json]
Sale con 1 si hay imports no resueltos que no estén ya en la línea base.
"""
import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / 'tools'
EXTERNOS = {'numpy', 'PIL', 'capstone'}


def modulos_tools():
    return {p.stem for p in TOOLS.glob('*.py')} | {p.name for p in TOOLS.iterdir() if (p / '__init__.py').is_file()}


def usa_tools(texto):
    return any(m in texto for m in ("'tools'", '"tools"', '/tools', 'tools/'))


def importados(arbol):
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for a in nodo.names:
                yield nodo.lineno, a.name.split('.')[0], None
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and nodo.module:
            yield nodo.lineno, nodo.module.split('.')[0], [a.name for a in nodo.names]


def definidos(ruta, cache={}):
    if ruta not in cache:
        nombres = set()
        for nodo in ast.walk(ast.parse(ruta.read_text(encoding='utf-8', errors='replace'))):
            if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                nombres.add(nodo.name)
            elif isinstance(nodo, (ast.Assign, ast.AnnAssign)):
                for t in (nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]):
                    nombres.update(n.id for n in ast.walk(t) if isinstance(n, ast.Name))
            elif isinstance(nodo, (ast.Import, ast.ImportFrom)):
                nombres.update((a.asname or a.name).split('.')[0] for a in nodo.names)
        cache[ruta] = nombres
    return cache[ruta]


def analizar(work):
    disponibles = modulos_tools()
    scripts = sorted(Path(work).rglob('*.py'))
    # Módulos hermanos de otras capas (p. ej. v33/eve_labels/common.py) no son de tools/.
    conocidos = set(sys.stdlib_module_names) | EXTERNOS | ({p.stem for p in scripts} - disponibles)
    fallos, total = [], 0
    for script in scripts:
        if script.stat().st_size > 3_000_000:
            continue
        texto = script.read_text(encoding='utf-8', errors='replace')
        if not usa_tools(texto):
            continue
        total += 1
        rel = script.relative_to(ROOT).as_posix()
        try:
            arbol = ast.parse(texto)
        except SyntaxError as e:
            fallos.append(f'{rel}: sintaxis línea {e.lineno}')
            continue
        locales = {p.stem for p in script.parent.glob('*.py')}
        for linea, mod, nombres in importados(arbol):
            if mod in conocidos or mod in locales:
                continue
            if mod not in disponibles:
                fallos.append(f'{rel}:{linea}: módulo {mod}')
            elif nombres and (TOOLS / f'{mod}.py').is_file():
                fallos += [f'{rel}:{linea}: {mod}.{n}' for n in nombres
                           if n != '*' and n not in definidos(TOOLS / f'{mod}.py')]
    return total, sorted(set(fallos))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', default=str(ROOT / 'work'))
    ap.add_argument('--baseline')
    ap.add_argument('--capturar')
    args = ap.parse_args()
    total, fallos = analizar(args.work)
    if args.capturar:
        Path(args.capturar).write_text(json.dumps(fallos, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    previos = set(json.loads(Path(args.baseline).read_text(encoding='utf-8'))) if args.baseline else set()
    nuevos = [f for f in fallos if f not in previos]
    for f in nuevos:
        print('NO RESUELTO', f)
    print(f'{total} scripts de work/ usan tools/; {len(fallos)} no resueltos '
          f'({len(fallos) - len(nuevos)} en línea base); {len(nuevos)} nuevos')
    return 1 if nuevos and not args.capturar else 0


if __name__ == '__main__':
    sys.exit(main())
