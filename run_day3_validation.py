from pathlib import Path

from src.etl.loader import load_and_normalize
from src.etl.validator import DataValidator


# =========================================================
# CONFIGURATION
# =========================================================

RAW_PATH = Path("data/raw")


# =========================================================
# CREATE VALIDATOR
# =========================================================

validator = DataValidator()


# =========================================================
# LOAD ALL EXCEL FILES
# =========================================================

excel_files = list(
    RAW_PATH.glob("*.xlsx")
)

all_data = {}

for file in excel_files:

    print("\n" + "=" * 70)
    print(f"LOADING: {file.name}")
    print("=" * 70)

    df = load_and_normalize(file)

    table_name = file.stem

    all_data[table_name] = df


# =========================================================
# DATASET SUMMARY
# =========================================================

print("\n" + "=" * 70)
print("ALL DATASETS LOADED SUCCESSFULLY")
print("=" * 70)

for table_name, df in all_data.items():

    print(
        f"{table_name}: "
        f"{len(df)} rows, "
        f"{len(df.columns)} columns"
    )


# =========================================================
# DQ-01: PRIMARY KEY UNIQUENESS
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-01: PRIMARY KEY UNIQUENESS")
print("=" * 70)

for table_name, df in all_data.items():

    validator.validate_primary_key(
        df=df,
        table_name=table_name
    )


# =========================================================
# DQ-02: COMPANY + YEAR UNIQUENESS
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-02: COMPANY + YEAR UNIQUENESS")
print("=" * 70)

company_year_tables = [
    "balancesheet",
    "cashflow",
    "documents",
    "profitandloss"
]

for table_name in company_year_tables:

    if table_name in all_data:

        validator.validate_company_year_uniqueness(
            df=all_data[table_name],
            table_name=table_name
        )


# =========================================================
# DQ-03: FOREIGN KEY INTEGRITY
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-03: FOREIGN KEY INTEGRITY")
print("=" * 70)

child_tables = [
    "analysis",
    "balancesheet",
    "cashflow",
    "documents",
    "profitandloss",
    "prosandcons"
]

if "companies" in all_data:

    for table_name in child_tables:

        if table_name in all_data:

            validator.validate_foreign_key(
                child_df=all_data[table_name],
                parent_df=all_data["companies"],
                child_table=table_name,
                parent_table="companies"
            )


# =========================================================
# DQ-04: BALANCE SHEET BALANCE
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-04: BALANCE SHEET BALANCE")
print("=" * 70)

if "balancesheet" in all_data:

    validator.validate_balance_sheet(
        all_data["balancesheet"]
    )


# =========================================================
# DQ-05: OPM CROSS-CHECK
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-05: OPM CROSS-CHECK")
print("=" * 70)

if "profitandloss" in all_data:

    validator.validate_opm(
        all_data["profitandloss"]
    )


# =========================================================
# DQ-06: POSITIVE SALES
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-06: POSITIVE SALES")
print("=" * 70)

if "profitandloss" in all_data:

    validator.validate_positive_sales(
        all_data["profitandloss"]
    )


# =========================================================
# DQ-07: NET CASH FLOW
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-07: NET CASH FLOW")
print("=" * 70)

if "cashflow" in all_data:

    validator.validate_net_cash_flow(
        all_data["cashflow"]
    )


# =========================================================
# DQ-08: TAX RATE
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-08: TAX RATE")
print("=" * 70)

if "profitandloss" in all_data:

    validator.validate_tax_rate(
        all_data["profitandloss"]
    )


# =========================================================
# DQ-09: DIVIDEND PAYOUT CAP
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-09: DIVIDEND PAYOUT")
print("=" * 70)

if "profitandloss" in all_data:

    validator.validate_dividend_payout(
        all_data["profitandloss"]
    )


# =========================================================
# DQ-10: URL VALIDATION
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-10: URL VALIDATION")
print("=" * 70)

if "companies" in all_data:

    validator.validate_urls(
        df=all_data["companies"],
        table_name="companies",
        url_columns=[
            "website",
            "chart_link",
            "nse_profile",
            "bse_profile"
        ]
    )

if "documents" in all_data:

    validator.validate_urls(
        df=all_data["documents"],
        table_name="documents",
        url_columns=[
            "annual_report"
        ]
    )


