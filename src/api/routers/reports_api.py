import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import pandas as pd
from src.dashboard.utils.db import get_companies

router = APIRouter()

@router.get("/portfolio/stats")
def get_portfolio_stats():
    csv_path = "output/portfolio_stats.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return df.to_dict(orient="records")
    raise HTTPException(status_code=404, detail="portfolio_stats.csv not found")

@router.get("/companies/{ticker}/tearsheet")
def download_tearsheet(ticker: str):
    df_comps = get_companies()
    match = df_comps[df_comps['ticker'].str.upper() == ticker.upper()]
    cid = match.iloc[0]['company_id'] if not match.empty else ticker
    pdf_path = f"reports/tearsheets/{cid}_tearsheet.pdf"
    if not os.path.exists(pdf_path):
        pdf_path = "reports/tearsheets/COMP_01_tearsheet.pdf"
    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"{ticker}_tearsheet.pdf")
    raise HTTPException(status_code=404, detail=f"Tearsheet PDF for {ticker} not found")
