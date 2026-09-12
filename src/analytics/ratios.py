"""
Sprint 2 - Day 09
Financial Ratio Engine

Day 08:
    - Net Profit Margin
    - Operating Profit Margin
    - ROE
    - ROCE
    - ROA

Day 09:
    - Debt-to-Equity
    - High Leverage Flag
    - Interest Coverage Ratio
    - Interest Coverage Label
    - Interest Coverage Warning
    - Net Debt
    - Asset Turnover
"""

from __future__ import annotations

from typing import Optional


# ============================================================
# HELPER
# ============================================================

def _safe_float(value) -> Optional[float]:
    """Convert value to float. Return None for invalid values."""

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ============================================================
# DAY 08 - PROFITABILITY RATIOS
# ============================================================

def calculate_net_profit_margin(
    net_profit,
    sales,
) -> Optional[float]:

    net_profit = _safe_float(net_profit)
    sales = _safe_float(sales)

    if net_profit is None or sales is None:
        return None

    if sales == 0:
        return None

    return (net_profit / sales) * 100


def calculate_operating_profit_margin(
    operating_profit,
    sales,
) -> Optional[float]:

    operating_profit = _safe_float(
        operating_profit
    )

    sales = _safe_float(sales)

    if operating_profit is None or sales is None:
        return None

    if sales == 0:
        return None

    return (operating_profit / sales) * 100


def check_opm_mismatch(
    calculated_opm,
    source_opm,
    threshold=1.0,
) -> bool:

    calculated_opm = _safe_float(
        calculated_opm
    )

    source_opm = _safe_float(
        source_opm
    )

    if calculated_opm is None or source_opm is None:
        return False

    return abs(
        calculated_opm - source_opm
    ) > threshold


def calculate_roe(
    net_profit,
    equity_capital,
    reserves,
) -> Optional[float]:

    net_profit = _safe_float(net_profit)
    equity_capital = _safe_float(equity_capital)
    reserves = _safe_float(reserves)

    if (
        net_profit is None
        or equity_capital is None
        or reserves is None
    ):
        return None

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return (net_profit / equity) * 100


def calculate_roce(
    ebit,
    equity_capital,
    reserves,
    borrowings,
) -> Optional[float]:

    ebit = _safe_float(ebit)
    equity_capital = _safe_float(equity_capital)
    reserves = _safe_float(reserves)
    borrowings = _safe_float(borrowings)

    if (
        ebit is None
        or equity_capital is None
        or reserves is None
        or borrowings is None
    ):
        return None

    capital_employed = (
        equity_capital
        + reserves
        + borrowings
    )

    if capital_employed <= 0:
        return None

    return (ebit / capital_employed) * 100


def calculate_roa(
    net_profit,
    total_assets,
) -> Optional[float]:

    net_profit = _safe_float(net_profit)
    total_assets = _safe_float(total_assets)

    if net_profit is None or total_assets is None:
        return None

    if total_assets == 0:
        return None

    return (net_profit / total_assets) * 100


# ============================================================
# DAY 09 - DEBT TO EQUITY
# ============================================================

def calculate_debt_to_equity(
    borrowings,
    equity_capital,
    reserves,
) -> Optional[float]:
    """
    Debt-to-Equity

    Formula:
        borrowings / (equity_capital + reserves)

    Special case:
        borrowings == 0 -> 0

    Invalid/negative equity:
        return None
    """

    borrowings = _safe_float(borrowings)
    equity_capital = _safe_float(equity_capital)
    reserves = _safe_float(reserves)

    if (
        borrowings is None
        or equity_capital is None
        or reserves is None
    ):
        return None

    if borrowings == 0:
        return 0.0

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return borrowings / equity


# ============================================================
# HIGH LEVERAGE FLAG
# ============================================================

def calculate_high_leverage_flag(
    debt_to_equity,
    broad_sector=None,
) -> bool:
    """
    High leverage warning.

    D/E > 5 is considered high leverage.

    Financials are excluded because high leverage
    is structurally normal for banks/NBFCs/insurance.
    """

    debt_to_equity = _safe_float(
        debt_to_equity
    )

    if debt_to_equity is None:
        return False

    if (
        broad_sector is not None
        and str(broad_sector).strip().lower()
        == "financials"
    ):
        return False

    return debt_to_equity > 5


# ============================================================
# INTEREST COVERAGE RATIO
# ============================================================

def calculate_interest_coverage(
    operating_profit,
    other_income,
    interest,
) -> Optional[float]:
    """
    Interest Coverage Ratio

    Formula:
        (operating_profit + other_income) / interest

    Special case:
        interest == 0 -> None

    A None value is treated as Debt Free by the
    separate label function.
    """

    operating_profit = _safe_float(
        operating_profit
    )

    other_income = _safe_float(
        other_income
    )

    interest = _safe_float(
        interest
    )

    if (
        operating_profit is None
        or other_income is None
        or interest is None
    ):
        return None

    if interest == 0:
        return None

    return (
        operating_profit + other_income
    ) / interest


