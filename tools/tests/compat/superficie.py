"""Envoltorio (F1.1, #42): la lógica vive en ie123kit.nucleo.compat.superficie."""
import importlib.util
import sys
from pathlib import Path

if importlib.util.find_spec('ie123kit') is None:
    _aqui = Path(__file__).resolve().parent
    for _d in [_aqui, *_aqui.parents]:
        if (_d / 'src' / 'ie123kit' / '__init__.py').is_file():
            sys.path.insert(0, str(_d / 'src'))
            break

from ie123kit.nucleo.compat.superficie import main

if __name__ == '__main__':
    sys.exit(main())
