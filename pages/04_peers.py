import sys
import os
sys.path.append(os.path.abspath('.'))

# pages/04_peers.py

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.dashboard.utils.db import get_peers, get_ratios

st.title("🎯 Peer Group Analytics & Radar Comparison")

df_peers = get_peers()
unique_groups = df_peers['peer_group_name'].unique().tolist()

selected_group = st.selectbox("Select Peer Group", options=unique_groups)

# Get companies in group
group_companies = df_peers[df_peers['peer_group_name'] == selected_group]
group_tickers = group_companies['ticker'].tolist()

df_all_ratios = get_ratios()
group_ratios = df_all_ratios[df_all_ratios['ticker'].isin(group_tickers)]

if group_ratios.empty:
    st.info("No ratios found for this peer cohort.")
else:
    selected_ticker = st.selectbox("Select Benchmark Company for Radar Overlay", options=group_tickers)
    
    comp_data = group_ratios[group_ratios['ticker'] == selected_ticker].iloc[0]
    peer_avg = group_ratios.mean(numeric_only=True)

    # 8-Axis Radar Chart
    radar_metrics = ['roe', 'roce', 'npm', 'rev_cagr_5yr', 'pat_cagr_5yr', 'composite_quality_score']
    radar_labels = ['ROE', 'ROCE', 'NPM', '5Y Rev CAGR', '5Y PAT CAGR', 'Composite Score']

    comp_vals = [float(comp_data.get(m, 50)) for m in radar_metrics]
    avg_vals = [float(peer_avg.get(m, 50)) for m in radar_metrics]

    # Close polygon
    comp_vals += comp_vals[:1]
    avg_vals += avg_vals[:1]
    radar_labels += radar_labels[:1]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(r=comp_vals, theta=radar_labels, fill='toself', name=selected_ticker, line_color='#1F4E78'))
    fig_radar.add_trace(go.Scatterpolar(r=avg_vals, theta=radar_labels, fill='none', name='Peer Group Avg', line=dict(color='#D9534F', dash='dash')))

    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, height=450)
    
    st.subheader(f"8-Axis Radar: {selected_ticker} vs {selected_group} Average")
    st.plotly_chart(fig_radar, use_container_width=True)

    # Side-by-Side Metric Table
    st.subheader(f"Cohort Metrics Comparison — {selected_group}")
    disp_cols = ['ticker', 'roe', 'roce', 'npm', 'de_ratio', 'rev_cagr_5yr', 'composite_quality_score']
    table_df = group_ratios[[c for c in disp_cols if c in group_ratios.columns]].copy()
    
    st.dataframe(table_df, use_container_width=True, hide_index=True)
