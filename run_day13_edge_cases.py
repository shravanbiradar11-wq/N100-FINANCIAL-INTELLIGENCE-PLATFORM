from pathlib import Path
import re
import sqlite3
from datetime import datetime

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================
DB_PATH = Path("db/nifty100.db")
SOURCE_PATH = Path("data/raw/companies.xlsx")
LOG_PATH = Path("output/ratio_edge_cases.log")

FINANCIALS_LABEL = "Financials"
ROCE_TOLERANCE = 5.0   # percentage points
ROE_TOLERANCE = 5.0    # percentage points


# ============================================================
# HELPERS
# ============================================================
def norm(value):
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def clean_id(value):
    if pd.isna(value):
        return None
    value = str(value).strip().upper()
    if value in {"", "NAN", "NONE", "NULL", "NA"}:
        return None
    return value


def number(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "na", "-"}:
        return None

    text = text.replace(",", "")
    text = text.replace("%", "")
    text = text.replace("₹", "")

    # Handle accounting negatives: (12.5) -> -12.5
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]

    try:
        return float(text)
    except ValueError:
        return None


def table_columns(conn, table):
    rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    return [row[1] for row in rows]


def find_column(columns, candidates, contains=False):
    normalized = {norm(c): c for c in columns}

    for candidate in candidates:
        key = norm(candidate)
        if key in normalized:
            return normalized[key]

    if contains:
        for col in columns:
            n = norm(col)
            for candidate in candidates:
                if norm(candidate) in n:
                    return col

    return None


# ============================================================
# LOGGING
# ============================================================
def write_log(lines):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("SPRINT 2 - DAY 13\n")
        f.write("BANK ROCE CARVE-OUT & RATIO EDGE CASE LOG\n")
        f.write("=" * 90 + "\n")
        f.write(f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}\n\n")
        for line in lines:
            f.write(line + "\n")


# ============================================================
# READ SOURCE FILE ROBUSTLY
# ============================================================
def read_source_file(path, valid_company_ids):
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")

    raw = pd.read_excel(path, header=None, engine="openpyxl")

    if raw.empty:
        raise ValueError("companies.xlsx is empty")

    # Find the column that contains the most known company IDs.
    best_col = None
    best_matches = -1

    valid = {clean_id(x) for x in valid_company_ids}
    valid.discard(None)

    for col in raw.columns:
        matches = raw[col].map(clean_id).isin(valid).sum()
        if matches > best_matches:
            best_matches = int(matches)
            best_col = col

    if best_col is None or best_matches <= 0:
        raise ValueError(
            "Could not detect company ID column in companies.xlsx. "
            "Check that the workbook contains NIFTY company tickers."
        )

    # Try to find columns whose headers contain ROE / ROCE.
    header_row = None
    for i in range(min(30, len(raw))):
        row_text = " ".join(
            str(v).strip().lower()
            for v in raw.iloc[i].tolist()
            if not pd.isna(v)
        )
        if "roe" in row_text or "roce" in row_text:
            header_row = i
            break

    if header_row is not None:
        data = raw.iloc[header_row + 1:].copy()
        data.columns = [str(x).strip() for x in raw.iloc[header_row].tolist()]
    else:
        data = raw.copy()
        data.columns = [str(x).strip() for x in raw.iloc[0].tolist()]
        data = data.iloc[1:].copy()

    # If header processing changed the detected ID column, find it again.
    id_col = None
    for col in data.columns:
        matches = data[col].map(clean_id).isin(valid).sum()
        if matches >= best_matches or (id_col is None and matches > 0):
            id_col = col
            best_matches = int(matches)

    if id_col is None:
        # Fall back to original raw column position.
        id_col = data.columns[min(int(best_col), len(data.columns) - 1)]

    data["company_id"] = data[id_col].map(clean_id)
    data = data[data["company_id"].isin(valid)].copy()

    if data.empty:
        raise ValueError("No company rows could be matched from companies.xlsx")

    # Locate ROE and ROCE columns from the actual column names.
    roe_col = find_column(
        data.columns,
        [
            "roe_percentage", "roe_percent", "roe_pct", "roe",
            "return_on_equity", "return_on_equity_percentage"
        ],
        contains=True,
    )

    roce_col = find_column(
        data.columns,
        [
            "roce_percentage", "roce_percent", "roce_pct", "roce",
            "return_on_capital_employed", "return_on_capital_employed_percentage"
        ],
        contains=True,
    )

    print(f"Company column detected : {id_col}")
    print(f"ROE column detected     : {roe_col}")
    print(f"ROCE column detected    : {roce_col}")
    print(f"Matched company rows    : {len(data)}")

    return data, roe_col, roce_col


