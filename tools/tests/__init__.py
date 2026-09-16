"""Paquete de los tests del toolkit.

Existe para que `python -m unittest discover -s tools -p "test_*.py"` —la puerta (1) de
todas las fases en docs/toolkit/ESPECIFICACION.md— vuelva a recoger los tests heredados
de `unittest.TestCase`. Desde Python 3.11 `unittest` ya no desciende a directorios que no
sean paquetes importables, así que al trasladar los antiguos `tools/test_*.py` a
`tools/tests/unidad/**` (F1.5, #46) la orden pasó a decir «Ran 0 tests». Con este
`__init__.py` y los de los subpaquetes vuelve a encontrarlos.

Además repite el arranque de `conftest.py` (añadir `tools/src` a sys.path si el paquete no
está instalado) porque `unittest` no lee conftest.

Solo son paquetes `unidad/` y sus subcarpetas, que es donde viven los `unittest.TestCase`
heredados. `arquitectura/`, `compat/`, `contrato/` y `requiere_rom/` se dejan a propósito
sin `__init__.py`: son tests de pytest (funciones, fixtures y marcas) y así `unittest` ni
siquiera los importa. Para ellos la puerta es `python -m pytest tools/tests`.
"""

import importlib.util
import sys
from pathlib import Path

if importlib.util.find_spec("ie123kit") is None:
    aqui = Path(__file__).resolve().parent
    for d in [aqui, *aqui.parents]:
        if (d / "src" / "ie123kit" / "__init__.py").is_file():
            sys.path.insert(0, str(d / "src"))
            break