# =========================================================
# DQ-11: EPS SIGN VALIDATION
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-11: EPS SIGN VALIDATION")
print("=" * 70)

if "profitandloss" in all_data:

    validator.validate_eps_sign(
        all_data["profitandloss"]
    )


# =========================================================
# DQ-12: BALANCE SHEET COMPONENT CHECK
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-12: BALANCE COMPONENT CHECK")
print("=" * 70)

if "balancesheet" in all_data:

    validator.validate_balance_components(
        all_data["balancesheet"]
    )


# =========================================================
# DQ-13: YEAR VALIDATION
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-13: YEAR VALIDATION")
print("=" * 70)

year_tables = [
    "balancesheet",
    "cashflow",
    "documents",
    "profitandloss"
]

for table_name in year_tables:

    if table_name in all_data:

        validator.validate_year_range(
            df=all_data[table_name],
            table_name=table_name
        )


# =========================================================
# DQ-14: REQUIRED FIELD CHECK
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-14: REQUIRED FIELD CHECK")
print("=" * 70)

required_field_config = {

    "companies": [
        "id",
        "company_name"
    ],

    "balancesheet": [
        "id",
        "company_id",
        "year"
    ],

    "cashflow": [
        "id",
        "company_id",
        "year"
    ],

    "profitandloss": [
        "id",
        "company_id",
        "year",
        "sales"
    ],

    "documents": [
        "id",
        "company_id",
        "year"
    ]
}

for table_name, columns in required_field_config.items():

    if table_name in all_data:

        validator.validate_required_fields(
            df=all_data[table_name],
            table_name=table_name,
            required_columns=columns
        )


# =========================================================
# DQ-15: NUMERIC COLUMN VALIDATION
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-15: NUMERIC VALUE VALIDATION")
print("=" * 70)

numeric_config = {

    "balancesheet": [
        "equity_capital",
        "reserves",
        "borrowings",
        "other_liabilities",
        "total_liabilities",
        "fixed_assets",
        "cwip",
        "investments",
        "other_asset",
        "total_assets"
    ],

    "cashflow": [
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow"
    ],

    "profitandloss": [
        "sales",
        "expenses",
        "operating_profit",
        "opm_percentage",
        "other_income",
        "interest",
        "depreciation",
        "profit_before_tax",
        "tax_percentage",
        "net_profit",
        "eps",
        "dividend_payout"
    ]
}

for table_name, columns in numeric_config.items():

    if table_name in all_data:

        validator.validate_numeric_columns(
            df=all_data[table_name],
            table_name=table_name,
            numeric_columns=columns
        )


# =========================================================
# DQ-16: COMPANY YEAR COVERAGE
# =========================================================

print("\n" + "=" * 70)
print("RUNNING DQ-16: COMPANY YEAR COVERAGE")
print("=" * 70)

coverage_tables = [
    "balancesheet",
    "cashflow",
    "profitandloss"
]

for table_name in coverage_tables:

    if table_name in all_data:

        validator.validate_company_coverage(
            df=all_data[table_name],
            table_name=table_name,
            minimum_years=5
        )


# =========================================================
# SAVE FAILURES
# =========================================================

print("\n" + "=" * 70)
print("SAVING VALIDATION FAILURES")
print("=" * 70)

failures_df = validator.save_failures()


# =========================================================
# VALIDATION SUMMARY
# =========================================================

print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

if failures_df.empty:

    print("\n✓ No validation failures found.")

else:

    summary = (
        failures_df
        .groupby(
            ["rule_id", "severity"]
        )
        .size()
        .reset_index(
            name="failure_count"
        )
    )

    print()

    print(
        summary.to_string(
            index=False
        )
    )


# =========================================================
# FINAL PROGRESS
# =========================================================

print("\n" + "=" * 70)
print("DAY 03 DATA QUALITY VALIDATION COMPLETED")
print("=" * 70)

for i in range(1, 17):

    print(f"✓ DQ-{i:02d} executed")


print("\nOutput file:")
print("output/validation_failures.csv")

print("\n" + "=" * 70)
print("SPRINT 1 - DAY 03 COMPLETED")
print("=" * 70)