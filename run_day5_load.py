from pathlib import Path
from datetime import datetime
import sqlite3

import pandas as pd

from src.etl.loader import load_and_normalize
from src.etl.database_loader import DatabaseLoader


# =========================================================
# DAY 05 - FINAL FIXED DATA LOADER
# =========================================================
#
# Fixes:
# 1. AGTL -> ATGL ticker alias
# 2. Missing companies referenced by child tables are added
#    to the master table as minimal master records.
# 3. NULL years are removed before SQLite insertion.
# 4. Duplicate (company_id, year) rows are deduplicated.
# 5. Database is always rebuilt from a clean state.
# 6. Audit distinguishes repaired/deduplicated rows from
#    genuinely unresolved rows.
#
# IMPORTANT:
# The source companies.xlsx currently contains 92 companies,
# while the child files reference 8 additional valid IDs:
# ULTRACEMCO, UNIONBANK, UNITDSPR, VBL, VEDL, WIPRO,
# ZOMATO, ZYDUSLIFE.
#
# Therefore the final master table becomes 100 companies.
# The missing master records are marked as AUTO-ADDED and
# contain the ticker/company ID as their company_name.
# Replace those placeholder records with complete metadata
# later if desired.
# =========================================================


RAW_DATA_PATH = Path("data/raw")
DATABASE_PATH = "db/nifty100.db"
SCHEMA_PATH = "db/schema.sql"

OUTPUT_DIR = Path("output")
AUDIT_PATH = OUTPUT_DIR / "load_audit.csv"
REPAIR_AUDIT_PATH = OUTPUT_DIR / "day5_repairs.csv"

LOAD_ORDER = [
    "companies",
    "analysis",
    "balancesheet",
    "cashflow",
    "profitandloss",
    "documents",
    "prosandcons",
]

YEAR_TABLES = {
    "balancesheet",
    "cashflow",
    "profitandloss",
}

# Known source ticker correction.
TICKER_ALIASES = {
    "AGTL": "ATGL",
}


# =========================================================
# HELPERS
# =========================================================

def heading(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def normalize_company_id(value):
    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    if not value or value in {"NAN", "NONE", "NULL"}:
        return None

    return TICKER_ALIASES.get(value, value)


def normalize_company_ids(df):
    df = df.copy()

    if "id" in df.columns:
        df["id"] = df["id"].apply(normalize_company_id)

    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].apply(
            normalize_company_id
        )

    return df


def clean_year(df):
    df = df.copy()

    if "year" not in df.columns:
        return df, 0

    original = len(df)

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce"
    )

    invalid = df["year"].isna()

    removed = int(invalid.sum())

    if removed:
        df = df.loc[~invalid].copy()

    if not df.empty:
        df["year"] = df["year"].astype(int)

    return df, removed


def deduplicate_company_year(df):
    if (
        "company_id" not in df.columns
        or "year" not in df.columns
    ):
        return df, 0, pd.DataFrame()

    df = df.copy()

    df["company_id"] = df["company_id"].apply(
        normalize_company_id
    )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce"
    )

    # NULL years are handled separately.
    df = df.loc[df["year"].notna()].copy()
    df["year"] = df["year"].astype(int)

    # Keep the highest source id when duplicate
    # company/year records exist.
    if "id" in df.columns:
        df["_sort_id"] = pd.to_numeric(
            df["id"],
            errors="coerce"
        ).fillna(-1)
    else:
        df["_sort_id"] = range(len(df))

    df = df.sort_values(
        "_sort_id",
        ascending=False
    )

    duplicate_mask = df.duplicated(
        subset=["company_id", "year"],
        keep="first"
    )

    duplicate_rows = df.loc[
        duplicate_mask
    ].copy()

    cleaned = df.loc[
        ~duplicate_mask
    ].copy()

    cleaned = cleaned.sort_values(
        "_sort_id"
    )

    duplicate_rows = duplicate_rows.drop(
        columns=["_sort_id"],
        errors="ignore"
    )

    cleaned = cleaned.drop(
        columns=["_sort_id"],
        errors="ignore"
    )

    return (
        cleaned,
        len(duplicate_rows),
        duplicate_rows,
    )


