from pathlib import Path
import sqlite3
import math
import re

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

DB_PATH = Path("db/nifty100.db")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# GENERAL HELPERS
# ============================================================

def clean_column_name(name):
    """Normalize column names for matching."""

    return (
        str(name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("%", "pct")
    )


def number(value):
    """Convert value to float safely."""

    if value is None:
        return None

    if pd.isna(value):
        return None

    if isinstance(value, str):

        value = (
            value
            .strip()
            .replace(",", "")
            .replace("₹", "")
            .replace("%", "")
        )

        if value in ("", "-", "NA", "N/A", "None", "null"):
            return None

    try:

        value = float(value)

        if math.isnan(value):
            return None

        return value

    except (TypeError, ValueError):

        return None


def find_column(df, candidates):
    """
    Find a column using multiple possible names.
    """

    normalized = {
        clean_column_name(col): col
        for col in df.columns
    }

    for candidate in candidates:

        key = clean_column_name(candidate)

        if key in normalized:
            return normalized[key]

    return None


def get_value(row, column):

    if column is None:
        return None

    if column not in row.index:
        return None

    return number(row[column])


# ============================================================
# YEAR NORMALIZATION
# ============================================================

def normalize_year_value(value):

    if value is None or pd.isna(value):
        return None

    text = str(value).strip()

    # 2024, 2023 etc.
    match = re.search(
        r"(19\d{2}|20\d{2})",
        text
    )

    if match:

        return int(match.group(1))

    return None


def prepare_year_table(df, table_name):

    """
    Prepare tables that have company_id + year.

    IMPORTANT:
    analysis is NOT passed through this function because
    analysis is company-level and does not contain year.
    """

    df = df.copy()

    # --------------------------------------------------------
    # COMPANY ID
    # --------------------------------------------------------

    company_col = find_column(
        df,
        [
            "company_id",
            "company",
            "ticker",
            "symbol",
            "code"
        ]
    )

    if company_col is None:

        raise ValueError(
            f"\n{table_name}: company_id not found.\n"
            f"Available columns:\n{list(df.columns)}"
        )

    if company_col != "company_id":

        df.rename(
            columns={
                company_col: "company_id"
            },
            inplace=True
        )

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------
    # YEAR
    # --------------------------------------------------------

    year_col = find_column(
        df,
        [
            "year",
            "financial_year",
            "fiscal_year",
            "fy",
            "fiscalyear",
            "report_year",
            "period"
        ]
    )

    if year_col is None:

        raise ValueError(
            f"\n{table_name}: YEAR column not found.\n"
            f"Available columns:\n{list(df.columns)}"
        )

    if year_col != "year":

        df.rename(
            columns={
                year_col: "year"
            },
            inplace=True
        )

    df["year"] = df["year"].apply(
        normalize_year_value
    )

    # --------------------------------------------------------
    # REMOVE INVALID RECORDS
    # --------------------------------------------------------

    df = df[
        df["company_id"].notna()
        & (df["company_id"] != "")
        & df["year"].notna()
    ].copy()

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=[
            "company_id",
            "year"
        ],
        keep="first"
    )

    return df


# ============================================================
# ANALYSIS TABLE PREPARATION
# ============================================================

def prepare_analysis(df):

    """
    analysis is a company-level table.

    Expected columns from your database:

        id
        company_id
        compounded_sales_growth
        compounded_profit_growth
        stock_price_cagr
        roe

    There is NO year column.
    """

    df = df.copy()

    company_col = find_column(
        df,
        [
            "company_id",
            "company",
            "ticker",
            "symbol",
            "code"
        ]
    )

    if company_col is None:

        raise ValueError(
            "analysis: company_id column not found.\n"
            f"Available columns: {list(df.columns)}"
        )

    if company_col != "company_id":

        df.rename(
            columns={
                company_col: "company_id"
            },
            inplace=True
        )

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df = df.drop_duplicates(
        subset=["company_id"],
        keep="first"
    )

    return df


# ============================================================
# RATIO FUNCTIONS
# ============================================================

