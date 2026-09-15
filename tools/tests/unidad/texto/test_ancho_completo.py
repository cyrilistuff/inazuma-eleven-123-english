"""Trasladado de tools/test_dialogue_typography.py (F1.5, #46); fixtures sintéticos."""

import unittest

from ie123kit.nucleo.config.congelados import cargar

encode_fullwidth = cargar("dialogue_typography").encode_fullwidth


class EncodingTests(unittest.TestCase):
    def test_controls_remain_ascii(self):
        data = encode_fullwidth(r"A B\nC\f%1FD")
        self.assertEqual(data, b"\x82\x60\x81\x40\x82\x61\\n\x82\x62\\f%1F\x82\x63")

    def test_accents_keep_spanish_carriers(self):
        self.assertEqual(encode_fullwidth("á"), "Α".encode("shift_jis"))

    def test_missing_character_fails(self):
        with self.assertRaises(UnicodeEncodeError):
            encode_fullwidth("\U0001f600")


def test_ancho_completo_reexporta_el_congelado():
    from ie123kit.nucleo.texto import ancho_completo

    assert ancho_completo.encode_fullwidth is encode_fullwidth
