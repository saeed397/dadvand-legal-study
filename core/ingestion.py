
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from core.extractors import TextExtractor


class IngestionManager:
    """دریافت متن از فایل‌ها و صفحات وب."""

    def __init__(self):
        self.extractor = TextExtractor()

    def extract_file(self, file_path):
        return self.extractor.extract(file_path)

    def extract_url(self, url):
        url = (url or "").strip()

        if not url:
            raise ValueError("نشانی اینترنتی وارد نشده است.")

        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                "نشانی باید با http:// یا https:// شروع شود."
            )

        if not parsed.hostname:
            raise ValueError("نشانی اینترنتی معتبر نیست.")

        # جلوگیری از دسترسی به نشانی‌های محلی و خصوصی
        host = parsed.hostname.lower()

        blocked_hosts = {
            "localhost",
            "127.0.0.1",
            "::1",
            "0.0.0.0",
        }

        if host in blocked_hosts or host.endswith(".local"):
            raise ValueError(
                "دسترسی به نشانی‌های محلی مجاز نیست."
            )

        try:
            response = requests.get(
                url,
                timeout=20,
                headers={
                    "User-Agent": "DadvandLegalArchive/1.0"
                },
                allow_redirects=False,
            )
            response.raise_for_status()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"دریافت صفحه اینترنتی ناموفق بود: {exc}"
            ) from exc

        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        if "text/html" not in content_type:
            raise ValueError(
                "این نشانی صفحه HTML نیست؛ "
                "برای فایل PDF یا Word از بخش بارگذاری فایل استفاده کنید."
            )

        soup = BeautifulSoup(
            response.content,
            "html.parser"
        )

        for element in soup([
            "script",
            "style",
            "noscript",
            "nav",
            "footer",
            "header",
        ]):
            element.decompose()

        title = ""

        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        main_content = soup.find("main") or soup.find("article")

        if main_content:
            text = main_content.get_text(
                separator="\n",
                strip=True,
            )
        else:
            text = soup.get_text(
                separator="\n",
                strip=True,
            )

        if not text:
            raise ValueError(
                "متنی از صفحه اینترنتی استخراج نشد."
            )

        if title:
            return f"عنوان صفحه: {title}\n\n{text}"

        return text