def calculate_npm(net_profit, sales):

    if net_profit is None:
        return None

    if sales is None or sales == 0:
        return None

    return (
        net_profit / sales
    ) * 100


def calculate_opm(operating_profit, sales):

    if operating_profit is None:
        return None

    if sales is None or sales == 0:
        return None

    return (
        operating_profit / sales
    ) * 100


def calculate_roe(
    net_profit,
    equity_capital,
    reserves
):

    if None in (
        net_profit,
        equity_capital,
        reserves
    ):
        return None

    denominator = (
        equity_capital
        + reserves
    )

    if denominator <= 0:
        return None

    return (
        net_profit / denominator
    ) * 100


def calculate_roce(
    ebit,
    equity_capital,
    reserves,
    borrowings
):

    if None in (
        ebit,
        equity_capital,
        reserves,
        borrowings
    ):
        return None

    denominator = (
        equity_capital
        + reserves
        + borrowings
    )

    if denominator <= 0:
        return None

    return (
        ebit / denominator
    ) * 100


def calculate_roa(net_profit, total_assets):

    if net_profit is None:
        return None

    if total_assets is None or total_assets == 0:
        return None

    return (
        net_profit / total_assets
    ) * 100


def calculate_debt_equity(
    borrowings,
    equity_capital,
    reserves
):

    if None in (
        borrowings,
        equity_capital,
        reserves
    ):
        return None

    # Debt-free company
    if borrowings == 0:
        return 0.0

    denominator = (
        equity_capital
        + reserves
    )

    if denominator <= 0:
        return None

    return (
        borrowings / denominator
    )


def calculate_interest_coverage(
    operating_profit,
    other_income,
    interest
):

    if None in (
        operating_profit,
        other_income,
        interest
    ):
        return None

    if interest == 0:
        return None

    return (
        operating_profit
        + other_income
    ) / interest


def calculate_asset_turnover(
    sales,
    total_assets
):

    if sales is None:
        return None

    if total_assets is None or total_assets == 0:
        return None

    return sales / total_assets


def calculate_net_debt(
    borrowings,
    investments
):

    if borrowings is None:
        return None

    if investments is None:
        investments = 0

    return borrowings - investments


def calculate_free_cash_flow(
    operating_activity,
    investing_activity
):

    if None in (
        operating_activity,
        investing_activity
    ):
        return None

    return (
        operating_activity
        + investing_activity
    )


def calculate_capex(
    investing_activity
):

    if investing_activity is None:
        return None

    return abs(investing_activity)


def calculate_capex_intensity(
    investing_activity,
    sales
):

    if investing_activity is None:
        return None

    if sales is None or sales == 0:
        return None

    return (
        abs(investing_activity)
        / sales
    ) * 100


def calculate_fcf_conversion(
    free_cash_flow,
    operating_profit
):

    if free_cash_flow is None:
        return None

    if operating_profit is None or operating_profit == 0:
        return None

    return (
        free_cash_flow
        / operating_profit
    ) * 100


def calculate_eps(
    net_profit,
    equity_capital
):

    """
    Fallback EPS calculation.

    If a true EPS column exists in the source,
    the source EPS will be used instead.
    """

    if net_profit is None:
        return None

    if equity_capital is None or equity_capital == 0:
        return None

    return net_profit / equity_capital


def calculate_book_value_per_share(
    equity_capital,
    reserves
):

    if None in (
        equity_capital,
        reserves
    ):
        return None

    total_equity = (
        equity_capital
        + reserves
    )

    if equity_capital == 0:
        return None

    return total_equity / equity_capital


# ============================================================
# CAGR ENGINE
# ============================================================

def calculate_cagr(
    start_value,
    end_value,
    years
):

    if start_value is None or end_value is None:
        return None, "INSUFFICIENT"

    if years <= 0:
        return None, "INSUFFICIENT"

    # Zero base
    if start_value == 0:

        return None, "ZERO_BASE"

    # Positive -> Positive
    if start_value > 0 and end_value > 0:

        value = (
            (end_value / start_value)
            ** (1 / years)
            - 1
        ) * 100

        return value, None

    # Positive -> Negative
    if start_value > 0 and end_value < 0:

        return None, "DECLINE_TO_LOSS"

    # Negative -> Positive
    if start_value < 0 and end_value > 0:

        return None, "TURNAROUND"

    # Negative -> Negative
    if start_value < 0 and end_value < 0:

        return None, "BOTH_NEGATIVE"

    return None, "INSUFFICIENT"


