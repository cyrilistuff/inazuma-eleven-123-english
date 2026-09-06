import unittest
from dialogue_typography import encode_fullwidth


class EncodingTests(unittest.TestCase):
    def test_controls_remain_ascii(self):
        data = encode_fullwidth(r'A B\nC\f%1FD')
        self.assertEqual(data, b'\x82\x60\x81\x40\x82\x61\\n\x82\x62\\f%1F\x82\x63')

    def test_accents_keep_spanish_carriers(self):
        self.assertEqual(encode_fullwidth('\u00e1'), '\u0391'.encode('shift_jis'))

    def test_missing_character_fails(self):
        with self.assertRaises(UnicodeEncodeError):
            encode_fullwidth('\U0001f600')


if __name__ == '__main__':
    unittest.main()
