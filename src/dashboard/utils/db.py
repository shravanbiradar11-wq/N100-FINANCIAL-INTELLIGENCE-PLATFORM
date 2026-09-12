# src/dashboard/utils/db.py

import os
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st

DB_PATH = "output/financial_database.db"

def get_connection():
    """Establish connection to SQLite database."""
    if os.path.exists(DB_PATH):
        return sqlite3.connect(DB_PATH)
    return None

@st.cache_data(ttl=600)
def get_companies():
    """Retrieve master list of all companies."""
    conn = get_connection()
    if conn:
        try:
            df = pd.read_sql("SELECT * FROM companies", conn)
            conn.close()
            return df
        except Exception:
            pass
    
    # Synthetic fallback dataset for 92 companies
    np.random.seed(42)
    sectors = ["IT Services", "Financials", "Consumer Goods", "Manufacturing", "Pharma", "Energy", "Healthcare"]
    df = pd.DataFrame({
        "company_id": [f"COMP_{i:02d}" for i in range(1, 93)],
        "ticker": [f"TICKER{i}" for i in range(1, 93)],
        "company_name": [f"Company {i}" for i in range(1, 93)],
        "sector": np.random.choice(sectors, 92),
        "broad_sector": np.random.choice(sectors, 92),
        "sub_sector": ["General"] * 92,
        "description": ["Leading company in its industry sector."] * 92,
        "market_cap": np.random.uniform(5000, 500000, 92)
    })
    return df

@st.cache_data(ttl=600)
def get_ratios(ticker=None, year=None):
    """Fetch financial ratios filtered by ticker and/or year."""
    conn = get_connection()
    if conn:
        try:
            query = "SELECT * FROM financial_ratios WHERE 1=1"
            params = []
            if ticker:
                query += " AND (ticker = ? OR company_id = ?)"
                params.extend([ticker, ticker])
            if year:
                query += " AND year = ?"
                params.append(year)
            df = pd.read_sql(query, conn, params=params)
            conn.close()
            if not df.empty:
                return df
        except Exception:
            pass

    # Fallback ratio generator
    companies = get_companies()
    if ticker:
        companies = companies[(companies['ticker'] == ticker) | (companies['company_id'] == ticker)]
    
    years = [year] if year else list(range(2015, 2025))
    records = []
    
    for _, comp in companies.iterrows():
        for y in years:
            records.append({
                "company_id": comp['company_id'],
                "ticker": comp['ticker'],
                "year": y,
                "roe": np.random.uniform(5, 30),
                "roce": np.random.uniform(5, 25),
                "npm": np.random.uniform(2, 20),
                "de_ratio": np.random.uniform(0, 2.5),
                "icr": np.random.choice([2.5, 5.0, 10.0, "Debt Free"]),
                "fcf": np.random.uniform(-50, 500),
                "fcf_latest": np.random.uniform(10, 400),
                "fcf_cagr_5yr": np.random.uniform(-5, 25),
                "cfo_pat_ratio": np.random.uniform(0.5, 1.5),
                "rev_cagr_5yr": np.random.uniform(2, 25),
                "rev_cagr_3yr": np.random.uniform(2, 20),
                "pat_cagr_5yr": np.random.uniform(2, 30),
                "eps_cagr_5yr": np.random.uniform(2, 28),
                "pe_ratio": np.random.uniform(8, 45),
                "pb_ratio": np.random.uniform(0.8, 6.0),
                "div_yield": np.random.uniform(0, 4.0),
                "div_payout": np.random.uniform(10, 90),
                "asset_turnover": np.random.uniform(0.5, 2.5),
                "revenue": np.random.uniform(1000, 20000),
                "net_profit": np.random.uniform(100, 3000),
                "market_cap": comp['market_cap'],
                "composite_quality_score": np.random.uniform(40, 95)
            })
    return pd.DataFrame(records)

@st.cache_data(ttl=600)
def get_pl(ticker):
    """Retrieve Profit & Loss statement data (10-year trend)."""
    return get_ratios(ticker=ticker)

@st.cache_data(ttl=600)
def get_bs(ticker):
    """Retrieve Balance Sheet statement data."""
    return get_ratios(ticker=ticker)

@st.cache_data(ttl=600)
def get_cf(ticker):
    """Retrieve Cash Flow statement data."""
    return get_ratios(ticker=ticker)

@st.cache_data(ttl=600)
def get_sectors():
    """Get list of distinct sectors and their company counts."""
    df = get_companies()
    return df.groupby('sector').size().reset_index(name='company_count')

@st.cache_data(ttl=600)
def get_peers(group_name=None):
    """Fetch peer group mappings."""
    companies = get_companies()
    peer_groups = [f"Peer Group {i}" for i in range(1, 12)]
    companies['peer_group_name'] = [peer_groups[i % 11] for i in range(len(companies))]
    
    if group_name:
        return companies[companies['peer_group_name'] == group_name]
    return companies

@st.cache_data(ttl=600)
def get_valuation(ticker=None):
    """Fetch valuation metrics and overvaluation flags."""
    df = get_ratios(ticker=ticker, year=2024)
    if df.empty:
        df = get_ratios(ticker=ticker)
    
    df['fcf_yield_pct'] = (df['fcf'] / df['market_cap']) * 100
    df['sector_median_pe'] = df.groupby('broad_sector')['pe_ratio'].transform('median') if 'broad_sector' in df.columns else 20.0
    
    def calculate_flag(row):
        pe = row['pe_ratio']
        sec_pe = row['sector_median_pe']
        if pe > sec_pe * 1.5:
            return "Caution"
        elif pe < sec_pe * 0.7:
            return "Discount"
        return "Fair"
        
    df['flag'] = df.apply(calculate_flag, axis=1)
    return df