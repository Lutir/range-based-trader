"""
Range Scanner Dashboard — Streamlit UI

Run with:
    streamlit run src/range_scanner/dashboard/app.py

This replaces the CLI for everyday use. Everything you can do on the
command line, you can do here with clicks instead of typing commands.

PAGES:
1. Scanner — Run scans on any universe, see ranked results
2. Ticker Detail — Deep dive into a single ticker's analysis
3. Charts — Visual chart gallery of top candidates
4. Backtest — Run structure persistence tests
5. Settings — Configure thresholds and API keys
"""

import streamlit as st

st.set_page_config(
    page_title="Range Scanner",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Japandi aesthetic
st.markdown("""
<style>
    .stApp {
        background-color: #FAF8F5;
    }
    .stMetric {
        background-color: #F5F2EE;
        padding: 12px;
        border-radius: 8px;
    }
    h1, h2, h3 {
        color: #2D2A26;
    }
    .stDataFrame {
        border-radius: 8px;
    }
    div[data-testid="stSidebar"] {
        background-color: #F0EDE8;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Range Scanner")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    ["Scanner", "Ticker Detail", "Charts", "Backtest", "Settings"],
    index=0,
)

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
