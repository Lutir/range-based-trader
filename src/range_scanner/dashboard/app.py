"""
Range Scanner Dashboard — Streamlit UI

Run with:
    streamlit run src/range_scanner/dashboard/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Range Scanner",
    page_icon="◐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Japandi design system — warm, minimal, readable
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Base */
    .stApp {
        background-color: #FAF8F5;
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar */
    div[data-testid="stSidebar"] {
        background-color: #F0EDE8;
        border-right: 1px solid #E8E4DF;
    }
    div[data-testid="stSidebar"] .stRadio label {
        font-size: 0.95rem;
        padding: 8px 12px;
        border-radius: 6px;
        transition: background 0.2s;
    }
    div[data-testid="stSidebar"] .stRadio label:hover {
        background-color: #E8E4DF;
    }

    /* Typography */
    h1 {
        color: #2D2A26;
        font-weight: 700;
        font-size: 1.8rem !important;
        letter-spacing: -0.02em;
        margin-bottom: 0.2em !important;
    }
    h2 {
        color: #2D2A26;
        font-weight: 600;
        font-size: 1.3rem !important;
        letter-spacing: -0.01em;
        border-bottom: 1px solid #E8E4DF;
        padding-bottom: 8px;
        margin-top: 2rem !important;
    }
    h3 {
        color: #4A4540;
        font-weight: 500;
        font-size: 1.05rem !important;
    }
    p, li, label, .stMarkdown {
        color: #4A4540;
        line-height: 1.6;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #F5F2EE;
        border: 1px solid #E8E4DF;
        border-radius: 10px;
        padding: 16px 20px;
    }
    div[data-testid="stMetric"] label {
        color: #7A756E !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 500;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #2D2A26 !important;
        font-weight: 600;
        font-size: 1.4rem !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #5B8A72;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 500;
        font-size: 0.9rem;
        letter-spacing: 0.01em;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #4A7360;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(91, 138, 114, 0.2);
    }
    .stButton > button[kind="primary"] {
        background-color: #5B8A72;
    }

    /* DataFrames */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #E8E4DF;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        border-radius: 8px;
        border-color: #E8E4DF;
        font-family: 'Inter', sans-serif;
    }

    /* Info/Warning boxes */
    .stAlert {
        border-radius: 10px;
        border: none;
    }
    div[data-testid="stAlert"][data-baseweb="notification"] {
        background-color: #F5F2EE;
        border-left: 3px solid #5B8A72;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 8px 16px;
    }

    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 500;
        color: #4A4540;
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #5B8A72;
    }

    /* Hide hamburger and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom classes */
    .subtitle {
        color: #7A756E;
        font-size: 0.95rem;
        margin-top: -8px;
        margin-bottom: 24px;
    }
    .verdict-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        letter-spacing: 0.02em;
    }
    .badge-excellent { background: #D4EDDA; color: #2D5F3B; }
    .badge-watchlist { background: #FFF3CD; color: #664D03; }
    .badge-pressing { background: #D1ECF1; color: #0C5460; }
    .badge-broken { background: #F8D7DA; color: #721C24; }
    .badge-trending { background: #E2E3E5; color: #383D41; }

    .score-pill {
        display: inline-block;
        width: 36px;
        height: 36px;
        line-height: 36px;
        text-align: center;
        border-radius: 50%;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .score-high { background: #D4EDDA; color: #2D5F3B; }
    .score-mid { background: #FFF3CD; color: #664D03; }
    .score-low { background: #F8D7DA; color: #721C24; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <span style="font-size: 2.5rem;">◐</span>
        <h1 style="font-size: 1.4rem !important; margin: 8px 0 4px 0; border: none; padding: 0;">Range Scanner</h1>
        <p style="color: #7A756E; font-size: 0.8rem; margin: 0;">Market Structure Filter</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["◉ Scanner", "◎ Ticker Detail", "◧ Charts", "◫ Backtest", "◈ Settings"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.markdown("""
    <div style="padding: 12px; background: #E8E4DF; border-radius: 8px; font-size: 0.75rem; color: #7A756E;">
        <strong style="color: #4A4540;">Quick Guide</strong><br><br>
        <strong>Scanner</strong> — Scan universes for range candidates<br>
        <strong>Detail</strong> — Deep-dive any single ticker<br>
        <strong>Charts</strong> — Visual gallery of exported charts<br>
        <strong>Backtest</strong> — Test if ranges actually held<br>
        <strong>Settings</strong> — API keys and thresholds
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("""
    <div style="font-size: 0.7rem; color: #B8B2A8; text-align: center; padding-top: 20px;">
        Not financial advice.<br>Structure filter only.
    </div>
    """, unsafe_allow_html=True)

# Route to pages
page_key = page.split(" ", 1)[1] if " " in page else page

if page_key == "Scanner":
    from range_scanner.dashboard.pages.scanner import render
    render()
elif page_key == "Ticker Detail":
    from range_scanner.dashboard.pages.detail import render
    render()
elif page_key == "Charts":
    from range_scanner.dashboard.pages.charts import render
    render()
elif page_key == "Backtest":
    from range_scanner.dashboard.pages.backtest import render
    render()
elif page_key == "Settings":
    from range_scanner.dashboard.pages.settings import render
    render()
