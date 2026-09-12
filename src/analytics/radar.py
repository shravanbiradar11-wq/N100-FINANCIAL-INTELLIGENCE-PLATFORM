"""
SPRINT 3 - DAY 19
RADAR / POLAR CHARTS

Generates radar charts for companies using:
ROE, ROCE, NPM, D/E, FCF Score,
PAT CAGR 5yr, Revenue CAGR 5yr, Composite Score

Output:
reports/radar_charts/<company_id>_radar.png
"""

from pathlib import Path
import sqlite3
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "db" / "nifty100.db"
OUTPUT_DIR = ROOT / "reports" / "radar_charts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONSTANTS
# ============================================================

AXES = [
    "ROE",
    "ROCE",
    "NPM",
    "D/E",
    "FCF Score",
    "PAT CAGR 5yr",
    "Revenue CAGR 5yr",
    "Composite Score",
]

METRIC_ALIASES = {
    "ROE": [
        "roe",
        "return_on_equity",
        "return on equity",
    ],

    "ROCE": [
        "roce",
        "return_on_capital_employed",
        "return on capital employed",
    ],

    "NPM": [
        "npm",
        "net_profit_margin",
        "net profit margin",
        "net_profit_margin_percent",
    ],

    "D/E": [
        "de",
        "d_e",
        "debt_equity",
        "debt_to_equity",
        "debt equity",
        "de_ratio",
    ],

    "FCF Score": [
        "fcf_score",
        "free_cash_flow_score",
        "fcf",
        "free_cash_flow",
    ],

    "PAT CAGR 5yr": [
        "pat_cagr_5yr",
        "pat_cagr_5yr_percent",
        "profit_cagr_5yr",
        "profit_growth_5yr",
        "compounded_profit_growth",
    ],

    "Revenue CAGR 5yr": [
        "revenue_cagr_5yr",
        "revenue_cagr_5yr_percent",
        "sales_cagr_5yr",
        "revenue_growth_5yr",
        "compounded_sales_growth",
    ],

    "Composite Score": [
        "composite_quality_score",
        "composite_score",
        "quality_score",
    ],
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def clean_name(value):
    """Convert a column name to a comparable form."""

    if value is None:
        return ""

    value = str(value).strip().lower()

    value = value.replace("%", "")
    value = value.replace("/", "_")
    value = value.replace("-", "_")
    value = value.replace(" ", "_")

    value = re.sub(r"_+", "_", value)

    return value.strip("_")


def find_column(columns, aliases):
    """
    Find a column using flexible aliases.
    """

    normalized = {
        clean_name(col): col
        for col in columns
    }

    for alias in aliases:

        key = clean_name(alias)

        if key in normalized:
            return normalized[key]

    # Partial matching fallback
    for col in columns:

        normalized_col = clean_name(col)

        for alias in aliases:

            normalized_alias = clean_name(alias)

            if (
                normalized_alias in normalized_col
                or normalized_col in normalized_alias
            ):
                return col

    return None


def find_company_id_column(df):
    candidates = [
        "company_id",
        "id",
        "companyid",
        "ticker",
        "symbol",
        "code",
        "nse_code",
    ]

    return find_column(df.columns, candidates)


def find_company_name_column(df):
    candidates = [
        "company_name",
        "name",
        "company",
        "companyname",
        "stock_name",
        "stock",
    ]

    return find_column(df.columns, candidates)


def find_peer_group_column(df):
    candidates = [
        "peer_group_name",
        "peer_group",
        "peer_groupname",
        "group_name",
        "group",
    ]

    return find_column(df.columns, candidates)


def find_year_column(df):
    candidates = [
        "year",
        "fy",
        "financial_year",
        "fiscal_year",
    ]

    return find_column(df.columns, candidates)


# ============================================================
# DATABASE
# ============================================================

def connect_database():

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found:\n{DB_PATH}"
        )

    return sqlite3.connect(DB_PATH)


