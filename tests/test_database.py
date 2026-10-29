
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import database


class DatabaseTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = (
            Path(self.temp_dir.name) / "test_dadvand.db"
        )

        self.database_patch = patch.multiple(
            database,
            DATABASE_DIR=self.db_path.parent,
            DATABASE_PATH=self.db_path,
        )
        self.database_patch.start()

        database.initialize_database()

    def tearDown(self):
        self.database_patch.stop()
        self.temp_dir.cleanup()

    def test_database_tables_are_created(self):
        with database.get_connection() as connection:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()

        table_names = {row["name"] for row in rows}

        self.assertIn("sources", table_names)
        self.assertIn("documents", table_names)
        self.assertIn("legal_topics", table_names)
        self.assertIn("search_topics", table_names)

    def test_source_and_document_are_saved(self):
        source_id = database.add_source(
            source_type="test",
            source_name="آزمون منبع",
            file_hash="test-hash-001",
        )

        document_id = database.add_document(
            source_id=source_id,
            title="آزمون سند",
            content="این متن صرفاً برای آزمون پایگاه داده است.",
        )

        with database.get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM documents
                WHERE id = ?
                """,
                (document_id,),
            ).fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row["source_id"], source_id)
        self.assertEqual(row["title"], "آزمون سند")

    def test_duplicate_hash_can_be_found(self):
        database.add_source(
            source_type="test",
            source_name="منبع آزمایشی",
            file_hash="unique-test-hash",
        )

        found = database.find_source_by_hash(
            "unique-test-hash"
        )

        self.assertIsNotNone(found)
        self.assertEqual(
            found["source_name"],
            "منبع آزمایشی",
        )

    def test_empty_document_is_rejected(self):
        source_id = database.add_source(
            source_type="test",
            source_name="منبع آزمون",
        )

        with self.assertRaises(ValueError):
            database.add_document(
                source_id=source_id,
                content="   ",
            )


if __name__ == "__main__":
    unittest.main()
