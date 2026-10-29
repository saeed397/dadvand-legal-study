
import streamlit as st

from core.archive_manager import ArchiveManager
from core.legal_answer import LegalAnswer
from core.legal_search import LegalSearch
from core.topic_extractor import TopicExtractor


SECTION_TITLES = {
    "dashboard": "خانه",
    "civil_law": "حقوق مدنی",
    "civil_procedure": "آیین دادرسی مدنی",
    "commercial_law": "حقوق تجارت",
    "criminal_law": "حقوق جزا",
    "criminal_procedure": "آیین دادرسی کیفری",
    "legal_opinions": "نظریات مشورتی",
    "precedents": "آرای وحدت رویه",
    "court_decisions": "آرای قضایی",
    "archive": "بایگانی منابع",
    "settings": "تنظیمات",
}


def render_dashboard():
    st.title("دادوند")
    st.caption("سامانه مطالعه و بایگانی منابع حقوقی")

    st.info(
        "مطالب حقوقی باید بر اساس منابع ثبت‌شده در بایگانی "
        "بررسی شوند. اگر مطلبی پیدا نشود، برنامه آن را "
        "به‌عنوان مطلب تأییدنشده نمایش نمی‌دهد."
    )

    query = st.text_input(
        "عبارت یا پرسش حقوقی",
        placeholder="عبارت موردنظر را وارد کنید",
        key="dashboard_search",
    )

    if st.button("جست‌وجو", key="dashboard_search_button"):
        result = LegalSearch().search(query)

        if not result["found"]:
            st.warning(result["message"])
            return

        for item in result["results"]:
            with st.expander(item["title"]):
                st.write(item["content"])
                st.caption(
                    f"منبع: {item['source_name']}"
                )

                if item["page_number"] is not None:
                    st.caption(
                        f"صفحه: {item['page_number']}"
                    )

                if item["source_url"]:
                    st.markdown(
                        f"[مشاهده منبع اینترنتی]"
                        f"({item['source_url']})"
                    )


def render_archive():
    st.title("بایگانی منابع")

    st.write(
        "فایل‌ها و نشانی‌های اینترنتی را برای استخراج متن "
        "و ذخیره در بایگانی ثبت کنید."
    )

    uploaded_file = st.file_uploader(
        "انتخاب فایل",
        type=[
            "pdf", "docx", "png", "jpg",
            "jpeg", "tif", "tiff", "bmp"
        ],
        key="archive_upload",
    )

    category = st.selectbox(
        "دسته‌بندی",
        options=[
            "بدون دسته‌بندی",
            "حقوق مدنی",
            "آیین دادرسی مدنی",
            "حقوق تجارت",
            "حقوق جزا",
            "آیین دادرسی کیفری",
            "نظریات مشورتی",
            "آرای وحدت رویه",
            "آرای قضایی",
        ],
        key="archive_category",
    )

    if st.button("ثبت فایل در بایگانی"):
        if uploaded_file is None:
            st.warning("ابتدا یک فایل انتخاب کنید.")
        else:
            try:
                import tempfile
                from pathlib import Path

                suffix = Path(uploaded_file.name).suffix

                with tempfile.NamedTemporaryFile(
                    suffix=suffix,
                    delete=False,
                ) as temp_file:
                    temp_file.write(uploaded_file.getvalue())
                    temp_path = temp_file.name

                try:
                    manager = ArchiveManager()
                    result = manager.import_file(
                        temp_path,
                        category=(
                            None
                            if category == "بدون دسته‌بندی"
                            else category
                        ),
                    )
                finally:
                    Path(temp_path).unlink(missing_ok=True)

                if result["status"] == "duplicate":
                    st.info(result["message"])
                else:
                    st.success(result["message"])

            except Exception as exc:
                st.error(f"ثبت فایل انجام نشد: {exc}")

    st.divider()
    st.subheader("ثبت صفحه اینترنتی")

    url = st.text_input(
        "نشانی کامل صفحه",
        placeholder="https://example.com/page",
        key="archive_url",
    )

    if st.button("ثبت نشانی اینترنتی"):
        if not url.strip():
            st.warning("نشانی اینترنتی را وارد کنید.")
        else:
            try:
                manager = ArchiveManager()
                result = manager.import_url(url)

                if result["status"] == "duplicate":
                    st.info(result["message"])
                else:
                    st.success(result["message"])

            except Exception as exc:
                st.error(f"ثبت صفحه انجام نشد: {exc}")


def render_legal_section(page_key):
    title = SECTION_TITLES.get(
        page_key,
        "بخش حقوقی",
    )

    st.title(title)

    st.caption(
        "نتایج این بخش از متن منابع ثبت‌شده در بایگانی "
        "بازیابی می‌شوند."
    )

    query = st.text_input(
        "موضوع یا عبارت موردنظر",
        key=f"search_{page_key}",
    )

    if st.button(
        "جست‌وجو در این بخش",
        key=f"button_{page_key}",
    ):
        results = LegalSearch().search_topics(query)

        results = [
            item
            for item in results
            if item["category"] == title
        ]

        if not results:
            st.warning("در بایگانی یافت نشد.")
            return

        for item in results:
            with st.expander(item["topic_title"]):
                st.write(item["topic_content"])
                st.caption(
                    f"سند منبع: {item['source_name']}"
                )


def render_settings():
    st.title("تنظیمات")

    st.write(
        "ظاهر برنامه و وضعیت بایگانی در این بخش "
        "مدیریت خواهند شد."
    )

    st.info(
        "انتخاب حالت روشن و تیره در فایل theme.py تعریف شده است "
        "و در فایل اصلی برنامه فعال خواهد شد."
    )

    if st.button("استخراج موضوعات از اسناد بایگانی"):
        try:
            results = TopicExtractor().extract_all_documents()

            total = sum(
                item["topics_saved"]
                for item in results
            )

            st.success(
                f"عملیات پایان یافت؛ {total} موضوع ثبت شد."
            )

        except Exception as exc:
            st.error(f"استخراج موضوعات انجام نشد: {exc}")


def render_page(page_key):
    if page_key == "dashboard":
        render_dashboard()

    elif page_key == "archive":
        render_archive()

    elif page_key == "settings":
        render_settings()

    else:
        render_legal_section(page_key)
