import sqlite3
import random
from pathlib import Path


# =========================================================
# CONFIGURATION
# =========================================================

DB_PATH = Path("db/nifty100.db")


# =========================================================
# CONNECT DATABASE
# =========================================================

def connect_database():

    if not DB_PATH.exists():

        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    connection = sqlite3.connect(
        DB_PATH
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# =========================================================
# GET TABLE COUNT
# =========================================================

def get_table_count(
    connection,
    table_name
):

    cursor = connection.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    )

    return cursor.fetchone()[0]


# =========================================================
# GET COMPANY LIST
# =========================================================

def get_companies(connection):

    cursor = connection.execute(
        """
        SELECT id, company_name
        FROM companies
        ORDER BY id
        """
    )

    return cursor.fetchall()


# =========================================================
# YEAR COVERAGE FOR COMPANY
# =========================================================

def get_year_coverage(
    connection,
    company_id
):

    tables = [
        "profitandloss",
        "balancesheet",
        "cashflow",
        "documents"
    ]

    results = {}

    for table in tables:

        cursor = connection.execute(
            f"""
            SELECT
                MIN(year),
                MAX(year),
                COUNT(DISTINCT year)
            FROM {table}
            WHERE company_id = ?
            """,
            (company_id,)
        )

        row = cursor.fetchone()

        results[table] = {
            "min_year": row[0],
            "max_year": row[1],
            "year_count": row[2]
        }

    return results


# =========================================================
# CHECK COMPANY
# =========================================================

def review_company(
    connection,
    company_id,
    company_name
):

    print("\n" + "-" * 70)

    print(
        f"COMPANY: {company_name}"
    )

    print(
        f"COMPANY ID: {company_id}"
    )

    print("-" * 70)

    coverage = get_year_coverage(
        connection,
        company_id
    )

    for table, data in coverage.items():

        print(
            f"{table:18} "
            f"Years: {data['min_year']} - "
            f"{data['max_year']} | "
            f"Count: {data['year_count']}"
        )


# =========================================================
# FIND COMPANIES WITH LESS THAN 5 YEARS
# =========================================================

def find_companies_less_than_5_years(
    connection
):

    print("\n" + "=" * 70)

    print(
        "COMPANIES WITH LESS THAN 5 YEARS"
    )

    print("=" * 70)

    cursor = connection.execute(
        """
        SELECT
            c.id,
            c.company_name,
            COUNT(DISTINCT p.year) AS year_count
        FROM companies c
        LEFT JOIN profitandloss p
            ON c.id = p.company_id
        GROUP BY
            c.id,
            c.company_name
        HAVING COUNT(DISTINCT p.year) < 5
        ORDER BY year_count
        """
    )

    rows = cursor.fetchall()

    if not rows:

        print(
            "✓ No companies have fewer than 5 "
            "P&L years."
        )

        return rows

    for row in rows:

        print(
            f"{row[0]:15} "
            f"{row[1]:35} "
            f"Years: {row[2]}"
        )

    return rows


# =========================================================
# TABLE ROW COUNTS
# =========================================================

def show_table_counts(connection):

    tables = [
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons"
    ]

    print("\n" + "=" * 70)

    print(
        "DATABASE ROW COUNTS"
    )

    print("=" * 70)

    for table in tables:

        count = get_table_count(
            connection,
            table
        )

        print(
            f"{table:18} : {count}"
        )


# =========================================================
# CHECK NULL YEARS
# =========================================================

