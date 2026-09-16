"""Inspección SADL sobre cabeceras sintéticas."""
import dataclasses
import hashlib
import struct

import pytest

from ie123kit.nucleo.media.audio import SadInfo, inspect_sad, sha256


def _sad(tmp_path, flags, largo=0x60):
    data = bytearray(largo)
    data[:4] = b"sadl"
    if largo > 0x4C:
        data[0x31] = 1
        data[0x32] = 2
        data[0x33] = flags
        struct.pack_into("<I", data, 0x40, 0x1234)
        struct.pack_into("<I", data, 0x48, 0x100)
    p = tmp_path / "x.SAD"
    p.write_bytes(bytes(data))
    return p


@pytest.mark.parametrize("flags,frecuencia", [(0x04, 32728), (0x02, 16364), (0x00, 16364), (0x74, 32728)])
def test_frecuencias(tmp_path, flags, frecuencia):
    p = _sad(tmp_path, flags)
    info = inspect_sad(p)
    assert info == SadInfo(size=0x60, channels=2, sample_rate=frecuencia, codec_flag=f"0x{flags:02x}",
                           loop=True, data_size=0x1234, start_offset=0x100,
                           sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    assert sha256(p) == info.sha256


def test_flags_desconocidos(tmp_path):
    with pytest.raises(ValueError, match="frecuencia"):
        inspect_sad(_sad(tmp_path, 0x06))


def test_no_sadl(tmp_path):
    with pytest.raises(ValueError):
        inspect_sad(_sad(tmp_path, 0x04, largo=0x57))
    p = tmp_path / "y.SAD"
    p.write_bytes(b"xxxx" + bytes(0x60))
    with pytest.raises(ValueError):
        inspect_sad(p)


def test_inmutable(tmp_path):
    info = inspect_sad(_sad(tmp_path, 0x04))
    with pytest.raises(dataclasses.FrozenInstanceError):
        info.size = 1
