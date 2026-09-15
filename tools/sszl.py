"""Shim generado por ie123kit.nucleo.compat.shims (no editar): alias de ie123kit.nucleo.compresion.sszl."""
import importlib
import sys
from pathlib import Path

_SRC = str(Path(__file__).resolve().parent / 'src')
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
sys.modules[__name__] = importlib.import_module('ie123kit.nucleo.compresion.sszl')
