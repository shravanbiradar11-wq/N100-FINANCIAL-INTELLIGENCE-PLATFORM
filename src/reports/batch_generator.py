import os
import sys
import pandas as pd

sys.path.append(os.path.abspath('.'))

from src.dashboard.utils.db import get_companies, get_ratios
from src.reports.tearsheet import generate_company_tearsheet
from src.reports.sector_report import generate_sector_report

def run_batch_generation():
    os.makedirs("reports/tearsheets", exist_ok=True)
    os.makedirs("reports/sector", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    df_comps = get_companies()
    df_ratios = get_ratios()
    
    skipped = []
    generated_tearsheets = 0

    print("\n--- Generating 92 Company Tearsheet PDFs ---")
    for _, comp in df_comps.iterrows():
        cid = comp['company_id']
        comp_history = df_ratios[df_ratios['company_id'] == cid]
        
        # Skip companies with fewer than 3 years of historical data
        if len(comp_history) < 3:
            skipped.append({"company_id": cid, "reason": "Fewer than 3 years of historical data"})
            continue
            
        out_pdf = f"reports/tearsheets/{cid}_tearsheet.pdf"
        try:
            generate_company_tearsheet(cid, out_pdf)
            generated_tearsheets += 1
        except Exception as e:
            print(f"[X] Failed generating tearsheet for {cid}: {e}")
            skipped.append({"company_id": cid, "reason": str(e)})

    # Log skipped tickers
    df_skipped = pd.DataFrame(skipped)
    df_skipped.to_csv("output/skipped_tearsheets.csv", index=False)
    print(f"[✓] Completed tearsheet generation. Generated: {generated_tearsheets}, Skipped: {len(skipped)}")

    print("\n--- Generating 11 Sector Analysis PDFs ---")
    sectors = df_comps['sector'].dropna().unique()
    for sec in sectors:
        sec_clean = str(sec).replace(" ", "_").replace("/", "_")
        sec_pdf = f"reports/sector/{sec_clean}_report.pdf"
        try:
            generate_sector_report(str(sec), sec_pdf)
        except Exception as e:
            print(f"[X] Failed sector PDF for {sec}: {e}")

if __name__ == "__main__":
    run_batch_generation()
