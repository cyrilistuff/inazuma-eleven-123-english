"""Trasladado de tools/test_legacy_sprite.py (F1.5, #46), caso de LZ10 óptimo; datos sintéticos."""

import unittest
from functools import lru_cache

from ie123kit.nucleo.compresion.lz10 import compress_optimal, decompress


class LegacySpriteTests(unittest.TestCase):
    def test_optimal_compression_matches_exhaustive_token_search(self):
        for data in [b"", b"a", b"a" * 35, b"abcabcabcabcdabc", b"AB" * 20, bytes(range(40))]:

            @lru_cache(None)
            def cost(i, slot, data=data):
                if i == len(data):
                    return 0
                nxt = (slot + 1) % 8
                flag = int(slot == 0)
                result = flag + 1 + cost(i + 1, nxt)
                for distance in range(1, min(i, 4096) + 1):
                    for length in range(3, min(18, len(data) - i) + 1):
                        if data[i : i + length] == data[i - distance : i - distance + length]:
                            result = min(result, flag + 2 + cost(i + length, nxt))
                return result

            encoded = compress_optimal(data)
            self.assertEqual(decompress(encoded), data)
            self.assertEqual(len(encoded) - 4, cost(0, 0))
