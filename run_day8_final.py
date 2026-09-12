from pathlib import Path
import sqlite3
import subprocess
import sys

import pandas as pd


DATABASE_PATH = Path("db/nifty100.db")
OUTPUT_DIR = Path("output")

# The source companies.xlsx contains 92 records, but the
# child tables reference 8 additional company IDs.
# Day 05 now resolves those IDs into the master table.
EXPECTED_COMPANIES = 100

YEAR_TABLES = [
    "profitandloss",
    "balancesheet",
    "cashflow",
    "documents",
]

UNIQUE_YEAR_TABLES = [
    "profitandloss",
    "balancesheet",
    "cashflow",
]

EXPECTED_TABLES = [
    "companies",
    "analysis",
    "balancesheet",
    "cashflow",
    "documents",
    "profitandloss",
    "prosandcons",
]


def heading(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def passed(message):
    print(f"✓ {message}")


def failed(message):
    print(f"✗ {message}")


def get_connection():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.execute(
        "PRAGMA foreign_keys = ON;"
    )

    return connection


def check_database():
    heading("DATABASE CHECK")

    if not DATABASE_PATH.exists():
        failed(
            f"Database not found: {DATABASE_PATH}"
        )
        return False

    passed(
        f"Database exists: {DATABASE_PATH}"
    )

    return True


def check_tables(connection):
    heading("TABLE CHECK")

    actual = {
        row[0]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%';
            """
        ).fetchall()
    }

    missing = set(
        EXPECTED_TABLES
    ) - actual

    if missing:
        failed(
            "Missing tables: "
            + ", ".join(sorted(missing))
        )
        return False

    passed(
        f"All {len(EXPECTED_TABLES)} required tables exist."
    )

    return True


def check_row_counts(connection):
    heading("DATABASE ROW COUNT CHECK")

    results = []
    all_ok = True

    cursor = connection.cursor()

    for table in EXPECTED_TABLES:

        cursor.execute(
            f"SELECT COUNT(*) FROM {table};"
        )

        actual = cursor.fetchone()[0]

        if table == "companies":
            expected = EXPECTED_COMPANIES
        else:
            expected = None

        results.append({
            "table_name": table,
            "actual_rows": actual,
            "expected_rows": expected,
        })

        if table == "companies":

            if actual == expected:
                passed(
                    f"{table}: {actual} rows"
                )
            else:
                failed(
                    f"{table}: {actual} rows "
                    f"(expected {expected})"
                )
                all_ok = False

        else:
            passed(
                f"{table}: {actual} rows"
            )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    pd.DataFrame(results).to_csv(
        OUTPUT_DIR /
        "day8_row_count_check.csv",
        index=False
    )

    passed(
        "All child-table counts reported."
    )

    return all_ok


def check_foreign_keys(connection):
    heading("FOREIGN KEY CHECK")

    enabled = connection.execute(
        "PRAGMA foreign_keys;"
    ).fetchone()[0]

    if enabled != 1:
        failed(
            "SQLite foreign-key enforcement disabled."
        )
        return False

    passed(
        "SQLite foreign-key enforcement enabled."
    )

    violations = connection.execute(
        "PRAGMA foreign_key_check;"
    ).fetchall()

    if violations:
        failed(
            f"{len(violations)} foreign-key violations found."
        )

        for row in violations[:20]:
            print(row)

        return False

    passed(
        "0 foreign-key violations."
    )

    return True


def check_null_years(connection):
    heading("NULL YEAR CHECK")

    all_ok = True

    for table in YEAR_TABLES:

        count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM {table}
            WHERE year IS NULL;
            """
        ).fetchone()[0]

        if count == 0:
            passed(
                f"{table}: 0 NULL years"
            )
        else:
            failed(
                f"{table}: {count} NULL years"
            )
            all_ok = False

    return all_ok


def check_duplicates(connection):
    heading("DUPLICATE CHECK")

    all_ok = True

    for table in UNIQUE_YEAR_TABLES:

        duplicates = connection.execute(
            f"""
            SELECT company_id, year, COUNT(*)
            FROM {table}
            GROUP BY company_id, year
            HAVING COUNT(*) > 1;
            """
        ).fetchall()

        if not duplicates:
            passed(
                f"{table}: 0 duplicate company/year groups"
            )
        else:
            failed(
                f"{table}: {len(duplicates)} duplicate groups"
            )
            all_ok = False

    return all_ok


def check_primary_keys(connection):
    heading("PRIMARY KEY CHECK")

    all_ok = True

    for table in EXPECTED_TABLES:

        null_ids = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM {table}
            WHERE id IS NULL;
            """
        ).fetchone()[0]

        duplicate_ids = connection.execute(
            f"""
            SELECT COUNT(*) - COUNT(DISTINCT id)
            FROM {table};
            """
        ).fetchone()[0]

        if (
            null_ids == 0
            and duplicate_ids == 0
        ):
            passed(
                f"{table}: primary key values valid"
            )
        else:
            failed(
                f"{table}: {null_ids} NULL IDs, "
                f"{duplicate_ids} duplicate IDs"
            )
            all_ok = False

    return all_ok


def check_audit():
    heading("LOAD AUDIT CHECK")

    audit_path = (
        OUTPUT_DIR /
        "load_audit.csv"
    )

    if not audit_path.exists():
        failed(
            f"Audit file not found: {audit_path}"
        )
        return False

    df = pd.read_csv(
        audit_path
    )

    required = {
        "table_name",
        "rows_received",
        "rows_loaded",
        "rows_repaired",
        "rows_deduplicated",
        "rows_unresolved",
        "status",
    }

    missing = (
        required
        - set(df.columns)
    )

    if missing:
        failed(
            "Missing audit columns: "
            + ", ".join(sorted(missing))
        )
        return False

    unresolved = int(
        df["rows_unresolved"]
        .fillna(0)
        .sum()
    )

    if unresolved != 0:
        failed(
            f"Audit reports {unresolved} unresolved rows."
        )
        return False

    if (
        (df["status"] == "SUCCESS")
        .all()
    ):
        passed(
            "Load audit reports SUCCESS for all tables."
        )
        return True

    failed(
        "One or more tables are not marked SUCCESS."
    )

    return False


def run_tests():
    heading("AUTOMATED TEST CHECK")

    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/etl",
        "-v",
    ]

    result = subprocess.run(
        command,
        check=False
    )

    if result.returncode == 0:
        passed(
            "All ETL automated tests passed."
        )
        return True

    failed(
        "ETL automated tests failed."
    )

    return False


def main():

    heading(
        "SPRINT 1 - DAY 08\n"
        "FINAL ETL PIPELINE VERIFICATION"
    )

    checks = {}

    checks["database"] = (
        check_database()
    )

    if not checks["database"]:
        sys.exit(1)

    connection = get_connection()

    try:
        checks["tables"] = (
            check_tables(connection)
        )

        checks["row_counts"] = (
            check_row_counts(connection)
        )

        checks["foreign_keys"] = (
            check_foreign_keys(connection)
        )

        checks["null_years"] = (
            check_null_years(connection)
        )

        checks["duplicates"] = (
            check_duplicates(connection)
        )

        checks["primary_keys"] = (
            check_primary_keys(connection)
        )

    finally:
        connection.close()

    checks["audit"] = check_audit()
    checks["tests"] = run_tests()

    heading("DAY 08 FINAL SUMMARY")

    for name, result in checks.items():

        label = (
            name
            .replace("_", " ")
            .title()
        )

        if result:
            passed(label)
        else:
            failed(label)

    heading(
        "SPRINT 1 - DAY 08 FINAL STATUS"
    )

    if all(checks.values()):

        passed(
            "COMPLETE ETL PIPELINE VERIFIED"
        )

        passed(
            "DATABASE STRUCTURE VERIFIED"
        )

        passed(
            "DATA INTEGRITY VERIFIED"
        )

        passed(
            "FOREIGN KEYS VERIFIED"
        )

        passed(
            "YEAR VALIDATION VERIFIED"
        )

        passed(
            "DUPLICATE CHECK VERIFIED"
        )

        passed(
            "PRIMARY KEYS VERIFIED"
        )

        passed(
            "LOAD AUDIT VERIFIED"
        )

        passed(
            "AUTOMATED TESTS VERIFIED"
        )

        print(
            "\n" + "=" * 70
        )
        print(
            "DAY 08 COMPLETED SUCCESSFULLY"
        )
        print(
            "=" * 70
        )

    else:

        failed(
            "DAY 08 VERIFICATION FAILED"
        )

        print(
            "Review the failed checks above."
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
