
import streamlit as st

from core import database
import ui.navigation as navigation
from ui.pages import render_page
from ui.theme import apply_theme, render_theme_selector
from core.topic_extractor import TopicExtractor


st.set_page_config(
    page_title="دادوند | مطالعه حقوق",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# حذف تنظیمات از منوی کناری
navigation.LEGAL_SECTIONS = [
    (key, label)
    for key, label in navigation.LEGAL_SECTIONS
    if key != "settings"
]


def render_home_settings():
    with st.expander("تنظیمات صفحه اصلی", expanded=False):

        st.subheader("تنظیمات ظاهر")

        render_theme_selector()

        st.divider()

        st.subheader("مدیریت بایگانی")

        if st.button(
            "استخراج موضوعات از اسناد بایگانی",
            key="home_extract_topics",
            use_container_width=True,
        ):
            try:
                with st.spinner("در حال استخراج موضوعات..."):
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


def main():

    database.initialize_database()

    apply_theme()

    # سربرگ و منوی کناری
    with st.sidebar:
        st.markdown(
            """
            <div style="
                text-align:center;
                padding:12px 0 18px;
            ">
                <div style="font-size:42px;">⚖️</div>
                <div style="font-size:25px;font-weight:700;">
                    دادوند
                </div>
                <div style="font-size:12px;opacity:0.75;">
                    بایگانی و مطالعه حقوقی
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

    page_key = navigation.render_navigation()

    # تنظیمات عمومی نمایش
    st.markdown(
        """
        <style>

        .block-container {
            width: 100% !important;
            max-width: 100% !important;
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            padding-left: clamp(1rem, 4vw, 3rem) !important;
            padding-right: clamp(1rem, 4vw, 3rem) !important;
        }

        [data-testid="stSidebar"] {
            min-width: 0 !important;
            width: 18rem !important;
        }

        .stApp {
            overflow-x: hidden;
        }

        h1, h2, h3 {
            font-weight: 700;
        }

        [data-testid="stExpander"] {
            border-radius: 12px;
        }

        @media (max-width: 768px) {

            .block-container {
                width: 100% !important;
                max-width: 100% !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-top: 1rem !important;
            }

            [data-testid="stSidebar"] {
                min-width: 0 !important;
                width: min(85vw, 18rem) !important;
            }

            h1 {
                font-size: 1.7rem !important;
            }

            h2 {
                font-size: 1.4rem !important;
            }

            p, label {
                overflow-wrap: anywhere;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # نمایش صفحه انتخاب‌شده
    render_page(page_key)

    # تنظیمات فقط در صفحه اصلی
    if page_key == "dashboard":
        st.divider()
        render_home_settings()

    st.divider()

    st.caption(
        "دادوند | پاسخ‌ها باید بر اساس منابع ثبت‌شده در بایگانی باشند."
    )


if __name__ == "__main__":
    main()
