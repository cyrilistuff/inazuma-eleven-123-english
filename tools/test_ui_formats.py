"""Synthetic fixtures only: no recovered game assets needed."""
import struct
import tempfile
import unittest

from PIL import Image

from ctpk_ui import decode, encode
from translate_ui_textures import paint
from ui_archive import entries, unwrap
from qna_regions import regions


class UiFormats(unittest.TestCase):
    def test_untextured_qna_part_is_not_a_texture_reference(self):
        raw=bytearray(64+32+128*2)
        raw[:8]=b' QNA 051'
        struct.pack_into('<III',raw,8,1,0,2)
        struct.pack_into('<III',raw,36,64,0,96)
        raw[64:69]=b'icon\0'
        for offset,index in [(96,0),(224,0xffffffff)]:
            struct.pack_into('<4f',raw,offset,0,16,16,32)
            struct.pack_into('<I',raw,offset+88,index)
        self.assertEqual(regions(raw),[('icon',(0,16,16,32))])
        struct.pack_into('<I',raw,224+88,1)
        with self.assertRaises(ValueError):regions(raw)

    def test_text_stroke_and_background_stay_inside_button(self):
        from PIL import ImageChops, ImageDraw
        canvas=Image.new('RGBA',(80,32),(40,40,40,255))
        ImageDraw.Draw(canvas).rectangle((1,1,78,30),outline='white',width=2)
        before=canvas.copy()
        paint(canvas,{'box':[5,5,75,27],'text':'Siguiente','size':20,
                      'stroke_width':2,'erase':'row_sample','sample_x':4},
              'C:/Windows/Fonts/arialbd.ttf')
        diff=ImageChops.difference(canvas,before)
        ImageDraw.Draw(diff).rectangle((5,5,74,26),fill=(0,0,0,0))
        self.assertFalse(any(c.getbbox() for c in diff.split()))

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

    def test_scaled_image_is_centered_inside_its_original_box(self):
        with tempfile.TemporaryDirectory() as directory:
            source = f'{directory}/logo.png'
            Image.new('RGBA',(40,20),(255,0,0,255)).save(source)
            canvas = Image.new('RGBA',(40,20))
            paint(canvas, {
                'box': [0,0,40,20],
                'image': source,
                'scale': .5,
            }, 'C:/Windows/Fonts/arialbd.ttf')
            self.assertEqual(canvas.getbbox(), (10,5,30,15))
            with self.assertRaises(ValueError):
                paint(canvas, {
                    'box': [0,0,40,20],
                    'image': source,
                    'scale': 0,
                }, 'C:/Windows/Fonts/arialbd.ttf')


if __name__=='__main__':
    unittest.main()
