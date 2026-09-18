import hashlib
from datetime import datetime, timezone, timedelta

import feedparser
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf

from openai import OpenAI
from streamlit.components.v1 import html as component_html


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="Ticker Tape",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
# ============================================================

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.investing.com/rss/news.rss",
]


MARKETS = {
    "S&P 500": {
        "ticker": "^GSPC",
        "country": "United States",
        "country_code": "US",
        "region": "America",
        "keywords": [
            "america",
            "united states",
            "us",
            "wall street",
            "s&p",
            "nasdaq",
            "dow",
            "federal reserve",
            "fed",
        ],
    },
    "Nasdaq 100": {
        "ticker": "^NDX",
        "country": "United States",
        "country_code": "US",
        "region": "America",
        "keywords": [
            "nasdaq",
            "technology",
            "tech",
            "artificial intelligence",
            "nvidia",
            "microsoft",
            "apple",
        ],
    },
    "Russell 2000": {
        "ticker": "^RUT",
        "country": "United States",
        "country_code": "US",
        "region": "America",
        "keywords": [
            "russell",
            "small cap",
            "small-cap",
            "united states",
            "america",
            "fed",
        ],
    },
    "TSX Composite": {
        "ticker": "^GSPTSE",
        "country": "Canada",
        "country_code": "CA",
        "region": "North America",
        "keywords": [
            "canada",
            "canadian",
            "tsx",
            "bank of canada",
        ],
    },
    "Nikkei 225": {
        "ticker": "^N225",
        "country": "Japan",
        "country_code": "JP",
        "region": "Asia",
        "keywords": [
            "japan",
            "japanese",
            "nikkei",
            "tokyo",
            "bank of japan",
            "boj",
            "yen",
        ],
    },
    "Hang Seng": {
        "ticker": "^HSI",
        "country": "Hong Kong",
        "country_code": "HK",
        "region": "Asia",
        "keywords": [
            "hong kong",
            "hang seng",
            "china",
            "chinese",
            "beijing",
        ],
    },
    "Shanghai Composite": {
        "ticker": "000001.SS",
        "country": "China",
        "country_code": "CN",
        "region": "Asia",
        "keywords": [
            "china",
            "chinese",
            "shanghai",
            "beijing",
            "yuan",
        ],
    },
    "KOSPI": {
        "ticker": "^KS11",
        "country": "South Korea",
        "country_code": "KR",
        "region": "Asia",
        "keywords": [
            "south korea",
            "korea",
            "korean",
            "kospi",
            "seoul",
        ],
    },
    "Nifty 50": {
        "ticker": "^NSEI",
        "country": "India",
        "country_code": "IN",
        "region": "Asia",
        "keywords": [
            "india",
            "indian",
            "nifty",
            "mumbai",
            "sensex",
        ],
    },
    "FTSE 100": {
        "ticker": "^FTSE",
        "country": "United Kingdom",
        "country_code": "GB",
        "region": "Europe",
        "keywords": [
            "uk",
            "britain",
            "british",
            "london",
            "ftse",
            "bank of england",
            "sterling",
            "pound",
        ],
    },
    "DAX": {
        "ticker": "^GDAXI",
        "country": "Germany",
        "country_code": "DE",
        "region": "Europe",
        "keywords": [
            "germany",
            "german",
            "dax",
            "frankfurt",
            "europe",
            "ecb",
            "euro",
        ],
    },
    "CAC 40": {
        "ticker": "^FCHI",
        "country": "France",
        "country_code": "FR",
        "region": "Europe",
        "keywords": [
            "france",
            "french",
            "cac",
            "paris",
            "europe",
            "ecb",
            "euro",
        ],
    },
    "Euro Stoxx 50": {
        "ticker": "^STOXX50E",
        "country": "Eurozone",
        "country_code": "EU",
        "region": "Europe",
        "keywords": [
            "eurozone",
            "europe",
            "ecb",
            "euro",
        ],
    },
    "FTSE MIB": {
        "ticker": "FTSEMIB.MI",
        "country": "Italy",
        "country_code": "IT",
        "region": "Europe",
        "keywords": [
            "italy",
            "italian",
            "milan",
            "mib",
            "europe",
            "ecb",
            "euro",
        ],
    },
    "SMI": {
        "ticker": "^SSMI",
        "country": "Switzerland",
        "country_code": "CH",
        "region": "Europe",
        "keywords": [
            "switzerland",
            "swiss",
            "smi",
            "zurich",
            "franc",
        ],
    },
    "ASX 200": {
        "ticker": "^AXJO",
        "country": "Australia",
        "country_code": "AU",
        "region": "Asia-Pacific",
        "keywords": [
            "australia",
            "australian",
            "asx",
            "sydney",
            "rba",
        ],
    },
}


