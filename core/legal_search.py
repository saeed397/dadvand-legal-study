# -*- coding: utf-8 -*-
"""جست‌وجوی سراسری و مستند در بایگانی دادوند.

این ماژول فقط داده‌های ثبت‌شده در پایگاه داده را بازیابی می‌کند و
هیچ متن یا محتوای حقوقی تولید، تکمیل یا حدس نمی‌زند.
"""

import re
from typing import Dict, List, Optional, Iterable, Any

try:
    from .database import LegalDatabase
except ImportError:
    from database import LegalDatabase


class LegalSearch:
    """جست‌وجوی اسناد و موضوعات در تمام دسته‌های بایگانی."""

    def __init__(self, db: Optional[LegalDatabase] = None):
        self.db = db or LegalDatabase()

    @staticmethod
    def _normalize(value: Any) -> str:
        """یکسان‌سازی حروف عربی/فارسی و فاصله‌ها، فقط برای تطبیق جست‌وجو."""
        text = str(value or "").casefold()
        text = text.replace("ي", "ی").replace("ى", "ی").replace("ك", "ک")
        text = text.replace("\u0640", "")  # کشیده
        text = re.sub(r"[\u064B-\u065F\u0670]", "", text)  # اعراب
        text = text.replace("\u200c", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @classmethod
    def _terms(cls, query: str) -> List[str]:
        normalized = cls._normalize(query)
        return list(dict.fromkeys(
            token for token in re.findall(r"[a-z0-9\u0600-\u06ff]+", normalized)
            if len(token) > 1
        ))

    @classmethod
    def _variants(cls, term: str) -> List[str]:
        """صورت‌های رایج عربی/فارسی برای پوشش تفاوت تایپی در اسناد."""
        variants = {
            term,
            term.replace("ی", "ي"),
            term.replace("ک", "ك"),
        }
        return [item for item in variants if item]

    @classmethod
    def _score(cls, value: str, terms: List[str], normalized_query: str) -> int:
        text = cls._normalize(value)
        score = sum(text.count(term) for term in terms)
        if normalized_query and normalized_query in text:
            score += 8
        return score

    def _document_candidates(
        self, terms: Iterable[str], category: Optional[str]
    ) -> Dict[int, Dict[str, Any]]:
        candidates: Dict[int, Dict[str, Any]] = {}
        searched = set()

        for term in terms:
            for variant in self._variants(term):
                if variant in searched:
                    continue
                searched.add(variant)

                for doc in self.db.search_documents(
                    variant, category=category, limit=500
                ):
                    doc_id = int(doc["id"])
                    candidates[doc_id] = {
                        "document_id": doc_id,
                        "title": doc.get("title") or "",
                        "category": doc.get("category") or "",
                        "source_name": doc.get("source_name") or "",
                        "source_type": doc.get("source_type") or "",
                        "source_url": doc.get("source_url"),
                        "page_number": doc.get("page_or_location"),
                        "content": doc.get("extracted_text") or "",
                        "result_type": "document",
                        "topic_id": None,
                    }

        return candidates

    def _topic_candidates(
        self, terms: Iterable[str], category: Optional[str],
        normalized_query: str
    ) -> Dict[str, Dict[str, Any]]:
        candidates: Dict[str, Dict[str, Any]] = {}
        topic_ids = set()
        searched = set()

        for term in terms:
            for variant in self._variants(term):
                if variant in searched:
                    continue
                searched.add(variant)

                for topic in self.db.search_topics(
                    variant, category=category, limit=500
                ):
                    topic_id = int(topic["id"])
                    if topic_id in topic_ids:
                        continue
                    topic_ids.add(topic_id)

                    full = self.db.get_topic(topic_id)
                    if not full:
                        continue

                    # موضوع بدون سند مرجع، منبع مستقل و قابل استناد محسوب نمی‌شود.
                    source_id = full.get("source_document_id")
                    if source_id is None:
                        continue

                    with self.db._connect() as conn:
                        row = conn.execute(
                            """SELECT d.id, d.title, d.category,
                                      d.page_or_location, s.source_name,
                                      s.source_type, s.source_url
                               FROM documents AS d
                               LEFT JOIN sources AS s ON s.id = d.source_id
                               WHERE d.id = ?""",
                            (int(source_id),),
                        ).fetchone()

                    if not row:
                        continue

                    source_doc = dict(row)
                    official_text = full.get("official_text") or ""
                    title = full.get("title") or source_doc.get("title") or ""
                    searchable_text = "\n".join((
                        title,
                        official_text,
                        full.get("plain_explanation") or "",
                        full.get("hypothetical_court_example") or "",
                    ))

                    candidates[f"topic:{topic_id}"] = {
                        "document_id": int(source_doc["id"]),
                        "title": title,
                        "category": (
                            full.get("category")
                            or source_doc.get("category")
                            or ""
                        ),
                        "source_name": source_doc.get("source_name") or "",
                        "source_type": source_doc.get("source_type") or "",
                        "source_url": source_doc.get("source_url"),
                        "page_number": (
                            full.get("source_location")
                            or source_doc.get("page_or_location")
                        ),
                        "content": official_text,
                        "result_type": "topic",
                        "topic_id": topic_id,
                        "_searchable_text": searchable_text,
                    }

        return candidates

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        original_query = str(query or "").strip()
        if not original_query:
            return {
                "found": False,
                "message": "عبارت جست‌وجو را وارد کنید.",
                "query": original_query,
                "results": [],
            }

        try:
            limit = max(1, min(int(limit), 100))
        except (TypeError, ValueError):
            limit = 10

        normalized_query = self._normalize(original_query)
        terms = self._terms(original_query)
        if not terms:
            return {
                "found": False,
                "message": "عبارت قابل جست‌وجویی وارد نشده است.",
                "query": original_query,
                "results": [],
            }

        # category=None یعنی جست‌وجو در همه دسته‌های بایگانی.
        candidates = self._document_candidates(terms, category)
        candidates.update(
            self._topic_candidates(terms, category, normalized_query)
        )

        ranked = []
        for item in candidates.values():
            searchable = item.pop("_searchable_text", None)
            if searchable is None:
                searchable = (item.get("title") or "") + "\n" + (
                    item.get("content") or ""
                )

            score = self._score(searchable, terms, normalized_query)
            if score > 0:
                item["_score"] = score
                ranked.append(item)

        ranked.sort(
            key=lambda item: (
                item["_score"],
                item.get("result_type") == "topic",
                item["document_id"],
            ),
            reverse=True,
        )

        results = []
        for item in ranked[:limit]:
            item.pop("_score", None)
            results.append(item)

        return {
            "found": bool(results),
            "message": (
                "نتایج زیر از اسناد و موضوعات دارای منبع ثبت‌شده در بایگانی بازیابی شده‌اند."
                if results else "در بایگانی یافت نشد."
            ),
            "query": original_query,
            "results": results,
        }


def search_legal_archive(
    query: str,
    category: Optional[str] = None,
    limit: int = 10,
    db: Optional[LegalDatabase] = None,
) -> Dict[str, Any]:
    """رابط ساده برای استفاده در صفحه جست‌وجوی دادوند."""
    return LegalSearch(db=db).search(
        query=query, category=category, limit=limit
    )
