"""nucleo.eventos.alineado_ids con buffers sintéticos; salidas capturadas de audit_dialogo_ids en 0af2abd."""
import struct

from ie123kit.nucleo.eventos.alineado_ids import emparejar, tabla_3ds, tabla_nds

KONNICHIWA = "こんにちは".encode("cp932")
SAYONARA = "さようなら".encode("cp932")


def _nds(sid, typ, s):
    return struct.pack("<HHI", sid, typ, 8 + len(s) + 1) + s + b"\x00"


def _e3(sid, typ, s):
    return struct.pack("<HBB", sid, typ, 4 + len(s) + 1) + s + b"\x00"


NDS = (struct.pack("<I", 0) + _nds(3, 1, b"Hola") + _nds(3, 2, b"dup") + _nds(5, 1, b"file.SAD")
       + _nds(9, 1, b"Adi\xb2s") + b"\x01\x00")
SSD = (b"SSD\x00" + bytes(12) + struct.pack("<I", 24) + bytes(4) + bytes(32)
       + _e3(2, 1, KONNICHIWA) + _e3(2, 2, "よみ".encode("cp932")) + _e3(4, 1, b"file.SAD")
       + _e3(8, 1, SAYONARA) + b"\xff")


def test_buffers_como_en_la_captura():
    assert NDS.hex() == ("00000000030001000d000000486f6c6100030002000c00000064757000050001001100000066696c65"
                         "2e53414400090001000e000000416469b273000100")
    assert SSD.hex().endswith("0200010f82b182f182c982bf82cd000200020982e682dd000400010d66696c652e5341"
                              "44000800010f82b382e682a482c882e700ff")


def test_tabla_nds():
    assert tabla_nds(NDS) == {3: (1, b"Hola"), 5: (1, b"file.SAD"), 9: (1, b"Adi\xb2s")}


def test_tabla_3ds():
    assert tabla_3ds(SSD) == {2: (1, KONNICHIWA, "こんにちは"), 4: (1, b"file.SAD", "file.SAD"),
                              8: (1, SAYONARA, "さようなら")}
    assert tabla_3ds(b"XXXX" + bytes(40)) is None


def test_emparejar():
    assert emparejar(tabla_3ds(SSD), tabla_nds(NDS)) == ({4: 5, 8: 9, 2: 3}, 1, 0)
    assert emparejar({}, {1: (1, b"a")}) == ({}, 0, 0)
    a = {1: (1, b"abc", None), 4: (1, b"zz", None), 6: (1, b"q", None)}
    b = {2: (1, b"abc"), 5: (1, b"yy"), 7: (1, b"\xb2")}
    assert emparejar(a, b) == ({4: 5, 6: 7, 1: 2}, 1, 1)
