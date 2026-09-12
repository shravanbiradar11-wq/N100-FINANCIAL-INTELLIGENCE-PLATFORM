# src/screener/export.py

import os
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
import pandas as pd
from src.screener.engine import ScreenerEngine

# Cell Fills
GREEN_FILL = PatternFill(start_color="D9EAD3", end_color="D9EAD3", fill_type="solid") # Pass
RED_FILL   = PatternFill(start_color="F4CCCC", end_color="F4CCCC", fill_type="solid") # Fail
HEADER_FILL = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid") # Dark Blue

KPI_COLUMNS = [
    'company_id', 'company_name', 'broad_sector', 'composite_quality_score',
    'roe', 'roce', 'npm', 'de_ratio', 'icr', 'fcf', 'fcf_cagr_5yr',
    'cfo_pat_ratio', 'rev_cagr_5yr', 'rev_cagr_3yr', 'pat_cagr_5yr',
    'pe_ratio', 'pb_ratio', 'div_yield', 'div_payout', 'revenue'
]

def export_screener_output(df_universe: pd.DataFrame, output_path: str = "output/screener_output.xlsx"):
    """Export 6 preset sheets to screener_output.xlsx with cell-level threshold color coding."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    engine = ScreenerEngine()
    
    wb = openpyxl.Workbook()
    wb.remove(wb.active) # Remove default initial sheet
    
    presets = engine.config.get('presets', {})
    
    for preset_key, preset_info in presets.items():
        preset_name = preset_info['name']
        criteria = preset_info['criteria']
        
        # Filter data
        filtered_df = engine.apply_filters(df_universe, criteria)
        
        # Select available KPI columns
        cols_to_write = [c for c in KPI_COLUMNS if c in filtered_df.columns]
        export_df = filtered_df[cols_to_write].copy()
        
        ws = wb.create_sheet(title=preset_name[:31]) # Excel sheet title length limit
        ws.views.sheetView[0].showGridLines = True
        
        # Write Header
        ws.append(cols_to_write)
        for col_idx in range(1, len(cols_to_write) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = HEADER_FILL
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")

        # Write Rows & Apply Conditional Formatting
        for row_idx, record in enumerate(export_df.to_dict('records'), start=2):
            for col_idx, col_name in enumerate(cols_to_write, start=1):
                val = record[col_name]
                cell = ws.cell(row=row_idx, column=col_idx, value=val if val != float('inf') else "Debt Free")
                
                # Check threshold pass/fail for styling
                min_key = f"{col_name}_min"
                max_key = f"{col_name}_max"
                
                if min_key in criteria and isinstance(val, (int, float)):
                    cell.fill = GREEN_FILL if val >= criteria[min_key] else RED_FILL
                elif max_key in criteria and isinstance(val, (int, float)):
                    cell.fill = GREEN_FILL if val <= criteria[max_key] else RED_FILL
                elif col_name == 'de_ratio' and 'de_ratio_max' in criteria:
                    # Skip check if sector is financial
                    sector_val = record.get('broad_sector', record.get('sector', ''))
                    if sector_val in ["Financials", "Banking", "NBFC"]:
                        cell.fill = GREEN_FILL
                    elif isinstance(val, (int, float)):
                        cell.fill = GREEN_FILL if val <= criteria['de_ratio_max'] else RED_FILL

    wb.save(output_path)
    print(f"Successfully generated {output_path} with 6 preset sheets.")

if __name__ == "__main__":
    # Test script with mock universe data
    np.random.seed(42)
    sectors = ["IT Services", "Financials", "Consumer Goods", "Manufacturing", "Pharma"]
    
    mock_universe = pd.DataFrame({
        "company_id": [f"COMP_{i:02d}" for i in range(1, 93)],
        "company_name": [f"Company {i}" for i in range(1, 93)],
        "broad_sector": np.random.choice(sectors, 92),
        "roe": np.random.uniform(5, 30, 92),
        "roce": np.random.uniform(5, 25, 92),
        "npm": np.random.uniform(2, 20, 92),
        "de_ratio": np.random.uniform(0, 3, 92),
        "icr": np.random.choice([2.5, 5.0, 10.0, "Debt Free"], 92),
        "fcf": np.random.uniform(-50, 500, 92),
        "fcf_cagr_5yr": np.random.uniform(-5, 25, 92),
        "cfo_pat_ratio": np.random.uniform(0.5, 1.5, 92),
        "rev_cagr_5yr": np.random.uniform(2, 25, 92),
        "rev_cagr_3yr": np.random.uniform(2, 20, 92),
        "pat_cagr_5yr": np.random.uniform(2, 30, 92),
        "pe_ratio": np.random.uniform(8, 45, 92),
        "pb_ratio": np.random.uniform(0.8, 6.0, 92),
        "div_yield": np.random.uniform(0, 4.0, 92),
        "div_payout": np.random.uniform(10, 90, 92),
        "revenue": np.random.uniform(1000, 20000, 92),
        "de_ratio_yoy_change": np.random.uniform(-0.5, 0.5, 92)
    })
    
    export_screener_output(mock_universe)