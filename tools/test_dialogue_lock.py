import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import dialogue_lock as lock
from build_ie1_probe import layout


class DialogueLockTests(unittest.TestCase):
    def test_ascii_is_rejected_before_reading_files(self):
        with self.assertRaisesRegex(ValueError, 'ASCII'):
            lock.validate(False, None, layout)

    def test_missing_fonts_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'archivo cambiado o ausente'):
                lock.validate(True, Path(folder), layout)

    def test_changed_layout_is_rejected(self):
        # Isolate the layout check from local binary resources.
        with patch.object(lock, 'FONT_HASHES', {}), patch.object(lock, 'SOURCE_HASHES', {}):
            with self.assertRaisesRegex(ValueError, 'ajuste de lineas'):
                lock.validate(True, '.', self.test_ascii_is_rejected_before_reading_files)


if __name__ == '__main__':
    unittest.main()
