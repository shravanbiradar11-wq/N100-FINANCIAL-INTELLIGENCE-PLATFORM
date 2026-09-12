import sqlite3

DB = "db/nifty100.db"

REQUIRED_COLUMNS = [
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
    "composite_quality_score",
]


def main():
    print("=" * 70)
    print("SPRINT 2 - DAY 14")
    print("FINAL RATIO ENGINE VALIDATION")
    print("=" * 70)

    conn = sqlite3.connect(DB)

    # ---------------------------------------------------------
    # ROW COUNT
    # ---------------------------------------------------------

    row_count = conn.execute(
        "SELECT COUNT(*) FROM financial_ratios"
    ).fetchone()[0]

    print("\nDATABASE CHECK")
    print("-" * 70)
    print(f"financial_ratios rows: {row_count}")

    if row_count >= 1100:
        print("✓ Row count >= 1100")
    else:
        print("✗ Row count below 1100")

    # ---------------------------------------------------------
    # COLUMNS
    # ---------------------------------------------------------

    actual_columns = {
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(financial_ratios)"
        ).fetchall()
    }

    print("\nKPI COLUMN CHECK")
    print("-" * 70)

    missing = []

    for column in REQUIRED_COLUMNS:
        if column in actual_columns:
            print(f"✓ {column}")
        else:
            print(f"✗ {column}")
            missing.append(column)

    # ---------------------------------------------------------
    # NULL-ONLY CHECK
    # ---------------------------------------------------------

    print("\nNULL-ONLY KPI CHECK")
    print("-" * 70)

    null_only = []

    for column in REQUIRED_COLUMNS:

        if column not in actual_columns:
            continue

        query = f"""
            SELECT COUNT(*)
            FROM financial_ratios
            WHERE "{column}" IS NOT NULL
        """

        populated = conn.execute(query).fetchone()[0]

        if populated > 0:
            print(f"✓ {column}: {populated} populated")
        else:
            print(f"✗ {column}: completely NULL")
            null_only.append(column)

    # ---------------------------------------------------------
    # FOREIGN KEYS
    # ---------------------------------------------------------

    print("\nFOREIGN KEY CHECK")
    print("-" * 70)

    violations = conn.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    if len(violations) == 0:
        print("✓ 0 foreign-key violations")
    else:
        print(f"✗ {len(violations)} foreign-key violations")

    conn.close()

    # ---------------------------------------------------------
    # FINAL STATUS
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("DAY 14 FINAL STATUS")
    print("=" * 70)

    if (
        row_count >= 1100
        and not missing
        and not null_only
        and len(violations) == 0
    ):
        print("✓ DAY 14 DATABASE VALIDATION PASSED")
        print("✓ SPRINT 2 RATIO ENGINE DATABASE CHECK PASSED")
    else:
        print("✗ DAY 14 VALIDATION FAILED")
        print("Review the failed checks above.")


if __name__ == "__main__":
    main()