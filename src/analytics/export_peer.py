# src/analytics/export_peer.py

import os
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
import pandas as pd
import numpy as np

# Color Fills
GREEN_FILL  = PatternFill(start_color="D9EAD3", end_color="D9EAD3", fill_type="solid") # >= 75th percentile
YELLOW_FILL = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid") # 25th to 75th percentile
RED_FILL    = PatternFill(start_color="F4CCCC", end_color="F4CCCC", fill_type="solid") # <= 25th percentile
GOLD_FILL   = PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid") # Benchmark company row
HEADER_FILL = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid") # Header Dark Blue
MEDIAN_FILL = PatternFill(start_color="EFEFEF", end_color="EFEFEF", fill_type="solid") # Summary row light grey

METRICS_20 = [
    'roe', 'roce', 'npm', 'de_ratio', 'icr', 'fcf', 'fcf_cagr_5yr',
    'cfo_pat_ratio', 'rev_cagr_5yr', 'rev_cagr_3yr', 'pat_cagr_5yr', 'eps_cagr_5yr',
    'pe_ratio', 'pb_ratio', 'div_yield', 'div_payout', 'asset_turnover',
    'market_cap', 'net_profit', 'revenue'
]

def generate_peer_comparison_report(
    df_companies: pd.DataFrame, 
    df_percentiles: pd.DataFrame, 
    df_peer_mapping: pd.DataFrame, 
    output_path: str = "output/peer_comparison.xlsx"
):
    """
    Generates output/peer_comparison.xlsx with 11 sheets covering all 11 peer groups.
    Applies percentile heatmapping, benchmark row highlighting, and median summary rows.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Merge metrics, peer assignments, and benchmark flags
    merged_df = df_companies.merge(df_peer_mapping, on='company_id', how='inner')
    
    wb = openpyxl.Workbook()
    wb.remove(wb.active) # Remove default sheet
    
    unique_peer_groups = [g for g in merged_df['peer_group_name'].dropna().unique() if g != "No peer group assigned"]
    
    # Ensure all 11 peer groups are represented
    if len(unique_peer_groups) == 0:
        unique_peer_groups = [f"Peer Group {i}" for i in range(1, 12)]

    for group_name in unique_peer_groups:
        group_data = merged_df[merged_df['peer_group_name'] == group_name].copy()
        
        if len(group_data) == 0:
            continue

        ws = wb.create_sheet(title=str(group_name)[:31])
        ws.views.sheetView[0].showGridLines = True
        
        # Build dynamic columns list: company_id, company_name, + 20 metrics + 10 pct ranks
        columns_header = ['company_id', 'company_name']
        for m in METRICS_20:
            columns_header.append(m)
            columns_header.append(f"{m}_pct")

        # Write Header Row
        ws.append(columns_header)
        for col_idx in range(1, len(columns_header) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = HEADER_FILL
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")

        # Pivot percentiles for quick lookup: (company_id, metric) -> percentile_rank
        group_pcts = df_percentiles[df_percentiles['peer_group_name'] == group_name]
        pct_map = {}
        for _, pct_row in group_pcts.iterrows():
            pct_map[(pct_row['company_id'], pct_row['metric'])] = pct_row['percentile_rank']

        # Populate Company Rows
        current_row = 2
        for _, company in group_data.iterrows():
            cid = company['company_id']
            cname = company.get('company_name', cid)
            is_benchmark = company.get('is_benchmark', False)
            
            row_vals = [cid, cname]
            for m in METRICS_20:
                raw_val = company.get(m, np.nan)
                pct_val = pct_map.get((cid, m), np.nan)
                
                row_vals.append(raw_val if raw_val != float('inf') else "Debt Free")
                row_vals.append(pct_val if not pd.isna(pct_val) else "N/A")
                
            ws.append(row_vals)
            
            # Row Styling
            for col_idx, col_name in enumerate(columns_header, start=1):
                cell = ws.cell(row=current_row, column=col_idx)
                
                # Highlight benchmark company row in Gold
                if is_benchmark:
                    cell.fill = GOLD_FILL
                # Percentile rank heatmapping (Green >= 75, Yellow 25-75, Red <= 25)
                elif col_name.endswith('_pct') and isinstance(cell.value, (int, float)):
                    pct_score = cell.value
                    if pct_score >= 75.0:
                        cell.fill = GREEN_FILL
                    elif pct_score >= 25.0:
                        cell.fill = YELLOW_FILL
                    else:
                        cell.fill = RED_FILL
            
            current_row += 1

        # Append Peer Group Median Summary Row
        median_row_vals = ["MEDIAN", "Peer Group Median"]
        for m in METRICS_20:
            numeric_vals = pd.to_numeric(
                group_data[m].replace(['Debt Free', 'DEBT FREE', np.inf], np.nan), 
                errors='coerce'
            )
            med = numeric_vals.median()
            median_row_vals.append(round(med, 2) if not pd.isna(med) else "N/A")
            median_row_vals.append("-") # No percentile for median row

        ws.append(median_row_vals)
        for col_idx in range(1, len(columns_header) + 1):
            cell = ws.cell(row=current_row, column=col_idx)
            cell.fill = MEDIAN_FILL
            cell.font = Font(bold=True)

    wb.save(output_path)
    print(f"[✓] Generated '{output_path}' with {len(wb.sheetnames)} peer group sheets.")

if __name__ == "__main__":
    np.random.seed(42)
    peer_groups = [f"Peer Group {i}" for i in range(1, 12)]

    # Mock Universe
    companies_df = pd.DataFrame({
        "company_id": [f"COMP_{i:02d}" for i in range(1, 93)],
        "company_name": [f"Company {i}" for i in range(1, 93)],
        "is_benchmark": [i % 8 == 0 for i in range(1, 93)] # Sample benchmark flag
    })
    for m in METRICS_20:
        companies_df[m] = np.random.uniform(5, 50, 92)

    peer_mapping_df = pd.DataFrame({
        "company_id": [f"COMP_{i:02d}" for i in range(1, 93)],
        "peer_group_name": [peer_groups[(i - 1) % 11] for i in range(1, 93)]
    })

    # Mock Percentiles DataFrame
    pct_records = []
    for cid in companies_df['company_id']:
        p_name = peer_mapping_df.loc[peer_mapping_df['company_id'] == cid, 'peer_group_name'].values[0]
        for m in METRICS_20[:10]:
            pct_records.append({
                'company_id': cid,
                'peer_group_name': p_name,
                'metric': m,
                'percentile_rank': round(np.random.uniform(0, 100), 2)
            })
    df_percentiles = pd.DataFrame(pct_records)

    generate_peer_comparison_report(companies_df, df_percentiles, peer_mapping_df)