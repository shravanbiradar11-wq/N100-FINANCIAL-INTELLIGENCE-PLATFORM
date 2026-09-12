"""
Sprint 2 - Day 11
Capital Allocation Analysis

Generates:
    output/capital_allocation.csv

Columns:
    company_id
    year
    cfo_sign
    cfi_sign
    cff_sign
    pattern_label
"""

from pathlib import Path
import sqlite3

import pandas as pd


# ============================================================
# PATHS
# ============================================================

DB_PATH = Path("db/nifty100.db")
OUTPUT_PATH = Path("output/capital_allocation.csv")


# ============================================================
# HELPERS
# ============================================================

def get_sign(value):
    """Return +, -, or 0 for a numeric value."""

    if pd.isna(value):
        return "0"

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "0"

    if value > 0:
        return "+"

    if value < 0:
        return "-"

    return "0"


def classify_pattern(
    cfo,
    cfi,
    cff,
    cfo_pat_ratio=None
):
    """
    Classify capital allocation pattern.

    (+,-,-) = Reinvestor
    (+,-,-) with high CFO/PAT = Shareholder Returns
    (+,+,-) = Liquidating Assets
    (-,+,+) = Distress Signal
    (-,-,+) = Growth Funded by Debt
    (+,+,+) = Cash Accumulator
    (-,-,-) = Pre-Revenue
    (+,-,+) = Mixed
    """

    cfo_sign = get_sign(cfo)
    cfi_sign = get_sign(cfi)
    cff_sign = get_sign(cff)

    pattern = (
        cfo_sign,
        cfi_sign,
        cff_sign
    )

    # (+,-,-)
    if pattern == ("+", "-", "-"):

        if (
            cfo_pat_ratio is not None
            and not pd.isna(cfo_pat_ratio)
            and cfo_pat_ratio > 1.0
        ):
            return "Shareholder Returns"

        return "Reinvestor"

    # (+,+,-)
    if pattern == ("+", "+", "-"):
        return "Liquidating Assets"

    # (-,+,+)
    if pattern == ("-", "+", "+"):
        return "Distress Signal"

    # (-,-,+)
    if pattern == ("-", "-", "+"):
        return "Growth Funded by Debt"

    # (+,+,+)
    if pattern == ("+", "+", "+"):
        return "Cash Accumulator"

    # (-,-,-)
    if pattern == ("-", "-", "-"):
        return "Pre-Revenue"

    # (+,-,+)
    if pattern == ("+", "-", "+"):
        return "Mixed"

    # Any combination involving zero
    return "Mixed"


def calculate_cfo_pat_ratio(cfo, pat):
    """Calculate CFO / PAT."""

    if pd.isna(cfo) or pd.isna(pat):
        return None

    try:
        cfo = float(cfo)
        pat = float(pat)
    except (TypeError, ValueError):
        return None

    if pat == 0:
        return None

    return cfo / pat


# ============================================================
# FIND COLUMN
# ============================================================

def find_column(df, candidates):
    """
    Find the first matching column from candidates.
    Matching is case-insensitive.
    """

    column_map = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    for candidate in candidates:

        key = candidate.strip().lower()

        if key in column_map:
            return column_map[key]

    return None


# ============================================================
# LOAD CASH FLOW DATA
# ============================================================

def load_cashflow_data(connection):
    """Load required cash-flow information."""

    query = """
        SELECT *
        FROM cashflow
    """

    df = pd.read_sql_query(
        query,
        connection
    )

    if df.empty:
        raise ValueError(
            "cashflow table contains no rows."
        )

    return df


# ============================================================
# LOAD PROFIT & LOSS DATA
# ============================================================

