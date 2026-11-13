
# -*- coding: utf-8 -*-
"""آزمون‌های اولیه پایگاه داده دادوند."""

import pytest

from core.database import LegalDatabase


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "test_legal_archive.db"

    db = LegalDatabase(db_path=str(db_path))
    db.initialize()

    return db


def test_database_initializes(test_db):
    status = test_db.get_archive_status()

    assert isinstance(status, dict)
    assert status.get("sources") == 0
    assert status.get("documents") == 0
    assert status.get("legal_topics") == 0


def test_database_connection_works(test_db):
    with test_db._connect() as conn:
        result = conn.execute("SELECT 1").fetchone()

    assert result[0] == 1


def test_database_file_is_created(test_db, tmp_path):
    db_path = tmp_path / "test_legal_archive.db"

    assert db_path.exists()
