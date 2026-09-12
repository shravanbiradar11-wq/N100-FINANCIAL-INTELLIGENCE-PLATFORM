import pytest

from src.etl.normaliser import normalize_year, normalize_ticker


# ==========================================
# TESTS FOR normalize_year()
# ==========================================

@pytest.mark.parametrize(
    "value, expected",
    [
        (2024, 2024),
        (2023, 2023),
        (2022, 2022),
        (2024.0, 2024),
        (2023.0, 2023),
        ("2024", 2024),
        ("FY24", 2024),
        ("FY23", 2023),
        (" FY24 ", 2024),
        ("FY 24", 2024),
        ("FY2024", 2024),
        ("2023-24", 2024),
        ("2022-23", 2023),
        ("2023/24", 2024),
        ("2022/23", 2023),
        ("FY23-24", 2024),
        ("FY22-23", 2023),
        ("1999", 1999),
        (None, None),
        ("", None),
        ("INVALID", None),
        ("ABC", None),
    ],
)
def test_normalize_year(value, expected):
    assert normalize_year(value) == expected


# ==========================================
# TESTS FOR normalize_ticker()
# ==========================================

@pytest.mark.parametrize(
    "value, expected",
    [
        ("RELIANCE", "RELIANCE"),
        ("reliance", "RELIANCE"),
        ("Reliance", "RELIANCE"),
        (" RELIANCE ", "RELIANCE"),
        ("RELIANCE.NS", "RELIANCE"),
        ("reliance.ns", "RELIANCE"),
        ("RELIANCE.BO", "RELIANCE"),
        ("TCS-EQ", "TCS"),
        ("INFY.NS", "INFY"),
        ("HDFCBANK.NS", "HDFCBANK"),
        ("SBIN.BO", "SBIN"),
        ("ICICIBANK", "ICICIBANK"),
        ("MARUTI", "MARUTI"),
        ("BAJFINANCE.NS", "BAJFINANCE"),
        ("SUNPHARMA.NS", "SUNPHARMA"),
        (None, None),
        ("", None),
        ("   ", None),
    ],
)
def test_normalize_ticker(value, expected):
    assert normalize_ticker(value) == expected