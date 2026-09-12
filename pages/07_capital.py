import sys
import os
sys.path.append(os.path.abspath('.'))

# pages/07_capital.py

import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from src.dashboard.utils.db import get_companies

st.title("🗺️ Capital Allocation Map")

df_companies = get_companies()

patterns = [
    "Aggressive Growth", "Debt Reduction", "Shareholder Return", 
    "Capital Preservation", "Balanced Allocation", "R&D Focus", 
    "M&A Heavy", "Asset Light"
]

np.random.seed(42)
df_companies['capital_pattern'] = [patterns[i % 8] for i in range(len(df_companies))]

st.subheader("Treemap of Capital Allocation Strategies across Nifty 100")
fig_tree = px.treemap(
    df_companies,
    path=['capital_pattern', 'company_name'],
    values='market_cap',
    color='capital_pattern',
    height=500
)
st.plotly_chart(fig_tree, use_container_width=True)

selected_pattern = st.selectbox("Select Capital Pattern to View Companies", options=patterns)
pattern_companies = df_companies[df_companies['capital_pattern'] == selected_pattern]

st.write(f"**{len(pattern_companies)} companies following '{selected_pattern}' Strategy:**")
st.dataframe(pattern_companies[['ticker', 'company_name', 'sector', 'market_cap']], use_container_width=True, hide_index=True)
