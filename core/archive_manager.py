
# -*- coding: utf-8 -*-

"""مدیریت دریافت، استخراج و ذخیره منابع در بایگانی دادوند."""

import hashlib
from pathlib import Path
from urllib.parse import urlparse, urlsplit, urlunsplit

try:
    from .database import LegalDatabase, LEGAL_CATEGORIES
    from .ingestion import DocumentIngestion
except ImportError:
    from database import LegalDatabase, LEGAL_CATEGORIES
    from ingestion import DocumentIngestion


IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".tif",
    ".tiff", ".webp", ".bmp"
}


class ArchiveManager:

    def __init__(self, db=None, inbox_path=None):
        self.db = db if db is not None else LegalDatabase()

        if inbox_path is None:
            inbox_path = (
                Path(__file__).resolve().parent.parent
                / "storage" / "inbox"
            )

        self.inbox_path = Path(inbox_path)
        self.inbox_path.mkdir(parents=True, exist_ok=True)

        self.ingestion = DocumentIngestion(self.inbox_path)

    @staticmethod
    def _failure(message, source_id=None, details=None):
        return {
            "success": False,
            "error": str(message),
            "source_id": source_id,
            "document_id": None,
            "details": details,
        }

    @staticmethod
    def _sha256_file(path):
        digest = hashlib.sha256()

        with open(path, "rb") as handle:
            for chunk in iter(
                lambda: handle.read(1024 * 1024), b""
            ):
                digest.update(chunk)

        return digest.hexdigest()

    @staticmethod
    def _is_url(source):
        if not isinstance(source, str):
            return False

        return urlparse(source.strip()).scheme.lower() in {
            "http", "https"
        }

    @staticmethod
    def _normalize_url(url):
        parts = urlsplit(url.strip())

        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path or "/",
            parts.query,
            "",
        ))

    @staticmethod
    def _source_type(source):
        if ArchiveManager._is_url(source):
            return "url"

        suffix = Path(source).suffix.lower()

        if suffix == ".pdf":
            return "pdf"

        if suffix == ".docx":
            return "docx"

        if suffix in IMAGE_EXTENSIONS:
            return "image"

        return "other"

    @staticmethod
    def _source_name(source):
        if ArchiveManager._is_url(source):
            parsed = urlparse(source.strip())
            return parsed.netloc + (parsed.path or "/")

        return Path(source).name

    def import_source(
        self,
        source,
        category,
        title=None,
        subject=None,
        page_or_location=None,
        document_reference=None,
    ):
        """استخراج و ثبت یک فایل یا URL در بایگانی."""

        if category not in LEGAL_CATEGORIES:
            return self._failure("دسته حقوقی معتبر نیست.")

        if not isinstance(source, (str, Path)):
            return self._failure("مسیر فایل یا URL معتبر نیست.")

        source = str(source).strip()

        if not source:
            return self._failure("مسیر فایل یا URL وارد نشده است.")

        is_url = self._is_url(source)

        # اعتبارسنجی URL با نمونه ingestion انجام می‌شود.
        if is_url:
            validator = getattr(
                self.ingestion, "validate_url", None
            )

            if not callable(validator):
                validator = DocumentIngestion.validate_url

            validation = validator(source)

            if (
                not isinstance(validation, tuple)
                or len(validation) != 2
            ):
                return self._failure(
                    "خروجی اعتبارسنجی URL معتبر نیست."
                )

            valid, message = validation

            if not valid:
                return self._failure(message)

            source_url = self._normalize_url(source)
            source_path = None
            source_hash = None

        else:
            valid, message = self.ingestion.validate_file(source)

            if not valid:
                return self._failure(message)

            source_path = str(Path(source).resolve())
            source_url = None

            try:
                source_hash = self._sha256_file(source_path)
            except OSError as exc:
                return self._failure(
                    f"محاسبه شناسه فایل ناموفق بود: {exc}"
                )

        source_type = self._source_type(source)
        source_name = self._source_name(source)
        source_id = None

        try:
            # بررسی منبع تکراری
            if is_url:
                existing_source = self.db.find_source_by_url(
                    source_url
                )
            else:
                existing_source = self.db.find_source_by_sha256(
                    source_hash
                )

            if existing_source:
                source_id = existing_source["id"]

                existing_document = self.db.get_document_by_source(
                    source_id
                )

                if (
                    existing_document
                    and (
                        existing_document.get("extracted_text") or ""
                    ).strip()
                ):
                    return {
                        "success": True,
                        "duplicate": True,
                        "message": (
                            "این منبع قبلاً در بایگانی ثبت شده است؛ "
                            "رکورد تکراری ایجاد نشد."
                        ),
                        "source_id": source_id,
                        "document_id": existing_document["id"],
                        "source_type": existing_source.get(
                            "source_type", source_type
                        ),
                        "title": existing_document.get(
                            "title", title or source_name
                        ),
                        "character_count": len(
                            existing_document.get("extracted_text") or ""
                        ),
                        "text_quality": existing_document.get(
                            "text_quality", "unknown"
                        ),
                    }

                self.db.update_source_status(
                    source_id,
                    extraction_status="pending",
                )

            else:
                source_id = self.db.add_source(
                    source_type=source_type,
                    source_name=source_name,
                    source_path=source_path,
                    source_url=source_url,
                    sha256=source_hash,
                    extraction_status="pending",
                    review_status="not_reviewed",
                )

            # استخراج متن
            result = self.ingestion.process_source(
                source_url if is_url else source_path
            )

            if not isinstance(result, dict):
                error = "خروجی استخراج معتبر نیست."

                self.db.update_source_status(
                    source_id,
                    extraction_status="failed",
                    notes=error,
                )

                return self._failure(error, source_id, result)

            if not result.get("success"):
                error = result.get(
                    "error", "استخراج متن ناموفق بود."
                )

                self.db.update_source_status(
                    source_id,
                    extraction_status="failed",
                    notes=str(error),
                )

                return self._failure(error, source_id, result)

            extracted_text = result.get("text", "")

            if (
                not isinstance(extracted_text, str)
                or not extracted_text.strip()
            ):
                error = "متن قابل‌استفاده‌ای از منبع استخراج نشد."

                self.db.update_source_status(
                    source_id,
                    extraction_status="failed",
                    notes=error,
                )

                return self._failure(error, source_id, result)

            actual_url = (
                result.get("source_url") if is_url else None
            )

            if actual_url and actual_url != source_url:
                self.db.update_source_status(
                    source_id,
                    extraction_status="extracted",
                    notes="URL نهایی: " + actual_url,
                )
            else:
                self.db.update_source_status(
                    source_id,
                    extraction_status="extracted",
                )

            doc_title = (
                str(title).strip()
                if title is not None
                else source_name
            )

            doc_title = doc_title or source_name

            extraction_method = result.get("extraction_method")

            text_quality = (
                "extracted"
                if extraction_method
                else "needs_review"
            )

            doc_id = self.db.add_document(
                source_id=source_id,
                title=doc_title,
                category=category,
                subject=subject,
                extracted_text=extracted_text,
                text_quality=text_quality,
                page_or_location=page_or_location,
                document_reference=(
                    document_reference
                    or actual_url
                    or source_path
                ),
            )

            return {
                "success": True,
                "duplicate": False,
                "message": (
                    "متن استخراج و در بایگانی ذخیره شد. "
                    "بررسی دقت متن و محل استناد همچنان ضروری است."
                ),
                "source_id": source_id,
                "document_id": doc_id,
                "source_type": source_type,
                "title": doc_title,
                "character_count": len(extracted_text),
                "text_quality": text_quality,
                "details": result,
            }

        except Exception as exc:
            if source_id is not None:
                try:
                    self.db.update_source_status(
                        source_id,
                        extraction_status="failed",
                        notes=f"خطای بایگانی: {exc}",
                    )
                except Exception:
                    pass

            return self._failure(
                f"خطا در بایگانی منبع: {exc}",
                source_id,
            )

    def import_inbox(self, category, subject=None):
        results = []

        for path in self.ingestion.list_supported_files():
            results.append(
                self.import_source(
                    path,
                    category=category,
                    subject=subject,
                )
            )

        return {
            "total": len(results),
            "succeeded": sum(
                1 for item in results if item.get("success")
            ),
            "failed": sum(
                1 for item in results if not item.get("success")
            ),
            "results": results,
        }

    def get_status(self):
        return self.db.get_archive_status()
