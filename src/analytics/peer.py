# src/analytics/peer.py

import os
import sqlite3
import pandas as pd
import numpy as np

RANK_METRICS = [
    'roe', 'roce', 'npm', 'de_ratio', 'fcf', 
    'pat_cagr_5yr', 'rev_cagr_5yr', 'eps_cagr_5yr', 
    'icr', 'asset_turnover'
]

class PeerEngine:
    def __init__(self, db_path: str = "output/financial_database.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _clean_numeric(self, val):
        """Helper to convert string labels like 'Debt Free' to np.inf or float."""
        if pd.isna(val):
            return np.nan
        if isinstance(val, str):
            clean_str = val.strip().lower()
            if clean_str in ['debt free', 'n/a', 'none', 'inf', 'infinity']:
                return np.inf
            try:
                return float(val)
            except ValueError:
                return np.nan
        return float(val)

    def compute_peer_percentiles(self, df_companies: pd.DataFrame, df_peer_mapping: pd.DataFrame, year: int = 2026) -> pd.DataFrame:
        merged_df = df_companies.merge(df_peer_mapping, on='company_id', how='left')
        results = []

        for idx, row in merged_df.iterrows():
            company_id = row['company_id']
            peer_group = row.get('peer_group_name')

            # Unassigned peer group handling
            if pd.isna(peer_group) or str(peer_group).strip() in ["", "Unassigned", "None"]:
                for metric in RANK_METRICS:
                    results.append({
                        "company_id": company_id,
                        "peer_group_name": "No peer group assigned",
                        "metric": metric,
                        "value": row.get(metric, np.nan),
                        "percentile_rank": np.nan,
                        "year": year
                    })
                continue

            peer_cohort = merged_df[merged_df['peer_group_name'] == peer_group].copy()
            cohort_size = len(peer_cohort)

            for metric in RANK_METRICS:
                raw_val = row.get(metric, np.nan)
                
                # Sanitize numeric value for comparison
                val = self._clean_numeric(raw_val)

                if pd.isna(val) or cohort_size <= 1:
                    rank_pct = 0.50
                else:
                    # Clean all cohort values to numeric float/inf series
                    cohort_values = peer_cohort[metric].apply(self._clean_numeric)
                    
                    # Percentile rank computation: count strictly smaller values
                    rank_pct = (cohort_values < val).sum() / float(cohort_size - 1) if cohort_size > 1 else 1.0

                    # Invert D/E percentile rank (lower leverage = higher percentile)
                    if metric == 'de_ratio':
                        rank_pct = 1.0 - rank_pct

                results.append({
                    "company_id": company_id,
                    "peer_group_name": peer_group,
                    "metric": metric,
                    "value": "Debt Free" if val == np.inf else raw_val,
                    "percentile_rank": round(float(rank_pct) * 100, 2) if not pd.isna(rank_pct) else np.nan,
                    "year": year
                })

        return pd.DataFrame(results)

    def save_to_sqlite(self, percentiles_df: pd.DataFrame):
        conn = sqlite3.connect(self.db_path)
        percentiles_df.to_sql("peer_percentiles", conn, if_exists="replace", index=False)
        conn.close()
        print(f"[✓] Saved {len(percentiles_df)} percentile records to SQLite database at {self.db_path}")

if __name__ == "__main__":
    os.makedirs("src/analytics", exist_ok=True)
    np.random.seed(42)
    peer_groups = [f"Peer Group {i}" for i in range(1, 12)]

    companies_df = pd.DataFrame({
        "company_id": [f"COMP_{i:02d}" for i in range(1, 93)],
        "company_name": [f"Company {i}" for i in range(1, 93)],
        "roe": np.random.uniform(5, 30, 92),
        "roce": np.random.uniform(5, 25, 92),
        "npm": np.random.uniform(2, 20, 92),
        "de_ratio": np.random.uniform(0, 3, 92),
        "fcf": np.random.uniform(-50, 500, 92),
        "pat_cagr_5yr": np.random.uniform(2, 30, 92),
        "rev_cagr_5yr": np.random.uniform(2, 25, 92),
        "eps_cagr_5yr": np.random.uniform(2, 28, 92),
        "icr": np.random.choice([2.5, 5.0, 10.0, "Debt Free"], 92),
        "asset_turnover": np.random.uniform(0.5, 2.5, 92)
    })

    peer_mapping_df = pd.DataFrame({
        "company_id": [f"COMP_{i:02d}" for i in range(1, 93)],
        "peer_group_name": [np.random.choice(peer_groups) if i <= 85 else None for i in range(1, 93)]
    })

    engine = PeerEngine()
    percentiles_result = engine.compute_peer_percentiles(companies_df, peer_mapping_df)
    engine.save_to_sqlite(percentiles_result)