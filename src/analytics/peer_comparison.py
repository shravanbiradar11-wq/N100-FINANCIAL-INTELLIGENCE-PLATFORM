"""
SPRINT 3 - DAY 20
PEER COMPARISON EXCEL REPORT

Creates:
output/peer_comparison.xlsx

Requirements:
- Exactly 11 peer-group sheets
- Company ID and company name
- 10 peer metrics
- Percentile rank for each metric
- Percentile colour coding
- Benchmark company highlighting
- Median summary row
"""

from pathlib import Path
import sqlite3
import re

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "db" / "nifty100.db"
OUTPUT_DIR = ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "peer_comparison.xlsx"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# REQUIRED 11 PEER GROUPS
# ============================================================

EXPECTED_GROUP_COUNT = 11


# ============================================================
# METRICS
# ============================================================

METRICS = {
    "ROE": [
        "return_on_equity_pct",
        "roe",
        "roe_pct",
        "roe_percentage",
    ],

    "ROCE": [
        "return_on_capital_employed_pct",
        "roce",
        "roce_pct",
        "roce_percentage",
    ],

    "NPM": [
        "net_profit_margin_pct",
        "net_profit_margin",
        "npm",
        "npm_pct",
    ],

    "D/E": [
        "debt_to_equity",
        "de_ratio",
        "de",
        "d_e",
    ],

    "FCF": [
        "free_cash_flow_cr",
        "free_cash_flow",
        "fcf",
    ],

    "PAT CAGR 5yr": [
        "pat_cagr_5yr",
        "net_profit_cagr_5yr",
        "profit_cagr_5yr",
    ],

    "Revenue CAGR 5yr": [
        "revenue_cagr_5yr",
        "sales_cagr_5yr",
        "revenue_growth_5yr",
    ],

    "EPS CAGR 5yr": [
        "eps_cagr_5yr",
        "eps_growth_5yr",
    ],

    "Interest Coverage": [
        "interest_coverage",
        "interest_coverage_ratio",
        "icr",
    ],

    "Asset Turnover": [
        "asset_turnover",
        "asset_turnover_ratio",
    ],
}


# ============================================================
# COLUMN HELPERS
# ============================================================

def clean_column(value):

    value = str(value).strip().lower()

    value = value.replace(
        "%",
        "pct"
    )

    value = value.replace(
        "/",
        "_"
    )

    value = value.replace(
        "-",
        "_"
    )

    value = value.replace(
        " ",
        "_"
    )

    value = re.sub(
        r"[^a-z0-9_]",
        "_",
        value
    )

    value = re.sub(
        r"_+",
        "_",
        value
    )

    return value.strip("_")


def find_column(df, candidates):

    normalized = {
        clean_column(col): col
        for col in df.columns
    }

    for candidate in candidates:

        key = clean_column(candidate)

        if key in normalized:
            return normalized[key]

    return None


def find_company_id(df):

    return find_column(
        df,
        [
            "company_id",
            "companyid",
            "id",
            "ticker",
            "symbol",
            "nse_code",
            "code",
        ]
    )


def find_company_name(df):

    return find_column(
        df,
        [
            "company_name",
            "companyname",
            "name",
            "company",
            "stock_name",
        ]
    )


def find_peer_group(df):

    return find_column(
        df,
        [
            "peer_group_name",
            "peer_group",
            "group_name",
            "group",
        ]
    )


def find_year(df):

    return find_column(
        df,
        [
            "year",
            "financial_year",
            "fiscal_year",
            "fy",
        ]
    )


# ============================================================
# DATABASE
# ============================================================

def connect_db():

    if not DB_PATH.exists():

        raise FileNotFoundError(
            f"Database not found:\n{DB_PATH}"
        )

    return sqlite3.connect(
        DB_PATH
    )


# ============================================================
# LOAD DATA
# ============================================================

