"""
Sprint 2 - Day 10
CAGR Engine

Calculates Compound Annual Growth Rate for:
    - Revenue
    - PAT / Net Profit
    - EPS

Handles six required edge cases:
    1. Positive -> Positive
    2. Positive -> Negative
    3. Negative -> Positive
    4. Negative -> Negative
    5. Zero Base
    6. Insufficient Data

Formula:

    CAGR = ((end / start) ** (1 / n) - 1) * 100
"""

from __future__ import annotations

from typing import Optional, Tuple


# ============================================================
# CONSTANTS
# ============================================================

FLAG_DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
FLAG_TURNAROUND = "TURNAROUND"
FLAG_BOTH_NEGATIVE = "BOTH_NEGATIVE"
FLAG_ZERO_BASE = "ZERO_BASE"
FLAG_INSUFFICIENT = "INSUFFICIENT"


# ============================================================
# HELPER
# ============================================================

def _safe_float(value) -> Optional[float]:
    """Convert value to float safely."""

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ============================================================
# BASIC CAGR
# ============================================================

def calculate_cagr(
    start_value,
    end_value,
    years,
) -> Optional[float]:
    """
    Calculate standard CAGR.

    Formula:
        ((end / start) ** (1 / years) - 1) * 100

    This function is intended for valid
    positive -> positive values.

    Edge cases should be handled by
    calculate_cagr_with_flag().
    """

    start_value = _safe_float(start_value)
    end_value = _safe_float(end_value)

    try:
        years = int(years)
    except (TypeError, ValueError):
        return None

    if (
        start_value is None
        or end_value is None
    ):
        return None

    if years <= 0:
        return None

    if start_value <= 0 or end_value <= 0:
        return None

    return (
        ((end_value / start_value) ** (1 / years))
        - 1
    ) * 100


# ============================================================
# CAGR WITH EDGE-CASE FLAG
# ============================================================

def calculate_cagr_with_flag(
    start_value,
    end_value,
    years,
) -> Tuple[Optional[float], Optional[str]]:
    """
    Calculate CAGR and return an edge-case flag.

    Returns:

        (cagr_value, flag)

    Normal case:
        (value, None)

    Edge cases:
        (None, DECLINE_TO_LOSS)
        (None, TURNAROUND)
        (None, BOTH_NEGATIVE)
        (None, ZERO_BASE)
        (None, INSUFFICIENT)
    """

    start_value = _safe_float(start_value)
    end_value = _safe_float(end_value)

    try:
        years = int(years)
    except (TypeError, ValueError):
        return None, FLAG_INSUFFICIENT

    # --------------------------------------------------------
    # Missing / insufficient data
    # --------------------------------------------------------

    if (
        start_value is None
        or end_value is None
    ):
        return None, FLAG_INSUFFICIENT

    if years <= 0:
        return None, FLAG_INSUFFICIENT

    # --------------------------------------------------------
    # Zero base
    # --------------------------------------------------------

    if start_value == 0:
        return None, FLAG_ZERO_BASE

    # --------------------------------------------------------
    # Positive -> Negative
    # --------------------------------------------------------

    if (
        start_value > 0
        and end_value < 0
    ):
        return None, FLAG_DECLINE_TO_LOSS

    # --------------------------------------------------------
    # Negative -> Positive
    # --------------------------------------------------------

    if (
        start_value < 0
        and end_value > 0
    ):
        return None, FLAG_TURNAROUND

    # --------------------------------------------------------
    # Negative -> Negative
    # --------------------------------------------------------

    if (
        start_value < 0
        and end_value < 0
    ):
        return None, FLAG_BOTH_NEGATIVE

    # --------------------------------------------------------
    # Positive -> Positive
    # --------------------------------------------------------

    if (
        start_value > 0
        and end_value > 0
    ):
        cagr = calculate_cagr(
            start_value,
            end_value,
            years,
        )

        return cagr, None

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    return None, FLAG_INSUFFICIENT


# ============================================================
# YEAR AVAILABILITY CHECK
# ============================================================

def has_required_years(
    available_years,
    required_years,
) -> bool:
    """
    Check whether enough years of data exist.

    Example:

        available_years = [2020, 2021, 2022, 2023, 2024]
        required_years = 5

        -> True
    """

    if available_years is None:
        return False

    try:
        years = {
            int(year)
            for year in available_years
            if year is not None
        }
    except (TypeError, ValueError):
        return False

    return len(years) >= int(required_years)


# ============================================================
# CAGR FROM YEARLY DATA
# ============================================================

def calculate_cagr_from_years(
    values_by_year,
    end_year,
    window,
) -> Tuple[Optional[float], Optional[str]]:
    """
    Calculate CAGR using a dictionary of:

        {year: value}

    Example:

        {
            2020: 100,
            2021: 110,
            2022: 125,
            2023: 140,
            2024: 160,
        }

    For a 4-year CAGR ending in 2024:

        start year = 2020
        end year   = 2024
        years      = 4

    The function requires both the start and end year
    to be available.
    """

    if not values_by_year:
        return None, FLAG_INSUFFICIENT

    try:
        end_year = int(end_year)
        window = int(window)
    except (TypeError, ValueError):
        return None, FLAG_INSUFFICIENT

    if window <= 0:
        return None, FLAG_INSUFFICIENT

    normalized = {}

    for year, value in values_by_year.items():

        try:
            normalized[int(year)] = value
        except (TypeError, ValueError):
            continue

    start_year = end_year - window

    if (
        start_year not in normalized
        or end_year not in normalized
    ):
        return None, FLAG_INSUFFICIENT

    start_value = normalized[start_year]
    end_value = normalized[end_year]

    return calculate_cagr_with_flag(
        start_value=start_value,
        end_value=end_value,
        years=window,
    )


# ============================================================
# GENERIC GROWTH METRIC
# ============================================================

def calculate_growth_metric(
    values_by_year,
    end_year,
    window,
) -> dict:
    """
    Calculate a growth metric and return a structured result.

    Output:

        {
            "value": ...,
            "flag": ...,
            "start_year": ...,
            "end_year": ...,
            "years": ...
        }
    """

    try:
        end_year = int(end_year)
        window = int(window)
    except (TypeError, ValueError):

        return {
            "value": None,
            "flag": FLAG_INSUFFICIENT,
            "start_year": None,
            "end_year": None,
            "years": None,
        }

    start_year = end_year - window

    value, flag = calculate_cagr_from_years(
        values_by_year=values_by_year,
        end_year=end_year,
        window=window,
    )

    return {
        "value": value,
        "flag": flag,
        "start_year": start_year,
        "end_year": end_year,
        "years": window,
    }


# ============================================================
# COMPANY GROWTH METRICS
# ============================================================

def calculate_company_cagrs(
    revenue_by_year,
    pat_by_year,
    eps_by_year,
    end_year,
) -> dict:
    """
    Calculate Revenue, PAT and EPS CAGR for:

        3 years
        5 years
        10 years

    Returns a flat dictionary suitable for insertion
    into financial_ratios.
    """

    result = {}

    metrics = {
        "revenue": revenue_by_year,
        "pat": pat_by_year,
        "eps": eps_by_year,
    }

    for metric_name, values in metrics.items():

        for window in (3, 5, 10):

            value, flag = calculate_cagr_from_years(
                values_by_year=values,
                end_year=end_year,
                window=window,
            )

            result[
                f"{metric_name}_cagr_{window}yr"
            ] = value

            result[
                f"{metric_name}_cagr_{window}yr_flag"
            ] = flag

    return result