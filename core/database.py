
# -*- coding: utf-8 -*-
"""
Dadvand Legal Study
Local SQLite database.

اصل بنیادین:
هیچ محتوای حقوقی در این ماژول تولید یا حدس زده نمی‌شود.
متن رسمی باید عیناً از منابع بایگانی‌شده استخراج شود.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime


# مسیر پیش‌فرض پایگاه داده:
# ریشه پروژه / storage / database / legal_archive.db
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = (
    PROJECT_ROOT / "storage" / "database" / "legal_archive.db"
)

NO_SOURCE_MESSAGE = (
    "عدم وجود اطلاعات در بایگانی اسناد ارسالی؛ "
    "ارائه پاسخ مستند بر اساس مدارک موجود امکان‌پذیر نیست."
)

LEGAL_CATEGORIES = [
    "حقوق مدنی",
    "آیین دادرسی مدنی",
    "حقوق تجارت",
    "حقوق جزا",
    "آیین دادرسی کیفری",
    "حقوق اساسی",
    "فقه و اصول فقه",
    "حقوق ثبت",
    "سایر قوانین",
]


def _now():
    return datetime.now().isoformat(timespec="seconds")


class LegalDatabase:
    """مدیریت پایگاه داده SQLite اپلیکیشن دادوند."""

    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _connect(self):
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        return conn

    def initialize(self):
        """ساخت جداول و شاخص‌های پایگاه داده."""

        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode = WAL")

            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    source_path TEXT,
                    source_url TEXT,
                    sha256 TEXT,
                    imported_at TEXT NOT NULL,
                    extraction_status TEXT NOT NULL DEFAULT 'pending',
                    review_status TEXT NOT NULL DEFAULT 'not_reviewed',
                    notes TEXT
                );

                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    subject TEXT,
                    extracted_text TEXT NOT NULL DEFAULT '',
                    text_quality TEXT NOT NULL DEFAULT 'unknown',
                    page_or_location TEXT,
                    document_reference TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (source_id)
                        REFERENCES sources(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS legal_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    subject TEXT,
                    official_text TEXT NOT NULL DEFAULT '',
                    official_text_status TEXT NOT NULL DEFAULT 'not_available',
                    plain_explanation TEXT NOT NULL DEFAULT '',
                    hypothetical_court_example TEXT NOT NULL DEFAULT '',
                    mcq_items_json TEXT NOT NULL DEFAULT '[]',
                    source_document_id INTEGER,
                    source_location TEXT,
                    review_status TEXT NOT NULL DEFAULT 'not_reviewed',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (source_document_id)
                        REFERENCES documents(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS topic_sources (
                    topic_id INTEGER NOT NULL,
                    document_id INTEGER NOT NULL,
                    source_location TEXT,
                    relation_note TEXT,
                    PRIMARY KEY (topic_id, document_id),
                    FOREIGN KEY (topic_id)
                        REFERENCES legal_topics(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id)
                        REFERENCES documents(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_sources_sha256
                    ON sources(sha256);

                CREATE INDEX IF NOT EXISTS idx_sources_url
                    ON sources(source_url);

                CREATE INDEX IF NOT EXISTS idx_documents_category
                    ON documents(category);

                CREATE INDEX IF NOT EXISTS idx_documents_source
                    ON documents(source_id);

                CREATE INDEX IF NOT EXISTS idx_topics_category
                    ON legal_topics(category);

                CREATE INDEX IF NOT EXISTS idx_topics_title
                    ON legal_topics(title);
            """)

    @staticmethod
    def _validate_category(category):
        if category not in LEGAL_CATEGORIES:
            raise ValueError("دسته حقوقی معتبر نیست.")

    def find_source_by_sha256(self, sha256):
        if not sha256:
            return None

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM sources
                WHERE sha256 = ?
                ORDER BY id DESC LIMIT 1
                """,
                (sha256,)
            ).fetchone()

            return dict(row) if row else None

    def find_source_by_url(self, source_url):
        source_url = (source_url or "").strip()
        if not source_url:
            return None

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM sources
                WHERE source_url = ?
                ORDER BY id DESC LIMIT 1
                """,
                (source_url,)
            ).fetchone()

            return dict(row) if row else None

    def get_document_by_source(self, source_id):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM documents
                WHERE source_id = ?
                ORDER BY id DESC LIMIT 1
                """,
                (source_id,)
            ).fetchone()

            return dict(row) if row else None

    def add_source(
        self,
        source_type,
        source_name,
        source_path=None,
        source_url=None,
        sha256=None,
        extraction_status="pending",
        review_status="not_reviewed",
        notes=None
    ):
        allowed = {
            "pdf", "docx", "txt", "md",
            "image", "url", "other"
        }

        if source_type not in allowed:
            raise ValueError("نوع منبع نامعتبر است.")

        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO sources (
                    source_type, source_name, source_path,
                    source_url, sha256, imported_at,
                    extraction_status, review_status, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_type,
                    source_name,
                    source_path,
                    source_url,
                    sha256,
                    _now(),
                    extraction_status,
                    review_status,
                    notes
                )
            )

            return cur.lastrowid

    def update_source_status(
        self,
        source_id,
        extraction_status=None,
        review_status=None,
        notes=None
    ):
        fields = []
        values = []

        if extraction_status is not None:
            fields.append("extraction_status = ?")
            values.append(extraction_status)

        if review_status is not None:
            fields.append("review_status = ?")
            values.append(review_status)

        if notes is not None:
            fields.append("notes = ?")
            values.append(notes)

        if not fields:
            return False

        values.append(source_id)

        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE sources SET "
                + ", ".join(fields)
                + " WHERE id = ?",
                values
            )

            return cur.rowcount > 0

    def add_document(
        self,
        source_id,
        title,
        category,
        extracted_text="",
        subject=None,
        text_quality="unknown",
        page_or_location=None,
        document_reference=None
    ):
        self._validate_category(category)

        if not title:
            raise ValueError("عنوان سند نمی‌تواند خالی باشد.")

        now = _now()

        with self._connect() as conn:
            source = conn.execute(
                "SELECT id FROM sources WHERE id = ?",
                (source_id,)
            ).fetchone()

            if source is None:
                raise ValueError("منبع موردنظر وجود ندارد.")

            cur = conn.execute(
                """
                INSERT INTO documents (
                    source_id, title, category, subject,
                    extracted_text, text_quality,
                    page_or_location, document_reference,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    title,
                    category,
                    subject,
                    extracted_text or "",
                    text_quality,
                    page_or_location,
                    document_reference,
                    now,
                    now
                )
            )

            return cur.lastrowid

    def add_legal_topic(
        self,
        title,
        category,
        subject=None,
        official_text="",
        official_text_status="not_available",
        plain_explanation="",
        hypothetical_court_example="",
        mcq_items=None,
        source_document_id=None,
        source_location=None,
        review_status="not_reviewed"
    ):
        self._validate_category(category)

        if not title:
            raise ValueError("عنوان موضوع نمی‌تواند خالی باشد.")

        mcq_items = [] if mcq_items is None else mcq_items

        if not isinstance(mcq_items, list):
            raise TypeError("mcq_items باید فهرست باشد.")

        if official_text and source_document_id is None:
            official_text_status = "needs_source"

        now = _now()

        with self._connect() as conn:
            if source_document_id is not None:
                exists = conn.execute(
                    "SELECT id FROM documents WHERE id = ?",
                    (source_document_id,)
                ).fetchone()

                if exists is None:
                    raise ValueError("سند مرجع وجود ندارد.")

            cur = conn.execute(
                """
                INSERT INTO legal_topics (
                    title, category, subject,
                    official_text, official_text_status,
                    plain_explanation, hypothetical_court_example,
                    mcq_items_json, source_document_id,
                    source_location, review_status,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    category,
                    subject,
                    official_text,
                    official_text_status,
                    plain_explanation,
                    hypothetical_court_example,
                    json.dumps(mcq_items, ensure_ascii=False),
                    source_document_id,
                    source_location,
                    review_status,
                    now,
                    now
                )
            )

            topic_id = cur.lastrowid

            if source_document_id is not None:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO topic_sources (
                        topic_id, document_id,
                        source_location, relation_note
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        topic_id,
                        source_document_id,
                        source_location,
                        "منبع اصلی"
                    )
                )

            return topic_id

    def link_topic_source(
        self,
        topic_id,
        document_id,
        source_location=None,
        relation_note=None
    ):
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO topic_sources (
                    topic_id, document_id,
                    source_location, relation_note
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    topic_id,
                    document_id,
                    source_location,
                    relation_note
                )
            )

    def get_topic(self, topic_id):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    t.*,
                    d.title AS source_document_title,
                    d.page_or_location AS document_page_or_location,
                    s.source_name,
                    s.source_type,
                    s.source_url,
                    s.source_path
                FROM legal_topics t
                LEFT JOIN documents d
                    ON d.id = t.source_document_id
                LEFT JOIN sources s
                    ON s.id = d.source_id
                WHERE t.id = ?
                """,
                (topic_id,)
            ).fetchone()

            if row is None:
                return None

            result = dict(row)

            try:
                result["mcq_items"] = json.loads(
                    result.pop("mcq_items_json")
                )
            except (TypeError, json.JSONDecodeError):
                result["mcq_items"] = []

            return result

    def search_documents(self, query, category=None, limit=50):
        query = (query or "").strip()

        if not query:
            return []

        pattern = "%" + query + "%"

        sql = """
            SELECT
                d.*,
                s.source_name,
                s.source_type,
                s.source_url
            FROM documents d
            JOIN sources s ON s.id = d.source_id
            WHERE (
                d.title LIKE ?
                OR d.subject LIKE ?
                OR d.extracted_text LIKE ?
            )
        """

        params = [pattern, pattern, pattern]

        if category:
            sql += " AND d.category = ?"
            params.append(category)

        sql += " ORDER BY d.id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 500)))

        with self._connect() as conn:
            return [
                dict(row)
                for row in conn.execute(sql, params).fetchall()
            ]

    def search_topics(self, query, category=None, limit=50):
        query = (query or "").strip()

        if not query:
            return []

        pattern = "%" + query + "%"

        sql = """
            SELECT
                id, title, category, subject,
                official_text_status,
                source_document_id,
                source_location,
                review_status
            FROM legal_topics
            WHERE (
                title LIKE ?
                OR subject LIKE ?
                OR official_text LIKE ?
                OR plain_explanation LIKE ?
                OR hypothetical_court_example LIKE ?
                OR mcq_items_json LIKE ?
            )
        """

        params = [pattern] * 6

        if category:
            sql += " AND category = ?"
            params.append(category)

        sql += " ORDER BY id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 500)))

        with self._connect() as conn:
            return [
                dict(row)
                for row in conn.execute(sql, params).fetchall()
            ]

    def list_topics(self, category=None, limit=100):
        """فهرست موضوعات؛ بدون نیاز به عبارت جست‌وجو."""
        sql = """
            SELECT
                id, title, category, subject,
                official_text_status,
                source_document_id,
                source_location,
                review_status
            FROM legal_topics
        """

        params = []

        if category:
            sql += " WHERE category = ?"
            params.append(category)

        sql += " ORDER BY id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 500)))

        with self._connect() as conn:
            return [
                dict(row)
                for row in conn.execute(sql, params).fetchall()
            ]

    def list_documents(self, category=None, limit=100):
        sql = """
            SELECT
                d.*,
                s.source_name,
                s.source_type,
                s.source_url
            FROM documents d
            JOIN sources s ON s.id = d.source_id
        """

        params = []

        if category:
            sql += " WHERE d.category = ?"
            params.append(category)

        sql += " ORDER BY d.id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 500)))

        with self._connect() as conn:
            return [
                dict(row)
                for row in conn.execute(sql, params).fetchall()
            ]

    def get_archive_status(self):
        with self._connect() as conn:
            return {
                "sources": conn.execute(
                    "SELECT COUNT(*) FROM sources"
                ).fetchone()[0],

                "documents": conn.execute(
                    "SELECT COUNT(*) FROM documents"
                ).fetchone()[0],

                "legal_topics": conn.execute(
                    "SELECT COUNT(*) FROM legal_topics"
                ).fetchone()[0],

                "needs_review": conn.execute(
                    """
                    SELECT COUNT(*) FROM sources
                    WHERE review_status IN (
                        'not_reviewed', 'needs_review'
                    )
                    """
                ).fetchone()[0]
            }

    @staticmethod
    def missing_source_message():
        return NO_SOURCE_MESSAGE


# این پایگاه داده صرفاً متن و اطلاعات استخراج‌شده از منابع
# را ذخیره و بازیابی می‌کند و محتوای حقوقی تولید نمی‌کند.