def remove_invalid_required_values(df, table_name):
    required = {
        "companies": ["id"],
        "analysis": ["id", "company_id"],
        "balancesheet": ["id", "company_id", "year"],
        "cashflow": ["id", "company_id", "year"],
        "profitandloss": ["id", "company_id", "year"],
        "documents": ["id", "company_id"],
        "prosandcons": ["id", "company_id"],
    }.get(table_name, [])

    existing = [
        column
        for column in required
        if column in df.columns
    ]

    if not existing:
        return df.copy(), 0, pd.DataFrame()

    df = df.copy()

    for column in existing:
        if df[column].dtype == "object":
            df[column] = (
                df[column]
                .replace(
                    r"^\s*$",
                    pd.NA,
                    regex=True
                )
            )

    invalid_mask = (
        df[existing]
        .isna()
        .any(axis=1)
    )

    invalid_rows = df.loc[
        invalid_mask
    ].copy()

    cleaned = df.loc[
        ~invalid_mask
    ].copy()

    return (
        cleaned,
        len(invalid_rows),
        invalid_rows,
    )


# =========================================================
# AUTO-ADD MISSING MASTER COMPANIES
# =========================================================

def get_all_child_company_ids():
    ids = set()

    for table_name in LOAD_ORDER:
        if table_name == "companies":
            continue

        path = (
            RAW_DATA_PATH /
            f"{table_name}.xlsx"
        )

        if not path.exists():
            continue

        try:
            df = load_and_normalize(path)
        except Exception:
            continue

        if "company_id" not in df.columns:
            continue

        for value in df["company_id"].dropna():
            normalized = normalize_company_id(value)

            if normalized:
                ids.add(normalized)

    return ids


def build_missing_company_rows(
    companies_df,
    referenced_ids,
):
    companies_df = companies_df.copy()

    existing_ids = {
        normalize_company_id(value)
        for value in companies_df["id"]
        if normalize_company_id(value)
    }

    missing_ids = sorted(
        referenced_ids - existing_ids
    )

    if not missing_ids:
        return companies_df, []

    print(
        f"\n⚠ Missing master company IDs found: "
        f"{len(missing_ids)}"
    )

    for company_id in missing_ids:
        print(
            f"  + Auto-adding: {company_id}"
        )

    # Create rows using the exact columns of companies.xlsx.
    # Only id/company_name are populated with useful values.
    rows = []

    for company_id in missing_ids:

        row = {
            column: pd.NA
            for column in companies_df.columns
        }

        row["id"] = company_id

        if "company_name" in row:
            row["company_name"] = company_id

        rows.append(row)

    missing_df = pd.DataFrame(
        rows,
        columns=companies_df.columns
    )

    companies_df = pd.concat(
        [
            companies_df,
            missing_df,
        ],
        ignore_index=True
    )

    return companies_df, missing_ids


# =========================================================
# LOAD A TABLE
# =========================================================

def load_table(
    database_loader,
    df,
    table_name,
):
    try:
        database_loader.load_dataframe(
            df=df,
            table_name=table_name,
            if_exists="append",
        )
    except Exception as error:
        print(
            f"✗ SQLite loading failed for "
            f"{table_name}: {error}"
        )
        raise


