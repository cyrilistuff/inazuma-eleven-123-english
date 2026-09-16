"""Localización de herramientas externas: precedencia IE123_*, [herramientas], tools/bin y PATH."""
import pytest

from ie123kit.nucleo.config import herramientas as H
from ie123kit.nucleo.errores import ValidacionError


class _Ws:
    def __init__(self, raiz):
        self.raiz = raiz


def _repo(tmp_path):
    (tmp_path / "AGENTS.md").write_text("x", encoding="utf-8")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "pyproject.toml").write_text("x", encoding="utf-8")
    return _Ws(tmp_path)


def _exe(ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(b"MZ")
    return ruta.resolve()


def test_precedencia(tmp_path, monkeypatch):
    ws = _repo(tmp_path)
    monkeypatch.setattr(H.shutil, "which", lambda *a, **k: None)

    en_path = _exe(tmp_path / "path" / "3dstool.exe")
    monkeypatch.setattr(H.shutil, "which", lambda n, path=None: str(en_path) if n == "3dstool.exe" else None)
    assert H.localizar("3dstool", ws=ws, entorno={}) == en_path

    en_bin = _exe(tmp_path / "tools" / "bin" / "3dstool.exe")
    assert H.localizar("3dstool", ws=ws, entorno={}) == en_bin

    en_tabla = _exe(tmp_path / "otras" / "3dstool.exe")
    (tmp_path / "ie123.toml").write_text('[herramientas]\n3dstool = "otras/3dstool.exe"\n', encoding="utf-8")
    assert H.localizar("3dstool", ws=ws, entorno={}) == en_tabla

    local = _exe(tmp_path / "local" / "3dstool.exe")
    (tmp_path / "ie123.local.toml").write_text(
        f'[herramientas]\n3dstool = "{local.as_posix()}"\n', encoding="utf-8")
    assert H.localizar("3dstool", ws=ws, entorno={}) == local

    variable = _exe(tmp_path / "var" / "3dstool.exe")
    assert H.localizar("3dstool", ws=ws, entorno={"IE123_3DSTOOL": str(variable)}) == variable


def test_herramientas_externas_en_work(tmp_path, monkeypatch):
    ws = _repo(tmp_path)
    monkeypatch.setattr(H.shutil, "which", lambda *a, **k: None)
    suelta = _exe(tmp_path / "work" / "shared" / "herramientas" / "vgmstream" / "vgmstream-cli.exe")
    assert H.localizar("vgmstream", ws=ws, entorno={}) == suelta


def test_ausente_y_desconocida(tmp_path, monkeypatch):
    ws = _repo(tmp_path)
    monkeypatch.setattr(H.shutil, "which", lambda *a, **k: None)
    assert H.localizar("xdelta3", ws=ws, entorno={}) is None
    with pytest.raises(H.HerramientaAusente) as err:
        H.exigir("xdelta3", ws=ws, entorno={})
    assert err.value.codigo == "HERRAMIENTA_AUSENTE"
    assert "IE123_XDELTA3" in str(err.value)
    with pytest.raises(ValidacionError):
        H.localizar("inexistente", ws=ws, entorno={})


def test_variable_que_no_existe_no_gana(tmp_path, monkeypatch):
    ws = _repo(tmp_path)
    monkeypatch.setattr(H.shutil, "which", lambda *a, **k: None)
    en_bin = _exe(tmp_path / "tools" / "bin" / "ffmpeg.exe")
    assert H.localizar("ffmpeg", ws=ws, entorno={"IE123_FFMPEG": str(tmp_path / "no" / "ffmpeg.exe")}) == en_bin
