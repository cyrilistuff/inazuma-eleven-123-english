"""`python -m ie123kit.cli`.

El guardián `__name__` mantiene el módulo importable sin efectos (tests/arquitectura/test_sin_efectos.py):
bajo `python -m` el módulo se llama `__main__`, así que la orden se ejecuta igual.
"""

from __future__ import annotations

from ie123kit.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
