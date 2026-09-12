from pathlib import Path
import re
import pandas as pd

from src.etl.normaliser import (
    normalize_year,
    normalize_ticker,
    normalize_text
)


# =========================================================
# LOAD EXCEL FILE
# =========================================================

def load_excel(file_path):
    """
    Load an Excel file.

    Excel structure:

    Row 0 -> Dataset title / metadata
    Row 1 -> Actual column names
    Row 2 -> First data record

    Therefore, header=1 is used.
    """

    file_path = Path(file_path)

    if not file_path.exists():

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    df = pd.read_excel(
        file_path,
        header=1
    )

    return df


# =========================================================
# NORMALIZE COLUMN NAMES
# =========================================================

def normalize_columns(df):
    """
    Standardize column names.

    Example:

    'Company Name' -> 'company_name'
    'Total Assets' -> 'total_assets'
    """

    df = df.copy()

    cleaned_columns = []

    for column in df.columns:

        column = str(column)

        column = column.strip()

        column = column.lower()

        # Replace spaces, / and - with underscore
        column = re.sub(
            r"[\s\-/]+",
            "_",
            column
        )

        # Remove special characters
        column = re.sub(
            r"[^a-z0-9_]",
            "",
            column
        )

        # Replace multiple underscores
        column = re.sub(
            r"_+",
            "_",
            column
        )

        # Remove leading/trailing underscores
        column = column.strip("_")

        cleaned_columns.append(column)

    df.columns = cleaned_columns

    return df


# =========================================================
# CHECK DUPLICATE COLUMNS
# =========================================================

def check_duplicate_columns(df):
    """
    Check for duplicate column names.
    """

    duplicate_columns = df.columns[
        df.columns.duplicated()
    ].tolist()

    if duplicate_columns:

        raise ValueError(
            f"Duplicate columns found: "
            f"{duplicate_columns}"
        )

    return True


# =========================================================
# NORMALIZE DATAFRAME VALUES
# =========================================================

def normalize_dataframe(df):
    """
    Normalize values in known columns.
    """

    df = df.copy()

    # Normalize year
    if "year" in df.columns:

        df["year"] = df["year"].apply(
            normalize_year
        )

    # Normalize ticker
    if "ticker" in df.columns:

        df["ticker"] = df["ticker"].apply(
            normalize_ticker
        )

    # Normalize company name
    if "company_name" in df.columns:

        df["company_name"] = df[
            "company_name"
        ].apply(
            normalize_text
        )

    return df


# =========================================================
# COMPLETE LOADING PIPELINE
# =========================================================

def load_and_normalize(file_path):
    """
    Complete Day 02 ETL pipeline.

    Steps:
    1. Load Excel file
    2. Skip metadata row
    3. Use actual header row
    4. Normalize column names
    5. Check duplicate columns
    6. Normalize values
    """

    print(f"\nLoading: {file_path}")

    # Load Excel with header=1
    df = load_excel(
        file_path
    )

    print(
        f"Rows loaded: {len(df)}"
    )

    # Normalize column names
    df = normalize_columns(
        df
    )

    # Check duplicate columns
    check_duplicate_columns(
        df
    )

    # Normalize values
    df = normalize_dataframe(
        df
    )

    return df