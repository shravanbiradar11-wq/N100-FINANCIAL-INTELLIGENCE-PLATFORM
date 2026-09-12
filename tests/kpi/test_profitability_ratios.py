import pytest

from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    calculate_roe,
    calculate_roce,
    calculate_roa,
    check_opm_mismatch,
)


# ============================================================
# TEST 1 - NET PROFIT MARGIN: NORMAL CASE
# ============================================================

def test_net_profit_margin_normal():

    result = calculate_net_profit_margin(
        net_profit=200,
        sales=1000,
    )

    assert result == pytest.approx(20.0)


# ============================================================
# TEST 2 - NET PROFIT MARGIN: ZERO SALES
# ============================================================

def test_net_profit_margin_zero_sales():

    result = calculate_net_profit_margin(
        net_profit=200,
        sales=0,
    )

    assert result is None


# ============================================================
# TEST 3 - OPERATING PROFIT MARGIN: NORMAL CASE
# ============================================================

def test_operating_profit_margin_normal():

    result = calculate_operating_profit_margin(
        operating_profit=250,
        sales=1000,
    )

    assert result == pytest.approx(25.0)


# ============================================================
# TEST 4 - OPM CROSS-CHECK: MISMATCH
# ============================================================

def test_opm_cross_check_mismatch():

    calculated_opm = calculate_operating_profit_margin(
        operating_profit=250,
        sales=1000,
    )

    result = check_opm_mismatch(
        calculated_opm=calculated_opm,
        source_opm=20.0,
    )

    assert result is True


# ============================================================
# TEST 5 - RETURN ON EQUITY: NORMAL CASE
# ============================================================

def test_roe_normal():

    result = calculate_roe(
        net_profit=200,
        equity_capital=500,
        reserves=500,
    )

    assert result == pytest.approx(20.0)


# ============================================================
# TEST 6 - RETURN ON EQUITY: NEGATIVE EQUITY
# ============================================================

def test_roe_negative_equity():

    result = calculate_roe(
        net_profit=200,
        equity_capital=-600,
        reserves=500,
    )

    assert result is None


# ============================================================
# TEST 7 - RETURN ON CAPITAL EMPLOYED: NORMAL CASE
# ============================================================

def test_roce_normal():

    result = calculate_roce(
        ebit=300,
        equity_capital=500,
        reserves=500,
        borrowings=1000,
    )

    assert result == pytest.approx(15.0)


# ============================================================
# TEST 8 - RETURN ON ASSETS: ZERO ASSETS
# ============================================================

def test_roa_zero_assets():

    result = calculate_roa(
        net_profit=200,
        total_assets=0,
    )

    assert result is None