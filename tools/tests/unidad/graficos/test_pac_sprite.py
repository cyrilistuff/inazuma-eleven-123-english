"""Trasladado de tools/test_legacy_sprite.py (F1.5, #46), caso de sprite; fixtures sintéticos.

El caso de compresión óptima está en tools/tests/unidad/compresion/test_lz10.py.
"""

import struct
import unittest

from PIL import Image

from ie123kit.nucleo.graficos import pac_sprite as sprite


class LegacySpriteTests(unittest.TestCase):
    def fixture(self):
        b = bytearray(112)
        struct.pack_into("<7I", b, 0, 3, 32, 32, 64, 32, 96, 16)
        b[96:100] = bytes([1, 0, 0, 0])
        for i in range(16):
            struct.pack_into("<H", b, 64 + 2 * i, 31 if i else 0)
        b[32:64] = bytes([0x21] * 32)  # Índices distintos con colores idénticos.
        return bytes(b)

    def test_preserves_palette_indices_and_other_chunks(self):
        b = self.fixture()
        im = sprite.decode(b)
        self.assertEqual(sprite.encode(b, im), b)
        im.putpixel((0, 0), (0, 0, 0, 0))
        out = sprite.encode(b, im)
        self.assertEqual(out[32], 0x20)
        self.assertEqual(out[:32] + out[33:], b[:32] + b[33:])
        with self.assertRaises(ValueError):
            sprite.encode(b, Image.new("RGBA", (16, 8)))
