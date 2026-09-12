import pytest

from src.analytics.cagr import (
    calculate_cagr,
    calculate_cagr_with_flag,
    calculate_cagr_from_years,
    calculate_company_cagrs,
    FLAG_DECLINE_TO_LOSS,
    FLAG_TURNAROUND,
    FLAG_BOTH_NEGATIVE,
    FLAG_ZERO_BASE,
    FLAG_INSUFFICIENT,
)


# ============================================================
# TEST 1 - NORMAL CAGR
# ============================================================

def test_normal_cagr():

    result = calculate_cagr(
        start_value=100,
        end_value=121,
        years=2,
    )

    assert result == pytest.approx(10.0)


# ============================================================
# TEST 2 - POSITIVE TO NEGATIVE
# ============================================================

def test_decline_to_loss():

    value, flag = calculate_cagr_with_flag(
        start_value=100,
        end_value=-20,
        years=3,
    )

    assert value is None
    assert flag == FLAG_DECLINE_TO_LOSS


# ============================================================
# TEST 3 - NEGATIVE TO POSITIVE
# ============================================================

def test_turnaround():

    value, flag = calculate_cagr_with_flag(
        start_value=-100,
        end_value=200,
        years=3,
    )

    assert value is None
    assert flag == FLAG_TURNAROUND


# ============================================================
# TEST 4 - BOTH NEGATIVE
# ============================================================

def test_both_negative():

    value, flag = calculate_cagr_with_flag(
        start_value=-100,
        end_value=-150,
        years=3,
    )

    assert value is None
    assert flag == FLAG_BOTH_NEGATIVE


# ============================================================
# TEST 5 - ZERO BASE
# ============================================================

def test_zero_base():

    value, flag = calculate_cagr_with_flag(
        start_value=0,
        end_value=100,
        years=3,
    )

    assert value is None
    assert flag == FLAG_ZERO_BASE


# ============================================================
# TEST 6 - INSUFFICIENT DATA
# ============================================================

def test_insufficient_data():

    value, flag = calculate_cagr_from_years(
        values_by_year={
            2022: 100,
            2023: 110,
            2024: 120,
        },
        end_year=2024,
        window=5,
    )

    assert value is None
    assert flag == FLAG_INSUFFICIENT


# ============================================================
# TEST 7 - NORMAL 5-YEAR CAGR FROM YEARLY DATA
# ============================================================

def test_five_year_cagr():

    value, flag = calculate_cagr_from_years(
        values_by_year={
            2019: 100,
            2020: 110,
            2021: 120,
            2022: 130,
            2023: 140,
            2024: 161.051,
        },
        end_year=2024,
        window=5,
    )

    assert value == pytest.approx(
        10.0,
        abs=0.01,
    )

    assert flag is None


# ============================================================
# TEST 8 - ZERO BASE FROM YEARLY DATA
# ============================================================

def test_zero_base_from_yearly_data():

    value, flag = calculate_cagr_from_years(
        values_by_year={
            2019: 0,
            2020: 100,
            2021: 120,
            2022: 140,
            2023: 160,
            2024: 180,
        },
        end_year=2024,
        window=5,
    )

    assert value is None
    assert flag == FLAG_ZERO_BASE


# ============================================================
# TEST 9 - COMPANY CAGR OUTPUT
# ============================================================

def test_company_cagrs():

    revenue = {
        2019: 100,
        2020: 110,
        2021: 120,
        2022: 133.1,
        2023: 146.41,
        2024: 161.051,
    }

    pat = {
        2019: 50,
        2020: 55,
        2021: 60,
        2022: 66.55,
        2023: 73.205,
        2024: 80.5255,
    }

    eps = {
        2019: 10,
        2020: 11,
        2021: 12,
        2022: 13.31,
        2023: 14.641,
        2024: 16.1051,
    }

    result = calculate_company_cagrs(
        revenue_by_year=revenue,
        pat_by_year=pat,
        eps_by_year=eps,
        end_year=2024,
    )

    assert result["revenue_cagr_5yr"] == pytest.approx(
        10.0,
        abs=0.01,
    )

    assert result["pat_cagr_5yr"] == pytest.approx(
        10.0,
        abs=0.01,
    )

    assert result["eps_cagr_5yr"] == pytest.approx(
        10.0,
        abs=0.01,
    )


# ============================================================
# TEST 10 - CAGR FLAGS ARE STORED SEPARATELY
# ============================================================

def test_cagr_flag_separate_column():

    revenue = {
        2019: -100,
        2020: -90,
        2021: -80,
        2022: -70,
        2023: -60,
        2024: 100,
    }

    result = calculate_company_cagrs(
        revenue_by_year=revenue,
        pat_by_year={},
        eps_by_year={},
        end_year=2024,
    )

    assert result["revenue_cagr_5yr"] is None

    assert (
        result["revenue_cagr_5yr_flag"]
        == FLAG_TURNAROUND
    )

    assert "revenue_cagr_5yr" in result
    assert "revenue_cagr_5yr_flag" in result