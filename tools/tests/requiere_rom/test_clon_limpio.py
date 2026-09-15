"""Gate 5: un clon limpio de HEAD (git worktree) conserva el bloqueo v20 y su test pasa.

Cobertura de los 4 bloqueados importables: dialogue_typography.py y font_patch.py por
SOURCE_HASHES (extraído por AST de dialogue_lock.py del clon); dialogue_lock.py y
build_ie1_probe.py (y build_ui_revision.py) por tools/tests/compat/golden/congelados.sha256.
"""
import ast
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.requiere_rom

TEST_LOCK = 'tools/tests/unidad/texto/test_dialogue_lock.py'


def _source_hashes(ruta):
    arbol = ast.parse(ruta.read_text(encoding='utf-8'))
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and any(getattr(t, 'id', None) == 'SOURCE_HASHES' for t in nodo.targets):
            return ast.literal_eval(nodo.value)
    raise AssertionError('SOURCE_HASHES no encontrado en dialogue_lock.py')


def test_clon_limpio_conserva_bloqueo():
    from ie123kit.nucleo.compat.golden import sha
    from ie123kit.nucleo.config.raiz import find_root

    git = shutil.which('git')
    if git is None:
        pytest.skip('git no disponible')
    raiz = find_root()
    tmp = Path(tempfile.mkdtemp(prefix='ie123_gate5_'))
    clon = tmp / 'clon'
    creado = False
    try:
        r = subprocess.run([git, 'worktree', 'add', '--detach', str(clon), 'HEAD'],
                           cwd=raiz, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        creado = True

        lineas = (clon / 'tools/tests/compat/golden/congelados.sha256').read_text(encoding='utf-8').splitlines()
        assert len(lineas) == 5
        for linea in lineas:
            esperado, rel = linea.split('  ', 1)
            assert sha(clon / rel) == esperado, f'congelado distinto en el clon: {rel}'

        hashes = _source_hashes(clon / 'tools/dialogue_lock.py')
        assert hashes
        for rel, esperado in hashes.items():
            assert sha(clon / rel) == esperado, f'SOURCE_HASHES no cuadra en el clon: {rel}'

        if not (clon / TEST_LOCK).is_file():
            pytest.skip('test_dialogue_lock aún no está en HEAD')

        env = {k: v for k, v in os.environ.items() if k not in ('IE123_ROOT', 'PYTHONPATH')}
        env['IE123_ROOT'] = str(clon)
        env['PYTHONPATH'] = str(clon / 'tools' / 'src')

        r = subprocess.run([sys.executable, '-X', 'utf8', '-c', 'import ie123kit; print(ie123kit.__file__)'],
                           cwd=clon, env=env, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        origen = Path(r.stdout.strip()).resolve()
        assert str(origen).lower().startswith(str(clon.resolve()).lower()), f'ie123kit importado de {origen}'

        r = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'pytest', TEST_LOCK, '-q', '-p', 'no:cacheprovider'],
                           cwd=clon, env=env, capture_output=True, text=True)
        salida = r.stdout + r.stderr
        assert r.returncode == 0, salida
        assert 'passed' in salida, salida
    finally:
        if creado or clon.exists():
            subprocess.run([git, 'worktree', 'remove', '--force', str(clon)], cwd=raiz, capture_output=True)
        subprocess.run([git, 'worktree', 'prune'], cwd=raiz, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)
