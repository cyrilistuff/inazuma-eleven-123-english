"""Trasladado de tools/test_probe_layout.py (F1.5, #46); fixtures sintéticos."""

import unittest

from ie123kit.nucleo.config.congelados import cargar

layout = cargar("build_ie1_probe").layout


class LayoutTests(unittest.TestCase):
    def test_variable_width_changes_breaks(self):
        def advance(ch):
            return 9 if ch == "W" else 2

        self.assertEqual(layout("iiii iiii", advance, 20), "iiii iiii")
        self.assertEqual(layout("WW WW", advance, 20), r"WW\nWW")

    def test_word_not_split_and_pages_limited(self):
        text = "uno dos tres cuatro cinco seis siete"
        result = layout(text, lambda ch: 1, 6)
        self.assertEqual(result, r"uno\ndos\ntres\fcuatro\ncinco\nseis\fsiete")
        self.assertEqual(result.replace(r"\n", " ").replace(r"\f", " "), text)

    def test_existing_pages_preserved(self):
        self.assertEqual(layout(r"uno\fdos\ntres", lambda ch: 1, 20), r"uno\fdos tres")

    def test_oversize_word_rejected(self):
        with self.assertRaisesRegex(ValueError, "pixel"):
            layout("WWWW", lambda ch: 9, 20)


def test_tipografia_v20_reexporta_el_congelado():
    from ie123kit.nucleo.texto import tipografia_v20

    assert tipografia_v20.layout is layout
