import sys
import os
sys.path.append(os.path.abspath('.'))

# pages/03_screener.py

import streamlit as st
import pandas as pd
import numpy as np
from src.dashboard.utils.db import get_ratios

st.title("🔎 Financial Screener")

df_universe = get_ratios(year=2024)
if df_universe.empty:
    df_universe = get_ratios()

# Initialize Session State for Sliders
presets_config = {
    "Quality": {"roe_min": 15.0, "de_max": 1.0, "fcf_min": 0.0, "rev_cagr_min": 10.0},
    "Value": {"pe_max": 20.0, "pb_max": 3.0, "de_max": 2.0, "div_min": 1.0},
    "Growth": {"pat_cagr_min": 20.0, "rev_cagr_min": 15.0, "de_max": 2.0},
    "Dividend": {"div_min": 2.0, "fcf_min": 0.0},
    "Debt-Free": {"de_max": 0.0, "roe_min": 12.0},
    "Turnaround": {"rev_cagr_min": 10.0, "fcf_min": 0.0}
}

# Sidebar Preset Quick-Fill Buttons
st.sidebar.header("Preset Screeners")
col_p1, col_p2 = st.sidebar.columns(2)

preset_clicked = None
if col_p1.button("Quality"): preset_clicked = "Quality"
if col_p2.button("Value"): preset_clicked = "Value"
if col_p1.button("Growth"): preset_clicked = "Growth"
if col_p2.button("Dividend"): preset_clicked = "Dividend"
if col_p1.button("Debt-Free"): preset_clicked = "Debt-Free"
if col_p2.button("Turnaround"): preset_clicked = "Turnaround"

# Default values or preset overrides
default_vals = presets_config.get(preset_clicked, {}) if preset_clicked else {}

st.sidebar.markdown("---")
st.sidebar.header("Filter Sliders")

roe_min = st.sidebar.slider("Min ROE (%)", 0.0, 40.0, float(default_vals.get("roe_min", 0.0)))
de_max = st.sidebar.slider("Max D/E Ratio", 0.0, 5.0, float(default_vals.get("de_max", 5.0)))
fcf_min = st.sidebar.slider("Min FCF (Cr)", -100.0, 500.0, float(default_vals.get("fcf_min", -100.0)))
rev_cagr_min = st.sidebar.slider("Min 5Y Rev CAGR (%)", -10.0, 40.0, float(default_vals.get("rev_cagr_min", -10.0)))
pat_cagr_min = st.sidebar.slider("Min 5Y PAT CAGR (%)", -10.0, 40.0, float(default_vals.get("pat_cagr_min", -10.0)))
opm_min = st.sidebar.slider("Min Operating Margin (%)", 0.0, 50.0, 0.0)
pe_max = st.sidebar.slider("Max P/E Ratio", 5.0, 100.0, float(default_vals.get("pe_max", 100.0)))
pb_max = st.sidebar.slider("Max P/B Ratio", 0.5, 20.0, float(default_vals.get("pb_max", 20.0)))
div_min = st.sidebar.slider("Min Dividend Yield (%)", 0.0, 10.0, float(default_vals.get("div_min", 0.0)))
icr_min = st.sidebar.slider("Min Interest Coverage (ICR)", 0.0, 50.0, 0.0)

# Filter Engine Logic
filtered = df_universe.copy()

filtered = filtered[
    (filtered['roe'] >= roe_min) &
    (filtered['fcf'] >= fcf_min) &
    (filtered['rev_cagr_5yr'] >= rev_cagr_min) &
    (filtered['pat_cagr_5yr'] >= pat_cagr_min) &
    (filtered['pe_ratio'] <= pe_max) &
    (filtered['pb_ratio'] <= pb_max) &
    (filtered['div_yield'] >= div_min)
]

# Sector bypass for D/E check (Financials bypass)
if 'broad_sector' in filtered.columns:
    fin_mask = filtered['broad_sector'].isin(["Financials", "Banking", "NBFC"])
    filtered = filtered[(filtered['de_ratio'] <= de_max) | fin_mask]
else:
    filtered = filtered[filtered['de_ratio'] <= de_max]

# Header Badge
st.subheader(f"📊 {len(filtered)} companies match your active filters")

# Results Table
disp_cols = ['ticker', 'company_id', 'roe', 'de_ratio', 'fcf', 'rev_cagr_5yr', 'pat_cagr_5yr', 'pe_ratio', 'pb_ratio', 'div_yield', 'composite_quality_score']
disp_df = filtered[[c for c in disp_cols if c in filtered.columns]].sort_values(by='composite_quality_score', ascending=False)

st.dataframe(disp_df, use_container_width=True, hide_index=True)

# CSV Export Button
csv_data = disp_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Results as CSV",
    data=csv_data,
    file_name="screener_filtered_results.csv",
    mime="text/csv"
)
