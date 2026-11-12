# -*- coding: utf-8 -*-
"""
ساخت پاسخ مستند از نتایج بایگانی دادوند؛ بدون تولید محتوای حقوقی.
"""

from typing import Dict, Optional

try:
    from .legal_search import LegalSearch
    from .database import LegalDatabase
except ImportError:
    from legal_search import LegalSearch
    from database import LegalDatabase


class LegalAnswer:
    """پاسخ را فقط از متن‌های بازیابی‌شده از بایگانی تشکیل می‌دهد."""

    def __init__(self, db: Optional[LegalDatabase] = None):
        self.db = db or LegalDatabase()
        self.searcher = LegalSearch(db=self.db)

    def answer(
        self,
        question: str,
        limit: int = 10,
        category: Optional[str] = None
    ) -> Dict[str, object]:

        question = (question or "").strip()

        if not question:
            return {
                "found": False,
                "message": "پرسش خود را وارد کنید.",
                "question": question,
                "sources": [],
            }

        result = self.searcher.search(
            question,
            category=category,
            limit=limit,
        )

        if not result.get("found"):
            return {
                "found": False,
                "message": "در بایگانی یافت نشد.",
                "question": question,
                "sources": [],
            }

        sources = []

        for item in result.get("results", []):
            exact_text = item.get("content") or ""

            if not exact_text.strip():
                continue

            sources.append({
                "document_id": item.get("document_id"),
                "topic_id": item.get("topic_id"),
                "result_type": item.get(
                    "result_type", "document"
                ),
                "title": item.get("title") or "",
                "category": item.get("category") or "",
                "source_name": item.get("source_name") or "",
                "source_type": item.get("source_type") or "",
                "source_url": item.get("source_url"),
                "page_number": item.get("page_number"),

                # انتقال عین متن ذخیره‌شده بدون بازنویسی
                "exact_text": exact_text,
            })

        if not sources:
            return {
                "found": False,
                "message": "در بایگانی یافت نشد.",
                "question": question,
                "sources": [],
            }

        return {
            "found": True,
            "message": (
                "متن‌های مرتبط زیر عیناً از بایگانی بازیابی شده‌اند. "
                "این نتایج به‌تنهایی پاسخ قطعی حقوقی یا تأیید "
                "صحت رسمی متن نیستند. هیچ توضیح، مثال یا "
                "استدلال حقوقی خارج از منابع افزوده نشده است."
            ),
            "question": question,
            "sources": sources,
        }


def answer_from_archive(
    question: str,
    limit: int = 10,
    category: Optional[str] = None,
    db: Optional[LegalDatabase] = None
):
    """تابع کمکی برای فراخوانی از رابط کاربری."""

    return LegalAnswer(db=db).answer(
        question=question,
        limit=limit,
        category=category,
    )