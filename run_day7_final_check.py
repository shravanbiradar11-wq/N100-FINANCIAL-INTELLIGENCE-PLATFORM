import sqlite3
from pathlib import Path


DB_PATH = Path("db/nifty100.db")


EXPECTED_COUNTS = {
    "companies": 92,
    "analysis": 20,
    "balancesheet": 1312,
    "cashflow": 1187,
    "documents": 1585,
    "profitandloss": 1276,
    "prosandcons": 16,
}


def main():

    print("=" * 70)
    print("SPRINT 1 - FINAL DATABASE CHECK")
    print("=" * 70)

    if not DB_PATH.exists():

        print(
            f"✗ Database not found: {DB_PATH}"
        )

        return

    connection = sqlite3.connect(
        DB_PATH
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    try:

        all_passed = True

        # -------------------------------------------------
        # TABLE COUNTS
        # -------------------------------------------------

        print("\nTABLE COUNTS")
        print("-" * 70)

        for table, expected in EXPECTED_COUNTS.items():

            cursor = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            )

            actual = cursor.fetchone()[0]

            if actual == expected:

                print(
                    f"✓ {table:18} "
                    f"{actual}"
                )

            else:

                print(
                    f"✗ {table:18} "
                    f"{actual} "
                    f"(expected {expected})"
                )

                all_passed = False

        # -------------------------------------------------
        # FOREIGN KEY CHECK
        # -------------------------------------------------

        print("\nFOREIGN KEY CHECK")
        print("-" * 70)

        violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if not violations:

            print(
                "✓ 0 foreign key violations"
            )

        else:

            print(
                f"✗ {len(violations)} "
                f"foreign key violations"
            )

            all_passed = False

        # -------------------------------------------------
        # NULL YEAR CHECK
        # -------------------------------------------------

        print("\nNULL YEAR CHECK")
        print("-" * 70)

        year_tables = [
            "profitandloss",
            "balancesheet",
            "cashflow",
            "documents"
        ]

        for table in year_tables:

            cursor = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM {table}
                WHERE year IS NULL
                """
            )

            count = cursor.fetchone()[0]

            if count == 0:

                print(
                    f"✓ {table}: 0 NULL years"
                )

            else:

                print(
                    f"✗ {table}: "
                    f"{count} NULL years"
                )

                all_passed = False

        # -------------------------------------------------
        # DUPLICATE CHECK
        # -------------------------------------------------

        print("\nDUPLICATE CHECK")
        print("-" * 70)

        duplicate_tables = [
            "profitandloss",
            "balancesheet",
            "cashflow"
        ]

        for table in duplicate_tables:

            cursor = connection.execute(
                f"""
                SELECT
                    company_id,
                    year,
                    COUNT(*) AS cnt
                FROM {table}
                GROUP BY
                    company_id,
                    year
                HAVING COUNT(*) > 1
                """
            )

            duplicates = cursor.fetchall()

            if not duplicates:

                print(
                    f"✓ {table}: "
                    f"0 duplicate groups"
                )

            else:

                print(
                    f"✗ {table}: "
                    f"{len(duplicates)} "
                    f"duplicate groups"
                )

                all_passed = False

        # -------------------------------------------------
        # FINAL RESULT
        # -------------------------------------------------

        print("\n" + "=" * 70)

        if all_passed:

            print(
                "✓ SPRINT 1 DATABASE CHECK PASSED"
            )

            print(
                "✓ DATABASE IS READY FOR REVIEW"
            )

        else:

            print(
                "✗ SPRINT 1 DATABASE CHECK FAILED"
            )

            print(
                "Review the failed checks above."
            )

        print("=" * 70)

    finally:

        connection.close()


if __name__ == "__main__":
    main()