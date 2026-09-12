from fastapi import APIRouter, HTTPException
from src.dashboard.utils.db import get_companies, get_ratios

router = APIRouter()

@router.get("/sectors")
def list_sectors():
    df_comps = get_companies()
    df_ratios = get_ratios(year=2024)
    df = df_ratios.merge(df_comps[['company_id', 'sector']], on='company_id', how='left')
    
    sectors_list = []
    for sec, group in df.groupby('sector'):
        sectors_list.append({
            "sector": sec,
            "company_count": len(group),
            "median_roe": round(group['roe'].median(), 2) if 'roe' in group else 0,
            "median_pe": round(group['pe_ratio'].median(), 2) if 'pe_ratio' in group else 0,
            "median_de": round(group['de_ratio'].median(), 2) if 'de_ratio' in group else 0
        })
    return sectors_list

@router.get("/sectors/{sector_name}/companies")
def get_sector_companies(sector_name: str):
    df_comps = get_companies()
    df_ratios = get_ratios(year=2024)
    sec_comps = df_comps[df_comps['sector'].astype(str).str.lower() == sector_name.lower()]
    if sec_comps.empty:
        raise HTTPException(status_code=404, detail=f"Sector '{sector_name}' not found")
    merged = sec_comps.merge(df_ratios, on='company_id', how='left')
    return merged.to_dict(orient="records")
