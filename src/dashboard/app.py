import os
import sys
sys.path.append(os.path.abspath('.'))

import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Financial Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Define Streamlit Pages
page_home = st.Page(os.path.join(BASE_DIR, "pages", "01_home.py"), title="Executive Overview", default=True)
page_profile = st.Page(os.path.join(BASE_DIR, "pages", "02_profile.py"), title="Company Profile")
page_screener = st.Page(os.path.join(BASE_DIR, "pages", "03_screener.py"), title="Financial Screener")
page_peers = st.Page(os.path.join(BASE_DIR, "pages", "04_peers.py"), title="Peer Benchmarking")
page_trends = st.Page(os.path.join(BASE_DIR, "pages", "05_trends.py"), title="Trend Analysis")
page_sectors = st.Page(os.path.join(BASE_DIR, "pages", "06_sectors.py"), title="Sector Analysis")
page_capital = st.Page(os.path.join(BASE_DIR, "pages", "07_capital.py"), title="Capital Allocation Map")
page_reports = st.Page(os.path.join(BASE_DIR, "pages", "08_reports.py"), title="Annual Reports Archive")

# Define Navigation Groups
nav_groups = {
    "Overview & Screening": [page_home, page_screener, page_trends, page_capital],
    "Deep Dive & Sector Analytics": [page_profile, page_peers, page_sectors, page_reports]
}

# Register Navigation & Run Active Page
pg = st.navigation(nav_groups)
pg.run()
