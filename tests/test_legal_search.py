
# -*- coding: utf-8 -*-
"""آزمون‌های جست‌وجوی منابع حقوقی دادوند."""

from core.legal_search import normalize_text


def test_persian_and_arabic_characters_are_normalized():
    assert normalize_text("ي ك") == normalize_text("ی ک")


def test_diacritics_are_removed():
    assert normalize_text("قَانُون") == normalize_text("قانون")


def test_half_space_is_handled():
    assert normalize_text("آیین‌دادرسی") == normalize_text("آیین دادرسی")


def test_empty_input_returns_empty_text():
    assert normalize_text("") == ""


def test_normalization_preserves_meaningful_words():
    result = normalize_text("ماده ۱۰ قانون مدنی")

    assert "ماده" in result
    assert "۱۰" in result
    assert "قانون" in result
    assert "مدنی" in result
