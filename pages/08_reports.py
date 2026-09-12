import sys
import os
sys.path.append(os.path.abspath('.'))

# pages/08_reports.py

import streamlit as st
from src.dashboard.utils.db import get_companies

st.title("📁 Annual Reports Archive")

df_companies = get_companies()
company_list = (df_companies['ticker'] + " - " + df_companies['company_name']).tolist()
selected_option = st.selectbox("Search Company for Annual Reports", options=[""] + company_list)

if not selected_option:
    st.info("Select a company to view annual report BSE links.")
else:
    ticker = selected_option.split(" - ")[0]
    st.markdown(f"### Available Reports for `{ticker}`")

    years = list(range(2024, 2018, -1))
    for yr in years:
        col_yr, col_link = st.columns([1, 3])
        col_yr.write(f"**FY {yr} Annual Report**")
        
        # Simulate availability check (e.g. 2019 returns unavailable badge)
        if yr == 2019:
            col_link.error("🔴 Report unavailable")
        else:
            pdf_url = f"https://www.bseindia.com/bseplus/AnnualReport/{ticker}_{yr}.pdf"
            col_link.markdown(f"[📄 Download BSE Annual Report FY{yr}]({pdf_url})")