# ============================================================
# FIND COMPUTED RATIO COLUMNS
# ============================================================
def find_ratio_columns(ratio_columns):
    roce_col = find_column(
        ratio_columns,
        [
            "return_on_capital_employed_pct",
            "return_on_capital_employed_percentage",
            "roce_pct",
            "roce_percentage",
            "roce",
        ],
        contains=True,
    )

    roe_col = find_column(
        ratio_columns,
        [
            "return_on_equity_pct",
            "return_on_equity_percentage",
            "roe_pct",
            "roe_percentage",
            "roe",
        ],
        contains=True,
    )

    return roe_col, roce_col


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("SPRINT 2 - DAY 13")
    print("BANK ROCE CARVE-OUT & EDGE CASE LOG")
    print("=" * 70)

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    try:
        # ----------------------------------------------------
        # DATABASE CHECK
        # ----------------------------------------------------
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]

        if "companies" not in tables:
            raise ValueError("companies table not found")
        if "financial_ratios" not in tables:
            raise ValueError("financial_ratios table not found")

        companies_cols = table_columns(conn, "companies")
        ratio_cols = table_columns(conn, "financial_ratios")

        company_id_col = find_column(
            companies_cols,
            ["id", "company_id", "ticker", "symbol"],
            contains=True,
        )

        sector_col = find_column(
            companies_cols,
            ["broad_sector", "sector", "sector_name"],
            contains=True,
        )

        ratio_company_col = find_column(
            ratio_cols,
            ["company_id", "id", "ticker", "symbol"],
            contains=True,
        )

        year_col = find_column(
            ratio_cols,
            ["year", "financial_year", "fy"],
            contains=True,
        )

        if not company_id_col:
            raise ValueError("Could not find company ID column in companies table")
        if not ratio_company_col:
            raise ValueError("Could not find company ID column in financial_ratios")
        if not year_col:
            raise ValueError("Could not find year column in financial_ratios")
        if not sector_col:
            raise ValueError("Could not find broad_sector/sector column in companies")

        roe_ratio_col, roce_ratio_col = find_ratio_columns(ratio_cols)

        if not roe_ratio_col:
            raise ValueError(
                "Computed ROE column not found in financial_ratios. "
                f"Available columns: {ratio_cols}"
            )
        if not roce_ratio_col:
            raise ValueError(
                "Computed ROCE column not found in financial_ratios. "
                f"Available columns: {ratio_cols}"
            )

        companies = pd.read_sql_query(
            f'SELECT "{company_id_col}" AS company_id, "{sector_col}" AS broad_sector FROM companies',
            conn,
        )
        companies["company_id"] = companies["company_id"].map(clean_id)
        companies["broad_sector"] = companies["broad_sector"].astype(str).str.strip()

        ratios = pd.read_sql_query(
            f'SELECT * FROM financial_ratios',
            conn,
        )
        ratios["company_id"] = ratios[ratio_company_col].map(clean_id)
        ratios["year_clean"] = pd.to_numeric(ratios[year_col], errors="coerce")

        print("\nDATABASE LOADED")
        print("-" * 70)
        print(f"Companies           : {len(companies)}")
        print(f"Financial ratio rows: {len(ratios)}")
        print(f"Computed ROE column : {roe_ratio_col}")
        print(f"Computed ROCE column: {roce_ratio_col}")

        # ----------------------------------------------------
        # BANK / FINANCIALS CARVE-OUT
        # ----------------------------------------------------
        financial_ids = set(
            companies.loc[
                companies["broad_sector"].str.casefold() == FINANCIALS_LABEL.casefold(),
                "company_id",
            ].dropna()
        )

        print("\nFINANCIALS SECTOR CARVE-OUT")
        print("-" * 70)
        print(f"Financials companies: {len(financial_ids)}")

        lines = []
        lines.append(f"Financials companies detected: {len(financial_ids)}")

        # Suppress high leverage warning for Financials if the column exists.
        high_flag_col = find_column(
            ratio_cols,
            ["high_leverage_flag"],
            contains=True,
        )

        if high_flag_col:
            placeholders = ",".join("?" for _ in financial_ids)
            if financial_ids:
                conn.execute(
                    f'''UPDATE financial_ratios
                        SET "{high_flag_col}" = 0
                        WHERE "{ratio_company_col}" IN ({placeholders})''',
                    list(financial_ids),
                )
                conn.commit()
                print(f"✓ Suppressed {high_flag_col} for Financials companies")
                lines.append(
                    f"Bank/Financials carve-out: {len(financial_ids)} companies had high leverage flag suppressed."
                )
            else:
                print("⚠ No Financials companies detected")
        else:
            print("⚠ high_leverage_flag column not present. No flag update required.")
            lines.append("high_leverage_flag column not present, so no DB flag update was required.")

        # ----------------------------------------------------
        # READ SOURCE
        # ----------------------------------------------------
        print("\nSOURCE FILE LOADED")
        print("-" * 70)

        source, source_roe_col, source_roce_col = read_source_file(
            SOURCE_PATH,
            companies["company_id"].tolist(),
        )

        if not source_roe_col and not source_roce_col:
            raise ValueError(
                "Neither ROE nor ROCE source column could be detected in companies.xlsx"
            )

        # ----------------------------------------------------
        # LATEST RATIO PER COMPANY
        # ----------------------------------------------------
        ratios = ratios.dropna(subset=["company_id"]).copy()
        ratios = ratios.sort_values(["company_id", "year_clean"])
        latest = ratios.groupby("company_id", as_index=False).tail(1).copy()

        latest = latest[
            ["company_id", "year_clean", roe_ratio_col, roce_ratio_col]
        ].rename(
            columns={
                "year_clean": "latest_year",
                roe_ratio_col: "computed_roe",
                roce_ratio_col: "computed_roce",
            }
        )

        # ----------------------------------------------------
        # COMPARE SOURCE VS ENGINE
        # ----------------------------------------------------
        source_compare = source[["company_id"]].copy()

        if source_roe_col:
            source_compare["source_roe"] = source[source_roe_col].map(number)
        else:
            source_compare["source_roe"] = None

        if source_roce_col:
            source_compare["source_roce"] = source[source_roce_col].map(number)
        else:
            source_compare["source_roce"] = None

        compare = source_compare.merge(
            latest,
            on="company_id",
            how="left",
        )

        compare = compare.merge(
            companies,
            on="company_id",
            how="left",
        )

        anomaly_count = 0

        for _, row in compare.iterrows():
            cid = row["company_id"]
            sector = str(row.get("broad_sector", ""))
            year = row.get("latest_year")

            source_roce = row.get("source_roce")
            computed_roce = number(row.get("computed_roce"))
            source_roe = row.get("source_roe")
            computed_roe = number(row.get("computed_roe"))

            # ROCE check: required threshold > 5 percentage points.
            if source_roce is not None and computed_roce is not None:
                diff = abs(source_roce - computed_roce)
                if diff > ROCE_TOLERANCE:
                    anomaly_count += 1
                    category = (
                        "data source issue"
                        if abs(source_roce) < 1 and abs(computed_roce) > 5
                        else "version difference"
                    )
                    lines.append(
                        f"ROCE | {cid} | FY {year} | source={source_roce:.4f}% | "
                        f"engine={computed_roce:.4f}% | difference={diff:.4f} pp | "
                        f"sector={sector} | category={category}"
                    )

            # ROE check. Source values are display/reference only.
            if source_roe is not None and computed_roe is not None:
                diff = abs(source_roe - computed_roe)
                if diff > ROE_TOLERANCE:
                    anomaly_count += 1
                    category = (
                        "data source issue"
                        if abs(source_roe) < 1 and abs(computed_roe) > 5
                        else "version difference"
                    )
                    lines.append(
                        f"ROE  | {cid} | FY {year} | source={source_roe:.4f}% | "
                        f"engine={computed_roe:.4f}% | difference={diff:.4f} pp | "
                        f"sector={sector} | category={category} | "
                        f"analytics_value=engine"
                    )

        # ----------------------------------------------------
        # EXPLICIT TCS-SIZE SOURCE ANOMALY DETECTION
        # ----------------------------------------------------
        if "TCS" in set(compare["company_id"]):
            tcs = compare[compare["company_id"] == "TCS"].iloc[0]
            if tcs.get("source_roe") is not None and abs(float(tcs["source_roe"])) < 1:
                lines.append(
                    f"ROE SOURCE NOTE | TCS | source ROE={float(tcs['source_roe']):.4f}% | "
                    "source value appears anomalous; ratio-engine ROE is used for analytics."
                )
                print("✓ TCS source ROE anomaly documented")

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------
        lines.append("")
        lines.append(f"Total documented anomalies: {anomaly_count}")
        lines.append(
            "Formula decision: financial_ratios engine values are authoritative for analytics; "
            "companies.xlsx ROE/ROCE values are reference/display values."
        )
        lines.append(
            "Bank carve-out: Financials companies are excluded from the non-financial high-leverage warning."
        )

        write_log(lines)

        print("\nEDGE CASE CHECK")
        print("-" * 70)
        print(f"✓ ROCE anomalies (> {ROCE_TOLERANCE:.0f} pp): documented")
        print(f"✓ ROE anomalies (> {ROE_TOLERANCE:.0f} pp): documented")
        print("✓ Financials high-leverage carve-out applied where column exists")
        print(f"✓ Edge-case log saved: {LOG_PATH}")
        print(f"✓ Total documented anomalies: {anomaly_count}")

        print("\n" + "=" * 70)
        print("SPRINT 2 - DAY 13 COMPLETE")
        print("=" * 70)
        print("✓ Database loaded")
        print("✓ Financials carve-out checked")
        print("✓ ROCE cross-check completed")
        print("✓ ROE cross-check completed")
        print("✓ Edge cases documented")
        print("✓ ratio_edge_cases.log created")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
