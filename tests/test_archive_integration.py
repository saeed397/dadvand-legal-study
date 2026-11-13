# -*- coding: utf-8 -*-
"""آزمون یکپارچگی مدیریت بایگانی و پایگاه داده دادوند."""

import pytest

from core.database import LegalDatabase
from core.archive_manager import ArchiveManager


@pytest.fixture
def archive(tmp_path):
    db = LegalDatabase(db_path=tmp_path / "test_archive.db")
    manager = ArchiveManager(
        db=db,
        inbox_path=tmp_path / "inbox",
    )
    return manager, db


def test_import_url_saves_source_and_document(archive, monkeypatch):
    manager, db = archive

    extracted_text = "متن آزمایشی استخراج‌شده از منبع حقوقی."

    def fake_process_source(source):
        return {
            "success": True,
            "text": extracted_text,
            "extraction_method": "test",
        }

    monkeypatch.setattr(
        manager.ingestion,
        "process_source",
        fake_process_source,
    )

    result = manager.import_source(
        "https://example.com/law#section",
        category="حقوق مدنی",
        title="سند آزمایشی",
    )

    assert result["success"] is True
    assert result["document_id"] is not None

    document = db.get_document_by_source(result["source_id"])

    assert document is not None
    assert document["title"] == "سند آزمایشی"
    assert document["extracted_text"] == extracted_text
    assert document["category"] == "حقوق مدنی"

    status = db.get_archive_status()

    assert status["sources"] == 1
    assert status["documents"] == 1


def test_duplicate_url_is_not_saved_twice(archive, monkeypatch):
    manager, db = archive

    def fake_process_source(source):
        return {
            "success": True,
            "text": "متن ثابت برای آزمون تکراری نبودن.",
            "extraction_method": "test",
        }

    monkeypatch.setattr(
        manager.ingestion,
        "process_source",
        fake_process_source,
    )

    first = manager.import_source(
        "https://example.com/legal",
        category="حقوق مدنی",
    )

    second = manager.import_source(
        "https://EXAMPLE.com/legal#part",
        category="حقوق مدنی",
    )

    assert first["success"] is True
    assert second["success"] is True
    assert second.get("duplicate") is True

    status = db.get_archive_status()

    assert status["sources"] == 1
    assert status["documents"] == 1


def test_invalid_category_is_rejected(archive):
    manager, db = archive

    result = manager.import_source(
        "https://example.com/legal",
        category="دسته نامعتبر",
    )

    assert result["success"] is False
    assert result["source_id"] is None

    status = db.get_archive_status()

    assert status["sources"] == 0
    assert status["documents"] == 0


def test_failed_extraction_does_not_create_document(
    archive,
    monkeypatch,
):
    manager, db = archive

    def fake_process_source(source):
        return {
            "success": False,
            "error": "خطای آزمایشی استخراج",
            "text": "",
        }

    monkeypatch.setattr(
        manager.ingestion,
        "process_source",
        fake_process_source,
    )

    result = manager.import_source(
        "https://example.com/failed",
        category="حقوق مدنی",
    )

    assert result["success"] is False
    assert result["document_id"] is None

    status = db.get_archive_status()

    assert status["sources"] == 1
    assert status["documents"] == 0