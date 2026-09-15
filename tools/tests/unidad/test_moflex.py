"""MOFLEX: marca de rotación (layout 0x16), conversión de color y orden de errores."""
import hashlib
import struct

import numpy as np
import pytest
from PIL import Image

from ie123kit.nucleo.media import moflex


def _descriptor(layout):
    # 'L2' + 12 bytes de sincronía, type 3, tamaño 13, 13 bytes de payload (layout al final).
    return b"\x4c\x32" + bytes(12) + b"\x03\x0d" + bytes(12) + bytes([layout])


def test_rotacion_layout_0x16(tmp_path):
    p = tmp_path / "v.moflex"
    p.write_bytes(b"cabecera" + _descriptor(0x06) + b"\x4c\x32\x00" + _descriptor(0x06) + b"fin")
    assert moflex.disposicion_rotacion(p) == [0x06, 0x06]
    assert moflex.set_moflex_rotation(p, 1) == 2
    assert moflex.disposicion_rotacion(p) == [0x16, 0x16]


def test_sin_descriptores(tmp_path):
    p = tmp_path / "v.moflex"
    p.write_bytes(b"\x4c\x32" + bytes(40))
    assert moflex.disposicion_rotacion(p) == []
    with pytest.raises(ValueError, match="descriptor"):
        moflex.set_moflex_rotation(p, 1)
    with pytest.raises(ValueError):
        moflex.set_moflex_rotation(p, 16)


def test_color_igual_que_original():
    g = Image.fromarray(np.arange(8 * 6 * 3, dtype=np.uint8).reshape(6, 8, 3) * 3, "RGB")
    assert hashlib.sha256(moflex.rgb_to_yuv420(g)).hexdigest() == \
        "bd391b7a44a0fd737fc59cb218cdd1aca76b0722fea7bfff2909aff5a6f68016"
    rgb = moflex.ycgco420_to_rgb(bytes((i * 7) % 256 for i in range(72)), 8, 6)
    assert hashlib.sha256(rgb.tobytes()).hexdigest() == \
        "9d2bda769fac2c9a35d54aa008611f5b45d716480bdb6c43f83ca161c4250a1b"
    with pytest.raises(ValueError):
        moflex.ycgco420_to_rgb(bytes(71), 8, 6)


def test_convert_sin_fuente_con_subtitulos(tmp_path, monkeypatch):
    mobipeg = tmp_path / "mobipeg"
    mobipeg.mkdir()
    (mobipeg / "ffmpeg.exe").write_bytes(b"")
    (mobipeg / "ffprobe.exe").write_bytes(b"")
    dat = tmp_path / "s.dat"
    dat.write_bytes(struct.pack("<III", 0, 10, 2) + b"a\0" + b"\xff" * 4)
    monkeypatch.setattr(moflex, "probe", lambda ffprobe, source: (8, 6, "20/1"))

    def _no(*a, **k):
        raise AssertionError("no debe lanzar procesos")

    monkeypatch.setattr(moflex.subprocess, "Popen", _no)
    monkeypatch.setattr(moflex.subprocess, "run", _no)
    with pytest.raises(ValueError, match="falta font_path"):
        moflex.convert(tmp_path / "a.mods", tmp_path / "out" / "a.moflex", mobipeg, 28, dat)
    assert not (tmp_path / "out").exists()


def test_convert_sin_mobipeg(tmp_path):
    with pytest.raises(FileNotFoundError):
        moflex.convert(tmp_path / "a.mods", tmp_path / "a.moflex", tmp_path / "nada", 28)
