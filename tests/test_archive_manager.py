
# -*- coding: utf-8 -*-

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.archive_manager import ArchiveManager


class TestArchiveManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

        self.manager = ArchiveManager()

        self.sample_file = self.base_path / "sample.txt"
        self.sample_file.write_text(
            "این متن فقط برای آزمایش بایگانی دادوند است.",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sample_file_exists(self):
        self.assertTrue(self.sample_file.exists())

    def test_file_hash_is_stable(self):
        content = self.sample_file.read_bytes()

        first_hash = hashlib.sha256(content).hexdigest()
        second_hash = hashlib.sha256(content).hexdigest()

        self.assertEqual(first_hash, second_hash)

    def test_file_hash_changes_when_content_changes(self):
        first_hash = hashlib.sha256(
            self.sample_file.read_bytes()
        ).hexdigest()

        self.sample_file.write_text(
            "متن متفاوت برای آزمایش.",
            encoding="utf-8",
        )

        second_hash = hashlib.sha256(
            self.sample_file.read_bytes()
        ).hexdigest()

        self.assertNotEqual(first_hash, second_hash)


if __name__ == "__main__":
    unittest.main()
