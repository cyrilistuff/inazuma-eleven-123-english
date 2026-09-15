import pytest

from ie123kit.nucleo.config.raiz import find_root
from ie123kit.nucleo.errores import RaizNoEncontradaError


def _crear_raiz(tmp_path):
    (tmp_path / "AGENTS.md").write_text("x", encoding="utf-8")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "pyproject.toml").write_text("", encoding="utf-8")
    return tmp_path.resolve()


def test_sube_desde_subcarpeta(tmp_path, monkeypatch):
    monkeypatch.delenv("IE123_ROOT", raising=False)
    raiz = _crear_raiz(tmp_path)
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    assert find_root(inicio=sub) == raiz


def test_variable_de_entorno(tmp_path, monkeypatch):
    raiz = _crear_raiz(tmp_path)
    monkeypatch.setenv("IE123_ROOT", str(tmp_path))
    assert find_root() == raiz


def test_variable_invalida(tmp_path, monkeypatch):
    monkeypatch.setenv("IE123_ROOT", str(tmp_path))
    with pytest.raises(RaizNoEncontradaError, match="IE123_ROOT"):
        find_root()


def test_sin_raiz(tmp_path, monkeypatch):
    monkeypatch.delenv("IE123_ROOT", raising=False)
    with pytest.raises(RaizNoEncontradaError):
        find_root(inicio=tmp_path)


def test_repo_real(monkeypatch):
    monkeypatch.delenv("IE123_ROOT", raising=False)
    r = find_root()
    assert (r / "AGENTS.md").is_file()
    assert (r / "tools" / "pyproject.toml").is_file()
