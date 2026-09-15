import unittest
from pathlib import Path

from compact_typography import patch_pair
from font_patch import Font
from nftr_metrics import read_metrics


ROOT = Path(__file__).resolve().parents[1]


class CompactTypographyTests(unittest.TestCase):
    def test_native_mode_keeps_format_and_tightens_latin(self):
        source = ROOT/'work/fa_extract/font/FONT12.bcfnt'
        nftr_path = ROOT/'work/fa_extract/inazuma1/data_iz/font/FONT12.NFTR'
        if not source.exists() or not nftr_path.exists():
            self.skipTest('requires locally recovered IE1 FONT12 resources')
        nftr = nftr_path.read_bytes()
        bcfnt, changed_nftr, changed = patch_pair(source, nftr, mode='native')
        self.assertEqual(len(bcfnt), source.stat().st_size)
        self.assertEqual(len(changed_nftr), len(nftr))
        self.assertTrue(changed)
        read_metrics(changed_nftr)
        font = Font(source)
        patched = Font.__new__(Font)
        # Compare metric triples directly without writing a recovered asset.
        patched.path = None
        patched.b = font.b
        patched.data = bytearray(bcfnt)
        patched.t = font.t
        patched.cmap = font.cmap
        patched.PER = font.PER
        patched.doff = font.doff
        patched.sx = font.sx
        patched.sy = font.sy
        for character in ('i', 'j'):
            # j has a negative left bearing, so it guards the signed-metric
            # path as well as the ordinary narrow-letter path.
            self.assertEqual(
                patched.data[patched.cwdh_entry_off(patched.cmap[ord(character)+0xfee0]):][:3],
                font.data[
                    font.cwdh_entry_off(font.cmap[ord(character)]):
                    font.cwdh_entry_off(font.cmap[ord(character)]) + 3
                ],
            )


if __name__ == '__main__':
    unittest.main()
