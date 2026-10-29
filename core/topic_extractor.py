
import re

from core import database


class TopicExtractor:
    """استخراج ساختاری موضوعات از متن بایگانی، بدون تولید محتوای حقوقی."""

    # عنوان‌هایی که ممکن است در اسناد حقوقی دیده شوند
    HEADING_PATTERNS = [
        re.compile(
            r"^\s*(?:ماده|اصل)\s*[\u06F0-\u06F90-9]+"
            r"(?:\s*(?:مکرر|الحاقی))?.*$"
        ),
        re.compile(
            r"^\s*(?:فصل|بخش|باب|کتاب)\s+.+$"
        ),
        re.compile(
            r"^\s*(?:رأی|رای)\s+وحدت\s+رویه.*$"
        ),
        re.compile(
            r"^\s*نظریه\s+مشورتی.*$"
        ),
        re.compile(
            r"^\s*(?:دادنامه|شماره\s+دادنامه).*$"
        ),
        re.compile(
            r"^\s*(?:بخشنامه|آیین\s*نامه|تصویب\s*نامه).*$"
        ),
    ]

    def extract_from_document(self, document_id, category=None):
        with database.get_connection() as connection:
            document = connection.execute(
                """
                SELECT id, title, content
                FROM documents
                WHERE id = ?
                """,
                (document_id,),
            ).fetchone()

        if document is None:
            raise ValueError("سند موردنظر در بایگانی یافت نشد.")

        content = document["content"] or ""
        lines = content.splitlines()

        topics = []
        current_title = None
        current_lines = []

        def save_current():
            if not current_title:
                return

            topic_content = "\n".join(
                current_lines
            ).strip()

            if not topic_content:
                return

            topics.append(
                {
                    "title": current_title,
                    "content": topic_content,
                }
            )

        for line in lines:
            stripped = line.strip()

            if not stripped:
                continue

            is_heading = any(
                pattern.match(stripped)
                for pattern in self.HEADING_PATTERNS
            )

            if is_heading:
                save_current()
                current_title = stripped
                current_lines = [stripped]
            elif current_title:
                current_lines.append(stripped)

        save_current()

        # اگر عنوان ساختاری پیدا نشد، متن به‌صورت یک موضوع عمومی ثبت می‌شود.
        if not topics and content.strip():
            topics.append(
                {
                    "title": document["title"] or "متن سند",
                    "content": content.strip(),
                }
            )

        saved_count = 0

        for topic in topics:
            database.add_legal_topic(
                document_id=document_id,
                topic_title=topic["title"],
                topic_content=topic["content"],
                category=category,
            )
            saved_count += 1

        return {
            "document_id": document_id,
            "topics_found": len(topics),
            "topics_saved": saved_count,
            "topics": [
                topic["title"] for topic in topics
            ],
        }

    def extract_all_documents(self, category=None):
        with database.get_connection() as connection:
            documents = connection.execute(
                "SELECT id FROM documents ORDER BY id"
            ).fetchall()

        results = []

        for document in documents:
            result = self.extract_from_document(
                document["id"],
                category=category,
            )
            results.append(result)

        return results