SECTORS = {
    "All sectors": [],
    "Technology": [
        "technology",
        "tech",
        "artificial intelligence",
        "ai",
        "semiconductor",
        "chip",
        "software",
        "microsoft",
        "apple",
        "nvidia",
    ],
    "Financials": [
        "bank",
        "banks",
        "financial",
        "finance",
        "credit",
        "insurance",
        "mortgage",
    ],
    "Energy": [
        "oil",
        "gas",
        "energy",
        "opec",
        "crude",
        "renewable",
        "solar",
        "wind",
    ],
    "Healthcare": [
        "health",
        "healthcare",
        "hospital",
        "pharmaceutical",
        "drug",
        "medicine",
        "biotech",
    ],
    "Consumer": [
        "retail",
        "consumer",
        "shopping",
        "supermarket",
        "sales",
        "automotive",
        "car",
    ],
    "Industrials": [
        "industrial",
        "manufacturing",
        "factory",
        "construction",
        "aerospace",
        "defence",
        "infrastructure",
    ],
    "Commodities": [
        "gold",
        "silver",
        "copper",
        "commodity",
        "metals",
        "agriculture",
        "wheat",
    ],
}


TIMEFRAMES = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "Year to Date": "ytd",
    "1 Year": "1y",
    "5 Years": "5y",
}


# ============================================================
# SESSION STATE
# ============================================================

