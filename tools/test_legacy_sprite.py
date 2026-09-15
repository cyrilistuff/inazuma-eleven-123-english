"""Synthetic tests; no game files required."""
import struct
import unittest
from functools import lru_cache
from PIL import Image
import legacy_sprite as sprite
from lz10 import compress_optimal, decompress


class LegacySpriteTests(unittest.TestCase):
    def fixture(self):
        b=bytearray(112)
        struct.pack_into('<7I',b,0,3,32,32,64,32,96,16)
        b[96:100]=bytes([1,0,0,0])
        for i in range(16):struct.pack_into('<H',b,64+2*i,31 if i else 0)
        b[32:64]=bytes([0x21]*32)  # Distinct indices with identical colours.
        return bytes(b)

    def test_preserves_palette_indices_and_other_chunks(self):
        b=self.fixture();im=sprite.decode(b)
        self.assertEqual(sprite.encode(b,im),b)
        im.putpixel((0,0),(0,0,0,0));out=sprite.encode(b,im)
        self.assertEqual(out[32],0x20)
        self.assertEqual(out[:32]+out[33:],b[:32]+b[33:])
        with self.assertRaises(ValueError):sprite.encode(b,Image.new('RGBA',(16,8)))

    def test_optimal_compression_matches_exhaustive_token_search(self):
        for data in [b'',b'a',b'a'*35,b'abcabcabcabcdabc',b'AB'*20,bytes(range(40))]:
            @lru_cache(None)
            def cost(i,slot):
                if i==len(data):return 0
                nxt=(slot+1)%8;flag=int(slot==0)
                result=flag+1+cost(i+1,nxt)
                for distance in range(1,min(i,4096)+1):
                    for length in range(3,min(18,len(data)-i)+1):
                        if data[i:i+length]==data[i-distance:i-distance+length]:
                            result=min(result,flag+2+cost(i+length,nxt))
                return result
            encoded=compress_optimal(data)
            self.assertEqual(decompress(encoded),data)
            self.assertEqual(len(encoded)-4,cost(0,0))


if __name__=='__main__':unittest.main()
