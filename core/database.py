
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_ROOT / "storage" / "database"
DATABASE_PATH = DATABASE_DIR / "dadvand.db"


def get_connection():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(DATABASE_PATH))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_path TEXT,
                source_url TEXT,
                file_hash TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                page_number INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id)
                    REFERENCES sources(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS legal_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                topic_title TEXT NOT NULL,
                topic_content TEXT,
                category TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id)
                    REFERENCES documents(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS search_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_title TEXT NOT NULL,
                normalized_title TEXT,
                category TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_documents_source_id
                ON documents(source_id);

            CREATE INDEX IF NOT EXISTS idx_legal_topics_document_id
                ON legal_topics(document_id);

            CREATE INDEX IF NOT EXISTS idx_sources_file_hash
                ON sources(file_hash);

            CREATE INDEX IF NOT EXISTS idx_sources_source_url
                ON sources(source_url);

            CREATE INDEX IF NOT EXISTS idx_search_topics_normalized
                ON search_topics(normalized_title);
            """
        )


def add_source(
    source_type,
    source_name,
    source_path=None,
    source_url=None,
    file_hash=None,
):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO sources (
                source_type,
                source_name,
                source_path,
                source_url,
                file_hash
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                source_type,
                source_name,
                source_path,
                source_url,
                file_hash,
            ),
        )
        return cursor.lastrowid


def add_document(
    source_id,
    content,
    title=None,
    page_number=None,
):
    if not content or not content.strip():
        raise ValueError("متن سند خالی است.")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO documents (
                source_id,
                title,
                content,
                page_number
            )
            VALUES (?, ?, ?, ?)
            """,
            (source_id, title, content, page_number),
        )
        return cursor.lastrowid


def add_legal_topic(
    document_id,
    topic_title,
    topic_content=None,
    category=None,
):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO legal_topics (
                document_id,
                topic_title,
                topic_content,
                category
            )
            VALUES (?, ?, ?, ?)
            """,
            (document_id, topic_title, topic_content, category),
        )
        return cursor.lastrowid


def find_source_by_hash(file_hash):
    if not file_hash:
        return None

    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM sources WHERE file_hash = ? LIMIT 1",
            (file_hash,),
        ).fetchone()


def find_source_by_url(source_url):
    if not source_url:
        return None

    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM sources WHERE source_url = ? LIMIT 1",
            (source_url,),
        ).fetchone()


def search_documents(keyword, limit=50):
    keyword = (keyword or "").strip()

    if not keyword:
        return []

    limit = max(1, min(int(limit), 500))
    pattern = f"%{keyword}%"

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                documents.id,
                documents.title,
                documents.content,
                documents.page_number,
                sources.source_name,
                sources.source_type,
                sources.source_url
            FROM documents
            JOIN sources ON sources.id = documents.source_id
            WHERE documents.content LIKE ?
               OR documents.title LIKE ?
            ORDER BY documents.id DESC
            LIMIT ?
            """,
            (pattern, pattern, limit),
        ).fetchall()


def get_source_documents(source_id):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM documents
            WHERE source_id = ?
            ORDER BY id
            """,
            (source_id,),
        ).fetchall()


def get_all_sources():
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM sources ORDER BY id DESC"
        ).fetchall()
