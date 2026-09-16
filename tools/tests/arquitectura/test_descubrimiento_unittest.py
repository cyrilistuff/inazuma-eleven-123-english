"""La puerta `unittest discover` de ESPECIFICACION.md debe seguir recogiendo tests.

Al trasladar los antiguos `tools/test_*.py` a `tools/tests/unidad/**` (F1.5, #46) la orden
`python -m unittest discover -s tools -p "test_*.py"` pasó a decir «Ran 0 tests» sin fallar,
porque desde Python 3.11 `unittest` no desciende a directorios que no sean paquetes. Este
test fija el arreglo (los `__init__.py` de `tools/tests` y `tools/tests/unidad/**`) para que
la regresión no vuelva a pasar inadvertida.
"""

from __future__ import annotations

import re
import subprocess
import sys

from ie123kit.nucleo.config.raiz import find_root

MINIMO_ESPERADO = 20


def test_unittest_discover_recoge_los_tests_heredados() -> None:
    raiz = find_root()
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", "tools", "-p", "test_*.py"],
        cwd=raiz,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    salida = f"{proc.stdout}\n{proc.stderr}"
    encontrados = re.search(r"^Ran (\d+) tests?", salida, re.MULTILINE)
    assert encontrados, f"unittest no informó del recuento:\n{salida}"
    assert int(encontrados.group(1)) >= MINIMO_ESPERADO, salida
    assert proc.returncode == 0, salida
