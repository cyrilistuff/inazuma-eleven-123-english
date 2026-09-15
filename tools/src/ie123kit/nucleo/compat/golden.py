"""Hashes golden de la migración del toolkit (#41): ficheros congelados, capa v67 y candidatas.

Uso:
  python -m ie123kit.nucleo.compat.golden capturar
  python -m ie123kit.nucleo.compat.golden comprobar [--capa work/ie1/capas/v67/titulo_logo [--candidata probe_ie1_v67]]
Con --capa se vuelve a ejecutar apply.py y se exige que extra/ salga byte a byte igual; si no, se restaura.
Con --candidata se reconstruye la candidata en un temporal con build_ui_revision.py y se exige el mismo
archive.fa y los mismos CRO; nunca se escribe en work/shared/candidatas.
Solo se versionan hashes, nunca datos del juego (Norma 2).
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PureWindowsPath

CONGELADOS = ['tools/dialogue_typography.py', 'tools/font_patch.py', 'tools/dialogue_lock.py',
              'tools/build_ie1_probe.py', 'tools/build_ui_revision.py']
CAPA = 'work/ie1/capas/v67/titulo_logo'
CANDIDATAS = ['work/shared/candidatas/probe_ie1_v66', 'work/shared/candidatas/probe_ie1_v67']


def _raiz():
    from ie123kit.nucleo.config.raiz import find_root
    return find_root()


def _golden(raiz):
    return raiz / 'tools' / 'tests' / 'compat' / 'golden'


def grupos(raiz):
    return {
        'congelados.sha256': lambda: [raiz / p for p in CONGELADOS],
        'capas_v67.sha256': lambda: sorted(p for p in (raiz / CAPA / 'extra').rglob('*') if p.is_file()),
        'candidatas.sha256': lambda: [f for c in CANDIDATAS
                                      for f in [raiz / c / 'archive.fa', *sorted((raiz / c / 'romfs').rglob('*.cro'))]],
    }


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for bloque in iter(lambda: f.read(1 << 20), b''):
            h.update(bloque)
    return h.hexdigest()


def comprobar_grupo(nombre, raiz=None):
    raiz = raiz or _raiz()
    esperado = (_golden(raiz) / nombre).read_text(encoding='utf-8').splitlines()
    malos = []
    for linea in esperado:
        h, rel = linea.split('  ', 1)
        p = raiz / rel
        if not p.is_file():
            malos.append(f'ausente {rel}')
        elif sha(p) != h:
            malos.append(f'distinto {rel}')
    return len(esperado), malos


def regenerar_capa(raiz=None):
    raiz = raiz or _raiz()
    extra = raiz / CAPA / 'extra'
    copia = Path(tempfile.mkdtemp(prefix='ie123_golden_')) / 'extra'
    shutil.copytree(extra, copia)
    r = subprocess.run([sys.executable, str(raiz / CAPA / 'apply.py')], cwd=raiz, check=False)
    total, malos = comprobar_grupo('capas_v67.sha256', raiz)
    if r.returncode or malos:
        shutil.rmtree(extra, ignore_errors=True)
        shutil.copytree(copia, extra)
        malos.insert(0, f'apply.py devolvió {r.returncode}; extra/ restaurado')
    shutil.rmtree(copia.parent)
    return total, malos


def comprobar_candidata(raiz, nombre, capa):
    """Reconstruye la candidata en un temporal y la compara con la instalada; devuelve el número de fallos."""
    candidatas = raiz / 'work' / 'shared' / 'candidatas'
    carpeta = candidatas / nombre
    meta = json.loads((carpeta / 'archive.build.json').read_text(encoding='utf-8'))
    # Solo el nombre de la carpeta base: la ruta absoluta del JSON es de la máquina que la construyó.
    base = candidatas / PureWindowsPath(meta['base']).parent.name / 'archive.fa'
    if not base.is_file() or sha(base) != meta['base_sha256']:
        print(f'candidata {nombre}: base {base.parent.name}/archive.fa ausente o con sha256 distinto')
        return 1
    tmp = Path(tempfile.mkdtemp(prefix='ie123_regen_'))
    try:
        salida = tmp / nombre / 'archive.fa'
        orden = [sys.executable, '-X', 'utf8', str(raiz / 'tools' / 'build_ui_revision.py'),
                 '--base', str(base), '--ui', str(raiz / capa), '--output', str(salida)]
        # Si la capa no trae CRO, la candidata heredó el de su base: se le pasa el mismo (solo lectura).
        cro_base = base.parent / 'romfs' / 'cro' / 'ina_main1.cro'
        if not (raiz / capa / 'romfs' / 'cro' / 'ina_main1.cro').is_file() and cro_base.is_file():
            orden += ['--cro', str(cro_base)]
        r = subprocess.run(orden, cwd=raiz, check=False)
        fallos = 0
        if r.returncode:
            print(f'candidata {nombre}: build_ui_revision.py devolvió {r.returncode}')
            fallos += 1
        archive_ok = salida.is_file() and sha(salida) == meta['archive_sha256']
        if not archive_ok:
            fallos += 1
        cros = sorted((carpeta / 'romfs').rglob('*.cro'))
        cro_ok = 0
        for cro in cros:
            homologo = tmp / nombre / 'romfs' / cro.relative_to(carpeta / 'romfs')
            if homologo.is_file() and sha(homologo) == sha(cro):
                cro_ok += 1
            else:
                print(f'candidata {nombre}: CRO distinto o ausente {cro.relative_to(carpeta).as_posix()}')
                fallos += 1
        print(f'candidata {nombre}: archive {"OK" if archive_ok else "DISTINTO"}, cro {cro_ok}/{len(cros)} OK')
        return fallos
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('accion', choices=['capturar', 'comprobar'])
    ap.add_argument('--capa', help=f'regenera la capa antes de comprobar (solo {CAPA} tiene golden)')
    ap.add_argument('--candidata', help='reconstruye esta candidata (p. ej. probe_ie1_v67) en un temporal; exige --capa')
    args = ap.parse_args()
    if args.candidata and (args.accion != 'comprobar' or not args.capa):
        print('--candidata solo es válida con comprobar y exige --capa')
        return 2
    raiz = _raiz()
    golden = _golden(raiz)
    if args.accion == 'capturar':
        golden.mkdir(exist_ok=True)
        for nombre, ficheros in grupos(raiz).items():
            lineas = [f'{sha(p)}  {p.relative_to(raiz).as_posix()}' for p in ficheros()]
            (golden / nombre).write_text('\n'.join(lineas) + '\n', encoding='utf-8')
            print('capturado', nombre, len(lineas))
        return 0
    if args.capa and Path(args.capa).as_posix().rstrip('/') != CAPA:
        print(f'--capa {args.capa}: no hay golden para esa capa')
        return 1
    fallos = 0
    for nombre in grupos(raiz):
        total, malos = (regenerar_capa(raiz) if args.capa and nombre == 'capas_v67.sha256'
                        else comprobar_grupo(nombre, raiz))
        for m in malos:
            print(nombre, m)
        print(f'{nombre}: {total - len(malos)}/{total} OK')
        fallos += len(malos)
    if args.candidata:
        fallos += comprobar_candidata(raiz, args.candidata, args.capa)
    return 1 if fallos else 0


if __name__ == '__main__':
    sys.exit(main())
