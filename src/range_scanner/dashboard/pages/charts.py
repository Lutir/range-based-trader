"""
Charts Page — Visual gallery of exported chart PNGs.
"""

import streamlit as st
from pathlib import Path


def render():
    st.title("Charts")
    st.markdown("Visual gallery of exported chart images.")

    charts_dir = Path("charts")
    if not charts_dir.exists():
        st.info("No charts found. Run a scan with `--charts` flag or use the Scanner page first.")
        return

    pngs = sorted(charts_dir.glob("*.png"))
    if not pngs:
        st.info("No chart images found in charts/ directory.")
        return

    st.markdown(f"**{len(pngs)} charts available**")

    # Display in 2-column grid
    cols = st.columns(2)
    for i, png in enumerate(pngs):
        with cols[i % 2]:
            st.image(str(png), caption=png.stem, use_container_width=True)
