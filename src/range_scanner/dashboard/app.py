"""
Range Scanner Dashboard — Streamlit UI
Run with: streamlit run src/range_scanner/dashboard/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Range Scanner",
    page_icon="◐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Design System CSS — implements DESIGN_RULES.md
# Rule 1: Inter + JetBrains Mono only
# Rule 2: Modular type scale (0.7 → 1.8rem)
# Rule 3: Tight tracking on headings, loose on caps
# Rule 6: Warm neutrals, never cold grays
# Rule 7: One accent (#5B8A72)
# Rule 11: Whitespace as active design
# Rule 13: 4/8px spacing grid
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* === BASE === */
    .stApp {
        background-color: #FAF8F5;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* === SIDEBAR (Rule 35: max 5 nav items) === */
    div[data-testid="stSidebar"] {
        background-color: #F0EDE8;
        border-right: 1px solid #E8E4DF;
    }
    div[data-testid="stSidebar"] .stRadio > div {
        gap: 4px;
    }
    div[data-testid="stSidebar"] .stRadio label {
        font-size: 0.95rem;
        padding: 10px 16px;
        border-radius: 8px;
        transition: background 0.15s ease;
        color: #4A4540;
    }
    div[data-testid="stSidebar"] .stRadio label:hover {
        background-color: #E8E4DF;
    }
    div[data-testid="stSidebar"] .stRadio label[data-checked="true"] {
        background-color: #E8E4DF;
        font-weight: 500;
    }

    /* === TYPOGRAPHY (Rules 1-5) === */
    h1 {
        font-family: 'Inter', sans-serif;
        color: #2D2A26;
        font-weight: 700;
        font-size: 1.8rem !important;
        letter-spacing: -0.02em;
        line-height: 1.2;
        margin-bottom: 0.25em !important;
    }
    h2 {
        font-family: 'Inter', sans-serif;
        color: #2D2A26;
        font-weight: 600;
        font-size: 1.3rem !important;
        letter-spacing: -0.01em;
        line-height: 1.25;
        border-bottom: 1px solid #E8E4DF;
        padding-bottom: 8px;
        margin-top: 2rem !important;
    }
    h3 {
        font-family: 'Inter', sans-serif;
        color: #4A4540;
        font-weight: 500;
        font-size: 1.05rem !important;
        line-height: 1.3;
    }
    p, li, label, .stMarkdown {
        color: #4A4540;
        line-height: 1.6;
        font-size: 0.95rem;
    }

    /* === METRIC CARDS (Rules 3, 13, 15) === */
    div[data-testid="stMetric"] {
        background-color: #F5F2EE;
        border: 1px solid #E8E4DF;
        border-radius: 10px;
        padding: 16px 20px;
    }
    div[data-testid="stMetric"] label {
        font-family: 'Inter', sans-serif;
        color: #7A756E !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 500;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        color: #2D2A26 !important;
        font-weight: 500;
        font-size: 1.4rem !important;
    }

    /* === BUTTONS (Rule 7: sage accent only) === */
    .stButton > button {
        background-color: #5B8A72;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 0.9rem;
        letter-spacing: 0.01em;
        transition: all 0.15s ease;
    }
    .stButton > button:hover {
        background-color: #4A7360;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(91, 138, 114, 0.15);
    }

    /* === DATA TABLES (Rule 15, 49: right-align numbers, expert density) === */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #E8E4DF;
    }
    .stDataFrame td, .stDataFrame th {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
    }

    /* === INPUTS (Rule 11: breathing room) === */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        border-radius: 8px;
        border-color: #E8E4DF;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #5B8A72;
        box-shadow: 0 0 0 2px rgba(91, 138, 114, 0.1);
    }

    /* === ALERTS (Rule 22: progressive disclosure) === */
    div[data-testid="stAlert"] {
        border-radius: 10px;
        border: none;
        border-left: 3px solid #5B8A72;
        background-color: #F5F2EE;
    }

    /* === EXPANDERS (Rule 24) === */
    .streamlit-expanderHeader {
        font-weight: 500;
        font-size: 0.95rem;
        color: #4A4540;
    }

    /* === PROGRESS (Rule 44: batch feedback) === */
    .stProgress > div > div > div {
        background-color: #5B8A72;
        border-radius: 4px;
    }

    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid #E8E4DF;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 8px 16px;
        font-size: 0.9rem;
    }

    /* === UTILITY CLASSES === */
    .subtitle {
        color: #7A756E;
        font-size: 0.9rem;
        margin-top: -4px;
        margin-bottom: 24px;
        line-height: 1.5;
    }
    .mono {
        font-family: 'JetBrains Mono', monospace;
    }
    .narrative-block {
        background: #F5F2EE;
        border-left: 3px solid #5B8A72;
        padding: 20px 24px;
        border-radius: 0 10px 10px 0;
        line-height: 1.75;
        color: #2D2A26;
        font-size: 0.9rem;
        margin: 16px 0;
    }
    .disclaimer {
        color: #B8B2A8;
        font-size: 0.75rem;
        text-align: center;
        padding-top: 20px;
    }

    /* Rule 36: Hide non-essential chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# === SIDEBAR ===
with st.sidebar:
    # Logo area
    st.markdown("""
    <div style="text-align: center; padding: 24px 0 16px 0;">
        <span style="font-size: 2.2rem;">◐</span>
        <h1 style="font-size: 1.3rem !important; margin: 8px 0 4px 0; border: none; padding: 0; letter-spacing: -0.02em;">Range Scanner</h1>
        <p style="color: #7A756E; font-size: 0.8rem; margin: 0; letter-spacing: 0.02em;">MARKET STRUCTURE FILTER</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Rule 35: max 5 navigation items
    page = st.radio(
        "Navigate",
        ["Scanner", "Ticker Detail", "Charts", "Backtest", "Settings"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Quick help (Rule 42: inline help over external docs)
    st.markdown("""
    <div style="padding: 12px 16px; background: #E8E4DF; border-radius: 8px; font-size: 0.8rem; color: #7A756E; line-height: 1.6;">
        <strong style="color: #4A4540;">Quick Guide</strong><br><br>
        <strong>Scanner</strong> — Scan a universe for range candidates<br>
        <strong>Detail</strong> — Deep-dive any ticker<br>
        <strong>Charts</strong> — Exported chart gallery<br>
        <strong>Backtest</strong> — Test if ranges held<br>
        <strong>Settings</strong> — API keys &amp; thresholds
    </div>
    """, unsafe_allow_html=True)

    # Rule 50: Disclaimer as design element
    st.markdown('<p class="disclaimer">Not financial advice.<br>Structure filter only.</p>', unsafe_allow_html=True)

# === PAGE ROUTING ===
if page == "Scanner":
    from range_scanner.dashboard.pages.scanner import render
    render()
elif page == "Ticker Detail":
    from range_scanner.dashboard.pages.detail import render
    render()
elif page == "Charts":
    from range_scanner.dashboard.pages.charts import render
    render()
elif page == "Backtest":
    from range_scanner.dashboard.pages.backtest import render
    render()
elif page == "Settings":
    from range_scanner.dashboard.pages.settings import render
    render()
