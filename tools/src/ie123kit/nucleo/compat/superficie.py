"""Captura o compara la superficie pública (nombres y firmas, por AST) de los módulos de tools/.

Uso: python -m ie123kit.nucleo.compat.superficie capturar|comprobar|comparar [FICHERO] [--fichero superficie_v0.json]
Va por AST para no ejecutar módulos con efectos al importar. comprobar (o su alias comparar) falla si
desaparece un nombre o cambia una firma; un módulo convertido en shim (sys.modules[__name__]) se da por bueno.
"""
import argparse
import ast
import json
import sys
from pathlib import Path


def _tools():
    from ie123kit.nucleo.config.raiz import find_root
    return find_root() / 'tools'


def firma(nodo):
    a = nodo.args
    partes = [x.arg for x in a.posonlyargs + a.args]
    if a.vararg:
        partes.append('*' + a.vararg.arg)
    partes += [x.arg for x in a.kwonlyargs]
    if a.kwarg:
        partes.append('**' + a.kwarg.arg)
    return 'def(' + ', '.join(partes) + ')'


def superficie(ruta):
    out = {}
    for nodo in ast.parse(ruta.read_text(encoding='utf-8', errors='replace')).body:
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[nodo.name] = firma(nodo)
        elif isinstance(nodo, ast.ClassDef):
            out[nodo.name] = 'class'
            out.update({f'{nodo.name}.{m.name}': firma(m) for m in nodo.body
                        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))})
        elif isinstance(nodo, (ast.Assign, ast.AnnAssign)):
            for t in (nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]):
                if isinstance(t, ast.Name):
                    out[t.id] = 'var'
    return out


def es_shim(mod, tools=None):
    ruta = (tools or _tools()) / f'{mod}.py'
    return ruta.is_file() and 'sys.modules[__name__]' in ruta.read_text(encoding='utf-8', errors='replace')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('accion', choices=['capturar', 'comprobar', 'comparar'])
    ap.add_argument('posicional', nargs='?', metavar='FICHERO')
    ap.add_argument('--fichero')
    args = ap.parse_args()
    tools = _tools()
    fichero = args.posicional or args.fichero or str(tools / 'tests' / 'compat' / 'superficie_v0.json')
    actual = {p.stem: superficie(p) for p in sorted(tools.glob('*.py'))}
    if args.accion == 'capturar':
        Path(fichero).write_text(json.dumps(actual, ensure_ascii=False, indent=1, sort_keys=True) + '\n',
                                 encoding='utf-8')
        print(f'{len(actual)} módulos, {sum(map(len, actual.values()))} nombres capturados')
        return 0
    esperado = json.loads(Path(fichero).read_text(encoding='utf-8'))
    errores = []
    for mod, nombres in esperado.items():
        if es_shim(mod, tools):
            continue
        if mod not in actual:
            errores.append(f'{mod}: módulo ausente')
            continue
        for n, tipo in nombres.items():
            if n not in actual[mod]:
                errores.append(f'{mod}.{n}: desaparecido')
            elif actual[mod][n] != tipo:
                errores.append(f'{mod}.{n}: {tipo} -> {actual[mod][n]}')
    for e in errores:
        print('SUPERFICIE', e)
    print(f'{len(esperado)} módulos comprobados; {len(errores)} diferencias')
    return 1 if errores else 0


if __name__ == '__main__':
    sys.exit(main())
