
import hashlib
from pathlib import Path

from core import database
from core.ingestion import IngestionManager


class ArchiveManager:
    """مدیریت ورود منابع و ذخیره متن استخراج‌شده."""

    def __init__(self):
        self.ingestion = IngestionManager()
        database.initialize_database()

    @staticmethod
    def _file_hash(file_path):
        digest = hashlib.sha256()

        with open(file_path, "rb") as file:
            for chunk in iter(
                lambda: file.read(1024 * 1024),
                b"",
            ):
                digest.update(chunk)

        return digest.hexdigest()

    def import_file(self, file_path, category=None):
        path = Path(file_path)

        if not path.is_file():
            raise FileNotFoundError(
                f"فایل پیدا نشد: {path}"
            )

        file_hash = self._file_hash(path)

        existing = database.find_source_by_hash(file_hash)

        if existing:
            return {
                "status": "duplicate",
                "source_id": existing["id"],
                "message": "این فایل قبلاً در بایگانی ثبت شده است.",
            }

        content = self.ingestion.extract_file(path)

        source_id = database.add_source(
            source_type=path.suffix.lower().lstrip("."),
            source_name=path.name,
            source_path=str(path),
            file_hash=file_hash,
        )

        document_id = database.add_document(
            source_id=source_id,
            title=path.stem,
            content=content,
        )

        if category:
            database.add_legal_topic(
                document_id=document_id,
                topic_title=path.stem,
                topic_content=content,
                category=category,
            )

        return {
            "status": "imported",
            "source_id": source_id,
            "document_id": document_id,
            "message": "منبع با موفقیت به بایگانی اضافه شد.",
        }

    def import_url(self, url, title=None, category=None):
        url = (url or "").strip()

        if not url:
            raise ValueError("نشانی اینترنتی وارد نشده است.")

        existing = database.find_source_by_url(url)

        if existing:
            return {
                "status": "duplicate",
                "source_id": existing["id"],
                "message": "این نشانی قبلاً در بایگانی ثبت شده است.",
            }

        content = self.ingestion.extract_url(url)

        source_id = database.add_source(
            source_type="url",
            source_name=title or url,
            source_url=url,
        )

        document_id = database.add_document(
            source_id=source_id,
            title=title or url,
            content=content,
        )

        if category:
            database.add_legal_topic(
                document_id=document_id,
                topic_title=title or url,
                topic_content=content,
                category=category,
            )

        return {
            "status": "imported",
            "source_id": source_id,
            "document_id": document_id,
            "message": "متن صفحه به بایگانی اضافه شد.",
        }
