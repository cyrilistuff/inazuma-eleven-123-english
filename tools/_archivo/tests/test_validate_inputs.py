"""A missing build must fail rather than report a successful validation."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import validate


class InputTests(unittest.TestCase):
    def test_missing_pair_fails(self):
        with tempfile.TemporaryDirectory() as root, patch.object(validate,'REPO',root):
            self.assertFalse(validate.run(('game1',)))

    def test_missing_index_fails_without_parsing(self):
        with tempfile.TemporaryDirectory() as root, patch.object(validate,'REPO',root):
            d=Path(root)/'work/eve_var';d.mkdir(parents=True)
            (d/'game1.pkb').write_bytes(b'')
            with patch.object(validate,'validate') as check:
                self.assertFalse(validate.run(('game1',)))
                check.assert_not_called()

    def test_empty_selection_fails(self):
        self.assertFalse(validate.run(()))


if __name__=='__main__':unittest.main()