# ============================================================
# INTEREST COVERAGE LABEL
# ============================================================

def get_icr_label(
    interest_coverage,
) -> Optional[str]:
    """
    Return 'Debt Free' when ICR is None.

    Otherwise return None because the numeric ICR
    itself is sufficient for display.
    """

    if interest_coverage is None:
        return "Debt Free"

    return None


# ============================================================
# INTEREST COVERAGE WARNING
# ============================================================

def calculate_icr_warning(
    interest_coverage,
) -> bool:
    """
    Warning when ICR < 1.5.

    None means the company has no interest expense,
    so no warning is generated.
    """

    interest_coverage = _safe_float(
        interest_coverage
    )

    if interest_coverage is None:
        return False

    return interest_coverage < 1.5


# ============================================================
# NET DEBT
# ============================================================

def calculate_net_debt(
    borrowings,
    investments,
) -> Optional[float]:
    """
    Net Debt

    Formula:
        borrowings - investments

    Investments are used as a liquid asset proxy.
    """

    borrowings = _safe_float(
        borrowings
    )

    investments = _safe_float(
        investments
    )

    if (
        borrowings is None
        or investments is None
    ):
        return None

    return borrowings - investments


# ============================================================
# ASSET TURNOVER
# ============================================================

def calculate_asset_turnover(
    sales,
    total_assets,
) -> Optional[float]:
    """
    Asset Turnover

    Formula:
        sales / total_assets

    Edge case:
        total_assets == 0 -> None
    """

    sales = _safe_float(sales)
    total_assets = _safe_float(
        total_assets
    )

    if sales is None or total_assets is None:
        return None

    if total_assets == 0:
        return None

    return sales / total_assets


# ============================================================
# DAY 09 RATIO BUNDLE
# ============================================================

def calculate_leverage_efficiency_ratios(
    *,
    borrowings,
    equity_capital,
    reserves,
    operating_profit,
    other_income,
    interest,
    investments,
    sales,
    total_assets,
    broad_sector=None,
) -> dict:
    """
    Calculate all Day-09 leverage and efficiency KPIs.
    """

    debt_to_equity = calculate_debt_to_equity(
        borrowings=borrowings,
        equity_capital=equity_capital,
        reserves=reserves,
    )

    high_leverage_flag = calculate_high_leverage_flag(
        debt_to_equity=debt_to_equity,
        broad_sector=broad_sector,
    )

    interest_coverage = calculate_interest_coverage(
        operating_profit=operating_profit,
        other_income=other_income,
        interest=interest,
    )

    icr_label = get_icr_label(
        interest_coverage
    )

    icr_warning = calculate_icr_warning(
        interest_coverage
    )

    net_debt = calculate_net_debt(
        borrowings=borrowings,
        investments=investments,
    )

    asset_turnover = calculate_asset_turnover(
        sales=sales,
        total_assets=total_assets,
    )

    return {
        "debt_to_equity": debt_to_equity,
        "high_leverage_flag": high_leverage_flag,
        "interest_coverage": interest_coverage,
        "icr_label": icr_label,
        "icr_warning_flag": icr_warning,
        "net_debt_cr": net_debt,
        "asset_turnover": asset_turnover,
    }


# ============================================================
# COMPLETE RATIO BUNDLE
# ============================================================

def calculate_all_ratios(
    *,
    net_profit,
    sales,
    operating_profit,
    source_opm,
    equity_capital,
    reserves,
    ebit,
    borrowings,
    total_assets,
    other_income,
    interest,
    investments,
    broad_sector=None,
) -> dict:
    """
    Calculate all Day-08 and Day-09 ratios.
    """

    profitability = {
        "net_profit_margin_pct":
            calculate_net_profit_margin(
                net_profit,
                sales,
            ),

        "operating_profit_margin_pct":
            calculate_operating_profit_margin(
                operating_profit,
                sales,
            ),

        "return_on_equity_pct":
            calculate_roe(
                net_profit,
                equity_capital,
                reserves,
            ),

        "return_on_capital_employed_pct":
            calculate_roce(
                ebit,
                equity_capital,
                reserves,
                borrowings,
            ),

        "return_on_assets_pct":
            calculate_roa(
                net_profit,
                total_assets,
            ),
    }

    profitability["opm_mismatch_flag"] = (
        check_opm_mismatch(
            profitability[
                "operating_profit_margin_pct"
            ],
            source_opm,
        )
    )

    leverage = calculate_leverage_efficiency_ratios(
        borrowings=borrowings,
        equity_capital=equity_capital,
        reserves=reserves,
        operating_profit=operating_profit,
        other_income=other_income,
        interest=interest,
        investments=investments,
        sales=sales,
        total_assets=total_assets,
        broad_sector=broad_sector,
    )

    return {
        **profitability,
        **leverage,
    }