import sys
import os
sys.path.append(os.path.abspath('.'))

# pages/02_profile.py

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from src.dashboard.utils.db import get_companies, get_ratios

st.title("🏢 Company Profile & Financial Health")

df_companies = get_companies()

# Search Box with Autocomplete Dropdown
company_list = (df_companies['ticker'] + " - " + df_companies['company_name']).tolist()
selected_option = st.selectbox("Search Company by Name or Ticker", options=[""] + company_list)

if not selected_option:
    st.info("Please search and select a company to view its detailed profile.")
else:
    ticker = selected_option.split(" - ")[0]
    comp_info = df_companies[df_companies['ticker'] == ticker]

    if comp_info.empty:
        st.error("Ticker not found — please try another.")
    else:
        info = comp_info.iloc[0]
        df_history = get_ratios(ticker=ticker)

        # Company Header Card
        st.markdown(f"### {info['company_name']} (`{info['ticker']}`)")
        st.caption(f"**Sector:** {info['sector']} | **Sub-Sector:** {info.get('sub_sector', 'N/A')}")
        st.write(info.get('description', 'No description available.'))

        # 6 Latest KPI Tiles
        if not df_history.empty:
            latest = df_history.sort_values(by='year').iloc[-1]
            
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("ROE", f"{latest.get('roe', 0):.1f}%")
            c2.metric("ROCE", f"{latest.get('roce', 0):.1f}%")
            c3.metric("Net Margin", f"{latest.get('npm', 0):.1f}%")
            c4.metric("D/E Ratio", f"{latest.get('de_ratio', 0):.2f}")
            c5.metric("5Y Rev CAGR", f"{latest.get('rev_cagr_5yr', 0):.1f}%")
            c6.metric("Latest FCF (Cr)", f"₹{latest.get('fcf_latest', latest.get('fcf', 0)):.0f}")

            st.markdown("---")

            # 10-Year Trend Charts
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.subheader("10-Year Revenue & Net Profit")
                df_sorted = df_history.sort_values(by='year')
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(x=df_sorted['year'], y=df_sorted['revenue'], name='Revenue (Cr)', marker_color='#1F4E78'))
                fig_bar.add_trace(go.Bar(x=df_sorted['year'], y=df_sorted['net_profit'], name='Net Profit (Cr)', marker_color='#2CA02C'))
                fig_bar.update_layout(barmode='group', height=350, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_bar, use_container_width=True)

            with chart_col2:
                st.subheader("ROE vs ROCE Trend")
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(x=df_sorted['year'], y=df_sorted['roe'], mode='lines+markers', name='ROE (%)', line=dict(color='#FF7F0E', width=2)))
                fig_line.add_trace(go.Scatter(x=df_sorted['year'], y=df_sorted['roce'], mode='lines+markers', name='ROCE (%)', line=dict(color='#1F77B4', width=2)))
                fig_line.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_line, use_container_width=True)

            # Dynamic Pros & Cons Badges
            st.markdown("### 🔍 Pros & Cons Analysis")
            pro_col, con_col = st.columns(2)

            pros, cons = [], []
            if latest.get('roe', 0) > 15: pros.append("Strong Return on Equity (ROE > 15%)")
            else: cons.append("Low Return on Equity (ROE < 15%)")

            if latest.get('de_ratio', 1) < 0.5: pros.append("Healthy Balance Sheet (D/E < 0.5)")
            elif latest.get('de_ratio', 0) > 1.5: cons.append("High Financial Leverage (D/E > 1.5)")

            if latest.get('fcf', 0) > 0: pros.append("Positive Free Cash Flow Generation")
            else: cons.append("Negative Free Cash Flow")

            if latest.get('rev_cagr_5yr', 0) > 10: pros.append("Robust 5-Year Revenue Growth (> 10%)")

            with pro_col:
                for p in pros:
                    st.success(f"✅ {p}")

            with con_col:
                for c in cons:
                    st.error(f"❌ {c}")
