"""Regression tests with synthetic, redistributable SSD records."""
import struct
import unittest

import ssd_records as S


def sample():
    instruction = struct.pack('<HHHBBII', 137, 16, 0x301d, 1, 0, 3, 0)
    text = struct.pack('<HBB',137,1,12) + b'Hello\0\0\0'
    return struct.pack('<4sIIHHIIII',b'SSD\0',196609,60,1,1,16,12,0,0)+instruction+text


class RecordsTests(unittest.TestCase):
    def test_roundtrip(self):
        self.assertEqual(S.replace(sample(),{}),sample())

    def test_headerless_variant_preserves_missing_magic(self):
        source = b'\0\0\0\0' + sample()[4:]
        output = S.replace(source, {0:b'Hola'})
        self.assertEqual(output[:4], b'\0\0\0\0')
        end, _, records = S.parse(output)
        self.assertEqual(records[0].body, b'Hola')
        self.assertEqual(output[32:end], source[32:48])

    def test_grow_updates_record_and_sections_but_not_code(self):
        source=sample()
        output=S.replace(source,{0:b'A much longer sentence.'})
        end,_,records=S.parse(output)
        self.assertEqual(output[32:end],source[32:48])
        self.assertEqual(records[0].body,b'A much longer sentence.')
        self.assertEqual(records[0].raw[3],28)
        self.assertEqual(struct.unpack_from('<I',output,20)[0],28)

    def test_reject_old_growth_without_record_size_update(self):
        output=bytearray(sample()[:48])+sample()[48:52]+b'A much longer sentence.\0'
        struct.pack_into('<I',output,8,len(output))
        struct.pack_into('<I',output,20,len(output)-48)
        with self.assertRaises(ValueError):S.parse(output)

    def test_byte_length_limit_is_not_silently_truncated(self):
        S.replace(sample(),{0:b'A'*247})
        with self.assertRaises(ValueError):S.replace(sample(),{0:b'A'*248})

    def test_reject_embedded_nul_and_bad_index(self):
        with self.assertRaises(ValueError):S.replace(sample(),{0:b'a\0b'})
        with self.assertRaises(ValueError):S.replace(sample(),{1:b'text'})
        bad=bytearray(sample());struct.pack_into('<I',bad,44,1)
        with self.assertRaises(ValueError):S.parse(bad)


if __name__=='__main__':unittest.main()