if "selected_market" not in st.session_state:
    st.session_state.selected_market = "S&P 500"

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "news_summaries" not in st.session_state:
    st.session_state.news_summaries = {}


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("🐂 Ticker Tape")

    openai_key_value = st.session_state.get(
        "openai_key_dark",
        st.session_state.get("openai_key_light", ""),
    )

    if st.session_state.theme == "light":
        openai_key = st.text_input(
            "OpenAI API key",
            value=openai_key_value,
            type="password",
            key="openai_key_light",
            help="Used for MarketBot and AI news summaries.",
        )
    else:
        openai_key = st.text_input(
            "OpenAI API key",
            value=openai_key_value,
            type="password",
            key="openai_key_dark",
            help="Used for MarketBot and AI news summaries.",
        )

    if openai_key.strip():
        openai_key_colour = "#16a34a"
        openai_message = "OpenAI key entered"
    else:
        openai_key_colour = "#dc2626"
        openai_message = "OpenAI key required for AI features"

    st.markdown(
        f"""
        <style>
            div[data-testid="stTextInput"] input {{
                border: 1px solid #cbd5e1 !important;
                color: {openai_key_colour} !important;
                caret-color: {openai_key_colour} !important;
            }}

            div[data-testid="stTextInput"] input:focus {{
                border: 1px solid #64748b !important;
                box-shadow: 0 0 0 1px #64748b !important;
            }}
        </style>

        <p style="color:{openai_key_colour}; font-size:0.8rem;">
            {openai_message}
        </p>
        """,
        unsafe_allow_html=True,
    )

    trading_economics_key_value = st.session_state.get(
        "trading_economics_key_dark",
        st.session_state.get("trading_economics_key_light", ""),
    )

    if st.session_state.theme == "light":
        trading_economics_key = st.text_input(
            "Trading Economics API key",
            value=trading_economics_key_value,
            type="password",
            key="trading_economics_key_light",
            help=(
                "Used for upcoming economic-calendar releases. "
                "Get one from tradingeconomics.com."
            ),
        )
    else:
        trading_economics_key = st.text_input(
            "Trading Economics API key",
            value=trading_economics_key_value,
            type="password",
            key="trading_economics_key_dark",
            help=(
                "Used for upcoming economic-calendar releases. "
                "Get one from tradingeconomics.com."
            ),
        )

    if trading_economics_key.strip():
        trading_economics_key_colour = "#16a34a"
        trading_economics_message = "Trading Economics calendar connected"
    else:
        trading_economics_key_colour = "#dc2626"
        trading_economics_message = (
            "Enter a Trading Economics key to show upcoming events."
        )

    st.markdown(
        f"""
        <p style="color:{trading_economics_key_colour}; font-size:0.8rem;">
            {trading_economics_message}
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    selected_theme = st.radio(
        "Colour mode",
        ["Dark", "Light"],
        index=0 if st.session_state.theme == "dark" else 1,
    )

    if selected_theme.lower() != st.session_state.theme:
        st.session_state.theme = selected_theme.lower()
        st.rerun()

    st.divider()

    st.subheader("Choose a market")

    for market_name, details in MARKETS.items():
        selected = (
            market_name == st.session_state.selected_market
        )

        label = (
            f"● {market_name}"
            if selected
            else market_name
        )

        if st.button(
            label,
            key=f"market_button_{market_name}",
            use_container_width=True,
            help=(
                f"Country tracked: {details['country']} | "
                f"Region: {details['region']}"
            ),
        ):
            st.session_state.selected_market = market_name
            st.rerun()

    st.divider()

    timeframe_label = st.selectbox(
        "Chart timeframe",
        list(TIMEFRAMES.keys()),
        index=2,
    )

    timeframe = TIMEFRAMES[timeframe_label]


# ============================================================
# LIGHT AND DARK MODE
# ============================================================

if st.session_state.theme == "light":
    page_background = "#f4f8ff"
    sidebar_background = "#e5efff"
    card_background = "#ffffff"
    input_background = "#ffffff"
    text_colour = "#17345c"
    muted_colour = "#526985"
    border_colour = "#cbd5e1"
    chart_template = "plotly_white"
else:
    page_background = "#0e1726"
    sidebar_background = "#13233a"
    card_background = "#172943"
    input_background = "#1b304d"
    text_colour = "#f4f8ff"
    muted_colour = "#a9bad0"
    border_colour = "#475569"
    chart_template = "plotly_dark"


st.markdown(
    f"""
    <style>
        :root,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {{
            color-scheme: {"light" if st.session_state.theme == "light" else "dark"};
        }}

        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        [data-testid="stHeader"] {{
            background: {page_background} !important;
            color: {text_colour} !important;
        }}

        [data-testid="stSidebar"],
        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"],
        [data-testid="stSidebarContent"] > div {{
            background: {sidebar_background} !important;
        }}

        h1, h2, h3, h4, h5, h6,
        p, label, span,
        div, li, strong, b {{
            color: {text_colour} !important;
        }}

        [data-baseweb="popover"],
        [data-baseweb="menu"],
        [role="listbox"],
        [role="option"],
        [data-baseweb="popover"] ul,
        [data-baseweb="popover"] li {{
            background: {card_background} !important;
            color: {text_colour} !important;
        }}

        [role="option"]:hover,
        [role="option"][aria-selected="true"] {{
            background: {sidebar_background} !important;
            color: {text_colour} !important;
        }}

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] * {{
            color: {muted_colour} !important;
        }}

        [data-testid="stTextInput"] {{
            color: {text_colour} !important;
        }}

        [data-testid="stTextInput"] label,
        [data-testid="stTextInput"] label p,
        [data-testid="stTextInput"] small,
        [data-testid="stTextInput"] [data-testid="stMarkdownContainer"] {{
            color: {text_colour} !important;
        }}

        [data-testid="stChatInput"],
        [data-testid="stChatInputContainer"],
        [data-testid="stBottom"],
        [data-testid="stBottomBlockContainer"],
        [data-testid="stBottom"] > div,
        [data-testid="stBottomBlockContainer"] > div,
        section[data-testid="stChatInput"] {{
            background: transparent !important;
            border: 0 !important;
            border-radius: 0 !important;
            color: {text_colour} !important;
        }}

        [data-testid="stBottom"],
        [data-testid="stBottomBlockContainer"] {{
            box-shadow: none !important;
        }}

        [data-testid="stChatInput"] > div,
        [data-testid="stChatInput"] form,
        [data-testid="stChatInput"] textarea,
        [data-testid="stBottom"] form,
        [data-testid="stBottomBlockContainer"] form {{
            background: transparent !important;
            color: {text_colour} !important;
            border: 0 !important;
        }}

        [data-testid="stVerticalScrollContainer"] {{
            background: {card_background} !important;
            color: {text_colour} !important;
            scrollbar-color: {border_colour} {card_background};
            scrollbar-width: thin;
        }}

        [data-testid="stVerticalScrollContainer"] > div,
        [data-testid="stVerticalScrollContainer"] [data-testid="stVerticalBlock"] {{
            background: transparent !important;
        }}

        [data-testid="stVerticalScrollContainer"]::-webkit-scrollbar {{
            width: 0.6rem;
        }}

        [data-testid="stVerticalScrollContainer"]::-webkit-scrollbar-track {{
            background: {card_background};
        }}

        [data-testid="stVerticalScrollContainer"]::-webkit-scrollbar-thumb {{
            background: {border_colour};
            border-radius: 0.5rem;
        }}

        [data-testid="stChatInput"] textarea::placeholder {{
            color: {muted_colour} !important;
            -webkit-text-fill-color: {muted_colour} !important;
        }}

        [data-testid="stTooltipIcon"],
        [data-testid="stTooltipIcon"] svg,
        button[aria-label*="Show"],
        button[aria-label*="Hide"],
        button[aria-label*="password"],
        button[aria-label*="API"] {{
            color: {text_colour} !important;
            fill: {text_colour} !important;
            stroke: {text_colour} !important;
        }}

        [data-testid="stPopover"],
        [data-testid="stPopover"] > div,
        [data-baseweb="tooltip"] {{
            background: {card_background} !important;
            color: {text_colour} !important;
            border-color: {border_colour} !important;
        }}

        [data-testid="stPopover"] p,
        [data-testid="stPopover"] span,
        [data-baseweb="tooltip"] p,
        [data-baseweb="tooltip"] span {{
            color: {text_colour} !important;
        }}

        [data-testid="stExpander"],
        [data-testid="stExpanderDetails"],
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: {card_background} !important;
            border: 1px solid {border_colour} !important;
            border-radius: 10px !important;
        }}

        div[data-baseweb="select"] > div {{
            background-color: {input_background} !important;
            border-color: {border_colour} !important;
            color: {text_colour} !important;
        }}

        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div,
        div[data-baseweb="select"] input {{
            color: {text_colour} !important;
            -webkit-text-fill-color: {text_colour} !important;
        }}

        input,
        textarea,
        [data-testid="stTextInput"] > div,
        [data-testid="stTextInput"] input,
        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInput"] > div,
        [data-testid="stChatInputContainer"],
        [data-baseweb="base-input"],
        input[type="password"],
        input[type="text"],
        [data-testid="stBaseButton-secondary"],
        [data-testid^="stBaseButton-"] {{
            background: {input_background} !important;
            color: {text_colour} !important;
            border-color: {border_colour} !important;
        }}

        input[type="password"],
        input[type="text"],
        textarea,
        [data-testid="stChatInput"] textarea,
        [data-baseweb="base-input"] input {{
            color: {text_colour} !important;
            -webkit-text-fill-color: {text_colour} !important;
            caret-color: {text_colour} !important;
        }}

        input::placeholder,
        textarea::placeholder,
        [data-testid="stChatInput"] textarea::placeholder {{
            color: {muted_colour} !important;
            -webkit-text-fill-color: {muted_colour} !important;
            opacity: 1 !important;
        }}

        div.stButton > button {{
            background-color: {card_background} !important;
            color: {text_colour} !important;
            border-color: {border_colour} !important;
        }}

        div.stButton > button span,
        div.stButton > button p,
        [data-testid="stTextInput"] button,
        [data-testid="stTextInput"] button svg,
        [data-testid="stChatInput"] button,
        [data-testid="stChatInput"] button svg {{
            color: {text_colour} !important;
            fill: {text_colour} !important;
            stroke: {text_colour} !important;
        }}

        [data-testid="stTextInput"] button,
        [data-testid="stChatInput"] button {{
            background: {input_background} !important;
            border: 1px solid {border_colour} !important;
            color: {text_colour} !important;
        }}

        [data-testid="stTextInput"] button[aria-label="Show password"],
        [data-testid="stTextInput"] button[aria-label="Hide password"],
        [data-testid="stTextInput"] button[title="Show password"],
        [data-testid="stTextInput"] button[title="Hide password"] {{
            min-width: 2.5rem !important;
            min-height: 2.5rem !important;
            padding: 0.4rem !important;
            background: {input_background} !important;
            border: 1px solid {border_colour} !important;
            border-left: 0 !important;
            border-radius: 0 0.375rem 0.375rem 0 !important;
            color: {text_colour} !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            line-height: 1 !important;
        }}

        [data-testid="stTextInput"] button[aria-label="Show password"]:hover,
        [data-testid="stTextInput"] button[aria-label="Hide password"]:hover,
        [data-testid="stTextInput"] button[title="Show password"]:hover,
        [data-testid="stTextInput"] button[title="Hide password"]:hover {{
            background: {sidebar_background} !important;
            color: {text_colour} !important;
        }}

        [data-testid="stTextInput"] button[aria-label="Show password"] svg,
        [data-testid="stTextInput"] button[aria-label="Hide password"] svg,
        [data-testid="stTextInput"] button[title="Show password"] svg,
        [data-testid="stTextInput"] button[title="Hide password"] svg {{
            width: 1.15rem !important;
            height: 1.15rem !important;
            color: {text_colour} !important;
            fill: none !important;
            stroke: {text_colour} !important;
        }}

        [data-testid="stTextInput"] button[aria-label="Show password"]:focus,
        [data-testid="stTextInput"] button[aria-label="Hide password"]:focus,
        [data-testid="stTextInput"] button[title="Show password"]:focus,
        [data-testid="stTextInput"] button[title="Hide password"]:focus {{
            outline: 2px solid #64748b !important;
            outline-offset: 1px !important;
        }}

        div.stButton > button:hover {{
            background-color: #dbeafe !important;
            color: #17345c !important;
            border-color: #64748b !important;
        }}

        [data-testid="stMetric"] {{
            background-color: {card_background} !important;
            border: 1px solid {border_colour} !important;
            border-radius: 10px !important;
            padding: 12px !important;
        }}

        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"] {{
            color: {text_colour} !important;
        }}

        [data-testid="stChatMessage"] {{
            background-color: {card_background} !important;
            border: 1px solid {border_colour} !important;
            border-radius: 10px !important;
        }}

        [data-testid="stAlert"],
        .stInfo,
        .stWarning,
        .stSuccess,
        .stError {{
            background-color: {card_background} !important;
            border: 1px solid {border_colour} !important;
            color: {text_colour} !important;
        }}

        [data-testid="stAlert"] > div,
        .stInfo > div,
        .stWarning > div,
        .stSuccess > div,
        .stError > div {{
            color: {text_colour} !important;
        }}

        a {{
            color: #2563eb !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# NEWS FUNCTIONS
# ============================================================

@st.cache_data(ttl=900)
def fetch_news():
    news = []
    seen_titles = set()

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            source = feed.feed.get("title", feed_url)

            for entry in feed.entries[:50]:
                title = entry.get("title", "").strip()

                if not title:
                    continue

                if title.lower() in seen_titles:
                    continue

                seen_titles.add(title.lower())

                news.append(
                    {
                        "title": title,
                        "summary": entry.get("summary", ""),
                        "link": entry.get("link", "#"),
                        "source": source,
                        "published": entry.get(
                            "published",
                            entry.get("updated", ""),
                        ),
                    }
                )

        except Exception as error:
            print(f"News feed error: {error}")

    return news


def filter_news(news, keywords):
    if not keywords:
        return news

    matches = []

    for item in news:
        text = (
            item.get("title", "")
            + " "
            + item.get("summary", "")
        ).lower()

        if any(
            keyword.lower() in text
            for keyword in keywords
        ):
            matches.append(item)

    return matches


def summarise_news_item(item, api_key):
    if not api_key:
        return (
            "Enter your OpenAI API key in the sidebar "
            "to create an AI summary."
        )

    title = item.get("title", "")

    if title in st.session_state.news_summaries:
        return st.session_state.news_summaries[title]

    try:
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise financial news analyst."
                    ),
                },
                {
                    "role": "user",
                    "content": f"""
Summarise this financial news story in two concise sentences.
Explain why it may matter to markets.
Do not provide investment advice.

Headline:
{title}

Description:
{item.get("summary", "")}
""",
                },
            ],
        )

        summary = response.choices[0].message.content

        st.session_state.news_summaries[title] = summary

        return summary

    except Exception as error:
        return f"Could not create summary: {error}"


