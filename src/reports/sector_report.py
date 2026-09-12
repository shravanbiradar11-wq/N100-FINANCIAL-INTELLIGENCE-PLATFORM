import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath('.'))

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from src.dashboard.utils.db import get_companies, get_ratios

def generate_sector_report(sector_name: str, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df_comps = get_companies()
    df_ratios = get_ratios(year=2024)
    
    sector_comps = df_comps[df_comps['sector'].astype(str).str.lower() == sector_name.lower()]
    c_ids = sector_comps['company_id'].tolist()
    
    sec_ratios = df_ratios[df_ratios['company_id'].isin(c_ids)]
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('SecTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#FFFFFF'))
    body_style = ParagraphStyle('SecBody', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#1E293B'))
    header_col_style = ParagraphStyle('SecHCol', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor('#FFFFFF'))

    story = []

    # Sector Header
    header_data = [[Paragraph(f"<b>SECTOR ANALYSIS REPORT: {sector_name.upper()}</b>", title_style)]]
    header_table = Table(header_data, colWidths=[540])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0F172A')),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # Sector Overview Metrics Table
    if not sec_ratios.empty:
        med_roe = sec_ratios['roe'].median()
        med_pe = sec_ratios['pe_ratio'].median()
        med_de = sec_ratios['de_ratio'].median()
        comp_count = len(sec_ratios)
    else:
        med_roe, med_pe, med_de, comp_count = 0, 0, 0, 0

    summary_data = [
        [Paragraph("<b>Total Companies</b>", body_style), Paragraph("<b>Median ROE</b>", body_style), Paragraph("<b>Median P/E</b>", body_style), Paragraph("<b>Median D/E</b>", body_style)],
        [Paragraph(f"<b>{comp_count}</b>", body_style), Paragraph(f"<b>{med_roe:.1f}%</b>", body_style), Paragraph(f"<b>{med_pe:.1f}x</b>", body_style), Paragraph(f"<b>{med_de:.2f}</b>", body_style)]
    ]
    summary_table = Table(summary_data, colWidths=[135, 135, 135, 135])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # Company Breakdown List Table
    table_headers = [
        Paragraph("<b>ID</b>", header_col_style),
        Paragraph("<b>Ticker</b>", header_col_style),
        Paragraph("<b>ROE (%)</b>", header_col_style),
        Paragraph("<b>P/E (x)</b>", header_col_style),
        Paragraph("<b>D/E</b>", header_col_style),
        Paragraph("<b>5Y Rev CAGR</b>", header_col_style)
    ]
    
    rows = [table_headers]
    for _, r in sec_ratios.iterrows():
        rows.append([
            Paragraph(str(r.get('company_id', '')), body_style),
            Paragraph(str(r.get('ticker', '')), body_style),
            Paragraph(f"{float(r.get('roe', 0) or 0):.1f}%", body_style),
            Paragraph(f"{float(r.get('pe_ratio', 0) or 0):.1f}x", body_style),
            Paragraph(f"{float(r.get('de_ratio', 0) or 0):.2f}", body_style),
            Paragraph(f"{float(r.get('rev_cagr_5yr', 0) or 0):.1f}%", body_style)
        ])
        
    comp_table = Table(rows, colWidths=[80, 100, 90, 90, 80, 100])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284C7')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(comp_table)

    doc.build(story)
    print(f"[✓] Sector PDF created: {output_path}")

if __name__ == "__main__":
    generate_sector_report("IT", "reports/sector/IT_report.pdf")