# =========================================================
# MAIN
# =========================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    heading(
        "SPRINT 1 - DAY 05\n"
        "FULL DATA LOAD INTO SQLITE - FIXED VERSION"
    )

    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    database_loader = DatabaseLoader(
        database_path=DATABASE_PATH,
        schema_path=SCHEMA_PATH,
    )

    database_loader.create_database(
        reset=True
    )

    repair_records = []
    audit_records = []

    # -----------------------------------------------------
    # LOAD COMPANIES FIRST
    # -----------------------------------------------------

    companies_path = (
        RAW_DATA_PATH /
        "companies.xlsx"
    )

    if not companies_path.exists():
        raise FileNotFoundError(
            f"Missing source file: {companies_path}"
        )

    heading("PROCESSING: companies")

    companies_df = load_and_normalize(
        companies_path
    )

    companies_df = normalize_company_ids(
        companies_df
    )

    companies_df, required_rejected, rejected_rows = (
        remove_invalid_required_values(
            companies_df,
            "companies",
        )
    )

    # Find IDs referenced anywhere in child tables.
    referenced_ids = get_all_child_company_ids()

    companies_df, added_company_ids = (
        build_missing_company_rows(
            companies_df,
            referenced_ids,
        )
    )

    print(
        f"Source company rows: "
        f"{len(companies_df) - len(added_company_ids)}"
    )

    print(
        f"Final company rows: "
        f"{len(companies_df)}"
    )

    if added_company_ids:
        for company_id in added_company_ids:
            repair_records.append({
                "timestamp": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "table_name": "companies",
                "repair_type": "AUTO_ADDED_MASTER",
                "company_id": company_id,
                "year": None,
                "details": (
                    "Added missing master company ID "
                    "referenced by child tables."
                ),
            })

    load_table(
        database_loader,
        companies_df,
        "companies",
    )

    audit_records.append({
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "table_name": "companies",
        "rows_received": len(companies_df),
        "rows_loaded": len(companies_df),
        "rows_repaired": len(added_company_ids),
        "rows_deduplicated": 0,
        "rows_unresolved": 0,
        "status": "SUCCESS",
    })

    # IDs are now guaranteed to exist in master.
    valid_company_ids = set(
        companies_df["id"].dropna()
    )

    # -----------------------------------------------------
    # CHILD TABLES
    # -----------------------------------------------------

    for table_name in LOAD_ORDER:

        if table_name == "companies":
            continue

        heading(
            f"PROCESSING: {table_name}"
        )

        path = (
            RAW_DATA_PATH /
            f"{table_name}.xlsx"
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Missing source file: {path}"
            )

        df = load_and_normalize(path)

        source_rows = len(df)

        df = normalize_company_ids(df)

        # -----------------------------------------------
        # YEAR CLEANING
        # -----------------------------------------------

        year_removed = 0

        if table_name in YEAR_TABLES:
            df, year_removed = clean_year(df)

            if year_removed:
                print(
                    f"⚠ Removed NULL/invalid years: "
                    f"{year_removed}"
                )

                repair_records.append({
                    "timestamp": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "table_name": table_name,
                    "repair_type": "REMOVE_INVALID_YEAR",
                    "company_id": None,
                    "year": None,
                    "details": (
                        f"{year_removed} rows had "
                        "NULL/invalid year."
                    ),
                })

        # -----------------------------------------------
        # REQUIRED FIELDS
        # -----------------------------------------------

        (
            df,
            required_removed,
            required_rows,
        ) = remove_invalid_required_values(
            df,
            table_name,
        )

        if required_removed:
            print(
                f"⚠ Removed invalid required rows: "
                f"{required_removed}"
            )

        # -----------------------------------------------
        # FOREIGN KEY CHECK
        # -----------------------------------------------

        fk_removed = 0

        if "company_id" in df.columns:

            df["company_id"] = (
                df["company_id"]
                .apply(normalize_company_id)
            )

            invalid_fk_mask = (
                ~df["company_id"]
                .isin(valid_company_ids)
            )

            invalid_fk_rows = df.loc[
                invalid_fk_mask
            ].copy()

            fk_removed = len(
                invalid_fk_rows
            )

            if fk_removed:
                print(
                    "✗ Unresolved foreign-key rows: "
                    f"{fk_removed}"
                )

                print(
                    invalid_fk_rows[
                        ["company_id"]
                        + (
                            ["year"]
                            if "year" in invalid_fk_rows.columns
                            else []
                        )
                    ]
                    .drop_duplicates()
                    .to_string(index=False)
                )

                # Do NOT silently load unresolved FK rows.
                df = df.loc[
                    ~invalid_fk_mask
                ].copy()

        # -----------------------------------------------
        # DUPLICATES
        # -----------------------------------------------

        duplicate_removed = 0

        if table_name in YEAR_TABLES:

            (
                df,
                duplicate_removed,
                duplicate_rows,
            ) = deduplicate_company_year(df)

            if duplicate_removed:
                print(
                    f"⚠ Deduplicated "
                    f"{duplicate_removed} "
                    "(company_id, year) rows."
                )

                for _, row in duplicate_rows.iterrows():
                    repair_records.append({
                        "timestamp": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "table_name": table_name,
                        "repair_type": "DEDUPLICATE",
                        "company_id": row.get(
                            "company_id"
                        ),
                        "year": row.get(
                            "year"
                        ),
                        "details": (
                            "Duplicate company/year "
                            "record removed; highest "
                            "source ID retained."
                        ),
                    })

        # -----------------------------------------------
        # FINAL REQUIRED CHECK
        # -----------------------------------------------

        required_columns = {
            "analysis": ["id", "company_id"],
            "balancesheet": ["id", "company_id", "year"],
            "cashflow": ["id", "company_id", "year"],
            "profitandloss": ["id", "company_id", "year"],
            "documents": ["id", "company_id"],
            "prosandcons": ["id", "company_id"],
        }.get(table_name, [])

        final_invalid_mask = pd.Series(
            False,
            index=df.index
        )

        for column in required_columns:
            if column in df.columns:
                final_invalid_mask |= (
                    df[column].isna()
                )

        unresolved = int(
            final_invalid_mask.sum()
        )

        if unresolved:
            print(
                f"✗ UNRESOLVED required-field rows: "
                f"{unresolved}"
            )

            df = df.loc[
                ~final_invalid_mask
            ].copy()

        # -----------------------------------------------
        # LOAD
        # -----------------------------------------------

        rows_to_load = len(df)

        print("\n" + "-" * 70)
        print(
            f"LOADING TABLE: {table_name}"
        )
        print("-" * 70)

        print(
            f"Source rows: {source_rows}"
        )

        print(
            f"Rows to load: {rows_to_load}"
        )

        load_table(
            database_loader,
            df,
            table_name,
        )

        # -----------------------------------------------
        # AUDIT
        # -----------------------------------------------

        repaired = (
            year_removed
            + required_removed
        )

        audit_records.append({
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "table_name": table_name,
            "rows_received": source_rows,
            "rows_loaded": rows_to_load,
            "rows_repaired": repaired,
            "rows_deduplicated": duplicate_removed,
            "rows_unresolved": unresolved + fk_removed,
            "status": (
                "SUCCESS"
                if (unresolved + fk_removed) == 0
                else "SUCCESS_WITH_UNRESOLVED"
            ),
        })

    # -----------------------------------------------------
    # SAVE AUDITS
    # -----------------------------------------------------

    audit_df = pd.DataFrame(
        audit_records
    )

    audit_df.to_csv(
        AUDIT_PATH,
        index=False
    )

    repair_df = pd.DataFrame(
        repair_records,
        columns=[
            "timestamp",
            "table_name",
            "repair_type",
            "company_id",
            "year",
            "details",
        ],
    )

    repair_df.to_csv(
        REPAIR_AUDIT_PATH,
        index=False
    )

    # -----------------------------------------------------
    # DATABASE SUMMARY
    # -----------------------------------------------------

    database_loader.print_database_summary()

    # -----------------------------------------------------
    # FK CHECK
    # -----------------------------------------------------

    heading("FOREIGN KEY VALIDATION")

    violations = (
        database_loader.foreign_key_check()
    )

    if violations:
        print(
            f"✗ {len(violations)} "
            "foreign-key violations."
        )
    else:
        print(
            "✓ 0 foreign-key violations."
        )

    # -----------------------------------------------------
    # AUDIT
    # -----------------------------------------------------

    heading("LOAD AUDIT SUMMARY")

    print(
        audit_df.to_string(
            index=False
        )
    )

    # -----------------------------------------------------
    # FINAL
    # -----------------------------------------------------

    unresolved_total = int(
        audit_df["rows_unresolved"].sum()
    )

    heading(
        "SPRINT 1 - DAY 05 FINAL STATUS"
    )

    if (
        not violations
        and unresolved_total == 0
    ):

        print(
            "✓ DATABASE CREATED FROM CLEAN STATE"
        )

        print(
            "✓ MISSING MASTER IDs RESOLVED"
        )

        print(
            "✓ TICKER ALIASES NORMALIZED"
        )

        print(
            "✓ NULL/INVALID YEARS REMOVED"
        )

        print(
            "✓ DUPLICATE COMPANY/YEAR RECORDS RESOLVED"
        )

        print(
            "✓ ALL VALID ROWS LOADED"
        )

        print(
            "✓ FOREIGN KEY CHECK PASSED"
        )

        print(
            "✓ DAY 05 LOAD COMPLETED SUCCESSFULLY"
        )

    else:

        print(
            "✗ DAY 05 STILL HAS UNRESOLVED DATA"
        )

        print(
            f"Unresolved rows: "
            f"{unresolved_total}"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()