def load_data(connection):

    print()
    print("=" * 70)
    print("LOADING DATABASE DATA")
    print("=" * 70)

    tables = pd.read_sql_query(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """,
        connection
    )["name"].tolist()

    if "financial_ratios" not in tables:

        raise ValueError(
            "financial_ratios table not found."
        )

    if "companies" not in tables:

        raise ValueError(
            "companies table not found."
        )

    if "peer_percentiles" not in tables:

        raise ValueError(
            "peer_percentiles table not found. "
            "Complete Day 18 first."
        )

    ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios",
        connection
    )

    companies = pd.read_sql_query(
        "SELECT * FROM companies",
        connection
    )

    percentiles = pd.read_sql_query(
        "SELECT * FROM peer_percentiles",
        connection
    )

    print(
        f"✓ Financial ratio rows: {len(ratios)}"
    )

    print(
        f"✓ Company rows: {len(companies)}"
    )

    print(
        f"✓ Percentile rows: {len(percentiles)}"
    )

    return (
        ratios,
        companies,
        percentiles
    )


# ============================================================
# PREPARE COMPANY DATA
# ============================================================

def prepare_company_data(
    ratios,
    companies
):

    ratio_id = find_company_id(
        ratios
    )

    company_id = find_company_id(
        companies
    )

    if ratio_id is None:

        raise ValueError(
            "financial_ratios does not contain company ID."
        )

    if company_id is None:

        raise ValueError(
            "companies does not contain company ID."
        )

    ratios = ratios.copy()
    companies = companies.copy()

    ratios["_company_key"] = (
        ratios[ratio_id]
        .astype(str)
        .str.strip()
    )

    companies["_company_key"] = (
        companies[company_id]
        .astype(str)
        .str.strip()
    )

    name_col = find_company_name(
        companies
    )

    if name_col is None:

        companies["_company_name"] = (
            companies["_company_key"]
        )

    else:

        companies["_company_name"] = (
            companies[name_col]
            .fillna(
                companies["_company_key"]
            )
            .astype(str)
        )

    # --------------------------------------------------------
    # Use latest available year
    # --------------------------------------------------------

    year_col = find_year(
        ratios
    )

    if year_col is not None:

        ratios["_year_sort"] = pd.to_numeric(
            ratios[year_col],
            errors="coerce"
        )

        ratios = (
            ratios
            .sort_values("_year_sort")
            .groupby(
                "_company_key",
                as_index=False
            )
            .tail(1)
        )

    # --------------------------------------------------------
    # Company names
    # --------------------------------------------------------

    company_names = (
        companies[
            [
                "_company_key",
                "_company_name"
            ]
        ]
        .drop_duplicates(
            "_company_key"
        )
    )

    result = ratios.merge(
        company_names,
        on="_company_key",
        how="left"
    )

    return result


# ============================================================
# BUILD PEER ASSIGNMENTS
# ============================================================

def prepare_peer_assignments(
    percentiles
):

    if percentiles.empty:

        raise ValueError(
            "peer_percentiles table is empty."
        )

    id_col = find_company_id(
        percentiles
    )

    group_col = find_peer_group(
        percentiles
    )

    if id_col is None:

        raise ValueError(
            "peer_percentiles does not contain "
            "company ID."
        )

    if group_col is None:

        raise ValueError(
            "peer_percentiles does not contain "
            "peer group."
        )

    peers = percentiles[
        [
            id_col,
            group_col
        ]
    ].copy()

    peers.rename(
        columns={
            id_col: "_company_key",
            group_col: "_peer_group"
        },
        inplace=True
    )

    peers["_company_key"] = (
        peers["_company_key"]
        .astype(str)
        .str.strip()
    )

    peers["_peer_group"] = (
        peers["_peer_group"]
        .astype(str)
        .str.strip()
    )

    peers = (
        peers
        .drop_duplicates(
            "_company_key"
        )
    )

    return peers


# ============================================================
# ADD METRICS
# ============================================================

def add_metrics(
    result
):

    print()
    print("=" * 70)
    print("MAPPING METRICS")
    print("=" * 70)

    mapping = {}

    for metric, aliases in METRICS.items():

        col = find_column(
            result,
            aliases
        )

        mapping[metric] = col

        if col:

            print(
                f"✓ {metric}: {col}"
            )

        else:

            print(
                f"⚠ {metric}: NOT FOUND"
            )

        if col:

            result[metric] = pd.to_numeric(
                result[col],
                errors="coerce"
            )

        else:

            result[metric] = np.nan

    return result, mapping


# ============================================================
# PERCENTILE DATA
# ============================================================

def prepare_percentile_pivot(
    percentiles
):

    print()
    print("=" * 70)
    print("PREPARING PERCENTILE RANKINGS")
    print("=" * 70)

    id_col = find_company_id(
        percentiles
    )

    group_col = find_peer_group(
        percentiles
    )

    if id_col is None or group_col is None:

        raise ValueError(
            "Invalid peer_percentiles structure."
        )

    percentiles = percentiles.copy()

    percentiles["_company_key"] = (
        percentiles[id_col]
        .astype(str)
        .str.strip()
    )

    percentiles["_peer_group"] = (
        percentiles[group_col]
        .astype(str)
        .str.strip()
    )

    metric_col = find_column(
        percentiles,
        [
            "metric"
        ]
    )

    rank_col = find_column(
        percentiles,
        [
            "percentile_rank",
            "percentile",
            "percentile_rank_pct",
        ]
    )

    if metric_col is None:

        raise ValueError(
            "peer_percentiles does not contain metric column."
        )

    if rank_col is None:

        raise ValueError(
            "peer_percentiles does not contain "
            "percentile_rank column."
        )

    percentiles["_metric"] = (
        percentiles[metric_col]
        .astype(str)
        .str.strip()
    )

    percentiles["_rank"] = pd.to_numeric(
        percentiles[rank_col],
        errors="coerce"
    )

    # --------------------------------------------------------
    # If multiple years exist, use latest year
    # --------------------------------------------------------

    year_col = find_year(
        percentiles
    )

    if year_col is not None:

        percentiles["_year_sort"] = pd.to_numeric(
            percentiles[year_col],
            errors="coerce"
        )

        percentiles = (
            percentiles
            .sort_values("_year_sort")
            .groupby(
                [
                    "_company_key",
                    "_metric"
                ],
                as_index=False
            )
            .tail(1)
        )

    pivot = percentiles.pivot_table(
        index="_company_key",
        columns="_metric",
        values="_rank",
        aggfunc="first"
    ).reset_index()

    # --------------------------------------------------------
    # Rename percentile columns
    # --------------------------------------------------------

    rename = {}

    for metric in METRICS.keys():

        if metric in pivot.columns:

            rename[
                metric
            ] = f"{metric} Percentile"

    pivot.rename(
        columns=rename,
        inplace=True
    )

    return pivot


# ============================================================
# BUILD SHEET
# ============================================================

def build_sheet_data(
    group,
    company_data,
    percentile_pivot
):

    group_data = company_data[
        company_data["_peer_group"] == group
    ].copy()

    if group_data.empty:

        return pd.DataFrame()

    group_data = group_data.merge(
        percentile_pivot,
        on="_company_key",
        how="left"
    )

    # --------------------------------------------------------
    # Select output columns
    # --------------------------------------------------------

    output = pd.DataFrame()

    output["company_id"] = (
        group_data["_company_key"]
    )

    output["company_name"] = (
        group_data["_company_name"]
    )

    for metric in METRICS.keys():

        output[metric] = group_data[
            metric
        ]

    for metric in METRICS.keys():

        percentile_col = (
            f"{metric} Percentile"
        )

        if percentile_col in group_data.columns:

            output[
                percentile_col
            ] = group_data[
                percentile_col
            ]

        else:

            output[
                percentile_col
            ] = np.nan

    return output


# ============================================================
# BENCHMARK DETECTION
# ============================================================

def choose_benchmark(
    sheet_data
):

    if sheet_data.empty:
        return None

    # --------------------------------------------------------
    # Prefer company with highest composite score
    # if available.
    # --------------------------------------------------------

    possible = [
        "Composite Score",
        "composite_quality_score"
    ]

    for col in possible:

        if col in sheet_data.columns:

            values = pd.to_numeric(
                sheet_data[col],
                errors="coerce"
            )

            if values.notna().any():

                return values.idxmax()

    # --------------------------------------------------------
    # Otherwise choose company with highest average
    # percentile.
    # --------------------------------------------------------

    percentile_cols = [
        col
        for col in sheet_data.columns
        if "Percentile" in str(col)
    ]

    if percentile_cols:

        scores = (
            sheet_data[
                percentile_cols
            ]
            .apply(
                pd.to_numeric,
                errors="coerce"
            )
            .mean(axis=1)
        )

        if scores.notna().any():

            return scores.idxmax()

    return None


# ============================================================
# EXCEL FORMATTING
# ============================================================

def format_workbook(
    workbook
):

    print()
    print("=" * 70)
    print("FORMATTING EXCEL REPORT")
    print("=" * 70)

    # --------------------------------------------------------
    # Fills
    # --------------------------------------------------------

    green_fill = PatternFill(
        fill_type="solid",
        fgColor="C6EFCE"
    )

    yellow_fill = PatternFill(
        fill_type="solid",
        fgColor="FFEB9C"
    )

    red_fill = PatternFill(
        fill_type="solid",
        fgColor="FFC7CE"
    )

    benchmark_fill = PatternFill(
        fill_type="solid",
        fgColor="FFD966"
    )

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="D9EAF7"
    )

    # --------------------------------------------------------
    # Each sheet
    # --------------------------------------------------------

    for ws in workbook.worksheets:

        ws.freeze_panes = "A2"

        # Header
        for cell in ws[1]:

            cell.font = Font(
                bold=True
            )

            cell.fill = header_fill

            cell.alignment = Alignment(
                horizontal="center"
            )

        # ----------------------------------------------------
        # Identify percentile columns
        # ----------------------------------------------------

        percentile_columns = []

        for col_idx, cell in enumerate(
            ws[1],
            start=1
        ):

            if "Percentile" in str(
                cell.value
            ):

                percentile_columns.append(
                    col_idx
                )

        # ----------------------------------------------------
        # Colour percentile cells
        # ----------------------------------------------------

        for row in range(
            2,
            ws.max_row + 1
        ):

            for col_idx in percentile_columns:

                cell = ws.cell(
                    row=row,
                    column=col_idx
                )

                try:

                    value = float(
                        cell.value
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

                if value >= 75:

                    cell.fill = green_fill

                elif value <= 25:

                    cell.fill = red_fill

                else:

                    cell.fill = yellow_fill

        # ----------------------------------------------------
        # Detect benchmark row
        # ----------------------------------------------------

        # We mark the first row with the highest
        # average percentile.

        if ws.max_row >= 2:

            percentile_scores = []

            for row in range(
                2,
                ws.max_row + 1
            ):

                values = []

                for col_idx in percentile_columns:

                    value = ws.cell(
                        row=row,
                        column=col_idx
                    ).value

                    try:
                        values.append(
                            float(value)
                        )
                    except (
                        TypeError,
                        ValueError
                    ):
                        pass

                if values:

                    percentile_scores.append(
                        (
                            row,
                            np.mean(values)
                        )
                    )

            if percentile_scores:

                benchmark_row = max(
                    percentile_scores,
                    key=lambda x: x[1]
                )[0]

                for col in range(
                    1,
                    ws.max_column + 1
                ):

                    ws.cell(
                        row=benchmark_row,
                        column=col
                    ).fill = benchmark_fill

        # ----------------------------------------------------
        # Number formatting
        # ----------------------------------------------------

        for row in ws.iter_rows(
            min_row=2
        ):

            for cell in row:

                if isinstance(
                    cell.value,
                    (int, float)
                ):

                    cell.number_format = "0.00"

        # ----------------------------------------------------
        # Column widths
        # ----------------------------------------------------

        for col_idx in range(
            1,
            ws.max_column + 1
        ):

            letter = get_column_letter(
                col_idx
            )

            max_length = 0

            for cell in ws[letter]:

                if cell.value is not None:

                    max_length = max(
                        max_length,
                        len(str(cell.value))
                    )

            ws.column_dimensions[
                letter
            ].width = min(
                max(max_length + 2, 12),
                28
            )

        # ----------------------------------------------------
        # Auto-filter
        # ----------------------------------------------------

        ws.auto_filter.ref = (
            ws.dimensions
        )


# ============================================================
# ADD MEDIAN ROW
# ============================================================

def add_median_row(
    ws
):

    median_row = ws.max_row + 2

    ws.cell(
        row=median_row,
        column=1,
        value="PEER GROUP MEDIAN"
    )

    ws.cell(
        row=median_row,
        column=1
    ).font = Font(
        bold=True
    )

    # --------------------------------------------------------
    # Median for numeric columns
    # --------------------------------------------------------

    for col in range(
        3,
        ws.max_column + 1
    ):

        values = []

        for row in range(
            2,
            ws.max_row
        ):

            value = ws.cell(
                row=row,
                column=col
            ).value

            try:

                values.append(
                    float(value)
                )

            except (
                TypeError,
                ValueError
            ):

                pass

        if values:

            ws.cell(
                row=median_row,
                column=col,
                value=float(
                    np.median(values)
                )
            )

            ws.cell(
                row=median_row,
                column=col
            ).number_format = "0.00"


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SPRINT 3 - DAY 20")
    print("PEER COMPARISON EXCEL REPORT")
    print("=" * 70)

    connection = connect_db()

    try:

        # ----------------------------------------------------
        # Load
        # ----------------------------------------------------

        ratios, companies, percentiles = (
            load_data(connection)
        )

        # ----------------------------------------------------
        # Prepare
        # ----------------------------------------------------

        company_data = prepare_company_data(
            ratios,
            companies
        )

        peer_assignments = (
            prepare_peer_assignments(
                percentiles
            )
        )

        # ----------------------------------------------------
        # Add peer groups
        # ----------------------------------------------------

        company_data = company_data.merge(
            peer_assignments,
            on="_company_key",
            how="left"
        )

        company_data, mapping = add_metrics(
            company_data
        )

        percentile_pivot = (
            prepare_percentile_pivot(
                percentiles
            )
        )

        # ----------------------------------------------------
        # Get groups
        # ----------------------------------------------------

        groups = sorted(
            company_data[
                "_peer_group"
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        print()
        print(
            f"✓ Peer groups found: {len(groups)}"
        )

        for group in groups:

            print(
                f"  - {group}"
            )

        # ----------------------------------------------------
        # Requirement: exactly 11 sheets
        # ----------------------------------------------------

        if len(groups) != EXPECTED_GROUP_COUNT:

            print()
            print(
                "WARNING:"
            )

            print(
                f"Expected {EXPECTED_GROUP_COUNT} "
                f"peer groups."
            )

            print(
                f"Found {len(groups)}."
            )

            print(
                "The workbook will contain the "
                "available peer groups."
            )

        # ----------------------------------------------------
        # Create Excel writer
        # ----------------------------------------------------

        with pd.ExcelWriter(
            OUTPUT_FILE,
            engine="openpyxl"
        ) as writer:

            sheet_count = 0

            for group in groups:

                print()
                print(
                    f"Creating sheet: {group}"
                )

                sheet_data = build_sheet_data(
                    group,
                    company_data,
                    percentile_pivot
                )

                if sheet_data.empty:

                    print(
                        "  ⚠ No data, skipping."
                    )

                    continue

                # Excel sheet names max 31 chars
                sheet_name = str(group)[
                    :31
                ]

                # Avoid invalid Excel chars
                sheet_name = re.sub(
                    r"[\[\]\*:/\\?]",
                    "_",
                    sheet_name
                )

                sheet_data.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False
                )

                sheet_count += 1

                print(
                    f"  ✓ {len(sheet_data)} companies"
                )

        # ----------------------------------------------------
        # Format workbook
        # ----------------------------------------------------

        workbook = load_workbook(
            OUTPUT_FILE
        )

        # Add median rows
        for ws in workbook.worksheets:

            add_median_row(
                ws
            )

        format_workbook(
            workbook
        )

        workbook.save(
            OUTPUT_FILE
        )

        # ----------------------------------------------------
        # Final validation
        # ----------------------------------------------------

        print()
        print("=" * 70)
        print("DAY 20 VALIDATION")
        print("=" * 70)

        workbook = load_workbook(
            OUTPUT_FILE,
            read_only=True
        )

        final_sheet_count = len(
            workbook.sheetnames
        )

        print()
        print(
            f"✓ Excel sheets generated: "
            f"{final_sheet_count}"
        )

        for sheet in workbook.sheetnames:

            ws = workbook[sheet]

            print(
                f"  ✓ {sheet}: "
                f"{ws.max_row - 2} companies"
            )

        workbook.close()

        print()
        print(
            f"✓ File created:"
        )

        print(
            f"  {OUTPUT_FILE}"
        )

        print()
        print("=" * 70)
        print("DAY 20 COMPLETE")
        print("=" * 70)

    finally:

        connection.close()


if __name__ == "__main__":
    main()