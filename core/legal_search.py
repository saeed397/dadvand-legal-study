
from core import database


class LegalSearch:
    """جست‌وجوی مطالب حقوقی فقط در اسناد بایگانی‌شده."""

    def search(self, query, limit=30):
        query = (query or "").strip()

        if not query:
            return {
                "found": False,
                "message": "عبارت جست‌وجو را وارد کنید.",
                "results": [],
            }

        results = database.search_documents(
            keyword=query,
            limit=limit,
        )

        if not results:
            return {
                "found": False,
                "message": "در بایگانی یافت نشد.",
                "results": [],
            }

        return {
            "found": True,
            "message": f"{len(results)} نتیجه در بایگانی پیدا شد.",
            "results": [
                {
                    "document_id": row["id"],
                    "title": row["title"] or "بدون عنوان",
                    "content": row["content"],
                    "page_number": row["page_number"],
                    "source_name": row["source_name"],
                    "source_type": row["source_type"],
                    "source_url": row["source_url"],
                }
                for row in results
            ],
        }

    def search_topics(self, query, limit=30):
        query = (query or "").strip()

        if not query:
            return []

        limit = max(1, min(int(limit), 500))
        pattern = f"%{query}%"

        with database.get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    legal_topics.id,
                    legal_topics.document_id,
                    legal_topics.topic_title,
                    legal_topics.topic_content,
                    legal_topics.category,
                    documents.title AS document_title,
                    sources.source_name
                FROM legal_topics
                JOIN documents
                    ON documents.id = legal_topics.document_id
                JOIN sources
                    ON sources.id = documents.source_id
                WHERE legal_topics.topic_title LIKE ?
                   OR legal_topics.topic_content LIKE ?
                ORDER BY legal_topics.id DESC
                LIMIT ?
                """,
                (pattern, pattern, limit),
            ).fetchall()

        return [
            {
                "topic_id": row["id"],
                "document_id": row["document_id"],
                "topic_title": row["topic_title"],
                "topic_content": row["topic_content"],
                "category": row["category"],
                "document_title": row["document_title"],
                "source_name": row["source_name"],
            }
            for row in rows
        ]
