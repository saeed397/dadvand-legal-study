
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.ingestion import IngestionManager


class IngestionTests(unittest.TestCase):

    def setUp(self):
        self.manager = IngestionManager()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_file_raises_error(self):
        missing_path = self.test_dir / "missing.pdf"

        with self.assertRaises(FileNotFoundError):
            self.manager.extract_file(missing_path)

    def test_unsupported_extension_raises_error(self):
        file_path = self.test_dir / "unsupported.txt"
        file_path.write_text(
            "متن آزمایشی",
            encoding="utf-8",
        )

        with self.assertRaises(ValueError):
            self.manager.extract_file(file_path)

    def test_docx_extraction(self):
        try:
            from docx import Document
        except ImportError:
            self.skipTest("کتابخانه python-docx نصب نیست.")

        file_path = self.test_dir / "sample.docx"

        document = Document()
        document.add_paragraph(
            "این متن صرفاً برای آزمون استخراج است."
        )
        document.save(str(file_path))

        extracted = self.manager.extract_file(file_path)

        self.assertIn(
            "این متن صرفاً برای آزمون استخراج است.",
            extracted,
        )

    def test_url_requires_http_scheme(self):
        with self.assertRaises(ValueError):
            self.manager.extract_url("example.com")

    def test_url_rejects_localhost(self):
        with self.assertRaises(ValueError):
            self.manager.extract_url(
                "http://localhost/test"
            )


if __name__ == "__main__":
    unittest.main()
