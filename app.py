
import streamlit as st

from core import database
from ui.navigation import render_navigation
from ui.pages import render_page
from ui.theme import apply_theme, render_theme_selector


st.set_page_config(
    page_title="دادوند | مطالعه حقوق",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    database.initialize_database()

    apply_theme()

    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center; padding:12px 0 18px;">
                <div style="font-size:42px;">⚖️</div>
                <div style="font-size:25px; font-weight:700;">
                    دادوند
                </div>
                <div style="font-size:12px; opacity:0.75;">
                    بایگانی و مطالعه حقوقی
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_theme_selector()

        st.divider()

    page_key = render_navigation()

    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1100px;
        }

        [data-testid="stSidebar"] {
            min-width: 240px;
        }

        h1, h2, h3 {
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    render_page(page_key)

    st.divider()

    st.caption(
        "دادوند | پاسخ‌ها باید بر اساس منابع ثبت‌شده در بایگانی باشند."
    )


if __name__ == "__main__":
    main()
