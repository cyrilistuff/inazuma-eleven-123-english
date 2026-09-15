"""Trasladado de tools/test_dialogue_lock.py (F1.5, #46); fixtures sintéticos.

Conserva el nombre: el gate 5 lo ejecuta por esta ruta. Los módulos congelados se
cargan desde tools/ con ie123kit.nucleo.config.congelados.cargar, sin copiarlos.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ie123kit.nucleo.config.congelados import cargar

lock = cargar("dialogue_lock")
layout = cargar("build_ie1_probe").layout


class DialogueLockTests(unittest.TestCase):
    def test_ascii_is_rejected_before_reading_files(self):
        with self.assertRaisesRegex(ValueError, "ASCII"):
            lock.validate(False, None, layout)

    def test_missing_fonts_are_rejected(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            self.assertRaisesRegex(ValueError, "archivo cambiado o ausente"),
        ):
            lock.validate(True, Path(folder), layout)

    def test_changed_layout_is_rejected(self):
        # Aísla la comprobación del ajuste de los recursos binarios locales.
        with (
            patch.object(lock, "FONT_HASHES", {}),
            patch.object(lock, "SOURCE_HASHES", {}),
            self.assertRaisesRegex(ValueError, "ajuste de lineas"),
        ):
            lock.validate(True, ".", self.test_ascii_is_rejected_before_reading_files)


def test_hash_de_ajuste_coincide_con_tipografia_v20():
    from ie123kit.nucleo.texto import tipografia_v20

    assert tipografia_v20.LAYOUT_HASH == lock.LAYOUT_HASH


def test_fuentes_bloqueadas_coinciden_con_tipografia_v20():
    from ie123kit.nucleo.texto import tipografia_v20

    assert tuple(lock.FONT_HASHES) == tipografia_v20.FUENTES_BLOQUEADAS