def show_news(
    news,
    api_key,
    height=430,
    section_name="news",
):
    if not news:
        st.info("No relevant news was found.")
        return

    with st.container(
        height=height,
        border=True,
    ):
        for item in news:
            title = item.get("title", "Untitled")
            link = item.get("link", "#")

            unique_id = hashlib.md5(
                (
                    section_name
                    + title
                    + link
                ).encode("utf-8")
            ).hexdigest()

            st.markdown(
                f"**[{title}]({link})**"
            )

            st.caption(
                f"{item.get('source', 'Unknown source')} · "
                f"{item.get('published', '')}"
            )

            with st.expander("AI summary"):
                if st.button(
                    "Generate summary",
                    key=f"summary_{section_name}_{unique_id}",
                ):
                    with st.spinner(
                        "Creating AI summary..."
                    ):
                        summarise_news_item(
                            item,
                            api_key,
                        )

                saved_summary = (
                    st.session_state.news_summaries.get(
                        title
                    )
                )

                if saved_summary:
                    st.write(saved_summary)
                else:
                    st.caption(
                        "Click the button to generate a summary."
                    )

            st.divider()


# ============================================================
# MARKET DATA
# ============================================================

@st.cache_data(ttl=900)
def fetch_market_data(ticker, timeframe):
    try:
        data = yf.Ticker(ticker).history(
            period=timeframe,
            interval="1d",
            auto_adjust=False,
        )

        if data.empty:
            return pd.DataFrame()

        data = data.reset_index()

        if "Date" not in data.columns:
            if "Datetime" in data.columns:
                data = data.rename(
                    columns={"Datetime": "Date"}
                )
            else:
                return pd.DataFrame()

        data["Date"] = pd.to_datetime(data["Date"])

        return data

    except Exception as error:
        st.warning(f"Market data error: {error}")
        return pd.DataFrame()


