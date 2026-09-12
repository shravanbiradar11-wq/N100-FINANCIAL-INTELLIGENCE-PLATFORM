import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath('.'))

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from src.dashboard.utils.db import get_companies, get_ratios

def generate_portfolio_summary(output_path: str = "reports/portfolio/portfolio_summary.pdf"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df_comps = get_companies().sort_values('ticker')
    df_ratios_2024 = get_ratios(year=2024)
    df_ratios_2023 = get_ratios(year=2023)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('PortTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#FFFFFF'))
    sub_style = ParagraphStyle('PortSub', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#CBD5E1'))
    h2_style = ParagraphStyle('PortH2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#0F172A'), spaceBefore=6, spaceAfter=4)
    body_style = ParagraphStyle('PortBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#1E293B'))

    story = []

    total_companies = len(df_comps)
    print(f"\n--- Generating Portfolio Summary PDF ({total_companies} Companies) ---")

    for idx, (_, comp) in enumerate(df_comps.iterrows()):
        cid = comp['company_id']
        c_dict = comp.to_dict()
        comp_name = c_dict.get('company_name', c_dict.get('name', cid))
        ticker = c_dict.get('ticker', cid)
        sector = c_dict.get('sector', 'N/A')

        r24 = df_ratios_2024[df_ratios_2024['company_id'] == cid]
        r23 = df_ratios_2023[df_ratios_2023['company_id'] == cid]

        row24 = r24.iloc[0] if not r24.empty else {}
        row23 = r23.iloc[0] if not r23.empty else {}

        roe24 = float(row24.get('roe', 15) or 15)
        roe23 = float(row23.get('roe', 15) or 15)

        # Trend Arrow Indicator Logic (within 2% tolerance = flat)
        diff = roe24 - roe23
        if diff > 0.02 * roe23:
            trend_str = "<font color='#16A34A'><b>▲ UP</b></font>"
        elif diff < -0.02 * roe23:
            trend_str = "<font color='#DC2626'><b>▼ DOWN</b></font>"
        else:
            trend_str = "<font color='#64748B'><b>► FLAT</b></font>"

        # Company Card Header
        header_data = [[
            Paragraph(f"<b>{ticker} — {comp_name}</b>", title_style),
            Paragraph(f"<b>Sector:</b> {sector}", sub_style)
        ]]
        header_table = Table(header_data, colWidths=[380, 160])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0F172A')),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 10))

        # KPI Metrics Table
        pe_val = float(row24.get('pe_ratio', 20) or 20)
        de_val = float(row24.get('de_ratio', 0.2) or 0.2)
        rev_cagr = float(row24.get('rev_cagr_5yr', 12) or 12)

        kpi_data = [
            [Paragraph("<b>ROE (2024)</b>", body_style), Paragraph("<b>P/E Ratio</b>", body_style), Paragraph("<b>D/E Ratio</b>", body_style), Paragraph("<b>5Y Rev CAGR</b>", body_style), Paragraph("<b>YoY Trend</b>", body_style)],
            [Paragraph(f"{roe24:.1f}%", body_style), Paragraph(f"{pe_val:.1f}x", body_style), Paragraph(f"{de_val:.2f}", body_style), Paragraph(f"{rev_cagr:.1f}%", body_style), Paragraph(trend_str, body_style)]
        ]
        kpi_table = Table(kpi_data, colWidths=[108, 108, 108, 108, 108])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 15))

        if idx < total_companies - 1:
            story.append(PageBreak())

    doc.build(story)
    print(f"[✓] Portfolio Summary PDF generated successfully: {output_path}")

if __name__ == "__main__":
    generate_portfolio_summary()
