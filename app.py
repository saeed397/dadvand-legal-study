# -*- coding: utf-8 -*-
"""
Dadvand - Persian Legal Study App
Streamlit entry point
"""

from pathlib import Path
import streamlit as st

from core.database import LegalDatabase, LEGAL_CATEGORIES
from core.archive_manager import ArchiveManager


# --------------------------------------------------
# مسیرها و تنظیمات
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent
STORAGE_DIR = ROOT_DIR / "storage"
DOCUMENTS_DIR = STORAGE_DIR / "documents"

DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="دادوند | مطالعه و بایگانی حقوقی",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# پایگاه داده و مدیر بایگانی
# --------------------------------------------------

@st.cache_resource
def get_database():
    return LegalDatabase()


@st.cache_resource
def get_archive_manager():
    return ArchiveManager(
        db=get_database(),
        inbox_path=DOCUMENTS_DIR,
    )


db = get_database()
archive = get_archive_manager()


# --------------------------------------------------
# ظاهر برنامه
# --------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Vazirmatn', sans-serif;
        direction: rtl;
    }

    .stApp {
        background-color: var(--background-color);
    }

    h1, h2, h3, p, label, div {
        font-family: 'Vazirmatn', sans-serif;
    }

    .main-title {
        text-align: center;
        font-size: 34px;
        font-weight: 800;
        color: #2F6F68;
        margin-bottom: 4px;
    }

    .main-subtitle {
        text-align: center;
        font-size: 14px;
        color: #888888;
        margin-bottom: 25px;
    }

    .info-card {
        padding: 18px;
        border-radius: 14px;
        background: rgba(47, 111, 104, 0.08);
        border: 1px solid rgba(47, 111, 104, 0.20);
        text-align: center;
    }

    .info-number {
        font-size: 27px;
        font-weight: 800;
        color: #2F6F68;
    }

    .info-label {
        font-size: 13px;
        color: #888888;
    }

    div[data-testid="stSidebar"] {
        direction: rtl;
        text-align: right;
    }

    div[data-testid="stSidebar"] * {
        font-family: 'Vazirmatn', sans-serif;
    }

    .stButton button {
        border-radius: 10px;
        font-family: 'Vazirmatn', sans-serif;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# سربرگ
# --------------------------------------------------

st.markdown(
    '<div class="main-title">⚖️ دادوند</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-subtitle">'
    'سامانه مطالعه و بایگانی منابع حقوقی'
    '</div>',
    unsafe_allow_html=True,
)


# --------------------------------------------------
# منوی اصلی
# --------------------------------------------------

MENU_ITEMS = [
    "خانه",
    "بایگانی منابع",
    "جست‌وجوی حقوقی",
    "حقوق مدنی",
    "آیین دادرسی مدنی",
    "حقوق تجارت",
    "حقوق جزا",
    "آیین دادرسی کیفری",
    "حقوق اساسی",
    "فقه و اصول فقه",
    "حقوق ثبت",
    "سایر قوانین",
    "تنظیمات",
]

if "current_page" not in st.session_state:
    st.session_state.current_page = "خانه"


with st.sidebar:
    st.markdown("## ⚖️ دادوند")
    st.caption("سامانه مطالعه و بایگانی حقوقی")
    st.divider()

    selected_page = st.radio(
        "منوی اصلی",
        MENU_ITEMS,
        index=MENU_ITEMS.index(st.session_state.current_page),
    )

    st.session_state.current_page = selected_page

    st.divider()
    st.caption("نسخه اولیه وب")


# --------------------------------------------------
# صفحه خانه
# --------------------------------------------------

def show_home():

    st.subheader("صفحه اصلی")

    try:
        status = archive.get_status()
    except Exception as exc:
        st.error(f"خطا در دریافت وضعیت بایگانی: {exc}")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="info-card">
                <div class="info-number">{status.get("sources", 0)}</div>
                <div class="info-label">منابع ثبت‌شده</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="info-card">
                <div class="info-number">{status.get("documents", 0)}</div>
                <div class="info-label">اسناد استخراج‌شده</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="info-card">
                <div class="info-number">{status.get("legal_topics", 0)}</div>
                <div class="info-label">موضوعات حقوقی</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown("### دسته‌بندی‌های حقوقی")

    cols = st.columns(3)

    for index, category in enumerate(LEGAL_CATEGORIES):
        with cols[index % 3]:
            st.button(
                category,
                key=f"home_category_{index}",
                use_container_width=True,
                on_click=lambda value=category: (
                    st.session_state.update({"current_page": value})
                ),
            )


# --------------------------------------------------
# صفحه بایگانی منابع
# --------------------------------------------------

def show_archive():

    st.subheader("بایگانی منابع حقوقی")

    st.info(
        "منابع PDF، Word، تصاویر و URL را وارد کنید. "
        "متن استخراج‌شده در پایگاه داده ذخیره می‌شود."
    )

    category = st.selectbox(
        "دسته حقوقی",
        LEGAL_CATEGORIES,
    )

    title = st.text_input(
        "عنوان سند (اختیاری)",
    )

    subject = st.text_input(
        "موضوع سند (اختیاری)",
    )

    input_method = st.radio(
        "نوع ورود منبع",
        ["بارگذاری فایل", "نشانی اینترنتی URL"],
        horizontal=True,
    )

    if input_method == "بارگذاری فایل":

        uploaded_file = st.file_uploader(
            "انتخاب فایل",
            type=[
                "pdf",
                "docx",
                "png",
                "jpg",
                "jpeg",
                "tif",
                "tiff",
                "webp",
            ],
        )

        if st.button("ثبت و استخراج منبع", type="primary"):

            if uploaded_file is None:
                st.warning("ابتدا یک فایل انتخاب کنید.")
                return

            destination = DOCUMENTS_DIR / uploaded_file.name

            try:
                if destination.exists():
                    import hashlib

                    new_hash = hashlib.sha256(
                        uploaded_file.getvalue()
                    ).hexdigest()

                    old_hash = hashlib.sha256(
                        destination.read_bytes()
                    ).hexdigest()

                    if new_hash != old_hash:
                        destination = DOCUMENTS_DIR / (
                            f"{new_hash[:12]}_{uploaded_file.name}"
                        )

                if not destination.exists():
                    destination.write_bytes(uploaded_file.getvalue())

                with st.spinner("در حال استخراج و ذخیره متن..."):
                    result = archive.import_source(
                        str(destination),
                        category=category,
                        title=title or None,
                        subject=subject or None,
                    )

                if result.get("success"):
                    st.success(result.get("message", "منبع ثبت شد."))

                    if result.get("duplicate"):
                        st.info("این منبع قبلاً ثبت شده است.")

                    st.write(
                        f"شناسه سند: {result.get('document_id')}"
                    )
                    st.write(
                        f"تعداد نویسه‌ها: {result.get('character_count', 0)}"
                    )

                else:
                    st.error(result.get("error", "استخراج ناموفق بود."))

            except Exception as exc:
                st.error(f"خطا در ثبت فایل: {exc}")

    else:

        source_url = st.text_input(
            "نشانی کامل صفحه اینترنتی",
            placeholder="https://example.com/page",
        )

        if st.button("استخراج و ثبت URL", type="primary"):

            if not source_url.strip():
                st.warning("نشانی اینترنتی را وارد کنید.")
                return

            with st.spinner("در حال دریافت و استخراج صفحه..."):
                result = archive.import_source(
                    source_url.strip(),
                    category=category,
                    title=title or None,
                    subject=subject or None,
                )

            if result.get("success"):
                st.success(result.get("message", "منبع ثبت شد."))
                st.write(
                    f"شناسه سند: {result.get('document_id')}"
                )
                st.write(
                    f"تعداد نویسه‌ها: {result.get('character_count', 0)}"
                )
            else:
                st.error(result.get("error", "استخراج ناموفق بود."))


# --------------------------------------------------
# صفحه جست‌وجوی حقوقی
# --------------------------------------------------

def show_search():

    st.subheader("جست‌وجوی حقوقی")

    query = st.text_input(
        "عبارت یا پرسش حقوقی خود را وارد کنید",
        placeholder="مثلاً شرایط صحت معامله",
    )

    category = st.selectbox(
        "محدود کردن جست‌وجو به دسته",
        ["همه دسته‌ها"] + LEGAL_CATEGORIES,
    )

    if st.button("جست‌وجو", type="primary"):

        if not query.strip():
            st.warning("عبارت جست‌وجو را وارد کنید.")
            return

        selected_category = (
            None if category == "همه دسته‌ها" else category
        )

        with st.spinner("در حال جست‌وجو در بایگانی..."):
            results = db.search_documents(
                query=query.strip(),
                category=selected_category,
                limit=50,
            )

        if not results:
            st.warning("در بایگانی یافت نشد.")
            return

        st.success(f"{len(results)} نتیجه پیدا شد.")

        for item in results:

            with st.expander(
                item.get("title") or "سند بدون عنوان"
            ):

                st.caption(
                    f"دسته: {item.get('category', '-')}"
                )

                st.caption(
                    f"منبع: {item.get('source_name', '-')}"
                )

                st.caption(
                    f"محل سند: {item.get('page_or_location') or '-'}"
                )

                st.markdown("**متن استخراج‌شده از منبع:**")

                st.text(item.get("extracted_text", ""))

                st.warning(
                    "این متن استخراج‌شده است و تا زمان بررسی انسانی، "
                    "متن رسمی تأییدشده محسوب نمی‌شود."
                )


# --------------------------------------------------
# صفحه دسته‌بندی
# --------------------------------------------------

def show_category(category):

    st.subheader(category)

    results = db.search_documents(
        query="",
        category=category,
        limit=100,
    )

    if not results:
        st.info("هنوز سندی در این دسته ثبت نشده است.")
        return

    for item in results:

        with st.expander(item.get("title") or "سند بدون عنوان"):

            st.caption(
                f"منبع: {item.get('source_name', '-')}"
            )

            st.text(item.get("extracted_text", ""))


# --------------------------------------------------
# صفحه تنظیمات
# --------------------------------------------------

def show_settings():

    st.subheader("تنظیمات")

    st.info(
        "تنظیمات پیشرفته و انتخاب ظاهر برنامه "
        "در مرحله طراحی رابط کاربری تکمیل خواهد شد."
    )

    st.markdown("### وضعیت پایگاه داده")

    status = archive.get_status()

    st.json(status)

    st.caption(
        "مسیر پایگاه داده بر اساس تنظیمات ماژول LegalDatabase تعیین می‌شود."
    )


# --------------------------------------------------
# مسیریابی صفحات
# --------------------------------------------------

page = st.session_state.current_page

if page == "خانه":
    show_home()

elif page == "بایگانی منابع":
    show_archive()

elif page == "جست‌وجوی حقوقی":
    show_search()

elif page == "تنظیمات":
    show_settings()

elif page in LEGAL_CATEGORIES:
    show_category(page)

else:
    st.info("این بخش هنوز پیاده‌سازی نشده است.")