def get_tables(connection):

    query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """

    return pd.read_sql_query(query, connection)["name"].tolist()


# ============================================================
# LOAD FINANCIAL DATA
# ============================================================

def load_financial_data(connection):

    tables = get_tables(connection)

    if "financial_ratios" not in tables:
        raise ValueError(
            "financial_ratios table not found in SQLite database."
        )

    df = pd.read_sql_query(
        "SELECT * FROM financial_ratios",
        connection
    )

    if df.empty:
        raise ValueError(
            "financial_ratios table is empty."
        )

    return df


# ============================================================
# LOAD COMPANY DATA
# ============================================================

def load_companies(connection):

    tables = get_tables(connection)

    if "companies" not in tables:
        raise ValueError(
            "companies table not found in SQLite database."
        )

    df = pd.read_sql_query(
        "SELECT * FROM companies",
        connection
    )

    if df.empty:
        raise ValueError(
            "companies table is empty."
        )

    return df


# ============================================================
# LOAD PEER PERCENTILES
# ============================================================

def load_peer_percentiles(connection):

    tables = get_tables(connection)

    if "peer_percentiles" not in tables:

        print(
            "WARNING: peer_percentiles table not found."
        )

        return pd.DataFrame()

    df = pd.read_sql_query(
        "SELECT * FROM peer_percentiles",
        connection
    )

    return df


# ============================================================
# BUILD BASE DATASET
# ============================================================

def build_dataset(financial, companies, peer_percentiles):

    print()
    print("=" * 70)
    print("BUILDING RADAR DATASET")
    print("=" * 70)

    financial_id = find_company_id_column(financial)
    company_id = find_company_id_column(companies)

    if financial_id is None:
        raise ValueError(
            "financial_ratios does not contain a company ID column."
        )

    if company_id is None:
        raise ValueError(
            "companies does not contain a company ID column."
        )

    financial = financial.copy()
    companies = companies.copy()

    financial["_company_key"] = (
        financial[financial_id]
        .astype(str)
        .str.strip()
    )

    companies["_company_key"] = (
        companies[company_id]
        .astype(str)
        .str.strip()
    )

    name_col = find_company_name_column(companies)

    if name_col is None:
        companies["_company_name"] = companies["_company_key"]
    else:
        companies["_company_name"] = (
            companies[name_col]
            .fillna(companies["_company_key"])
            .astype(str)
        )

    # --------------------------------------------------------
    # Latest year per company
    # --------------------------------------------------------

    year_col = find_year_column(financial)

    if year_col is not None:

        financial["_year_numeric"] = pd.to_numeric(
            financial[year_col],
            errors="coerce"
        )

        financial = (
            financial
            .sort_values("_year_numeric")
            .groupby("_company_key", as_index=False)
            .tail(1)
        )

    # --------------------------------------------------------
    # Merge company names
    # --------------------------------------------------------

    result = financial.merge(
        companies[
            ["_company_key", "_company_name"]
        ].drop_duplicates("_company_key"),
        on="_company_key",
        how="left",
    )

    # --------------------------------------------------------
    # Add peer group
    # --------------------------------------------------------

    result["_peer_group"] = None

    if not peer_percentiles.empty:

        peer_id = find_company_id_column(
            peer_percentiles
        )

        peer_group_col = find_peer_group_column(
            peer_percentiles
        )

        if (
            peer_id is not None
            and peer_group_col is not None
        ):

            peers = peer_percentiles[
                [peer_id, peer_group_col]
            ].copy()

            peers["_company_key"] = (
                peers[peer_id]
                .astype(str)
                .str.strip()
            )

            peers["_peer_group"] = (
                peers[peer_group_col]
                .astype(str)
                .str.strip()
            )

            peers = (
                peers[
                    [
                        "_company_key",
                        "_peer_group",
                    ]
                ]
                .drop_duplicates("_company_key")
            )

            result = result.merge(
                peers,
                on="_company_key",
                how="left",
                suffixes=("", "_peer")
            )

            if "_peer_group_peer" in result.columns:

                result["_peer_group"] = (
                    result["_peer_group_peer"]
                    .where(
                        result["_peer_group_peer"]
                        .notna(),
                        result["_peer_group"]
                    )
                )

                result.drop(
                    columns=["_peer_group_peer"],
                    inplace=True
                )

    # --------------------------------------------------------
    # Map metrics
    # --------------------------------------------------------

    for axis in AXES:

        col = find_column(
            result.columns,
            METRIC_ALIASES[axis]
        )

        if col is not None:

            result[axis] = pd.to_numeric(
                result[col],
                errors="coerce"
            )

        else:

            print(
                f"WARNING: {axis} column not found."
            )

            result[axis] = np.nan

    # --------------------------------------------------------
    # Special handling for FCF
    # --------------------------------------------------------

    if result["FCF Score"].isna().all():

        fcf_col = find_column(
            result.columns,
            [
                "fcf",
                "free_cash_flow",
                "free_cash_flow_latest",
                "free_cash_flow_latest_year",
            ]
        )

        if fcf_col is not None:

            fcf = pd.to_numeric(
                result[fcf_col],
                errors="coerce"
            )

            # Convert FCF to a simple 0-100 score
            # based on positive/negative status.

            result["FCF Score"] = np.where(
                fcf > 0,
                100.0,
                0.0
            )

    return result


# ============================================================
# NORMALISATION
# ============================================================

def normalize_metric(series, inverse=False):

    values = pd.to_numeric(
        series,
        errors="coerce"
    )

    valid = values.dropna()

    if valid.empty:
        return pd.Series(
            50.0,
            index=series.index
        )

    p10 = valid.quantile(0.10)
    p90 = valid.quantile(0.90)

    # Avoid divide-by-zero
    if p90 == p10:

        normalized = pd.Series(
            50.0,
            index=series.index
        )

    else:

        clipped = values.clip(
            lower=p10,
            upper=p90
        )

        normalized = (
            (clipped - p10)
            / (p90 - p10)
            * 100
        )

    if inverse:
        normalized = 100 - normalized

    return normalized.fillna(50.0)


def normalize_radar_data(df):

    result = df.copy()

    # D/E is inverse
    inverse_axes = {"D/E"}

    for axis in AXES:

        result[f"_norm_{axis}"] = normalize_metric(
            result[axis],
            inverse=axis in inverse_axes
        )

    return result


# ============================================================
# RADAR CHART
# ============================================================

def create_radar_chart(
    company_row,
    peer_data,
    output_path,
    standalone=False
):

    labels = AXES

    company_values = [
        company_row[f"_norm_{axis}"]
        for axis in labels
    ]

    company_values = [
        float(v) if pd.notna(v) else 50.0
        for v in company_values
    ]

    if standalone:

        reference_values = [
            float(
                peer_data[f"_norm_{axis}"]
                .mean()
            )
            if not peer_data.empty
            else 50.0
            for axis in labels
        ]

        reference_label = "Nifty 100 Average"

    else:

        reference_values = [
            float(
                peer_data[f"_norm_{axis}"]
                .mean()
            )
            if not peer_data.empty
            else 50.0
            for axis in labels
        ]

        reference_label = "Peer Group Average"

    # --------------------------------------------------------
    # Angles
    # --------------------------------------------------------

    angles = np.linspace(
        0,
        2 * np.pi,
        len(labels),
        endpoint=False
    ).tolist()

    company_values += company_values[:1]
    reference_values += reference_values[:1]
    angles += angles[:1]

    # --------------------------------------------------------
    # Plot
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(9, 9),
        subplot_kw=dict(polar=True)
    )

    ax.plot(
        angles,
        company_values,
        linewidth=2,
        label=str(
            company_row["_company_name"]
        )
    )

    ax.fill(
        angles,
        company_values,
        alpha=0.20
    )

    ax.plot(
        angles,
        reference_values,
        linestyle="--",
        linewidth=2,
        label=reference_label
    )

    ax.set_xticks(
        angles[:-1]
    )

    ax.set_xticklabels(
        labels,
        fontsize=10
    )

    ax.set_ylim(
        0,
        100
    )

    ax.set_yticks(
        [20, 40, 60, 80, 100]
    )

    ax.set_yticklabels(
        ["20", "40", "60", "80", "100"],
        fontsize=8
    )

    company_name = str(
        company_row["_company_name"]
    )

    peer_group = company_row.get(
        "_peer_group",
        None
    )

    if (
        peer_group is None
        or str(peer_group).strip() == ""
        or str(peer_group).lower() == "nan"
    ):
        title = (
            f"{company_name}\n"
            "Nifty 100 Standalone Radar"
        )
    else:
        title = (
            f"{company_name}\n"
            f"Peer Group: {peer_group}"
        )

    ax.set_title(
        title,
        fontsize=14,
        pad=25
    )

    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.25, 1.10)
    )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)


# ============================================================
# MAIN RADAR GENERATION
# ============================================================

def generate_radars(df):

    print()
    print("=" * 70)
    print("GENERATING RADAR CHARTS")
    print("=" * 70)

    if df.empty:
        print("No data available.")
        return 0

    df = normalize_radar_data(df)

    generated = 0

    # --------------------------------------------------------
    # Generate one chart per company
    # --------------------------------------------------------

    for _, company in df.iterrows():

        company_id = str(
            company["_company_key"]
        ).strip()

        company_name = str(
            company["_company_name"]
        ).strip()

        peer_group = company["_peer_group"]

        has_peer = (
            pd.notna(peer_group)
            and str(peer_group).strip() != ""
            and str(peer_group).lower() != "nan"
        )

        if has_peer:

            peer_rows = df[
                df["_peer_group"].astype(str).str.strip()
                == str(peer_group).strip()
            ].copy()

            # Exclude current company from peer average
            peer_rows = peer_rows[
                peer_rows["_company_key"]
                != company_id
            ]

        else:

            # No peer group:
            # use entire Nifty 100 as reference
            peer_rows = df.copy()

            peer_rows = peer_rows[
                peer_rows["_company_key"]
                != company_id
            ]

        safe_id = re.sub(
            r"[^A-Za-z0-9_.-]",
            "_",
            company_id
        )

        output_path = (
            OUTPUT_DIR
            / f"{safe_id}_radar.png"
        )

        create_radar_chart(
            company,
            peer_rows,
            output_path,
            standalone=not has_peer
        )

        generated += 1

        print(
            f"✓ {company_name} -> "
            f"{output_path.name}"
        )

    return generated


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SPRINT 3 - DAY 19")
    print("RADAR / POLAR CHARTS")
    print("=" * 70)

    print()
    print("DATABASE")
    print("-" * 70)

    print(f"Database: {DB_PATH}")

    connection = connect_database()

    try:

        print()
        print("LOADING FINANCIAL DATA")
        print("-" * 70)

        financial = load_financial_data(
            connection
        )

        print(
            f"✓ Financial rows: {len(financial)}"
        )

        print()
        print("LOADING COMPANIES")
        print("-" * 70)

        companies = load_companies(
            connection
        )

        print(
            f"✓ Company rows: {len(companies)}"
        )

        print()
        print("LOADING PEER PERCENTILES")
        print("-" * 70)

        peer_percentiles = load_peer_percentiles(
            connection
        )

        if peer_percentiles.empty:

            print(
                "⚠ Peer percentile data unavailable."
            )

        else:

            print(
                f"✓ Peer percentile rows: "
                f"{len(peer_percentiles)}"
            )

        print()
        print("PREPARING RADAR DATA")

        df = build_dataset(
            financial,
            companies,
            peer_percentiles
        )

        print(
            f"✓ Radar rows: {len(df)}"
        )

        print()
        print("GENERATING PNG FILES")

        count = generate_radars(
            df
        )

        print()
        print("=" * 70)
        print("DAY 19 SUMMARY")
        print("=" * 70)

        print(
            f"✓ Radar charts generated: {count}"
        )

        print(
            f"✓ Output folder:\n"
            f"  {OUTPUT_DIR}"
        )

        print()
        print("=" * 70)
        print("DAY 19 COMPLETE")
        print("=" * 70)

    finally:

        connection.close()


if __name__ == "__main__":
    main()
    