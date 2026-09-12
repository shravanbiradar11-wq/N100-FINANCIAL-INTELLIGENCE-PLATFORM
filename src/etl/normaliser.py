import re
import pandas as pd
import numpy as np


def normalize_year(value):
    """
    Convert year values into a standard integer.

    Examples:
    2024       -> 2024
    2024.0     -> 2024
    FY24       -> 2024
    FY 2024    -> 2024
    2023-24    -> 2024
    2023/24    -> 2024

    Returns:
        int or None
    """

    # Missing value
    if pd.isna(value):
        return None

    # Integer
    if isinstance(value, (int, np.integer)):
        return int(value)

    # Float
    if isinstance(value, (float, np.floating)):

        if np.isnan(value):
            return None

        return int(value)

    # Convert to string
    value = str(value).strip().upper()

    # Remove spaces
    value = re.sub(r"\s+", "", value)

    # Remove FY
    value = value.replace("FY", "")

    # Find year-like numbers
    numbers = re.findall(r"\d{2,4}", value)

    if not numbers:
        return None

    # Use ending year
    year_value = numbers[-1]

    # Four digit year
    if len(year_value) == 4:

        year = int(year_value)

        if 1900 <= year <= 2100:
            return year

        return None

    # Two digit year
    if len(year_value) == 2:

        year = int(year_value)

        if year <= 50:
            return 2000 + year

        return 1900 + year

    return None

def normalize_ticker(value):
    """
    Standardize stock ticker values.

    Examples:
    reliance       -> RELIANCE
    RELIANCE.NS    -> RELIANCE
    RELIANCE.BO    -> RELIANCE
    """

    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    # Remove all extra spaces
    value = re.sub(r"\s+", "", value)

    # Remove exchange suffixes
    suffixes = [
        ".NS",
        ".BO",
        "-EQ"
    ]

    for suffix in suffixes:

        if value.endswith(suffix):
            value = value[:-len(suffix)]

    if value == "":
        return None

    return value

def normalize_text(value):
    """
    Remove unnecessary whitespace from text.
    """

    if pd.isna(value):
        return None

    value = str(value)

    # Replace multiple spaces/newlines/tabs
    value = re.sub(
        r"\s+",
        " ",
        value
    )

    value = value.strip()

    if value == "":
        return None

    return value

def normalize_dataframe(df):
    """
    Normalize a DataFrame using the existing year and ticker
    normalization functions.
    """
    result = df.copy()

    if "year" in result.columns:
        result["year"] = result["year"].apply(normalize_year)

    if "ticker" in result.columns:
        result["ticker"] = result["ticker"].apply(normalize_ticker)

    return result