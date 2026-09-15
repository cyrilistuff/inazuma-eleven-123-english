from pathlib import Path

from ie123kit.nucleo.errores import (
    BloqueoTipograficoError,
    FormatoError,
    Ie123Error,
    RaizNoEncontradaError,
    ValidacionError,
)


def test_jerarquia():
    assert issubclass(FormatoError, ValueError)
    assert issubclass(FormatoError, Ie123Error)
    assert issubclass(RaizNoEncontradaError, Ie123Error)
    assert issubclass(ValidacionError, Ie123Error)
    assert issubclass(BloqueoTipograficoError, ValidacionError)


def test_validacion_atributos_y_mensaje():
    ruta = Path("a") / "b.txt"
    e = ValidacionError("E1", ruta, "roto")
    assert (e.codigo, e.ruta, e.detalle) == ("E1", str(ruta), "roto")
    assert str(e) == f"E1: {ruta}: roto"
    assert str(ValidacionError("E2")) == "E2"
    assert ValidacionError("E2").ruta is None
    assert str(ValidacionError("E3", "x")) == "E3: x"
    assert str(BloqueoTipograficoError("V20", detalle="hash")) == "V20: hash"
