# -*- coding: utf-8 -*-

import hashlib
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch

from core.archive_manager import ArchiveManager
from core.database import LEGAL_CATEGORIES


class FakeDatabase:

    def __init__(self):
        self.sources = {}
        self.documents = {}
        self.next_source_id = 1
        self.next_document_id = 1

    def find_source_by_url(self, url):
        for source in self.sources.values():
            if source.get("source_url") == url:
                return source
        return None

    def find_source_by_sha256(self, sha256):
        for source in self.sources.values():
            if source.get("sha256") == sha256:
                return source
        return None

    def add_source(self, **kwargs):
        source_id = self.next_source_id
        self.next_source_id += 1

        source = {
            "id": source_id,
            **kwargs,
        }

        self.sources[source_id] = source
        return source_id

    def add_document(self, **kwargs):
        document_id = self.next_document_id
        self.next_document_id += 1

        document = {
            "id": document_id,
            **kwargs,
        }

        self.documents[document_id] = document
        return document_id

    def get_document_by_source(self, source_id):
        for document in self.documents.values():
            if document.get("source_id") == source_id:
                return document
        return None

    def update_source_status(self, source_id, **kwargs):
        if source_id in self.sources:
            self.sources[source_id].update(kwargs)

    def get_archive_status(self):
        return {
            "sources": len(self.sources),
            "documents": len(self.documents),
        }


class FakeIngestion:

    def __init__(self, inbox_path):
        self.inbox_path = Path(inbox_path)

        self.validation_result = (
            True,
            "اعتبارسنجی موفق بود.",
        )

        self.process_result = {
            "success": True,
            "text": "نمونه متن استخراج‌شده برای آزمایش دادوند",
            "extraction_method": "mock",
        }

        self.files = []

    def validate_file(self, source):
        return self.validation_result

    def validate_url(self, source):
        return self.validation_result

    def process_source(self, source):
        return dict(self.process_result)

    def list_supported_files(self):
        return list(self.files)


class TestArchiveManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        self.addCleanup(self.temp_dir.cleanup)

        self.inbox_path = Path(self.temp_dir.name)

        self.db = FakeDatabase()
        self.ingestion = FakeIngestion(self.inbox_path)

        patcher = patch(
            "core.archive_manager.DocumentIngestion",
            return_value=self.ingestion,
        )

        self.addCleanup(patcher.stop)
        patcher.start()

        self.manager = ArchiveManager(
            db=self.db,
            inbox_path=self.inbox_path,
        )

        self.category = next(iter(LEGAL_CATEGORIES))

    # -----------------------------------------
    # آزمایش محاسبه SHA256
    # -----------------------------------------

    def test_sha256_file(self):
        file_path = self.inbox_path / "sample.txt"
        file_path.write_text("دادوند", encoding="utf-8")

        expected = hashlib.sha256(
            "دادوند".encode("utf-8")
        ).hexdigest()

        result = self.manager._sha256_file(file_path)

        self.assertEqual(result, expected)

    # -----------------------------------------
    # آزمایش نرمال‌سازی URL
    # -----------------------------------------

    def test_normalize_url_removes_fragment(self):
        url = "https://example.com/legal/page#part"

        result = self.manager._normalize_url(url)

        self.assertEqual(
            result,
            "https://example.com/legal/page",
        )

    # -----------------------------------------
    # آزمایش تشخیص نوع منبع
    # -----------------------------------------

    def test_source_type_url(self):
        result = self.manager._source_type(
            "https://example.com/law"
        )

        self.assertEqual(result, "url")

    def test_source_type_pdf(self):
        result = self.manager._source_type(
            "sample.pdf"
        )

        self.assertEqual(result, "pdf")

    def test_source_type_docx(self):
        result = self.manager._source_type(
            "sample.docx"
        )

        self.assertEqual(result, "docx")

    def test_source_type_image(self):
        result = self.manager._source_type(
            "sample.png"
        )

        self.assertEqual(result, "image")

    # -----------------------------------------
    # آزمایش نام منبع
    # -----------------------------------------

    def test_source_name_url(self):
        result = self.manager._source_name(
            "https://example.com/legal/page"
        )

        self.assertEqual(
            result,
            "example.com/legal/page",
        )

    # -----------------------------------------
    # آزمایش دسته حقوقی نامعتبر
    # -----------------------------------------

    def test_import_source_invalid_category(self):
        result = self.manager.import_source(
            "https://example.com/law",
            category="دسته نامعتبر",
        )

        self.assertFalse(result["success"])
        self.assertEqual(len(self.db.sources), 0)

    # -----------------------------------------
    # آزمایش ثبت موفق URL
    # -----------------------------------------

    def test_import_url_saves_url_source(self):
        url = "https://example.com/legal/page#part"

        result = self.manager.import_source(
            url,
            category=self.category,
            title="صفحه قانونی",
        )

        print("\nIMPORT RESULT:", result)

        self.assertTrue(result["success"])

        saved_source = self.db.sources[
            result["source_id"]
        ]

        self.assertEqual(
            saved_source["source_type"],
            "url",
        )

        self.assertEqual(
            saved_source["source_url"],
            "https://example.com/legal/page",
        )

        self.assertIsNone(saved_source["sha256"])

        self.assertEqual(
            self.db.documents[
                result["document_id"]
            ]["title"],
            "صفحه قانونی",
        )

    # -----------------------------------------
    # آزمایش شکست اعتبارسنجی URL
    # -----------------------------------------

    def test_import_url_validation_failure(self):
        self.ingestion.validation_result = (
            False,
            "URL نامعتبر است.",
        )

        result = self.manager.import_source(
            "https://example.com/law",
            category=self.category,
        )

        self.assertFalse(result["success"])
        self.assertEqual(len(self.db.sources), 0)

    # -----------------------------------------
    # آزمایش شکست استخراج URL
    # -----------------------------------------

    def test_import_url_extraction_failure(self):
        self.ingestion.process_result = {
            "success": False,
            "error": "استخراج ناموفق بود.",
        }

        result = self.manager.import_source(
            "https://example.com/law",
            category=self.category,
        )

        self.assertFalse(result["success"])
        self.assertIsNone(result["document_id"])

    # -----------------------------------------
    # آزمایش ثبت موفق فایل
    # -----------------------------------------

    def test_import_file_saves_source(self):
        file_path = self.inbox_path / "sample.pdf"
        file_path.write_bytes(b"sample pdf content")

        result = self.manager.import_source(
            file_path,
            category=self.category,
            title="سند آزمایشی",
        )

        self.assertTrue(result["success"])

        saved_source = self.db.sources[
            result["source_id"]
        ]

        self.assertEqual(
            saved_source["source_type"],
            "pdf",
        )

        self.assertIsNotNone(
            saved_source["sha256"]
        )

        self.assertEqual(
            self.db.documents[
                result["document_id"]
            ]["title"],
            "سند آزمایشی",
        )

    # -----------------------------------------
    # آزمایش فایل نامعتبر
    # -----------------------------------------

    def test_import_file_validation_failure(self):
        file_path = self.inbox_path / "invalid.pdf"
        file_path.write_bytes(b"invalid")

        self.ingestion.validation_result = (
            False,
            "فایل معتبر نیست.",
        )

        result = self.manager.import_source(
            file_path,
            category=self.category,
        )

        self.assertFalse(result["success"])
        self.assertEqual(len(self.db.sources), 0)

    # -----------------------------------------
    # آزمایش متن استخراج‌شده خالی
    # -----------------------------------------

    def test_import_source_empty_text(self):
        self.ingestion.process_result = {
            "success": True,
            "text": "",
            "extraction_method": "mock",
        }

        result = self.manager.import_source(
            "https://example.com/law",
            category=self.category,
        )

        self.assertFalse(result["success"])
        self.assertIsNone(result["document_id"])

    # -----------------------------------------
    # آزمایش جلوگیری از ثبت منبع تکراری
    # -----------------------------------------

    def test_duplicate_url_is_not_saved_twice(self):
        url = "https://example.com/legal/page"

        first = self.manager.import_source(
            url,
            category=self.category,
        )

        second = self.manager.import_source(
            url,
            category=self.category,
        )

        self.assertTrue(first["success"])
        self.assertTrue(second["success"])

        self.assertEqual(len(self.db.sources), 1)
        self.assertEqual(len(self.db.documents), 1)

    # -----------------------------------------
    # آزمایش وضعیت بایگانی
    # -----------------------------------------

    def test_get_status(self):
        result = self.manager.get_status()

        self.assertEqual(result["sources"], 0)
        self.assertEqual(result["documents"], 0)


if __name__ == "__main__":
    unittest.main()