def calculate_returns(data):
    if data.empty or "Close" not in data.columns:
        return {}

    prices = data["Close"].dropna()

    if prices.empty:
        return {}

    latest = float(prices.iloc[-1])

    daily = (
        (prices.iloc[-1] / prices.iloc[-2]) - 1
    ) * 100 if len(prices) > 1 else 0.0

    period_return = (
        (prices.iloc[-1] / prices.iloc[0]) - 1
    ) * 100

    return {
        "latest": latest,
        "daily": daily,
        "period": period_return,
    }


def create_chart(data, market_name):
    """
    Creates a clean line chart.

    There are no permanent dots.
    Hovering shows a tracking point on the line.
    """

    if data.empty or "Close" not in data.columns:
        return None

    if st.session_state.theme == "dark":
        hover_background = "#17345c"
        hover_text = "#ffffff"
    else:
        hover_background = "#dbeafe"
        hover_text = "#172554"

    chart = go.Figure()

    chart.add_trace(
        go.Scatter(
            x=data["Date"],
            y=data["Close"],
            mode="lines",
            name=market_name,
            line={
                "color": "#2563eb",
                "width": 2.8,
            },
            hovertemplate=(
                "<b>%{x|%d %b %Y}</b><br>"
                "Index level: %{y:,.2f}"
                "<extra></extra>"
            ),
            hoverlabel={
                "bgcolor": hover_background,
                "font": {
                    "color": hover_text,
                    "size": 13,
                },
                "bordercolor": "#2563eb",
            },
        )
    )

    chart.update_layout(
        template=chart_template,
        height=460,
        margin={
            "l": 10,
            "r": 10,
            "t": 20,
            "b": 10,
        },
        hovermode="closest",
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={
            "showgrid": False,
            "showspikes": False,
        },
        yaxis={
            "showgrid": True,
            "showspikes": False,
            "gridcolor": (
                "rgba(37,99,235,0.16)"
                if st.session_state.theme == "light"
                else "rgba(150,150,150,0.20)"
            ),
        },
    )

    return chart


