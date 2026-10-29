
# -*- coding: utf-8 -*-

import tempfile
import unittest
from pathlib import Path

from core.database import LegalDatabase
from core.topic_extractor import (
    _extract_sections,
    extract_topics_from_document,
)


class TestTopicExtractor(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"

        self.db = LegalDatabase(db_path=str(self.db_path))

        with self.db._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    category TEXT,
                    extracted_text TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS legal_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    category TEXT,
                    subject TEXT,
                    official_text TEXT,
                    official_text_status TEXT,
                    plain_explanation TEXT,
                    hypothetical_court_example TEXT,
                    mcq_items TEXT,
                    source_document_id INTEGER,
                    source_location TEXT,
                    review_status TEXT
                )
            """)

        with self.db._connect() as conn:
            cursor = conn.execute("""
                INSERT INTO documents (title, category, extracted_text)
                VALUES (?, ?, ?)
            """, (
                "سند آزمایشی",
                "آزمایشی",
                "مقدمه متن آزمایشی\n"
                "ماده ۱\n"
                "متن اول منبع.\n"
                "ماده ۲\n"
                "متن دوم منبع."
            ))
            self.document_id = cursor.lastrowid

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extracts_article_headings(self):
        sections = _extract_sections(
            "ماده ۱\nمتن اول\nماده ۲\nمتن دوم"
        )

        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0]["title"], "ماده ۱")
        self.assertIn("متن اول", sections[0]["official_text"])
        self.assertEqual(sections[1]["title"], "ماده ۲")

    def test_preview_does_not_save_topics(self):
        result = extract_topics_from_document(
            self.document_id,
            db=self.db,
            save=False,
        )

        self.assertFalse(result["saved"])
        self.assertGreaterEqual(result["sections_found"], 2)

        with self.db._connect() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM legal_topics"
            ).fetchone()[0]

        self.assertEqual(count, 0)

    def test_saving_twice_skips_duplicates(self):
        first = extract_topics_from_document(
            self.document_id,
            db=self.db,
            save=True,
        )
        second = extract_topics_from_document(
            self.document_id,
            db=self.db,
            save=True,
        )

        self.assertEqual(first["sections_found"], second["sections_found"])
        self.assertEqual(
            second["duplicates_skipped"],
            second["sections_found"],
        )

        with self.db._connect() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM legal_topics"
            ).fetchone()[0]

        self.assertEqual(count, first["sections_found"])

    def test_missing_document_raises_error(self):
        with self.assertRaises(ValueError):
            extract_topics_from_document(
                999999,
                db=self.db,
                save=False,
            )

    def test_empty_text_has_no_sections(self):
        sections = _extract_sections("")
        self.assertEqual(sections, [])


if __name__ == "__main__":
    unittest.main()
