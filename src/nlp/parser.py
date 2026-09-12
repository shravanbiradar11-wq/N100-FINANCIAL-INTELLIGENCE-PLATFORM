import os
import re
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath('.'))

from src.dashboard.utils.db import get_companies, get_ratios

def parse_analysis_text(
    excel_path: str = "data/analysis.xlsx",
    output_dir: str = "output"
):
    os.makedirs(output_dir, exist_ok=True)
    
    parsed_records = []
    failures = []
    
    pattern = re.compile(r"(\d+)\s*Years?:?\s*([\d.]+)%", re.IGNORECASE)
    
    if os.path.exists(excel_path):
        df_analysis = pd.read_excel(excel_path)
    else:
        print(f"[!] {excel_path} not found. Generating mock analysis dataset for parsing...")
        df_comps = get_companies()
        mock_data = []
        for cid in df_comps['company_id']:
            mock_data.append({
                "company_id": cid,
                "compounded_sales_growth": "10 Years: 18.5%\n5 Years: 15.0%\n3 Years: 12.2%",
                "compounded_profit_growth": "10 Years: 22.0%\n5 Years: 18.4%\n3 Years: 14.1%",
                "stock_price_cagr": "10 Years: 15.0%\n5 Years: 12.0%",
                "roe": "10 Years: 20.0%\n5 Years: 22.5%\n3 Years: 21.0%\nLast Year: 19.5%"
            })
        df_analysis = pd.DataFrame(mock_data)

    metric_cols = [
        "compounded_sales_growth", 
        "compounded_profit_growth", 
        "stock_price_cagr", 
        "roe"
    ]

    for _, row in df_analysis.iterrows():
        cid = row.get("company_id")
        for col in metric_cols:
            text_val = str(row.get(col, ""))
            if not text_val or pd.isna(row.get(col)):
                continue
                
            lines = text_val.split("\n")
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    continue
                    
                match = pattern.search(line_str)
                if match:
                    period_years = int(match.group(1))
                    value_pct = float(match.group(2))
                    parsed_records.append({
                        "company_id": cid,
                        "metric_type": col,
                        "period_years": period_years,
                        "value_pct": value_pct
                    })
                else:
                    failures.append({
                        "company_id": cid,
                        "metric_type": col,
                        "raw_text": line_str,
                        "reason": "Pattern match failed"
                    })

    df_parsed = pd.DataFrame(parsed_records)
    parsed_csv_path = os.path.join(output_dir, "analysis_parsed.csv")
    df_parsed.to_csv(parsed_csv_path, index=False)
    print(f"[✓] Exported {parsed_csv_path} ({len(df_parsed)} records)")

    df_failures = pd.DataFrame(failures)
    failures_csv_path = os.path.join(output_dir, "parse_failures.csv")
    df_failures.to_csv(failures_csv_path, index=False)
    print(f"[✓] Exported {failures_csv_path} ({len(df_failures)} failed lines logged)")

    df_ratios = get_ratios(year=2024)
    if not df_ratios.empty and 'rev_cagr_5yr' in df_ratios.columns:
        print("\n--- Cross-Validating 5Y Sales CAGR against Ratio Engine ---")
        sales_5yr = df_parsed[
            (df_parsed['metric_type'] == 'compounded_sales_growth') & 
            (df_parsed['period_years'] == 5)
        ]
        
        divergence_count = 0
        for _, p_row in sales_5yr.iterrows():
            cid = p_row['company_id']
            parsed_val = p_row['value_pct']
            
            match_ratio = df_ratios[df_ratios['company_id'] == cid]
            if not match_ratio.empty:
                computed_val = match_ratio['rev_cagr_5yr'].values[0]
                if pd.notna(computed_val):
                    diff = abs(parsed_val - computed_val)
                    if diff > 5.0:
                        divergence_count += 1
                        print(f"[⚠️ WARNING] Divergence > 5% for {cid}: Parsed={parsed_val}%, Computed={computed_val:.1f}%")
        
        if divergence_count == 0:
            print("[✓] All parsed 5-Year CAGR values closely align with the Ratio Engine (<5% divergence).")

if __name__ == "__main__":
    parse_analysis_text()