# ============================================================
# FIND SOURCE COLUMN
# ============================================================

def source_column(df, candidates):

    return find_column(
        df,
        candidates
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("SPRINT 2 - DAY 12")
    print("FINANCIAL RATIOS ENGINE")
    print("=" * 70)

    # --------------------------------------------------------
    # DATABASE CHECK
    # --------------------------------------------------------

    if not DB_PATH.exists():

        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    conn = sqlite3.connect(
        DB_PATH
    )

    try:

        # ====================================================
        # LOAD TABLES
        # ====================================================

        companies = pd.read_sql_query(
            "SELECT * FROM companies",
            conn
        )

        analysis = pd.read_sql_query(
            "SELECT * FROM analysis",
            conn
        )

        balancesheet = pd.read_sql_query(
            "SELECT * FROM balancesheet",
            conn
        )

        cashflow = pd.read_sql_query(
            "SELECT * FROM cashflow",
            conn
        )

        profitloss = pd.read_sql_query(
            "SELECT * FROM profitandloss",
            conn
        )

        print(
            f"Companies       : {len(companies)}"
        )

        print(
            f"Analysis        : {len(analysis)}"
        )

        print(
            f"Balance Sheet   : {len(balancesheet)}"
        )

        print(
            f"Cash Flow       : {len(cashflow)}"
        )

        print(
            f"Profit & Loss   : {len(profitloss)}"
        )

        # ====================================================
        # PREPARE TABLES
        # ====================================================

        print()
        print("=" * 70)
        print("PREPARING SOURCE TABLES")
        print("=" * 70)

        # analysis DOES NOT HAVE YEAR
        analysis = prepare_analysis(
            analysis
        )

        balancesheet = prepare_year_table(
            balancesheet,
            "balancesheet"
        )

        cashflow = prepare_year_table(
            cashflow,
            "cashflow"
        )

        profitloss = prepare_year_table(
            profitloss,
            "profitandloss"
        )

        print(
            f"✓ analysis       : {len(analysis)} company rows"
        )

        print(
            f"✓ balancesheet   : {len(balancesheet)} company-year rows"
        )

        print(
            f"✓ cashflow       : {len(cashflow)} company-year rows"
        )

        print(
            f"✓ profitandloss  : {len(profitloss)} company-year rows"
        )

        # ====================================================
        # BUILD MASTER COMPANY-YEAR DATASET
        # ====================================================

        print()
        print("=" * 70)
        print("BUILDING COMPANY-YEAR DATASET")
        print("=" * 70)

        master = pd.concat(
            [
                balancesheet[
                    [
                        "company_id",
                        "year"
                    ]
                ],

                cashflow[
                    [
                        "company_id",
                        "year"
                    ]
                ],

                profitloss[
                    [
                        "company_id",
                        "year"
                    ]
                ]
            ],
            ignore_index=True
        )

        master = master.drop_duplicates(
            subset=[
                "company_id",
                "year"
            ]
        )

        master = master.sort_values(
            [
                "company_id",
                "year"
            ]
        ).reset_index(
            drop=True
        )

        print(
            f"✓ Company-year combinations: {len(master)}"
        )

        # ====================================================
        # STANDARDIZE SOURCE COLUMNS
        # ====================================================

        print()
        print("=" * 70)
        print("SOURCE COLUMN MAPPING")
        print("=" * 70)

        # ----------------------------------------------------
        # PROFIT & LOSS
        # ----------------------------------------------------

        sales_col = source_column(
            profitloss,
            [
                "sales",
                "revenue",
                "net_sales",
                "sales_cr",
                "revenue_cr",
                "total_revenue"
            ]
        )

        pat_col = source_column(
            profitloss,
            [
                "net_profit",
                "pat",
                "profit_after_tax",
                "profit"
            ]
        )

        operating_profit_col = source_column(
            profitloss,
            [
                "operating_profit",
                "op_profit",
                "operating_profit_cr",
                "ebit"
            ]
        )

        other_income_col = source_column(
            profitloss,
            [
                "other_income"
            ]
        )

        interest_col = source_column(
            profitloss,
            [
                "interest",
                "interest_expense",
                "interest_paid"
            ]
        )

        eps_col = source_column(
            profitloss,
            [
                "eps",
                "earnings_per_share",
                "eps_rs"
            ]
        )

        dividend_col = source_column(
            profitloss,
            [
                "dividend",
                "dividend_paid",
                "dividend_payout"
            ]
        )

        # ----------------------------------------------------
        # BALANCE SHEET
        # ----------------------------------------------------

        equity_col = source_column(
            balancesheet,
            [
                "equity_capital",
                "shareholders_equity",
                "shareholders_funds",
                "equity"
            ]
        )

        reserves_col = source_column(
            balancesheet,
            [
                "reserves",
                "reserves_surplus",
                "reserves_and_surplus"
            ]
        )

        borrowings_col = source_column(
            balancesheet,
            [
                "borrowings",
                "total_borrowings",
                "debt",
                "total_debt"
            ]
        )

        assets_col = source_column(
            balancesheet,
            [
                "total_assets",
                "assets",
                "total_assets_cr"
            ]
        )

        investments_col = source_column(
            balancesheet,
            [
                "investments",
                "investment"
            ]
        )

        cash_col = source_column(
            balancesheet,
            [
                "cash",
                "cash_and_bank",
                "cash_equivalents"
            ]
        )

        # ----------------------------------------------------
        # CASH FLOW
        # ----------------------------------------------------

        cfo_col = source_column(
            cashflow,
            [
                "operating_activity",
                "cash_from_operations",
                "cash_from_operating_activity",
                "cfo",
                "cash_from_operating_activities"
            ]
        )

        cfi_col = source_column(
            cashflow,
            [
                "investing_activity",
                "cash_from_investing_activity",
                "cfi",
                "cash_from_investing_activities"
            ]
        )

        cff_col = source_column(
            cashflow,
            [
                "financing_activity",
                "cash_from_financing_activity",
                "cff",
                "cash_from_financing_activities"
            ]
        )

        # ----------------------------------------------------
        # PRINT MAPPING
        # ----------------------------------------------------

        mapping = {
            "Sales": sales_col,
            "Net Profit": pat_col,
            "Operating Profit": operating_profit_col,
            "Other Income": other_income_col,
            "Interest": interest_col,
            "EPS": eps_col,
            "Dividend": dividend_col,
            "Equity Capital": equity_col,
            "Reserves": reserves_col,
            "Borrowings": borrowings_col,
            "Total Assets": assets_col,
            "Investments": investments_col,
            "Cash": cash_col,
            "CFO": cfo_col,
            "CFI": cfi_col,
            "CFF": cff_col
        }

        for name, column in mapping.items():

            print(
                f"{name:<22}: {column}"
            )

        # ====================================================
        # SELECT ONLY REQUIRED COLUMNS
        # ====================================================

        def select_source(
            df,
            columns,
            rename_map
        ):

            selected = df[
                [
                    c
                    for c in columns
                    if c in df.columns
                ]
            ].copy()

            selected.rename(
                columns=rename_map,
                inplace=True
            )

            return selected

        # ----------------------------------------------------
        # P&L SOURCE
        # ----------------------------------------------------

        pl_columns = [
            "company_id",
            "year"
        ]

        pl_rename = {}

        for source, target in [
            (sales_col, "sales"),
            (pat_col, "net_profit"),
            (operating_profit_col, "operating_profit"),
            (other_income_col, "other_income"),
            (interest_col, "interest"),
            (eps_col, "eps_source"),
            (dividend_col, "dividend")
        ]:

            if source is not None:

                pl_columns.append(source)
                pl_rename[source] = target

        pl = select_source(
            profitloss,
            pl_columns,
            pl_rename
        )

        # ----------------------------------------------------
        # BALANCE SHEET SOURCE
        # ----------------------------------------------------

        bs_columns = [
            "company_id",
            "year"
        ]

        bs_rename = {}

        for source, target in [
            (equity_col, "equity_capital"),
            (reserves_col, "reserves"),
            (borrowings_col, "borrowings"),
            (assets_col, "total_assets"),
            (investments_col, "investments"),
            (cash_col, "cash")
        ]:

            if source is not None:

                bs_columns.append(source)
                bs_rename[source] = target

        bs = select_source(
            balancesheet,
            bs_columns,
            bs_rename
        )

        # ----------------------------------------------------
        # CASH FLOW SOURCE
        # ----------------------------------------------------

        cf_columns = [
            "company_id",
            "year"
        ]

        cf_rename = {}

        for source, target in [
            (cfo_col, "cfo"),
            (cfi_col, "cfi"),
            (cff_col, "cff")
        ]:

            if source is not None:

                cf_columns.append(source)
                cf_rename[source] = target

        cf = select_source(
            cashflow,
            cf_columns,
            cf_rename
        )

        # ====================================================
        # MERGE
        # ====================================================

        print()
        print("=" * 70)
        print("MERGING FINANCIAL DATA")
        print("=" * 70)

        data = master.copy()

        for source in [
            pl,
            bs,
            cf
        ]:

            data = data.merge(
                source,
                on=[
                    "company_id",
                    "year"
                ],
                how="left"
            )

        # ----------------------------------------------------
        # ADD COMPANY LEVEL ANALYSIS
        # ----------------------------------------------------

        analysis_columns = [
            "company_id"
        ]

        for column in [
            "compounded_sales_growth",
            "compounded_profit_growth",
            "stock_price_cagr",
            "roe"
        ]:

            if column in analysis.columns:

                analysis_columns.append(
                    column
                )

        analysis_small = analysis[
            analysis_columns
        ].copy()

        data = data.merge(
            analysis_small,
            on="company_id",
            how="left"
        )

        print(
            f"✓ Final source rows: {len(data)}"
        )

        # ====================================================
        # CALCULATE RATIOS
        # ====================================================

        print()
        print("=" * 70)
        print("CALCULATING FINANCIAL KPIs")
        print("=" * 70)

        results = []

        # ----------------------------------------------------
        # PREPARE HISTORICAL SERIES FOR CAGR
        # ----------------------------------------------------

        history = {}

        for company_id, group in data.groupby(
            "company_id"
        ):

            group = group.sort_values(
                "year"
            )

            history[company_id] = group

        # ----------------------------------------------------
        # ROW-BY-ROW CALCULATION
        # ----------------------------------------------------

        for _, row in data.iterrows():

            company_id = row["company_id"]
            year = int(row["year"])

            sales = get_value(
                row,
                "sales"
            )

            net_profit = get_value(
                row,
                "net_profit"
            )

            operating_profit = get_value(
                row,
                "operating_profit"
            )

            other_income = get_value(
                row,
                "other_income"
            )

            interest = get_value(
                row,
                "interest"
            )

            equity_capital = get_value(
                row,
                "equity_capital"
            )

            reserves = get_value(
                row,
                "reserves"
            )

            borrowings = get_value(
                row,
                "borrowings"
            )

            total_assets = get_value(
                row,
                "total_assets"
            )

            investments = get_value(
                row,
                "investments"
            )

            cfo = get_value(
                row,
                "cfo"
            )

            cfi = get_value(
                row,
                "cfi"
            )

            # ------------------------------------------------
            # RATIOS
            # ------------------------------------------------

            npm_value = calculate_npm(
                net_profit,
                sales
            )

            opm_value = calculate_opm(
                operating_profit,
                sales
            )

            roe_value = calculate_roe(
                net_profit,
                equity_capital,
                reserves
            )

            roce_value = calculate_roce(
                operating_profit,
                equity_capital,
                reserves,
                borrowings
            )

            roa_value = calculate_roa(
                net_profit,
                total_assets
            )

            de_value = calculate_debt_equity(
                borrowings,
                equity_capital,
                reserves
            )

            icr_value = calculate_interest_coverage(
                operating_profit,
                other_income,
                interest
            )

            asset_turnover_value = calculate_asset_turnover(
                sales,
                total_assets
            )

            net_debt_value = calculate_net_debt(
                borrowings,
                investments
            )

            fcf_value = calculate_free_cash_flow(
                cfo,
                cfi
            )

            capex_value = calculate_capex(
                cfi
            )

            capex_intensity_value = calculate_capex_intensity(
                cfi,
                sales
            )

            fcf_conversion_value = calculate_fcf_conversion(
                fcf_value,
                operating_profit
            )

            # ------------------------------------------------
            # EPS
            # ------------------------------------------------

            source_eps = get_value(
                row,
                "eps_source"
            )

            if source_eps is not None:

                eps_value = source_eps

            else:

                eps_value = calculate_eps(
                    net_profit,
                    equity_capital
                )

            # ------------------------------------------------
            # BOOK VALUE PER SHARE
            # ------------------------------------------------

            bvps_value = calculate_book_value_per_share(
                equity_capital,
                reserves
            )

            # ------------------------------------------------
            # TOTAL DEBT
            # ------------------------------------------------

            total_debt = borrowings

            # ------------------------------------------------
            # CAGR
            # ------------------------------------------------

            company_history = history[
                company_id
            ]

            def historical_value(
                target_year,
                column
            ):

                match = company_history[
                    company_history["year"]
                    == target_year
                ]

                if match.empty:
                    return None

                return number(
                    match.iloc[0].get(
                        column
                    )
                )

            # 5-year window
            start_year = year - 5

            revenue_start = historical_value(
                start_year,
                "sales"
            )

            revenue_end = sales

            pat_start = historical_value(
                start_year,
                "net_profit"
            )

            pat_end = net_profit

            eps_start = historical_value(
                start_year,
                "eps_source"
            )

            eps_end = source_eps

            revenue_cagr, revenue_flag = calculate_cagr(
                revenue_start,
                revenue_end,
                5
            )

            pat_cagr, pat_flag = calculate_cagr(
                pat_start,
                pat_end,
                5
            )

            eps_cagr, eps_flag = calculate_cagr(
                eps_start,
                eps_end,
                5
            )

            # ------------------------------------------------
            # ICR LABEL
            # ------------------------------------------------

            if icr_value is None and interest == 0:

                icr_label = "Debt Free"

            else:

                icr_label = None

            # ------------------------------------------------
            # HIGH LEVERAGE FLAG
            # ------------------------------------------------

            high_leverage_flag = False

            if (
                de_value is not None
                and de_value > 5
            ):

                high_leverage_flag = True

            # ------------------------------------------------
            # ICR WARNING
            # ------------------------------------------------

            icr_warning_flag = False

            if (
                icr_value is not None
                and icr_value < 1.5
            ):

                icr_warning_flag = True

            # ------------------------------------------------
            # RESULT
            # ------------------------------------------------

            results.append(
                {
                    "company_id":
                        company_id,

                    "year":
                        year,

                    "net_profit_margin_pct":
                        npm_value,

                    "operating_profit_margin_pct":
                        opm_value,

                    "return_on_equity_pct":
                        roe_value,

                    "return_on_capital_employed_pct":
                        roce_value,

                    "return_on_assets_pct":
                        roa_value,

                    "debt_to_equity":
                        de_value,

                    "high_leverage_flag":
                        high_leverage_flag,

                    "interest_coverage":
                        icr_value,

                    "icr_label":
                        icr_label,

                    "icr_warning_flag":
                        icr_warning_flag,

                    "asset_turnover":
                        asset_turnover_value,

                    "net_debt_cr":
                        net_debt_value,

                    "free_cash_flow_cr":
                        fcf_value,

                    "capex_cr":
                        capex_value,

                    "capex_intensity_pct":
                        capex_intensity_value,

                    "fcf_conversion_rate_pct":
                        fcf_conversion_value,

                    "earnings_per_share":
                        eps_value,

                    "book_value_per_share":
                        bvps_value,

                    "dividend_payout_ratio_pct":
                        None,

                    "total_debt_cr":
                        total_debt,

                    "cash_from_operations_cr":
                        cfo,

                    "revenue_cagr_5yr":
                        revenue_cagr,

                    "revenue_cagr_5yr_flag":
                        revenue_flag,

                    "pat_cagr_5yr":
                        pat_cagr,

                    "pat_cagr_5yr_flag":
                        pat_flag,

                    "eps_cagr_5yr":
                        eps_cagr,

                    "eps_cagr_5yr_flag":
                        eps_flag,

                    "composite_quality_score":
                        None
                }
            )

        ratios = pd.DataFrame(
            results
        )

        # ====================================================
        # CLEAN TYPES
        # ====================================================

        ratios["year"] = pd.to_numeric(
            ratios["year"],
            errors="coerce"
        ).astype("Int64")

        # Remove duplicate company/year
        ratios = ratios.drop_duplicates(
            subset=[
                "company_id",
                "year"
            ],
            keep="first"
        )

        # ====================================================
        # SAVE DATABASE TABLE
        # ====================================================

        print()
        print("=" * 70)
        print("WRITING financial_ratios TABLE")
        print("=" * 70)

        conn.execute(
            "DROP TABLE IF EXISTS financial_ratios"
        )

        conn.commit()

        ratios.to_sql(
            "financial_ratios",
            conn,
            if_exists="replace",
            index=False
        )

        conn.commit()

        # ====================================================
        # DATABASE CHECK
        # ====================================================

        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM financial_ratios
            """
        ).fetchone()[0]

        columns = conn.execute(
            """
            PRAGMA table_info(financial_ratios)
            """
        ).fetchall()

        column_names = [
            row[1]
            for row in columns
        ]

        # ====================================================
        # OUTPUT SUMMARY
        # ====================================================

        print()
        print("=" * 70)
        print("DAY 12 DATABASE RESULT")
        print("=" * 70)

        print(
            f"financial_ratios rows : {count}"
        )

        print(
            f"companies represented : "
            f"{ratios['company_id'].nunique()}"
        )

        print(
            f"KPI columns           : "
            f"{len(column_names) - 2}"
        )

        print()

        print("Required KPI columns:")
        print("-" * 70)

        required_columns = [
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "debt_to_equity",
            "interest_coverage",
            "asset_turnover",
            "free_cash_flow_cr",
            "capex_cr",
            "earnings_per_share",
            "book_value_per_share",
            "dividend_payout_ratio_pct",
            "total_debt_cr",
            "cash_from_operations_cr",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "eps_cagr_5yr",
            "composite_quality_score"
        ]

        for column in required_columns:

            if column in column_names:

                print(
                    f"✓ {column}"
                )

            else:

                print(
                    f"✗ {column} MISSING"
                )

        # ====================================================
        # NULL-ONLY CHECK
        # ====================================================

        print()
        print("=" * 70)
        print("KPI NULL CHECK")
        print("=" * 70)

        for column in required_columns:

            if column not in ratios.columns:

                continue

            non_null = (
                ratios[column]
                .notna()
                .sum()
            )

            if non_null > 0:

                print(
                    f"✓ {column:<35} "
                    f"{non_null} populated"
                )

            else:

                print(
                    f"⚠ {column:<35} "
                    f"0 populated"
                )

        # ====================================================
        # FINAL STATUS
        # ====================================================

        print()
        print("=" * 70)

        if count >= 1100:

            print(
                "✓ DAY 12 ROW COUNT TARGET PASSED"
            )

        else:

            print(
                "✗ DAY 12 ROW COUNT TARGET FAILED"
            )

        print("=" * 70)

        # ====================================================
        # SAVE CSV PREVIEW
        # ====================================================

        preview_path = (
            OUTPUT_DIR
            / "financial_ratios_preview.csv"
        )

        ratios.head(100).to_csv(
            preview_path,
            index=False
        )

        print()
        print(
            f"✓ Preview saved: {preview_path}"
        )

        print()
        print("=" * 70)
        print("DAY 12 FINISHED")
        print("=" * 70)

    finally:

        conn.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()