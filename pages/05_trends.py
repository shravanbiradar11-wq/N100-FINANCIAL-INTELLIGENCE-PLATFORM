import sys
import os
sys.path.append(os.path.abspath('.'))

# pages/05_trends.py

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from src.dashboard.utils.db import get_companies, get_ratios

st.title("📈 10-Year Trend Analysis")

df_companies = get_companies()
company_list = (df_companies['ticker'] + " - " + df_companies['company_name']).tolist()
selected_option = st.selectbox("Search Company", options=[""] + company_list)

if not selected_option:
    st.info("Select a company to view historical multi-metric trends.")
else:
    ticker = selected_option.split(" - ")[0]
    df_history = get_ratios(ticker=ticker).sort_values(by='year')

    if df_history.empty:
        st.warning("No historical trend data available.")
    else:
        metric_options = {
            "ROE (%)": "roe",
            "ROCE (%)": "roce",
            "Net Profit Margin (%)": "npm",
            "D/E Ratio": "de_ratio",
            "Revenue (Cr)": "revenue",
            "Net Profit (Cr)": "net_profit"
        }

        selected_metrics = st.multiselect(
            "Select up to 3 metrics to overlay",
            options=list(metric_options.keys()),
            default=["ROE (%)", "ROCE (%)"],
            max_selections=3
        )

        if selected_metrics:
            fig = go.Figure()
            for m_label in selected_metrics:
                m_col = metric_options[m_label]
                if m_col in df_history.columns:
                    y_vals = df_history[m_col]
                    # Calculate YoY % change
                    yoy_change = y_vals.pct_change() * 100
                    annotations = [f"{v:.1f}%" if not pd.isna(v) else "" for v in yoy_change]

                    fig.add_trace(go.Scatter(
                        x=df_history['year'],
                        y=y_vals,
                        mode='lines+markers+text',
                        text=annotations,
                        textposition="top center",
                        name=m_label
                    ))

            fig.update_layout(
                title=f"10-Year Multi-Metric Trend — {ticker}",
                height=450,
                xaxis=dict(title="Year", tickmode='linear'),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
