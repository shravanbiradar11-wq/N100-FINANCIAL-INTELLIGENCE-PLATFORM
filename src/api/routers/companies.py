from fastapi import APIRouter, HTTPException
from src.dashboard.utils.db import get_companies, get_ratios

router = APIRouter()

@router.get("/companies")
def list_companies(sector: str = None, search: str = None):
    df_comps = get_companies()
    if sector:
        df_comps = df_comps[df_comps['sector'].astype(str).str.lower() == sector.lower()]
    if search:
        df_comps = df_comps[
            df_comps['ticker'].str.contains(search, case=False, na=False) |
            df_comps['company_id'].str.contains(search, case=False, na=False)
        ]
    return df_comps.to_dict(orient="records")

@router.get("/companies/{ticker}")
def get_company_profile(ticker: str):
    df_comps = get_companies()
    match = df_comps[df_comps['ticker'].str.upper() == ticker.upper()]
    if match.empty:
        match = df_comps[df_comps['company_id'].str.upper() == ticker.upper()]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    return match.iloc[0].to_dict()
