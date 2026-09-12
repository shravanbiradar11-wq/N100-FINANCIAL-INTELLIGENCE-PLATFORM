# tests/test_sprint3_dq.py

import unittest
import os
import sqlite3
import numpy as np
import pandas as pd
from src.screener.engine import ScreenerEngine
from src.analytics.peer import PeerEngine

class TestSprint3DataQuality(unittest.TestCase):

    def setUp(self):
        self.engine = ScreenerEngine()
        self.peer_engine = PeerEngine(db_path="output/test_database.db")
        
        # Synthetic universe for deterministic testing
        self.mock_companies = pd.DataFrame([
            {"company_id": "C1", "company_name": "Alpha IT", "sector": "IT Services", "broad_sector": "IT Services", "roe": 25.0, "de_ratio": 0.1, "icr": "Debt Free", "fcf": 200, "rev_cagr_5yr": 18.0, "pat_cagr_5yr": 22.0, "roce": 20.0, "npm": 15.0, "fcf_cagr_5yr": 12.0, "cfo_pat_ratio": 1.1, "eps_cagr_5yr": 15.0, "asset_turnover": 1.5},
            {"company_id": "C2", "company_name": "Beta Bank", "sector": "Financials", "broad_sector": "Financials", "roe": 18.0, "de_ratio": 6.0, "icr": 4.0, "fcf": 500, "rev_cagr_5yr": 15.0, "pat_cagr_5yr": 12.0, "roce": 14.0, "npm": 18.0, "fcf_cagr_5yr": 8.0, "cfo_pat_ratio": 0.9, "eps_cagr_5yr": 10.0, "asset_turnover": 0.8},
            {"company_id": "C3", "company_name": "Gamma Mfg", "sector": "Manufacturing", "broad_sector": "Manufacturing", "roe": 10.0, "de_ratio": 1.8, "icr": 2.0, "fcf": -50, "rev_cagr_5yr": 5.0, "pat_cagr_5yr": 4.0, "roce": 8.0, "npm": 5.0, "fcf_cagr_5yr": -2.0, "cfo_pat_ratio": 0.6, "eps_cagr_5yr": 3.0, "asset_turnover": 0.9},
            {"company_id": "C4", "company_name": "Delta Tech", "sector": "IT Services", "broad_sector": "IT Services", "roe": 30.0, "de_ratio": 0.0, "icr": "Debt Free", "fcf": 350, "rev_cagr_5yr": 25.0, "pat_cagr_5yr": 28.0, "roce": 28.0, "npm": 20.0, "fcf_cagr_5yr": 20.0, "cfo_pat_ratio": 1.3, "eps_cagr_5yr": 25.0, "asset_turnover": 1.8},
        ])
        
        self.peer_mapping = pd.DataFrame([
            {"company_id": "C1", "peer_group_name": "IT Services"},
            {"company_id": "C2", "peer_group_name": "Financials"},
            {"company_id": "C3", "peer_group_name": "Manufacturing"},
            {"company_id": "C4", "peer_group_name": "IT Services"},
        ])

    # --- Rule 1 to 4: Filter Engine & Exceptions ---
    def test_01_roe_min_filter(self):
        res = self.engine.apply_filters(self.mock_companies, {"roe_min": 20.0})
        self.assertTrue(all(res['roe'] >= 20.0))

    def test_02_de_max_financials_bypass(self):
        """Verify Financials sector passes even if D/E > de_ratio_max."""
        res = self.engine.apply_filters(self.mock_companies, {"de_ratio_max": 1.0})
        sectors = res['sector'].tolist()
        self.assertIn("Financials", sectors)

    def test_03_icr_debt_free_handling(self):
        """Verify 'Debt Free' ICR passes high minimum thresholds."""
        res = self.engine.apply_filters(self.mock_companies, {"icr_min": 10.0})
        ids = res['company_id'].tolist()
        self.assertIn("C1", ids)
        self.assertIn("C4", ids)

    def test_04_preset_quality_compounder(self):
        res = self.engine.run_preset(self.mock_companies, "quality_compounder")
        self.assertGreaterEqual(len(res), 1)

    # --- Rule 5 to 8: Winsorisation & Composite Score ---
    def test_05_winsorisation_bounds(self):
        s = pd.Series([1, 5, 10, 15, 20, 25, 30, 1000])
        scaled = self.engine.winsorize_and_scale(s)
        self.assertGreaterEqual(scaled.min(), 0.0)
        self.assertLessEqual(scaled.max(), 100.0)

    def test_06_composite_score_range(self):
        df_scored = self.engine.calculate_composite_score(self.mock_companies)
        scores = df_scored['composite_quality_score']
        self.assertTrue(all((scores >= 0) & (scores <= 100)))

    def test_07_composite_score_sorting(self):
        res = self.engine.apply_filters(self.mock_companies, {})
        scores = res['composite_quality_score'].tolist()
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_08_de_inversion_scoring(self):
        """Lower D/E should yield higher D/E component score."""
        s_low_de = self.engine.winsorize_and_scale(pd.Series([0.1, 2.0]), invert=True)
        self.assertGreater(s_low_de.iloc[0], s_low_de.iloc[1])

    # --- Rule 9 to 12: Peer Rankings ---
    def test_09_peer_percentile_computation(self):
        pcts = self.peer_engine.compute_peer_percentiles(self.mock_companies, self.peer_mapping)
        self.assertFalse(pcts.empty)

    def test_10_it_services_highest_roe_rank(self):
        """Company with highest ROE in IT Services must have 100th percentile rank."""
        pcts = self.peer_engine.compute_peer_percentiles(self.mock_companies, self.peer_mapping)
        c4_roe_pct = pcts[(pcts['company_id'] == 'C4') & (pcts['metric'] == 'roe')]['percentile_rank'].values[0]
        self.assertEqual(c4_roe_pct, 100.0)

    def test_11_de_percentile_inversion(self):
        """Inverted D/E percentile: lower D/E gets higher rank."""
        pcts = self.peer_engine.compute_peer_percentiles(self.mock_companies, self.peer_mapping)
        c4_de_pct = pcts[(pcts['company_id'] == 'C4') & (pcts['metric'] == 'de_ratio')]['percentile_rank'].values[0]
        c1_de_pct = pcts[(pcts['company_id'] == 'C1') & (pcts['metric'] == 'de_ratio')]['percentile_rank'].values[0]
        self.assertGreaterEqual(c4_de_pct, c1_de_pct)

    def test_12_unassigned_peer_group_graceful(self):
        unassigned_map = pd.DataFrame([{"company_id": "C1", "peer_group_name": None}])
        pcts = self.peer_engine.compute_peer_percentiles(self.mock_companies, unassigned_map)
        c1_group = pcts[pcts['company_id'] == 'C1']['peer_group_name'].values[0]
        self.assertEqual(c1_group, "No peer group assigned")

    # --- Rule 13 to 14: File Outputs & Database Integrity ---
    def test_13_sqlite_database_persistence(self):
        pcts = self.peer_engine.compute_peer_percentiles(self.mock_companies, self.peer_mapping)
        self.peer_engine.save_to_sqlite(pcts)
        self.assertTrue(os.path.exists("output/test_database.db"))

    def test_14_sqlite_record_count(self):
        conn = sqlite3.connect("output/test_database.db")
        count = pd.read_sql("SELECT COUNT(*) as cnt FROM peer_percentiles", conn)['cnt'].values[0]
        conn.close()
        self.assertEqual(count, 4 * 10) # 4 companies * 10 metrics

if __name__ == '__main__':
    unittest.main()