# ============================================================
# TRADING ECONOMICS CALENDAR
# ============================================================

@st.cache_data(ttl=1800)
def fetch_economic_calendar(api_key):
    """
    Fetch upcoming economic-calendar events from Trading Economics.

    The cache lasts 30 minutes so the API is not repeatedly called.
    """

    if not api_key:
        return {
            "events": [],
            "status": "No Trading Economics API key entered.",
        }

    today = datetime.now(timezone.utc).date()
    end_date = today + timedelta(days=45)

    url = (
        "https://api.tradingeconomics.com/calendar/country/All/"
        f"{today.isoformat()}/{end_date.isoformat()}"
    )

    try:
        response = requests.get(
            url,
            params={
                "c": api_key.strip(),
                "f": "json",
            },
            timeout=20,
        )

        if response.status_code != 200:
            return {
                "events": [],
                "status": (
                    f"Trading Economics returned HTTP "
                    f"{response.status_code}: "
                    f"{response.text[:300]}"
                ),
            }

        payload = response.json()

        if isinstance(payload, list):
            raw_events = payload
        else:
            raw_events = []

        if not raw_events:
            return {
                "events": [],
                "status": (
                    "Trading Economics connected successfully, but no events "
                    "were returned for the selected date range."
                ),
            }

        events = []

        for item in raw_events:
            event_name = str(
                item.get("Event", "")
            ).strip()

            country = str(
                item.get("Country", "")
            ).strip().upper()

            event_time = str(
                item.get("Date", "")
            ).strip()

            if event_time and " " in event_time:
                date_part, _ = event_time.split(" ", 1)
            else:
                date_part = event_time

            timing = date_part or "Date not provided"

            if event_time:
                timing = event_time

            impact = str(
                item.get("Importance", "")
            ).strip()

            estimate = item.get(
                "Forecast",
                "",
            )

            previous = item.get(
                "Previous",
                "",
            )

            actual = item.get(
                "Actual",
                "",
            )

            if not event_name:
                continue

            events.append(
                {
                    "event": event_name,
                    "country": country,
                    "date": timing,
                    "impact": impact,
                    "estimate": estimate,
                    "previous": previous,
                    "actual": actual,
                }
            )

        return {
            "events": events,
            "status": (
                f"Trading Economics connected. Received "
                f"{len(events)} economic events."
            ),
        }

    except requests.exceptions.Timeout:
        return {
            "events": [],
            "status": (
                "Trading Economics request timed out. "
                "Please try again."
            ),
        }

    except Exception as error:
        return {
            "events": [],
            "status": f"Calendar error: {error}",
        }


def get_market_events(market_name, api_key):
    market = MARKETS[market_name]

    all_events = fetch_economic_calendar(api_key)
    calendar_events = all_events.get("events", []) if isinstance(all_events, dict) else all_events

    if not calendar_events:
        return []

    selected_country = market["country_code"]

    matching_events = [
        event
        for event in calendar_events
        if str(event.get("country", "")).upper() == selected_country.upper()
    ]

    high_impact_events = [
        event
        for event in matching_events
        if str(event.get("impact", "")).lower()
        in ["high", "red", "3"]
    ]

    if high_impact_events:
        return high_impact_events[:12]

    return matching_events[:12]


