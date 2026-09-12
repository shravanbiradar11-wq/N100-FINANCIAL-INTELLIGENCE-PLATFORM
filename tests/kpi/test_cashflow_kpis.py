import pytest
from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_cfo_pat_ratio,
    classify_cfo_quality,
    classify_capex_intensity
)

def test_calculate_free_cash_flow():
    assert calculate_free_cash_flow(1000, 200) == 800
    assert calculate_free_cash_flow(500, -100) == 400

def test_calculate_cfo_pat_ratio():
    assert calculate_cfo_pat_ratio(120, 100) == 1.2
    assert calculate_cfo_pat_ratio(50, 0) == 1.0

def test_classify_cfo_quality():
    score, label = classify_cfo_quality(150, 100)
    assert label == "High Quality"
    score, label = classify_cfo_quality(80, 100)
    assert label == "Moderate"
    score, label = classify_cfo_quality(30, 100)
    assert label == "Accrual Risk"

def test_classify_capex_intensity():
    pct, label = classify_capex_intensity(20, 1000)
    assert label == "Asset Light"
    pct, label = classify_capex_intensity(50, 1000)
    assert label == "Moderate"
    pct, label = classify_capex_intensity(100, 1000)
    assert label == "Capital Intensive"
