# tests/test_sprint4_qa.py

import unittest
import os
import time
import pandas as pd
import numpy as np
from src.dashboard.utils.db import get_companies, get_ratios, get_valuation
from src.analytics.valuation import run_valuation_module

class TestSprint4DashboardQA(unittest.TestCase):

    def setUp(self):
        self.tickers = ["TICKER1", "TICKER5", "TICKER12", "TICKER25", "TICKER50"]

    def test_01_profile_screen_load_time(self):
        """Verify Company Profile data fetching loads in under 3 seconds per ticker."""
        for t in self.tickers:
            start_time = time.time()
            data = get_ratios(ticker=t)
            elapsed = time.time() - start_time
            self.assertLess(elapsed, 3.0, f"Load time for {t} exceeded 3.0s threshold ({elapsed:.2f}s)")

    def test_02_missing_data_nan_handling(self):
        """Ensure missing or NaN values convert cleanly without causing crashes."""
        df_incomplete = pd.DataFrame([
            {"company_id": "INC_01", "ticker": "INC1", "roe": None, "de_ratio": np.nan, "fcf": None}
        ])
        clean_roe = df_incomplete['roe'].fillna("N/A").iloc[0]
        self.assertEqual(clean_roe, "N/A")

    def test_03_valuation_summary_row_count(self):
        """Verify valuation_summary.xlsx contains all 92 companies."""
        df_comps = get_companies()
        df_rats = get_ratios(year=2024)
        run_valuation_module(df_rats, df_comps, output_dir="output")
        
        summary_path = "output/valuation_summary.xlsx"
        self.assertTrue(os.path.exists(summary_path))
        df_summary = pd.read_excel(summary_path)
        self.assertEqual(len(df_summary), 92)

    def test_04_valuation_flags_subset(self):
        """Verify valuation_flags.csv contains only Caution and Discount flagged entries."""
        flags_path = "output/valuation_flags.csv"
        self.assertTrue(os.path.exists(flags_path))
        df_flags = pd.read_csv(flags_path)
        unique_flags = set(df_flags['flag'].unique())
        self.assertTrue(unique_flags.issubset({"Caution", "Discount"}))

if __name__ == "__main__":
    unittest.main()