# ============================================================
# MARKETBOT
# ============================================================

def ask_marketbot(
    question,
    market_name,
    market_data,
    related_news,
    openai_key,
    economic_events,
):
    if not openai_key:
        return (
            "Please enter your OpenAI API key in the sidebar "
            "before using MarketBot."
        )

    try:
        client = OpenAI(
            api_key=openai_key
        )

        returns = calculate_returns(market_data)

        news_text = "\n".join(
            f"- {item['title']}"
            for item in related_news[:15]
        )

        event_text = "\n".join(
            f"- {event['event']} on {event['date']}"
            for event in economic_events
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": """
You are MarketBot, a concise financial markets assistant.

Explain market movements, financial terms, upcoming events and news.
Use only the supplied information.
Do not give personalised investment advice.
Do not make certain predictions about future prices.
""",
                },
                {
                    "role": "user",
                    "content": f"""
Selected market: {market_name}

Latest index level:
{returns.get("latest", "N/A")}

Daily return:
{returns.get("daily", 0):.2f}%

Selected-period return:
{returns.get("period", 0):.2f}%

Recent news:
{news_text}

Upcoming economic events:
{event_text}

Question:
{question}
""",
                },
            ],
        )

        return response.choices[0].message.content

    except Exception as error:
        return f"MarketBot error: {error}"


def show_robot():
    robot = """
    <style>
        body {
            margin: 0;
            background: transparent;
            font-family: Arial, sans-serif;
        }

        .wrapper {
            display: flex;
            align-items: center;
            gap: 18px;
            color: white;
        }

        .robot {
            position: relative;
            width: 100px;
            height: 115px;
        }

        .head {
            position: absolute;
            top: 10px;
            left: 10px;
            width: 80px;
            height: 58px;
            background: #273449;
            border: 3px solid #60a5fa;
            border-radius: 12px;
        }

        .screen {
            position: absolute;
            top: 10px;
            left: 8px;
            right: 8px;
            height: 28px;
            overflow: hidden;
            background: #07111f;
            border: 1px solid #22c55e;
            border-radius: 5px;
            color: #22c55e;
            font-family: monospace;
            font-size: 8px;
            line-height: 28px;
            text-align: center;
            white-space: nowrap;
        }

        .eye {
            position: absolute;
            top: 45px;
            width: 8px;
            height: 8px;
            background: white;
            border-radius: 50%;
        }

        .left-eye {
            left: 25px;
        }

        .right-eye {
            right: 25px;
        }

        .antenna {
            position: absolute;
            top: -8px;
            left: 48px;
            width: 3px;
            height: 12px;
            background: #60a5fa;
        }

        .light {
            position: absolute;
            top: -17px;
            left: 44px;
            width: 11px;
            height: 11px;
            background: #22c55e;
            border-radius: 50%;
        }

        .body {
            position: absolute;
            top: 75px;
            left: 25px;
            width: 50px;
            height: 35px;
            background: #273449;
            border: 3px solid #60a5fa;
            border-radius: 8px;
        }

        .button {
            position: absolute;
            top: 10px;
            left: 20px;
            width: 8px;
            height: 8px;
            background: #ef4444;
            border-radius: 50%;
        }

        h3 {
            margin: 0 0 5px 0;
        }

        p {
            margin: 0;
            color: #9ca3af;
            font-size: 14px;
        }
    </style>

    <div class="wrapper">
        <div class="robot">
            <div class="antenna"></div>
            <div class="light"></div>

            <div class="head">
                <div class="screen">
                    SPX +0.6% · N225 -0.3%
                </div>

                <div class="eye left-eye"></div>
                <div class="eye right-eye"></div>
            </div>

            <div class="body">
                <div class="button"></div>
            </div>
        </div>

        <div>
            <h3>MarketBot</h3>
            <p>Ask about markets, news or events.</p>
        </div>
    </div>
    """

    component_html(
        robot,
        height=160,
        scrolling=False,
    )


# ============================================================
# LOAD SELECTED MARKET
# ============================================================

selected_market = st.session_state.selected_market
market_details = MARKETS[selected_market]

all_news = fetch_news()

market_news = filter_news(
    all_news,
    market_details["keywords"],
)

if not market_news:
    market_news = all_news

market_data = fetch_market_data(
    market_details["ticker"],
    timeframe,
)

returns = calculate_returns(
    market_data
)

economic_events = get_market_events(
    selected_market,
    trading_economics_key,
)


# ============================================================
# HEADER
# ============================================================

st.title("🐂 Ticker Tape")
st.subheader(selected_market)

st.caption(
    f"Country: {market_details['country']} · "
    f"Region: {market_details['region']} · "
    f"{timeframe_label} · "
    f"Updated {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}"
)


# ============================================================
# METRICS
# ============================================================

latest = returns.get("latest")
daily = returns.get("daily")
period_return = returns.get("period")

one, two, three, four = st.columns(4)

with one:
    st.metric(
        "Latest level",
        f"{latest:,.2f}"
        if latest is not None
        else "N/A",
    )

with two:
    st.metric(
        "Daily change",
        f"{daily:+.2f}%"
        if daily is not None
        else "N/A",
        delta=(
            f"{daily:+.2f}%"
            if daily is not None
            else None
        ),
    )

with three:
    st.metric(
        f"{timeframe_label} return",
        f"{period_return:+.2f}%"
        if period_return is not None
        else "N/A",
        delta=(
            f"{period_return:+.2f}%"
            if period_return is not None
            else None
        ),
    )

with four:
    st.metric(
        "Related news",
        len(market_news),
    )


# ============================================================
# INDEX INFORMATION
# ============================================================

with st.expander("See more information about this index"):
    st.write(f"**Index:** {selected_market}")
    st.write(f"**Country tracked:** {market_details['country']}")
    st.write(f"**Region:** {market_details['region']}")
    st.write(f"**Yahoo Finance ticker:** {market_details['ticker']}")

    st.write(
        f"This graph shows the closing level of the index "
        f"over the {timeframe_label.lower()} period."
    )


st.divider()


# ============================================================
# CHART AND NEWS
# ============================================================

chart_column, news_column = st.columns(
    [1.6, 1],
    gap="large",
)

with chart_column:
    st.subheader(
        f"{selected_market} chart"
    )

    chart = create_chart(
        market_data,
        selected_market,
    )

    if chart is not None:
        st.plotly_chart(
            chart,
            use_container_width=True,
        )
    else:
        st.warning(
            "No market data was available."
        )

with news_column:
    st.subheader(
        f"{selected_market} news"
    )

    show_news(
        market_news,
        openai_key,
        height=430,
        section_name="market",
    )


# ============================================================
# SECTOR NEWS
# ============================================================

st.divider()

st.subheader("Sector news")

sector_name = st.selectbox(
    "Choose a sector",
    list(SECTORS.keys()),
)

if sector_name == "All sectors":
    sector_news = all_news
else:
    sector_news = filter_news(
        all_news,
        SECTORS[sector_name],
    )

show_news(
    sector_news,
    openai_key,
    height=430,
    section_name="sector",
)


# ============================================================
# MARKETBOT
# ============================================================

st.divider()

st.subheader("MarketBot")

show_robot()

for message in st.session_state.chat_messages:
    with st.chat_message(
        message["role"]
    ):
        st.markdown(
            message["content"]
        )

question = st.chat_input(
    f"Ask MarketBot about {selected_market}..."
)

if question:
    st.session_state.chat_messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner(
            "MarketBot is thinking..."
        ):
            answer = ask_marketbot(
                question=question,
                market_name=selected_market,
                market_data=market_data,
                related_news=market_news,
                openai_key=openai_key,
                economic_events=economic_events,
            )

        st.markdown(answer)

    st.session_state.chat_messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )


# ============================================================
# UPCOMING ECONOMIC EVENTS
# ============================================================

st.divider()

st.subheader(
    f"Upcoming events affecting {selected_market}"
)

if not trading_economics_key:
    st.warning(
        "Enter your Trading Economics API key in the sidebar "
        "to load the economic calendar."
    )
elif economic_events:
    for event in economic_events:
        extra_details = []

        if event["impact"]:
            extra_details.append(
                f"Impact: {event['impact']}"
            )

        if event["estimate"] not in ["", "None", "null"]:
            extra_details.append(
                f"Estimate: {event['estimate']}"
            )

        if event["previous"] not in ["", "None", "null"]:
            extra_details.append(
                f"Previous: {event['previous']}"
            )

        if event["actual"] not in ["", "None", "null"]:
            extra_details.append(
                f"Actual: {event['actual']}"
            )

        details_text = " · ".join(
            extra_details
        )

        st.info(
            f"**{event['event']}**\n\n"
            f"Expected timing: {event['date']}\n\n"
            f"Country: {event['country']}\n\n"
            f"{details_text}"
        )
else:
    st.info(
        "No upcoming events were returned for this market "
        "within the next 45 days."
    )

st.caption(
    "Economic-calendar data is supplied by Trading Economics. "
    "Check official release calendars before relying on event timings."
)