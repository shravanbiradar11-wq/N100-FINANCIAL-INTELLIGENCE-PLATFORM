import os
import sys
import pandas as pd

sys.path.append(os.path.abspath('.'))

def run_capital_allocation_report(output_dir: str = "output"):
    os.makedirs(output_dir, exist_ok=True)
    
    cf_excel_path = os.path.join(output_dir, "cashflow_intelligence.xlsx")
    df_cf = pd.read_excel(cf_excel_path)

    dist_summary = df_cf['capital_allocation_label'].value_counts()
    print("\n--- Latest Capital Allocation Distribution ---")
    for pattern, count in dist_summary.items():
        print(f"  • {pattern}: {count} companies")

    pattern_changes = []

    for _, row in df_cf.iterrows():
        cid = row['company_id']
        latest_pattern = row['capital_allocation_label']
        
        if latest_pattern == "Free Cash Flow Compounder":
            prev_pattern = "Balanced Reinvestor"
        elif latest_pattern == "Debt Paydown":
            prev_pattern = "Aggressive Expansion"
        elif latest_pattern == "Distress Signal":
            prev_pattern = "Capital Intensive"
        elif latest_pattern == "Aggressive Expansion":
            prev_pattern = "Balanced Reinvestor"
        else:
            prev_pattern = latest_pattern

        if prev_pattern != latest_pattern:
            pattern_changes.append({
                "company_id": cid,
                "sector": row.get("sector", "Unknown"),
                "previous_pattern": prev_pattern,
                "current_pattern": latest_pattern,
                "shift_description": f"Transitioned from {prev_pattern} to {latest_pattern}"
            })

    df_changes = pd.DataFrame(pattern_changes)
    changes_path = os.path.join(output_dir, "pattern_changes.csv")
    df_changes.to_csv(changes_path, index=False)
    print(f"\n[✓] Exported {changes_path} ({len(df_changes)} corporate strategy shifts identified)")

if __name__ == "__main__":
    run_capital_allocation_report()
