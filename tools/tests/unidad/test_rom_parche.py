"""ROM y parche: se comprueba la lista exacta de argumentos, sin ejecutar 3dstool ni xdelta3."""
import pytest

from ie123kit.nucleo.construir import parche, rom
from ie123kit.nucleo.errores import ValidacionError


def _base(tmp_path):
    base = tmp_path / "base_3ds"
    (base / "romfs" / "cro").mkdir(parents=True)
    (base / "romfs" / "archive.fa").write_bytes(b"archive original")
    (base / "romfs" / "cro" / "ina_main1.cro").write_bytes(b"cro original")
    for pieza in ("exefs.bin", "ncch_header.bin", "exh.bin", "ncsd_header.bin"):
        (base / pieza).write_bytes(b"pieza")
    return base


def _candidata(tmp_path):
    c = tmp_path / "probe_ie1_v70"
    (c / "romfs" / "cro").mkdir(parents=True)
    (c / "archive.fa").write_bytes(b"archive traducido")
    (c / "romfs" / "cro" / "ina_main1.cro").write_bytes(b"cro traducida")
    return c


def test_build_3ds_argumentos(tmp_path, monkeypatch):
    base, candidata = _base(tmp_path), _candidata(tmp_path)
    salida = tmp_path / "out" / "123_es.3ds"
    llamadas = []
    copias = {}

    def falso(argumentos):
        llamadas.append(list(argumentos))
        if argumentos[2] == "romfs":
            # El RomFS de la base no se toca: se empaqueta la copia temporal ya superpuesta.
            carpeta = tmp_path / argumentos[5]
            copias["archive"] = (carpeta / "archive.fa").read_bytes()
            copias["cro"] = (carpeta / "cro" / "ina_main1.cro").read_bytes()
        destino = tmp_path / argumentos[3]
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(b"salida de 3dstool")
        return {"argumentos": list(argumentos), "returncode": 0, "stdout": "ok", "stderr": ""}

    monkeypatch.setattr(rom, "_ejecutar", falso)
    informe = rom.build_3ds(candidata, salida, base=base, herramienta=tmp_path / "3dstool.exe")

    assert [a[2] for a in llamadas] == ["romfs", "cxi", "3ds"]
    assert llamadas[0][:3] == [str((tmp_path / "3dstool.exe").resolve()), "-ctf", "romfs"]
    assert llamadas[0][4] == "--romfs-dir"
    assert llamadas[1][4:] == [
        "--romfs", llamadas[0][3], "--exefs", str(base / "exefs.bin"),
        "--header", str(base / "ncch_header.bin"), "--exh", str(base / "exh.bin"), "--not-encrypt",
    ]
    assert llamadas[2][3] == str(salida)
    assert llamadas[2][4:] == ["-0", llamadas[1][3], "--header", str(base / "ncsd_header.bin")]
    assert copias == {"archive": b"archive traducido", "cro": b"cro traducida"}
    assert (base / "romfs" / "archive.fa").read_bytes() == b"archive original"
    assert informe["sustituidos"] == ["archive.fa", "cro/ina_main1.cro"]
    assert informe["size"] == len(b"salida de 3dstool")


def test_build_3ds_codigo_de_error(tmp_path, monkeypatch):
    base, candidata = _base(tmp_path), _candidata(tmp_path)
    monkeypatch.setattr(rom, "_ejecutar", lambda a: {"argumentos": list(a), "returncode": 3,
                                                    "stdout": "", "stderr": "romfs demasiado grande"})
    with pytest.raises(ValidacionError) as err:
        rom.build_3ds(candidata, tmp_path / "o.3ds", base=base, herramienta=tmp_path / "3dstool.exe")
    assert err.value.codigo == "3DSTOOL_FALLO"
    assert "romfs demasiado grande" in str(err.value)


def test_xdelta_argumentos_exactos(tmp_path, monkeypatch):
    original = tmp_path / "orig.3ds"
    traducida = tmp_path / "es.3ds"
    original.write_bytes(b"A" * 64)
    traducida.write_bytes(b"B" * 64)
    salida = tmp_path / "patch" / "inazuma123-es.xdelta"
    tool = tmp_path / "xdelta3.exe"
    vistos = []

    def falso(argumentos):
        vistos.append(list(argumentos))
        salida.write_bytes(b"delta")
        return {"argumentos": list(argumentos), "returncode": 0, "stdout": "", "stderr": ""}

    monkeypatch.setattr(parche, "_ejecutar", falso)
    informe = parche.xdelta(original, traducida, salida, herramienta=tool)
    assert vistos == [[
        str(tool.resolve()), "-e", "-f", "-B", "2147483648", "-s",
        str(original.resolve()), str(traducida.resolve()), str(salida.resolve()),
    ]]
    assert informe["bytes"] == 5


def test_xdelta_error(tmp_path, monkeypatch):
    original = tmp_path / "orig.3ds"
    traducida = tmp_path / "es.3ds"
    original.write_bytes(b"A")
    traducida.write_bytes(b"B")
    monkeypatch.setattr(parche, "_ejecutar", lambda a: {"argumentos": list(a), "returncode": 1,
                                                       "stdout": "", "stderr": "no source"})
    with pytest.raises(ValidacionError) as err:
        parche.xdelta(original, traducida, tmp_path / "p.xdelta", herramienta=tmp_path / "xdelta3.exe")
    assert err.value.codigo == "XDELTA_FALLO"
    with pytest.raises(FileNotFoundError):
        parche.xdelta(tmp_path / "no.3ds", traducida, tmp_path / "p2.xdelta",
                      herramienta=tmp_path / "xdelta3.exe")
