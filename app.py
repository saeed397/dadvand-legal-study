# -*- coding: utf-8 -*-
"""
Dadvand - Persian Legal Study App
Streamlit entry point

اصل بنیادین:
جست‌وجو و نمایش محتوا فقط بر اساس اسناد ثبت‌شده در بایگانی انجام می‌شود.
هیچ محتوای حقوقی از دانش داخلی برنامه تولید یا تکمیل نمی‌شود.
"""

from pathlib import Path
import re
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
# جست‌وجوی سراسری در تمام دسته‌ها و انواع رکورد
# --------------------------------------------------

def search_all_archive(query, limit=100):
    """جست‌وجوی همه واژه‌های پرسش در اسناد و موضوعات تمام دسته‌ها."""
    query = (query or "").strip()
    if not query:
        return []

    terms = list(dict.fromkeys(
        token for token in re.findall(r"[\w\u0600-\u06FF]+", query)
        if len(token) > 1
    ))
    if not terms:
        terms = [query]

    documents = {}
    topics = {}

    for term in terms:
        # category عمداً None است؛ جست‌وجو به هیچ دسته‌ای محدود نمی‌شود.
        for item in db.search_documents(term, category=None, limit=500):
            item_id = int(item["id"])
            documents[item_id] = item

        for item in db.search_topics(term, category=None, limit=500):
            item_id = int(item["id"])
            topics[item_id] = item

    results = []

    for item in documents.values():
        text_to_score = " ".join([
            item.get("title") or "",
            item.get("subject") or "",
            item.get("extracted_text") or "",
        ]).casefold()
        score = sum(text_to_score.count(term.casefold()) for term in terms)
        if score:
            results.append({
                "kind": "document",
                "id": int(item["id"]),
                "score": score,
                "data": item,
            })

    for item in topics.values():
        full = db.get_topic(int(item["id"]))
        if not full:
            continue

        text_to_score = " ".join([
            full.get("title") or "",
            full.get("subject") or "",
            full.get("official_text") or "",
            full.get("plain_explanation") or "",
            full.get("hypothetical_court_example") or "",
            full.get("mcq_items_json") or "",
        ]).casefold()
        score = sum(text_to_score.count(term.casefold()) for term in terms)
        if score:
            results.append({
                "kind": "topic",
                "id": int(item["id"]),
                "score": score + 2,
                "data": full,
            })

    results.sort(
        key=lambda result: (
            result["score"],
            result["data"].get("id", 0),
        ),
        reverse=True,
    )
    return results[:max(1, min(int(limit), 500))]


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
    '<div class="main-subtitle">سامانه مطالعه و بایگانی منابع حقوقی</div>',
    unsafe_allow_html=True,
)


# --------------------------------------------------
# منوی اصلی؛ تنظیمات از منوی کناری حذف شده است
# --------------------------------------------------

MENU_ITEMS = [
    "خانه",
    "بایگانی منابع",
    "جست‌وجوی حقوقی",
    *LEGAL_CATEGORIES,
]

if "current_page" not in st.session_state:
    st.session_state.current_page = "خانه"

if st.session_state.current_page not in MENU_ITEMS:
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
    st.caption("نسخه وب دادوند")


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

    # تنظیمات در صفحه اصلی قرار دارد، نه در منوی کناری.
    with st.expander("تنظیمات و وضعیت پایگاه داده"):
        st.markdown("### وضعیت پایگاه داده")
        try:
            st.json(db.get_archive_status())
            st.caption(
                "مسیر پایگاه داده بر اساس تنظیمات ماژول LegalDatabase تعیین می‌شود."
            )
        except Exception as exc:
            st.error(f"خطا در خواندن وضعیت پایگاه داده: {exc}")


# --------------------------------------------------
# صفحه بایگانی منابع
# --------------------------------------------------