def check_null_years(connection):

    print("\n" + "=" * 70)

    print(
        "NULL YEAR CHECK"
    )

    print("=" * 70)

    tables = [
        "profitandloss",
        "balancesheet",
        "cashflow",
        "documents"
    ]

    total = 0

    for table in tables:

        cursor = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM {table}
            WHERE year IS NULL
            """
        )

        count = cursor.fetchone()[0]

        total += count

        if count == 0:

            print(
                f"✓ {table}: 0 NULL years"
            )

        else:

            print(
                f"✗ {table}: {count} NULL years"
            )

    return total


# =========================================================
# CHECK FOREIGN KEYS
# =========================================================

def check_foreign_keys(connection):

    print("\n" + "=" * 70)

    print(
        "FOREIGN KEY CHECK"
    )

    print("=" * 70)

    cursor = connection.execute(
        "PRAGMA foreign_key_check"
    )

    rows = cursor.fetchall()

    if not rows:

        print(
            "✓ 0 foreign key violations"
        )

    else:

        print(
            f"✗ {len(rows)} foreign key violations"
        )

        for row in rows:

            print(row)

    return rows


# =========================================================
# CHECK DUPLICATE COMPANY + YEAR
# =========================================================

def check_duplicates(connection):

    print("\n" + "=" * 70)

    print(
        "DUPLICATE (COMPANY_ID, YEAR) CHECK"
    )

    print("=" * 70)

    tables = [
        "profitandloss",
        "balancesheet",
        "cashflow"
    ]

    total_duplicates = 0

    for table in tables:

        cursor = connection.execute(
            f"""
            SELECT
                company_id,
                year,
                COUNT(*) AS record_count
            FROM {table}
            GROUP BY
                company_id,
                year
            HAVING COUNT(*) > 1
            """
        )

        rows = cursor.fetchall()

        if not rows:

            print(
                f"✓ {table}: no duplicates"
            )

        else:

            print(
                f"✗ {table}: "
                f"{len(rows)} duplicate groups"
            )

            for row in rows:

                print(
                    f"  {row}"
                )

            total_duplicates += len(rows)

    return total_duplicates


# =========================================================
# MAIN
# =========================================================

def main():

    print("\n" + "=" * 70)
    print("SPRINT 1 - DAY 06")
    print("DATA QUALITY MANUAL REVIEW")
    print("=" * 70)

    connection = connect_database()

    try:

        # -------------------------------------------------
        # 1. DATABASE COUNTS
        # -------------------------------------------------

        show_table_counts(
            connection
        )

        # -------------------------------------------------
        # 2. NULL YEAR CHECK
        # -------------------------------------------------

        null_years = check_null_years(
            connection
        )

        # -------------------------------------------------
        # 3. FOREIGN KEY CHECK
        # -------------------------------------------------

        fk_errors = check_foreign_keys(
            connection
        )

        # -------------------------------------------------
        # 4. DUPLICATE CHECK
        # -------------------------------------------------

        duplicate_errors = check_duplicates(
            connection
        )

        # -------------------------------------------------
        # 5. GET COMPANIES
        # -------------------------------------------------

        companies = get_companies(
            connection
        )

        print("\n" + "=" * 70)

        print(
            "RANDOM COMPANY MANUAL REVIEW"
        )

        print("=" * 70)

        print(
            f"Total companies: "
            f"{len(companies)}"
        )

        # -------------------------------------------------
        # 6. SELECT 5 RANDOM COMPANIES
        # -------------------------------------------------

        sample_size = min(
            5,
            len(companies)
        )

        random_companies = random.sample(
            companies,
            sample_size
        )

        for company_id, company_name in random_companies:

            review_company(
                connection,
                company_id,
                company_name
            )

        # -------------------------------------------------
        # 7. LESS THAN 5 YEARS
        # -------------------------------------------------

        less_than_5 = (
            find_companies_less_than_5_years(
                connection
            )
        )

        # -------------------------------------------------
        # 8. FINAL SUMMARY
        # -------------------------------------------------

        print("\n" + "=" * 70)

        print(
            "DAY 06 REVIEW SUMMARY"
        )

        print("=" * 70)

        if null_years == 0:

            print(
                "✓ NULL year check: PASSED"
            )

        else:

            print(
                "✗ NULL year check: FAILED"
            )

        if len(fk_errors) == 0:

            print(
                "✓ Foreign key check: PASSED"
            )

        else:

            print(
                "✗ Foreign key check: FAILED"
            )

        if duplicate_errors == 0:

            print(
                "✓ Duplicate check: PASSED"
            )

        else:

            print(
                "✗ Duplicate check: FAILED"
            )

        print(
            f"✓ Random companies reviewed: "
            f"{sample_size}"
        )

        print(
            f"Companies with <5 P&L years: "
            f"{len(less_than_5)}"
        )

        print("\n" + "=" * 70)

        print(
            "DAY 06 REVIEW COMPLETED"
        )

        print("=" * 70)

    finally:

        connection.close()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()