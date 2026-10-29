
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import database
from core.legal_search import LegalSearch


class TestLegalSearch(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_dir = Path(self.temp_dir.name)
        self.db_path = self.db_dir / "test.db"

        self.patcher = patch.multiple(
            database,
            DATABASE_DIR=self.db_dir,
            DATABASE_PATH=self.db_path,
        )
        self.patcher.start()

        database.initialize_database()

        source_id = database.add_source(
            source_name="منبع آزمایشی",
            source_type="test",
            source_path=None,
            source_hash="test_hash_001",
            source_url=None,
            category="آزمایشی",
        )

        database.add_document(
            source_id=source_id,
            title="عنوان آزمایشی",
            content="این متن صرفاً برای آزمایش جستجو در بایگانی دادوند است.",
            category="آزمایشی",
            page_number=1,
        )

        self.searcher = LegalSearch()

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

    def test_search_finds_archived_text(self):
        results = self.searcher.search("آزمایش")

        self.assertTrue(results.get("found"))
        self.assertTrue(results.get("results"))

    def test_missing_text_is_not_found(self):
        results = self.searcher.search("عبارت‌ناموجود‌در‌بایگانی")

        self.assertFalse(results.get("found"))
        self.assertEqual(
            results.get("message"),
            "در بایگانی یافت نشد."
        )

    def test_empty_query_returns_no_results(self):
        results = self.searcher.search("   ")

        self.assertFalse(results.get("found"))

    def test_search_does_not_create_legal_facts(self):
        results = self.searcher.search(
            "ماده قانونی ساختگی برای آزمایش"
        )

        self.assertFalse(results.get("found"))


if __name__ == "__main__":
    unittest.main()