def load_profit_data(connection):
    """Load PAT/net-profit information."""

    query = """
        SELECT *
        FROM profitandloss
    """

    df = pd.read_sql_query(
        query,
        connection
    )

    if df.empty:
        print(
            "WARNING: profitandloss table is empty."
        )

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("SPRINT 2 - DAY 11")
    print("CAPITAL ALLOCATION ANALYSIS")
    print("=" * 70)

    # --------------------------------------------------------
    # Check database
    # --------------------------------------------------------

    if not DB_PATH.exists():

        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DB_PATH
    )

    try:

        # ----------------------------------------------------
        # Load cash flow
        # ----------------------------------------------------

        cashflow = load_cashflow_data(
            connection
        )

        print()
        print(
            f"Cash-flow rows loaded: {len(cashflow)}"
        )

        print(
            "Cash-flow columns:"
        )

        print(
            list(cashflow.columns)
        )

        # ----------------------------------------------------
        # Identify columns
        # ----------------------------------------------------

        company_col = find_column(
            cashflow,
            [
                "company_id",
                "company",
                "ticker",
                "symbol"
            ]
        )

        year_col = find_column(
            cashflow,
            [
                "year",
                "financial_year",
                "fy"
            ]
        )

        cfo_col = find_column(
            cashflow,
            [
                "operating_activity",
                "cash_from_operating_activity",
                "cash_from_operations",
                "cfo",
                "operating_cash_flow"
            ]
        )

        cfi_col = find_column(
            cashflow,
            [
                "investing_activity",
                "cash_from_investing_activity",
                "cash_from_investing",
                "cfi",
                "investing_cash_flow"
            ]
        )

        cff_col = find_column(
            cashflow,
            [
                "financing_activity",
                "cash_from_financing_activity",
                "cash_from_financing",
                "cff",
                "financing_cash_flow"
            ]
        )

        # ----------------------------------------------------
        # Validate columns
        # ----------------------------------------------------

        missing = []

        if company_col is None:
            missing.append("company_id")

        if year_col is None:
            missing.append("year")

        if cfo_col is None:
            missing.append("operating_activity / CFO")

        if cfi_col is None:
            missing.append("investing_activity / CFI")

        if cff_col is None:
            missing.append("financing_activity / CFF")

        if missing:

            raise ValueError(
                "Required cashflow columns not found: "
                + ", ".join(missing)
            )

        # ----------------------------------------------------
        # Load PAT
        # ----------------------------------------------------

        profit = load_profit_data(
            connection
        )

        pat_col = None

        if not profit.empty:

            pat_col = find_column(
                profit,
                [
                    "net_profit",
                    "pat",
                    "profit_after_tax",
                    "profit"
                ]
            )

        # ----------------------------------------------------
        # Merge PAT if available
        # ----------------------------------------------------

        if (
            not profit.empty
            and pat_col is not None
        ):

            profit_company_col = find_column(
                profit,
                [
                    "company_id",
                    "company",
                    "ticker",
                    "symbol"
                ]
            )

            profit_year_col = find_column(
                profit,
                [
                    "year",
                    "financial_year",
                    "fy"
                ]
            )

            if (
                profit_company_col is not None
                and profit_year_col is not None
            ):

                pat_df = profit[
                    [
                        profit_company_col,
                        profit_year_col,
                        pat_col
                    ]
                ].copy()

                pat_df.columns = [
                    "company_id",
                    "year",
                    "pat"
                ]

                cashflow = cashflow.rename(
                    columns={
                        company_col: "company_id",
                        year_col: "year"
                    }
                )

                cashflow = cashflow.merge(
                    pat_df,
                    on=[
                        "company_id",
                        "year"
                    ],
                    how="left"
                )

            else:

                cashflow = cashflow.rename(
                    columns={
                        company_col: "company_id",
                        year_col: "year"
                    }
                )

                cashflow["pat"] = None

        else:

            cashflow = cashflow.rename(
                columns={
                    company_col: "company_id",
                    year_col: "year"
                }
            )

            cashflow["pat"] = None

        # ----------------------------------------------------
        # Generate results
        # ----------------------------------------------------

        results = []

        for _, row in cashflow.iterrows():

            cfo = row[cfo_col]
            cfi = row[cfi_col]
            cff = row[cff_col]
            pat = row["pat"]

            cfo_pat_ratio = calculate_cfo_pat_ratio(
                cfo,
                pat
            )

            pattern_label = classify_pattern(
                cfo=cfo,
                cfi=cfi,
                cff=cff,
                cfo_pat_ratio=cfo_pat_ratio
            )

            results.append(
                {
                    "company_id":
                        row["company_id"],

                    "year":
                        row["year"],

                    "cfo_sign":
                        get_sign(cfo),

                    "cfi_sign":
                        get_sign(cfi),

                    "cff_sign":
                        get_sign(cff),

                    "pattern_label":
                        pattern_label
                }
            )

        output_df = pd.DataFrame(
            results
        )

        # ----------------------------------------------------
        # Remove invalid company/year rows
        # ----------------------------------------------------

        output_df = output_df[
            output_df["company_id"].notna()
            & output_df["year"].notna()
        ].copy()

        # ----------------------------------------------------
        # Remove duplicates
        # ----------------------------------------------------

        output_df = output_df.drop_duplicates(
            subset=[
                "company_id",
                "year"
            ]
        )

        # ----------------------------------------------------
        # Sort
        # ----------------------------------------------------

        output_df = output_df.sort_values(
            [
                "company_id",
                "year"
            ]
        ).reset_index(
            drop=True
        )

        # ----------------------------------------------------
        # Save CSV
        # ----------------------------------------------------

        output_df.to_csv(
            OUTPUT_PATH,
            index=False
        )

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        print()
        print("=" * 70)
        print("CAPITAL ALLOCATION SUMMARY")
        print("=" * 70)

        print(
            output_df[
                "pattern_label"
            ].value_counts().to_string()
        )

        print()
        print(
            f"✓ Rows generated: {len(output_df)}"
        )

        print(
            f"✓ Unique companies: "
            f"{output_df['company_id'].nunique()}"
        )

        print(
            f"✓ Output file: {OUTPUT_PATH}"
        )

        print()
        print("Sample records:")
        print(
            output_df.head(10).to_string(
                index=False
            )
        )

        print()
        print("=" * 70)
        print("✓ CAPITAL ALLOCATION GENERATION COMPLETE")
        print("=" * 70)

    finally:

        connection.close()


if __name__ == "__main__":
    main()