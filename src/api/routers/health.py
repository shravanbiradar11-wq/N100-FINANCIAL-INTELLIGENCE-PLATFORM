import time
from fastapi import APIRouter
from src.dashboard.utils.db import get_companies, get_ratios

router = APIRouter()
START_TIME = time.time()

@router.get("/health")
def health_check():
    df_comps = get_companies()
    df_ratios = get_ratios()
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "db_row_counts": {
            "companies": len(df_comps),
            "financial_ratios": len(df_ratios)
        }
    }
