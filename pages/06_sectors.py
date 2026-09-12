import sys
import os
sys.path.append(os.path.abspath('.'))

# pages/06_sectors.py

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.dashboard.utils.db import get_companies, get_ratios

st.title("🏭 Sector & Industry Analysis")

df_companies = get_companies()
df_ratios = get_ratios(year=2024)
if df_ratios.empty:
    df_ratios = get_ratios()

merged = df_ratios.merge(df_companies[['company_id', 'sector', 'sub_sector', 'market_cap']], on='company_id', how='left')

sector_list = ["All Sectors"] + sorted(merged['sector'].dropna().unique().tolist())
selected_sector = st.selectbox("Filter Sector", options=sector_list)

filtered = merged if selected_sector == "All Sectors" else merged[merged['sector'] == selected_sector]

st.subheader(f"4D Scatter Bubble Chart — {selected_sector}")
fig_bubble = px.scatter(
    filtered,
    x="revenue",
    y="roe",
    size="market_cap_x" if "market_cap_x" in filtered.columns else "market_cap",
    color="sub_sector" if "sub_sector" in filtered.columns else "sector",
    hover_name="company_id",
    log_x=True,
    labels={"revenue": "Revenue (Cr, Log Scale)", "roe": "ROE (%)"},
    height=450
)
st.plotly_chart(fig_bubble, use_container_width=True)

# Sector Median KPIs
st.subheader("Sector Median Key Performance Indicators")
median_kpis = merged.groupby('sector')[['roe', 'roce', 'npm', 'de_ratio', 'rev_cagr_5yr']].median().reset_index()

fig_median = go.Figure()
fig_median.add_trace(go.Bar(x=median_kpis['sector'], y=median_kpis['roe'], name="Median ROE (%)", marker_color="#1F4E78"))
fig_median.add_trace(go.Bar(x=median_kpis['sector'], y=median_kpis['rev_cagr_5yr'], name="Median 5Y Rev CAGR (%)", marker_color="#2CA02C"))
fig_median.update_layout(barmode='group', height=400)
st.plotly_chart(fig_median, use_container_width=True)
