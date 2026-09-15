"""Tests de la regla de módulos archivados en tools/_archivo del comparador de superficie."""
import json
import sys

import pytest

from ie123kit.nucleo.compat import superficie


@pytest.fixture
def raiz(tmp_path, monkeypatch):
    (tmp_path / 'AGENTS.md').write_text('sintético\n', encoding='utf-8')
    (tmp_path / 'tools').mkdir()
    (tmp_path / 'tools' / 'pyproject.toml').write_text('', encoding='utf-8')
    monkeypatch.setenv('IE123_ROOT', str(tmp_path))
    return tmp_path


def _escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding='utf-8')


def _ejecutar(monkeypatch, *argv):
    monkeypatch.setattr(sys, 'argv', ['x', *argv])
    return superficie.main()


@pytest.fixture
def base(raiz, monkeypatch):
    tools = raiz / 'tools'
    _escribir(tools / 'a.py', 'def fa(x): pass\n')
    _escribir(tools / 'b.py', 'def fb(y): pass\n')
    fichero = raiz / 'superficie.json'
    assert _ejecutar(monkeypatch, 'capturar', str(fichero)) == 0
    return tools, fichero


def test_archivado_se_omite(base, monkeypatch, capsys):
    tools, fichero = base
    _escribir(tools / '_archivo' / 'b.py', (tools / 'b.py').read_text(encoding='utf-8'))
    (tools / 'b.py').unlink()
    capsys.readouterr()
    assert _ejecutar(monkeypatch, 'comparar', str(fichero)) == 0
    assert '1 archivados omitidos' in capsys.readouterr().out


def test_archivado_en_tests_se_omite(base, monkeypatch):
    tools, fichero = base
    _escribir(tools / '_archivo' / 'tests' / 'b.py', 'X = 1\n')
    (tools / 'b.py').unlink()
    assert _ejecutar(monkeypatch, 'comparar', str(fichero)) == 0


def test_ausente_no_archivado_falla(base, monkeypatch, capsys):
    tools, fichero = base
    (tools / 'b.py').unlink()
    assert _ejecutar(monkeypatch, 'comparar', str(fichero)) == 1
    assert 'b: módulo ausente' in capsys.readouterr().out


def test_duplicado_falla(base, monkeypatch, capsys):
    tools, fichero = base
    _escribir(tools / '_archivo' / 'b.py', 'def fb(y): pass\n')
    assert _ejecutar(monkeypatch, 'comparar', str(fichero)) == 1
    assert 'duplicado' in capsys.readouterr().out


def test_capturar_no_incluye_archivo(base, monkeypatch, raiz):
    tools, _ = base
    _escribir(tools / '_archivo' / 'c.py', 'def fc(): pass\n')
    nuevo = raiz / 'nuevo.json'
    assert _ejecutar(monkeypatch, 'capturar', str(nuevo)) == 0
    assert sorted(json.loads(nuevo.read_text(encoding='utf-8'))) == ['a', 'b']
