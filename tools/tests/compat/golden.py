"""Hashes golden de la migración del toolkit (#41): ficheros congelados, capa v67 y candidatas.

Uso:
  python tools/tests/compat/golden.py capturar
  python tools/tests/compat/golden.py comprobar [--capa work/ie1/capas/v67/titulo_logo]
Con --capa se vuelve a ejecutar apply.py y se exige que extra/ salga byte a byte igual; si no, se restaura.
Solo se versionan hashes, nunca datos del juego (Norma 2).
"""
import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GOLDEN = Path(__file__).with_name('golden')
CONGELADOS = ['tools/dialogue_typography.py', 'tools/font_patch.py', 'tools/dialogue_lock.py',
              'tools/build_ie1_probe.py', 'tools/build_ui_revision.py']
CAPA = 'work/ie1/capas/v67/titulo_logo'
CANDIDATAS = ['work/shared/candidatas/probe_ie1_v66', 'work/shared/candidatas/probe_ie1_v67']
GRUPOS = {
    'congelados.sha256': lambda: [ROOT / p for p in CONGELADOS],
    'capas_v67.sha256': lambda: sorted(p for p in (ROOT / CAPA / 'extra').rglob('*') if p.is_file()),
    'candidatas.sha256': lambda: [f for c in CANDIDATAS
                                  for f in [ROOT / c / 'archive.fa', *sorted((ROOT / c / 'romfs').rglob('*.cro'))]],
}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for bloque in iter(lambda: f.read(1 << 20), b''):
            h.update(bloque)
    return h.hexdigest()


def comprobar_grupo(nombre):
    esperado = (GOLDEN / nombre).read_text(encoding='utf-8').splitlines()
    malos = []
    for linea in esperado:
        h, rel = linea.split('  ', 1)
        p = ROOT / rel
        if not p.is_file():
            malos.append(f'ausente {rel}')
        elif sha(p) != h:
            malos.append(f'distinto {rel}')
    return len(esperado), malos


def regenerar_capa():
    extra = ROOT / CAPA / 'extra'
    copia = Path(tempfile.mkdtemp(prefix='ie123_golden_')) / 'extra'
    shutil.copytree(extra, copia)
    r = subprocess.run([sys.executable, str(ROOT / CAPA / 'apply.py')], cwd=ROOT)
    total, malos = comprobar_grupo('capas_v67.sha256')
    if r.returncode or malos:
        shutil.rmtree(extra, ignore_errors=True)
        shutil.copytree(copia, extra)
        malos.insert(0, f'apply.py devolvió {r.returncode}; extra/ restaurado')
    shutil.rmtree(copia.parent)
    return total, malos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('accion', choices=['capturar', 'comprobar'])
    ap.add_argument('--capa', help=f'regenera la capa antes de comprobar (solo {CAPA} tiene golden)')
    args = ap.parse_args()
    if args.accion == 'capturar':
        GOLDEN.mkdir(exist_ok=True)
        for nombre, ficheros in GRUPOS.items():
            lineas = [f'{sha(p)}  {p.relative_to(ROOT).as_posix()}' for p in ficheros()]
            (GOLDEN / nombre).write_text('\n'.join(lineas) + '\n', encoding='utf-8')
            print('capturado', nombre, len(lineas))
        return 0
    if args.capa and Path(args.capa).as_posix().rstrip('/') != CAPA:
        print(f'--capa {args.capa}: no hay golden para esa capa')
        return 1
    fallos = 0
    for nombre in GRUPOS:
        total, malos = regenerar_capa() if args.capa and nombre == 'capas_v67.sha256' else comprobar_grupo(nombre)
        for m in malos:
            print(nombre, m)
        print(f'{nombre}: {total - len(malos)}/{total} OK')
        fallos += len(malos)
    return 1 if fallos else 0


if __name__ == '__main__':
    sys.exit(main())
