
import streamlit as st


THEMES = {
    "روشن": {
        "background": "#F7F4ED",
        "surface": "#FFFFFF",
        "primary": "#B89B5E",
        "text": "#202B35",
        "muted": "#697581",
        "border": "#E5DED0",
    },
    "تیره": {
        "background": "#171B22",
        "surface": "#222832",
        "primary": "#D2B574",
        "text": "#F1F0EC",
        "muted": "#B5BDC7",
        "border": "#3B424D",
    },
}


def initialize_theme():
    if "dadvand_theme" not in st.session_state:
        st.session_state["dadvand_theme"] = "روشن"


def get_theme():
    initialize_theme()
    return THEMES[st.session_state["dadvand_theme"]]


def render_theme_selector():
    initialize_theme()

    selected = st.radio(
        "حالت نمایش",
        options=["روشن", "تیره"],
        horizontal=True,
        key="dadvand_theme",
    )

    return THEMES[selected]


def apply_theme():
    theme = get_theme()

    st.markdown(
        f"""
        <style>
        :root {{
            color-scheme: light;
        }}

        .stApp {{
            background-color: {theme["background"]};
            color: {theme["text"]};
        }}

        [data-testid="stHeader"] {{
            background-color: {theme["background"]};
        }}

        [data-testid="stSidebar"] {{
            background-color: {theme["surface"]};
        }}

        .stApp, .stApp p, .stApp label,
        .stApp h1, .stApp h2, .stApp h3 {{
            color: {theme["text"]};
        }}

        .stButton > button {{
            border: 1px solid {theme["primary"]};
            border-radius: 10px;
            color: {theme["text"]};
        }}

        .stTextInput input,
        .stTextArea textarea {{
            border-radius: 8px;
        }}

        .dadvand-card {{
            background: {theme["surface"]};
            border: 1px solid {theme["border"]};
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 12px;
        }}

        .dadvand-muted {{
            color: {theme["muted"]};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
