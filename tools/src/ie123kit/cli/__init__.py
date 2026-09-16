"""Capa `cli` de ie123kit: adaptadores argparse sobre `ServicioToolkit`, sin lógica propia.

Regla de capas: esta capa importa SOLO `ie123kit.servicio` y la biblioteca estándar; nunca
`nucleo`, ni los juegos, ni `_legado`. Importar el paquete no tiene efectos: la orden vive en
`ie123kit.cli.main`.

F2.2 adelanta únicamente los verbos que exige el gate (`construir`, `parche`, `doctor`);
F2.4 añade el resto de verbos y los alias en inglés.
"""

from __future__ import annotations
