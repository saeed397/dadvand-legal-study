
from core.legal_search import LegalSearch


class LegalAnswer:
    """ارائه پاسخ مستند به اسناد بایگانی‌شده."""

    def __init__(self):
        self.searcher = LegalSearch()

    def answer(self, question, limit=10):
        question = (question or "").strip()

        if not question:
            return {
                "found": False,
                "message": "پرسش خود را وارد کنید.",
                "question": question,
                "sources": [],
            }

        search_result = self.searcher.search(
            question,
            limit=limit,
        )

        if not search_result["found"]:
            return {
                "found": False,
                "message": "در بایگانی یافت نشد.",
                "question": question,
                "sources": [],
            }

        sources = []

        for item in search_result["results"]:
            sources.append({
                "document_id": item["document_id"],
                "title": item["title"],
                "source_name": item["source_name"],
                "source_type": item["source_type"],
                "source_url": item["source_url"],
                "page_number": item["page_number"],
                "exact_text": item["content"],
            })

        return {
            "found": True,
            "message": (
                "متن‌های مرتبط زیر از بایگانی بازیابی شدند. "
                "این متن‌ها به‌تنهایی به معنای پاسخ قطعی حقوقی نیستند."
            ),
            "question": question,
            "sources": sources,
        }