def show_archive():
    st.subheader("بایگانی منابع حقوقی")

    st.info(
        "منابع PDF، Word، تصاویر و URL را وارد کنید. "
        "متن استخراج‌شده در پایگاه داده ذخیره می‌شود."
    )

    category = st.selectbox("دسته حقوقی", LEGAL_CATEGORIES)
    title = st.text_input("عنوان سند (اختیاری)")
    subject = st.text_input("موضوع سند (اختیاری)")

    input_method = st.radio(
        "نوع ورود منبع",
        ["بارگذاری فایل", "نشانی اینترنتی URL"],
        horizontal=True,
    )

    if input_method == "بارگذاری فایل":
        uploaded_file = st.file_uploader(
            "انتخاب فایل",
            type=[
                "pdf", "docx", "png", "jpg", "jpeg",
                "tif", "tiff", "webp", "bmp",
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
                    st.write(f"شناسه سند: {result.get('document_id')}")
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
                st.write(f"شناسه سند: {result.get('document_id')}")
                st.write(
                    f"تعداد نویسه‌ها: {result.get('character_count', 0)}"
                )
            else:
                st.error(result.get("error", "استخراج ناموفق بود."))


# --------------------------------------------------
# صفحه جست‌وجوی حقوقی؛ جست‌وجوی خودکار در کل بایگانی
# --------------------------------------------------

def show_search():
    st.subheader("جست‌وجوی حقوقی")

    st.caption(
        "هر جست‌وجو به‌صورت خودکار در تمام دسته‌های حقوقی، "
        "اسناد استخراج‌شده و موضوعات ثبت‌شده انجام می‌شود."
    )

    query = st.text_input(
        "عبارت یا پرسش حقوقی خود را وارد کنید",
        placeholder="مثلاً شرایط صحت معامله",
    )

    if st.button("جست‌وجو در تمام بایگانی", type="primary"):
        if not query.strip():
            st.warning("عبارت جست‌وجو را وارد کنید.")
            return

        with st.spinner("در حال جست‌وجو در تمام دسته‌های بایگانی..."):
            try:
                results = search_all_archive(query.strip(), limit=100)
            except Exception as exc:
                st.error(f"خطا در جست‌وجوی بایگانی: {exc}")
                return

        if not results:
            st.warning(
                "این عبارت در اسناد و موضوعات ثبت‌شده بایگانی یافت نشد."
            )
            return

        st.success(f"{len(results)} نتیجه مرتبط در تمام دسته‌ها پیدا شد.")

        for result in results:
            item = result["data"]
            category = item.get("category") or "دسته نامشخص"

            if result["kind"] == "document":
                title = item.get("title") or "سند بدون عنوان"
                with st.expander(f"{category} | {title}"):
                    st.caption(f"منبع: {item.get('source_name', '-')}")
                    st.caption(
                        f"محل سند: {item.get('page_or_location') or '-'}"
                    )
                    st.markdown("**متن استخراج‌شده از منبع:**")
                    st.text(item.get("extracted_text", ""))
                    st.warning(
                        "این متن استخراج‌شده است و تا زمان بررسی انسانی، "
                        "متن رسمی تأییدشده محسوب نمی‌شود."
                    )

            else:
                title = item.get("title") or "موضوع حقوقی بدون عنوان"
                with st.expander(f"{category} | {title}"):
                    st.caption(
                        f"منبع: {item.get('source_name') or 'منبع مشخص نشده'}"
                    )
                    st.caption(
                        f"محل استناد: "
                        f"{item.get('source_location') or item.get('document_page_or_location') or '-'}"
                    )

                    official_text = item.get("official_text") or ""
                    explanation = item.get("plain_explanation") or ""
                    example = item.get("hypothetical_court_example") or ""

                    if official_text:
                        st.markdown("**متن ثبت‌شده:**")
                        st.text(official_text)

                    if explanation:
                        st.markdown("**توضیح ثبت‌شده در بایگانی:**")
                        st.text(explanation)

                    if example:
                        st.markdown("**مثال ثبت‌شده در بایگانی:**")
                        st.text(example)

                    if not any([official_text, explanation, example]):
                        st.info(
                            "برای این موضوع متن تکمیلی در بایگانی ثبت نشده است."
                        )

                    st.warning(
                        "نمایش این اطلاعات به معنی تأیید رسمی یا صحت حقوقی "
                        "آن‌ها نیست؛ متن باید با منبع اصلی تطبیق داده شود."
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

    # جست‌وجوی خالی در database عمداً نتیجه‌ای ندارد؛
    # برای نمایش اسناد یک دسته از روش فهرست‌سازی استفاده می‌شود.
    if not results:
        try:
            with db._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT d.*, s.source_name, s.source_type, s.source_url
                    FROM documents d
                    JOIN sources s ON s.id = d.source_id
                    WHERE d.category = ?
                    ORDER BY d.id DESC
                    LIMIT 100
                    """,
                    (category,),
                ).fetchall()
            results = [dict(row) for row in rows]
        except Exception as exc:
            st.error(f"خطا در دریافت اسناد این دسته: {exc}")
            return

    if not results:
        st.info("هنوز سندی در این دسته ثبت نشده است.")
        return

    for item in results:
        with st.expander(item.get("title") or "سند بدون عنوان"):
            st.caption(f"منبع: {item.get('source_name', '-')}")
            st.text(item.get("extracted_text", ""))


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
elif page in LEGAL_CATEGORIES:
    show_category(page)
else:
    st.session_state.current_page = "خانه"
    show_home()
