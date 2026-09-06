"""Synthetic fixtures only: no recovered game assets needed."""
import struct
import unittest

from ctpk_ui import decode, encode
from ui_archive import entries, unwrap


class UiFormats(unittest.TestCase):
    def test_pixel_formats_are_lossless(self):
        for fmt,bits in [(0,32),(1,24),(2,16),(3,16),(4,16),(5,16),(9,8),(11,4)]:
            with self.subTest(format=fmt):
                size=16*16*bits//8
                raw=bytearray(128+size)
                raw[:4]=b'CTPK'
                struct.pack_into('<HHI',raw,4,1,1,128)
                struct.pack_into('<IIIIHH',raw,32,64,size,0,fmt,16,16)
                raw[64:70]=b'x.tga\0'
                raw[128:]=bytes((i*37+13)%256 for i in range(size))
                self.assertEqual(encode(raw,decode(raw)),raw)

    def test_literal_sszl_and_arcv(self):
        raw=b'ARCV'+struct.pack('<IIIII',1,28,24,4,123)+b'test'
        packed=b''.join(b'\xff'+raw[i:i+8] for i in range(0,len(raw),8))
        wrapped=b'SSZL'+bytes(4)+struct.pack('<II',len(packed),len(raw))+packed
        self.assertEqual(unwrap(wrapped),raw)
        self.assertEqual(entries(raw),[(24,4,123)])
        with self.assertRaises(ValueError): entries(raw[:-1])


if __name__=='__main__':
    unittest.main()
