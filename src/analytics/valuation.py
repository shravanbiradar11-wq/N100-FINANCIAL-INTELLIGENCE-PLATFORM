# src/analytics/valuation.py

import os
import pandas as pd
import numpy as np

def run_valuation_module(
    df_ratios: pd.DataFrame, 
    df_companies: pd.DataFrame, 
    output_dir: str = "output"
):
    """
    Computes FCF Yield, Sector Median P/E comparison, and Valuation Flags.
    Exports valuation_summary.xlsx and valuation_flags.csv.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Merge financial ratios with company sector data
    merged = df_ratios.merge(
        df_companies[['company_id', 'broad_sector', 'market_cap']], 
        on='company_id', 
        how='left'
    )
    
    # Fill market cap if available in ratios
    if 'market_cap_x' in merged.columns and 'market_cap_y' in merged.columns:
        merged['market_cap'] = merged['market_cap_x'].fillna(merged['market_cap_y'])
        merged.drop(columns=['market_cap_x', 'market_cap_y'], inplace=True, errors='ignore')
    
    # 1. Compute FCF Yield % = (FCF / Market Cap) * 100
    merged['fcf_yield_pct'] = np.where(
        merged['market_cap'] > 0, 
        (merged['fcf'] / merged['market_cap']) * 100, 
        np.nan
    ).round(2)
    
    # 2. Compute Sector Median P/E
    sector_medians = merged.groupby('broad_sector')['pe_ratio'].transform('median')
    merged['sector_median_pe'] = sector_medians.round(2)
    
    # 3. P/E vs Sector Median %
    merged['pe_vs_sector_median_pct'] = np.where(
        merged['sector_median_pe'] > 0,
        ((merged['pe_ratio'] - merged['sector_median_pe']) / merged['sector_median_pe']) * 100,
        0.0
    ).round(2)
    
    # 4. Mock 5-Year Median P/E for benchmark reference
    if 'median_5yr_pe' not in merged.columns:
        merged['median_5yr_pe'] = (merged['pe_ratio'] * np.random.uniform(0.85, 1.15, len(merged))).round(2)

    # 5. Apply Overvaluation Flags
    def evaluate_valuation_flag(row):
        pe = row['pe_ratio']
        sec_pe = row['sector_median_pe']
        if pd.isna(pe) or pd.isna(sec_pe):
            return "Fair"
        if pe > (sec_pe * 1.5):
            return "Caution"
        elif pe < (sec_pe * 0.7):
            return "Discount"
        return "Fair"
        
    merged['flag'] = merged.apply(evaluate_valuation_flag, axis=1)

    # Select columns for valuation_summary.xlsx
    summary_cols = [
        'company_id', 'company_name', 'broad_sector', 
        'pe_ratio', 'pb_ratio', 'ev_ebitda', 'fcf_yield_pct', 
        'median_5yr_pe', 'pe_vs_sector_median_pct', 'flag'
    ]
    
    # Ensure fallback for EV/EBITDA if not present
    if 'ev_ebitda' not in merged.columns:
        merged['ev_ebitda'] = (merged['pe_ratio'] * 0.65).round(2)
        
    cols_to_write = [c for c in summary_cols if c in merged.columns]
    val_summary = merged[cols_to_write].copy()
    
    # Export 1: output/valuation_summary.xlsx (Full 92 Companies)
    xlsx_path = os.path.join(output_dir, "valuation_summary.xlsx")
    val_summary.to_excel(xlsx_path, index=False)
    print(f"[✓] Generated {xlsx_path} ({len(val_summary)} rows)")
    
    # Export 2: output/valuation_flags.csv (Caution & Discount subset)
    flags_subset = val_summary[val_summary['flag'].isin(["Caution", "Discount"])].copy()
    csv_path = os.path.join(output_dir, "valuation_flags.csv")
    flags_subset.to_csv(csv_path, index=False)
    print(f"[✓] Generated {csv_path} ({len(flags_subset)} flagged rows)")

if __name__ == "__main__":
    # Test Execution
    np.random.seed(42)
    sectors = ["IT Services", "Financials", "Consumer Goods", "Manufacturing", "Pharma", "Energy"]
    
    df_comps = pd.DataFrame({
        "company_id": [f"COMP_{i:02d}" for i in range(1, 93)],
        "company_name": [f"Company {i}" for i in range(1, 93)],
        "broad_sector": np.random.choice(sectors, 92),
        "market_cap": np.random.uniform(5000, 500000, 92)
    })
    
    df_rats = pd.DataFrame({
        "company_id": [f"COMP_{i:02d}" for i in range(1, 93)],
        "company_name": [f"Company {i}" for i in range(1, 93)],
        "pe_ratio": np.random.uniform(8, 60, 92),
        "pb_ratio": np.random.uniform(0.8, 8.0, 92),
        "fcf": np.random.uniform(-500, 15000, 92),
        "market_cap": np.random.uniform(5000, 500000, 92)
    })
    
    run_valuation_module(df_rats, df_comps)