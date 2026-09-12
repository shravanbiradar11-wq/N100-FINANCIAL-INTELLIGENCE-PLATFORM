import pytest

from src.analytics.ratios import (
    calculate_debt_to_equity,
    calculate_high_leverage_flag,
    calculate_interest_coverage,
    get_icr_label,
    calculate_icr_warning,
    calculate_net_debt,
    calculate_asset_turnover,
)


# ============================================================
# TEST 1 - DEBT FREE D/E
# ============================================================

def test_debt_to_equity_debt_free():

    result = calculate_debt_to_equity(
        borrowings=0,
        equity_capital=500,
        reserves=500,
    )

    assert result == 0


# ============================================================
# TEST 2 - NORMAL D/E
# ============================================================

def test_debt_to_equity_normal():

    result = calculate_debt_to_equity(
        borrowings=500,
        equity_capital=500,
        reserves=500,
    )

    assert result == pytest.approx(0.5)


# ============================================================
# TEST 3 - HIGH D/E FLAG
# ============================================================

def test_high_debt_to_equity_flag():

    result = calculate_high_leverage_flag(
        debt_to_equity=6,
        broad_sector="Industrials",
    )

    assert result is True


# ============================================================
# TEST 4 - FINANCIALS HIGH D/E SUPPRESSED
# ============================================================

def test_financials_high_leverage_suppressed():

    result = calculate_high_leverage_flag(
        debt_to_equity=10,
        broad_sector="Financials",
    )

    assert result is False


# ============================================================
# TEST 5 - ICR INTEREST ZERO
# ============================================================

def test_interest_coverage_zero_interest():

    result = calculate_interest_coverage(
        operating_profit=500,
        other_income=100,
        interest=0,
    )

    assert result is None


# ============================================================
# TEST 6 - ICR DEBT FREE LABEL
# ============================================================

def test_icr_debt_free_label():

    icr = calculate_interest_coverage(
        operating_profit=500,
        other_income=100,
        interest=0,
    )

    label = get_icr_label(icr)

    assert label == "Debt Free"


# ============================================================
# TEST 7 - ICR WARNING
# ============================================================

def test_icr_warning():

    result = calculate_icr_warning(
        interest_coverage=1.2
    )

    assert result is True


# ============================================================
# TEST 8 - NORMAL ASSET TURNOVER
# ============================================================

def test_asset_turnover_normal():

    result = calculate_asset_turnover(
        sales=2000,
        total_assets=1000,
    )

    assert result == pytest.approx(2.0)