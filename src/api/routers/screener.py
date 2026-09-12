from fastapi import APIRouter, Query
from src.dashboard.utils.db import get_ratios

router = APIRouter()

@router.get("/screener")
def run_screener(
    min_roe: float = Query(None),
    max_de: float = Query(None),
    min_fcf: float = Query(None),
    sector: str = Query(None),
    min_rev_cagr_5yr: float = Query(None),
    min_pat_cagr_5yr: float = Query(None),
    max_pe: float = Query(None)
):
    df = get_ratios(year=2024)
    if df.empty:
        df = get_ratios()
        
    if min_roe is not None:
        df = df[df['roe'] >= min_roe]
    if max_de is not None:
        df = df[df['de_ratio'] <= max_de]
    if min_fcf is not None:
        df = df[df['fcf'] >= min_fcf]
    if min_rev_cagr_5yr is not None:
        df = df[df['rev_cagr_5yr'] >= min_rev_cagr_5yr]
    if min_pat_cagr_5yr is not None:
        df = df[df['pat_cagr_5yr'] >= min_pat_cagr_5yr]
    if max_pe is not None:
        df = df[df['pe_ratio'] <= max_pe]

    return df.to_dict(orient="records")
