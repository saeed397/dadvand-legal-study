
# -*- coding: utf-8 -*-
"""آزمون اولیه اتصال ماژول‌های اصلی دادوند."""


def test_core_modules_import():
    from core.database import LegalDatabase
    from core.archive_manager import ArchiveManager
    from core.ingestion import DocumentIngestion
    from core.extractors import TextExtractor
    from core.topic_extractor import extract_topics_from_document
    from core.legal_search import search_legal_archive
    from core.legal_answer import answer_from_archive

    assert LegalDatabase is not None
    assert ArchiveManager is not None
    assert DocumentIngestion is not None
    assert TextExtractor is not None
    assert callable(extract_topics_from_document)
    assert callable(search_legal_archive)
    assert callable(answer_from_archive)


def test_ui_modules_import():
    from ui.pages import render_pages
    from ui.navigation import render_navigation
    from ui.theme import apply_theme, render_theme_selector

    assert callable(render_pages)
    assert callable(render_navigation)
    assert callable(apply_theme)
    assert callable(render_theme_selector)
