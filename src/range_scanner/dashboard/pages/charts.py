"""
Charts Page — Visual gallery of exported chart PNGs.
Browse through your exported charts in a clean grid layout.
"""

import streamlit as st
from pathlib import Path


def render():
    st.title("Charts")
    st.markdown('<p class="subtitle">Visual gallery of exported candlestick charts with support/resistance zones.</p>', unsafe_allow_html=True)

    charts_dir = Path("charts")

    if not charts_dir.exists() or not list(charts_dir.glob("*.png")):
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: #F5F2EE; border-radius: 12px; margin: 20px 0;">
            <span style="font-size: 3rem;">◧</span>
            <h3 style="margin-top: 16px; border: none;">No charts exported yet</h3>
            <p style="color: #7A756E;">Run a scan with chart export to see them here:</p>
            <code style="background: #E8E4DF; padding: 8px 16px; border-radius: 6px; font-size: 0.85rem;">
                python -m range_scanner --universe nasdaq100 --charts --top 10
            </code>
        </div>
        """, unsafe_allow_html=True)
        return

    pngs = sorted(charts_dir.glob("*.png"))
    st.markdown(f"**{len(pngs)} charts** in `charts/` directory")

    # Filter
    filter_text = st.text_input("Filter by ticker or verdict", placeholder="Type to filter...", help="E.g. 'ADSK' or 'EXCELLENT'")

    if filter_text:
        pngs = [p for p in pngs if filter_text.upper() in p.stem.upper()]
        st.markdown(f"*Showing {len(pngs)} matching charts*")

    if not pngs:
        st.info("No charts match your filter.")
        return

    st.markdown("---")

    # Grid layout
    cols_per_row = st.radio("Grid", [1, 2], index=1, horizontal=True, label_visibility="collapsed")

    cols = st.columns(cols_per_row)
    for i, png in enumerate(pngs):
        with cols[i % cols_per_row]:
            # Parse filename for metadata
            parts = png.stem.split("_")
            rank = parts[0] if parts else ""
            ticker = parts[1] if len(parts) > 1 else ""

            st.image(str(png), use_container_width=True)
            st.markdown(f"<p style='text-align: center; color: #7A756E; font-size: 0.8rem; margin-top: -8px;'>#{rank} — {png.stem}</p>", unsafe_allow_html=True)
            st.markdown("")
