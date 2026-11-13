
# -*- coding: utf-8 -*-
"""آزمون‌های پاسخ مستند حقوقی دادوند."""

from core.legal_answer import LegalAnswer


class FakeLegalSearch:
    """جایگزین آزمایشی موتور جست‌وجو."""

    def __init__(self, result):
        self.result = result
        self.last_query = None

    def search(self, query, category=None, limit=10):
        self.last_query = {
            "query": query,
            "category": category,
            "limit": limit,
        }
        return self.result


def create_answer(search_result):
    """ساخت نمونه بدون اتصال به پایگاه داده واقعی."""
    answer = LegalAnswer.__new__(LegalAnswer)
    answer.searcher = FakeLegalSearch(search_result)
    return answer


def test_empty_question_is_rejected():
    answer = create_answer({"found": False, "results": []})

    result = answer.answer("   ")

    assert result["found"] is False
    assert result["sources"] == []
    assert "پرسش خود را وارد کنید" in result["message"]


def test_missing_archive_result_is_reported():
    answer = create_answer({
        "found": False,
        "results": [],
    })

    result = answer.answer("موضوع آزمایشی")

    assert result["found"] is False
    assert result["sources"] == []
    assert "یافت نشد" in result["message"]


def test_exact_source_text_is_preserved():
    exact_text = "این متن آزمایشی باید بدون تغییر منتقل شود."

    answer = create_answer({
        "found": True,
        "results": [
            {
                "document_id": 1,
                "title": "سند آزمایشی",
                "category": "حقوق مدنی",
                "content": exact_text,
                "source_name": "منبع آزمایشی",
                "result_type": "document",
            }
        ],
    })

    result = answer.answer("پرسش آزمایشی")

    assert result["found"] is True
    assert result["sources"][0]["exact_text"] == exact_text


def test_empty_source_text_is_not_returned():
    answer = create_answer({
        "found": True,
        "results": [
            {
                "document_id": 1,
                "title": "سند بدون متن",
                "content": "   ",
            }
        ],
    })

    result = answer.answer("پرسش آزمایشی")

    assert result["found"] is False
    assert result["sources"] == []


def test_search_parameters_are_forwarded():
    answer = create_answer({
        "found": False,
        "results": [],
    })

    answer.answer(
        "آزمایش",
        limit=5,
        category="حقوق مدنی",
    )

    assert answer.searcher.last_query == {
        "query": "آزمایش",
        "category": "حقوق مدنی",
        "limit": 5,
    }
