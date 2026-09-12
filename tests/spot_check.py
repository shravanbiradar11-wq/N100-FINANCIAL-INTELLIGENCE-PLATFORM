# tests/spot_check.py

import sys
import os
sys.path.append(os.path.abspath('.')) # Ensures 'src' module can be imported

import pandas as pd
import numpy as np
from src.screener.engine import ScreenerEngine
from src.analytics.peer import PeerEngine

def run_sprint3_spot_checks():
    print("==================================================")
    print("      SPRINT 3 SPOT-CHECK VERIFICATION")
    print("==================================================\n")

    np.random.seed(42)
    sectors = ["IT Services", "Financials", "Consumer Goods", "Manufacturing", "Pharma"]
    
    mock_universe = pd.DataFrame({
        "company_id": [f"COMP_{i:02d}" for i in range(1, 93)],
        "company_name": [f"Company {i}" for i in range(1, 93)],
        "sector": np.random.choice(sectors, 92),
        "broad_sector": np.random.choice(sectors, 92),
        "roe": np.random.uniform(5, 35, 92),
        "de_ratio": np.random.uniform(0, 3, 92),
        "fcf": np.random.uniform(-50, 500, 92),
        "rev_cagr_5yr": np.random.uniform(2, 25, 92),
        "roce": np.random.uniform(5, 25, 92),
        "npm": np.random.uniform(2, 20, 92),
        "icr": np.random.choice([2.5, 5.0, 10.0, "Debt Free"], 92),
        "fcf_cagr_5yr": np.random.uniform(-5, 25, 92),
        "cfo_pat_ratio": np.random.uniform(0.5, 1.5, 92),
        "pat_cagr_5yr": np.random.uniform(2, 30, 92),
        "eps_cagr_5yr": np.random.uniform(2, 28, 92),
        "asset_turnover": np.random.uniform(0.5, 2.5, 92)
    })

    peer_mapping = pd.DataFrame({
        "company_id": [f"COMP_{i:02d}" for i in range(1, 93)],
        "peer_group_name": ["IT Services" if i <= 10 else f"Peer Group {(i%10)+1}" for i in range(1, 93)]
    })

    screener = ScreenerEngine()
    qc_results = screener.run_preset(mock_universe, "quality_compounder")
    
    print("--> SPOT CHECK 1: Quality Compounder Screener Top 5 Results")
    print(qc_results[['company_id', 'company_name', 'sector', 'roe', 'de_ratio', 'composite_quality_score']].head(5).to_string(index=False))
    
    top5_valid = all((qc_results['roe'] >= 15.0) & (qc_results['de_ratio'] <= 1.0))
    print(f"\n[✓] Screener Criteria Check (ROE > 15%, D/E < 1.0): {'VERIFIED PASS' if top5_valid else 'FAIL'}\n")

    peer_engine = PeerEngine()
    percentiles = peer_engine.compute_peer_percentiles(mock_universe, peer_mapping)
    
    it_cohort = mock_universe[mock_universe['company_id'].isin([f"COMP_{i:02d}" for i in range(1, 11)])]
    highest_roe_company = it_cohort.sort_values(by='roe', ascending=False).iloc[0]
    
    top_company_id = highest_roe_company['company_id']
    top_company_roe = highest_roe_company['roe']
    
    top_pct_rank = percentiles[
        (percentiles['company_id'] == top_company_id) & 
        (percentiles['metric'] == 'roe')
    ]['percentile_rank'].values[0]

    print("--> SPOT CHECK 2: IT Services Peer Group ROE Ranking")
    print(f"Company with Highest ROE in IT Services: {top_company_id} (ROE: {top_company_roe:.2f}%)")
    print(f"Calculated ROE Percentile Rank: {top_pct_rank}%")
    print(f"[✓] Highest ROE equals 100th Percentile: {'VERIFIED PASS' if top_pct_rank == 100.0 else 'FAIL'}\n")

if __name__ == "__main__":
    run_sprint3_spot_checks()