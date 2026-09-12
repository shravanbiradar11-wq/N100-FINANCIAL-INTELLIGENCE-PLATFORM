import sys
import os
sys.path.append(os.path.abspath('.'))

import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from src.dashboard.utils.db import get_companies, get_ratios

st.title("🏠 Executive Overview — Nifty 100")

# Sidebar Year Selector
st.sidebar.header("Global Filters")
selected_year = st.sidebar.selectbox("Select Year", options=list(range(2024, 2018, -1)), index=0)

# Fetch Data
df_ratios = get_ratios(year=selected_year)
df_companies = get_companies()

if df_ratios.empty:
    st.warning("No data available for the selected year.")
else:
    # Calculate 6 Summary KPIs
    avg_roe = df_ratios['roe'].mean()
    med_pe = df_ratios['pe_ratio'].median()
    med_de = df_ratios['de_ratio'].median()
    total_comps = len(df_ratios['company_id'].unique())
    med_rev_cagr = df_ratios['rev_cagr_5yr'].median()
    
    # Debt-Free Count logic
    debt_free_count = (
        (df_ratios['de_ratio'] == 0) | 
        (df_ratios['icr'].astype(str).str.lower().str.contains("debt free|inf"))
    ).sum()

    # Render 6 KPI Tiles
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Average ROE", f"{avg_roe:.1f}%")
    col2.metric("Median P/E", f"{med_pe:.1f}x")
    col3.metric("Median D/E", f"{med_de:.2f}")
    col4.metric("Total Companies", f"{total_comps}")
    col5.metric("5Y Rev CAGR", f"{med_rev_cagr:.1f}%")
    col6.metric("Debt-Free", f"{debt_free_count}")

    st.markdown("---")

    col_chart, col_table = st.columns([1, 1])

    # Sector Breakdown Donut Chart
    with col_chart:
        st.subheader("Sector Breakdown")
        df_merged = df_ratios.merge(df_companies[['company_id', 'sector']], on='company_id', how='left')
        sector_counts = df_merged.groupby('sector_y' if 'sector_y' in df_merged.columns else 'sector').size().reset_index(name='count')
        sector_counts.columns = ['Sector', 'Count']

        fig_donut = px.pie(
            sector_counts, 
            values='Count', 
            names='Sector', 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_donut.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=380)
        st.plotly_chart(fig_donut, use_container_width=True)

    # Top 5 Companies by Composite Score
    with col_table:
        st.subheader("Top 5 Quality Performers")
        top_5 = df_ratios.sort_values(by='composite_quality_score', ascending=False).head(5)
        top_5_display = top_5[['ticker', 'company_id', 'roe', 'de_ratio', 'composite_quality_score']].copy()
        top_5_display.columns = ['Ticker', 'ID', 'ROE (%)', 'D/E', 'Composite Score']
        st.dataframe(top_5_display.style.format({'ROE (%)': '{:.1f}', 'D/E': '{:.2f}', 'Composite Score': '{:.1f}'}), use_container_width=True, hide_index=True)
