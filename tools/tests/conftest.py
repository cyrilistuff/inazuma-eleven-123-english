"""Permite ejecutar pytest antes de `pip install -e tools[dev]`."""

import importlib.util
import sys
from pathlib import Path

if importlib.util.find_spec("ie123kit") is None:
    aqui = Path(__file__).resolve().parent
    for d in [aqui, *aqui.parents]:
        if (d / "src" / "ie123kit" / "__init__.py").is_file():
            sys.path.insert(0, str(d / "src"))
            break
