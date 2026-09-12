from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

import pandas as pd


class DataValidator:

    def __init__(self):
        self.failures = []

    # =========================================================
    # ADD FAILURE
    # =========================================================

    def add_failure(
        self,
        rule_id,
        severity,
        table,
        column,
        record_identifier,
        message
    ):

        self.failures.append({
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "rule_id": rule_id,
            "severity": severity,
            "table": table,
            "column": column,
            "record_identifier": str(record_identifier),
            "message": message
        })

    # =========================================================
    # HELPER: GET RECORD ID
    # =========================================================

    def get_record_id(self, row, index):

        if "id" in row.index:
            return row["id"]

        return index

    # =========================================================
    # DQ-01: PRIMARY KEY UNIQUENESS
    # =========================================================

    def validate_primary_key(
        self,
        df,
        table_name,
        pk_column="id"
    ):

        if pk_column not in df.columns:

            print(
                f"WARNING: DQ-01 skipped for "
                f"{table_name}. Missing '{pk_column}'."
            )

            return

        null_rows = df[df[pk_column].isna()]

        duplicate_rows = df[
            df[pk_column].duplicated(keep=False)
        ]

        for index, row in null_rows.iterrows():

            self.add_failure(
                "DQ-01",
                "CRITICAL",
                table_name,
                pk_column,
                index,
                "Primary key is NULL."
            )

        for _, row in duplicate_rows.iterrows():

            self.add_failure(
                "DQ-01",
                "CRITICAL",
                table_name,
                pk_column,
                row[pk_column],
                f"Duplicate primary key: {row[pk_column]}"
            )

        if null_rows.empty and duplicate_rows.empty:

            print(
                f"✓ DQ-01 PASSED: "
                f"{table_name}.{pk_column}"
            )

        else:

            print(f"✗ DQ-01 FAILED: {table_name}")

    # =========================================================
    # DQ-02: COMPANY + YEAR UNIQUENESS
    # =========================================================

    def validate_company_year_uniqueness(
        self,
        df,
        table_name,
        company_column="company_id",
        year_column="year"
    ):

        required = [
            company_column,
            year_column
        ]

        if not all(
            column in df.columns
            for column in required
        ):

            print(
                f"WARNING: DQ-02 skipped for "
                f"{table_name}."
            )

            return

        null_rows = df[
            df[company_column].isna()
            |
            df[year_column].isna()
        ]

        duplicate_rows = df[
            df.duplicated(
                subset=[
                    company_column,
                    year_column
                ],
                keep=False
            )
        ]

        for index, row in null_rows.iterrows():

            self.add_failure(
                "DQ-02",
                "CRITICAL",
                table_name,
                f"{company_column}, {year_column}",
                index,
                "NULL in composite key."
            )

        for _, row in duplicate_rows.iterrows():

            identifier = (
                f"{row[company_column]}_"
                f"{row[year_column]}"
            )

            self.add_failure(
                "DQ-02",
                "CRITICAL",
                table_name,
                f"{company_column}, {year_column}",
                identifier,
                "Duplicate company-year combination."
            )

        if null_rows.empty and duplicate_rows.empty:

            print(
                f"✓ DQ-02 PASSED: "
                f"{table_name}"
            )

        else:

            print(
                f"✗ DQ-02 FAILED: "
                f"{table_name}"
            )

    # =========================================================
    # DQ-03: FOREIGN KEY INTEGRITY
    # =========================================================

    def validate_foreign_key(
        self,
        child_df,
        parent_df,
        child_table,
        parent_table,
        fk_column="company_id",
        pk_column="id"
    ):

        if (
            fk_column not in child_df.columns
            or pk_column not in parent_df.columns
        ):

            print(
                f"WARNING: DQ-03 skipped for "
                f"{child_table}."
            )

            return

        valid_ids = set(
            parent_df[pk_column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        invalid_rows = child_df[
            child_df[fk_column].notna()
            &
            ~child_df[fk_column]
            .astype(str)
            .str.strip()
            .isin(valid_ids)
        ]

        for index, row in invalid_rows.iterrows():

            self.add_failure(
                "DQ-03",
                "CRITICAL",
                child_table,
                fk_column,
                self.get_record_id(row, index),
                (
                    f"Invalid foreign key: "
                    f"{row[fk_column]}"
                )
            )

        if invalid_rows.empty:

            print(
                f"✓ DQ-03 PASSED: "
                f"{child_table}"
            )

        else:

            print(
                f"✗ DQ-03 FAILED: "
                f"{child_table}"
            )

    # =========================================================
    # DQ-04: BALANCE SHEET BALANCE
    # =========================================================

    def validate_balance_sheet(
        self,
        df,
        table_name="balancesheet",
        assets_column="total_assets",
        liabilities_column="total_liabilities",
        tolerance=0.01
    ):

        required = [
            assets_column,
            liabilities_column
        ]

        if not all(
            column in df.columns
            for column in required
        ):

            print("WARNING: DQ-04 skipped.")

            return

        temp = df.copy()

        for column in required:

            temp[column] = pd.to_numeric(
                temp[column],
                errors="coerce"
            )

        valid_rows = temp[
            temp[assets_column].notna()
            &
            temp[liabilities_column].notna()
            &
            (temp[assets_column] != 0)
        ].copy()

        valid_rows["difference"] = (
            (
                valid_rows[assets_column]
                -
                valid_rows[liabilities_column]
            ).abs()
            /
            valid_rows[assets_column].abs()
        )

        invalid_rows = valid_rows[
            valid_rows["difference"] > tolerance
        ]

        for index, row in invalid_rows.iterrows():

            self.add_failure(
                "DQ-04",
                "WARNING",
                table_name,
                "total_assets,total_liabilities",
                self.get_record_id(row, index),
                (
                    f"Balance difference: "
                    f"{row['difference'] * 100:.2f}%"
                )
            )

        if invalid_rows.empty:

            print("✓ DQ-04 PASSED")

        else:

            print(
                f"⚠ DQ-04 WARNING: "
                f"{len(invalid_rows)} failures"
            )

    # =========================================================
    # DQ-05: OPM CROSS CHECK
    # =========================================================

    def validate_opm(
        self,
        df,
        table_name="profitandloss",
        tolerance=1.0
    ):

        required = [
            "sales",
            "operating_profit",
            "opm_percentage"
        ]

        if not all(
            column in df.columns
            for column in required
        ):

            print("WARNING: DQ-05 skipped.")

            return

        temp = df.copy()

        for column in required:

            temp[column] = pd.to_numeric(
                temp[column],
                errors="coerce"
            )

        valid_rows = temp[
            temp["sales"].notna()
            &
            temp["operating_profit"].notna()
            &
            temp["opm_percentage"].notna()
            &
            (temp["sales"] != 0)
        ].copy()

        valid_rows["calculated_opm"] = (
            valid_rows["operating_profit"]
            /
            valid_rows["sales"]
        ) * 100

        valid_rows["difference"] = (
            valid_rows["calculated_opm"]
            -
            valid_rows["opm_percentage"]
        ).abs()

        invalid_rows = valid_rows[
            valid_rows["difference"] > tolerance
        ]

        for index, row in invalid_rows.iterrows():

            self.add_failure(
                "DQ-05",
                "WARNING",
                table_name,
                "opm_percentage",
                self.get_record_id(row, index),
                (
                    f"Stored={row['opm_percentage']:.2f}, "
                    f"Calculated="
                    f"{row['calculated_opm']:.2f}"
                )
            )

        if invalid_rows.empty:

            print("✓ DQ-05 PASSED")

        else:

            print(
                f"⚠ DQ-05 WARNING: "
                f"{len(invalid_rows)} mismatches"
            )

    # =========================================================
    # DQ-06: POSITIVE SALES
    # =========================================================

    def validate_positive_sales(
        self,
        df,
        table_name="profitandloss"
    ):

        if "sales" not in df.columns:

            print("WARNING: DQ-06 skipped.")

            return

        temp = df.copy()

        temp["sales"] = pd.to_numeric(
            temp["sales"],
            errors="coerce"
        )

        invalid_rows = temp[
            temp["sales"].isna()
            |
            (temp["sales"] <= 0)
        ]

        for index, row in invalid_rows.iterrows():

            self.add_failure(
                "DQ-06",
                "WARNING",
                table_name,
                "sales",
                self.get_record_id(row, index),
                f"Invalid sales: {row['sales']}"
            )

        if invalid_rows.empty:

            print("✓ DQ-06 PASSED")

        else:

            print(
                f"⚠ DQ-06 WARNING: "
                f"{len(invalid_rows)} invalid values"
            )

    # =========================================================
    # DQ-07: NET CASH FLOW
    # =========================================================

    def validate_net_cash_flow(
        self,
        df,
        table_name="cashflow",
        tolerance=1.0
    ):

        required = [
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow"
        ]

        if not all(
            column in df.columns
            for column in required
        ):

            print("WARNING: DQ-07 skipped.")

            return

        temp = df.copy()

        for column in required:

            temp[column] = pd.to_numeric(
                temp[column],
                errors="coerce"
            )

        valid_rows = temp.dropna(
            subset=required
        ).copy()

        valid_rows["calculated"] = (
            valid_rows["operating_activity"]
            +
            valid_rows["investing_activity"]
            +
            valid_rows["financing_activity"]
        )

        valid_rows["difference"] = (
            valid_rows["calculated"]
            -
            valid_rows["net_cash_flow"]
        ).abs()

        invalid_rows = valid_rows[
            valid_rows["difference"] > tolerance
        ]

        for index, row in invalid_rows.iterrows():

            self.add_failure(
                "DQ-07",
                "WARNING",
                table_name,
                "net_cash_flow",
                self.get_record_id(row, index),
                (
                    f"Stored={row['net_cash_flow']}, "
                    f"Calculated={row['calculated']}"
                )
            )

        if invalid_rows.empty:

            print("✓ DQ-07 PASSED")

        else:

            print(
                f"⚠ DQ-07 WARNING: "
                f"{len(invalid_rows)} mismatches"
            )

    # =========================================================
    # DQ-08: TAX RATE
    # =========================================================

    def validate_tax_rate(
        self,
        df,
        table_name="profitandloss",
        tolerance=1.0
    ):

        required = [
            "profit_before_tax",
            "tax_percentage",
            "net_profit"
        ]

        if not all(
            column in df.columns
            for column in required
        ):

            print("WARNING: DQ-08 skipped.")

            return

        temp = df.copy()

        for column in required:

            temp[column] = pd.to_numeric(
                temp[column],
                errors="coerce"
            )

        valid_rows = temp[
            temp["profit_before_tax"].notna()
            &
            temp["tax_percentage"].notna()
            &
            temp["net_profit"].notna()
            &
            (temp["profit_before_tax"] != 0)
        ].copy()

        valid_rows["calculated_tax"] = (
            (
                valid_rows["profit_before_tax"]
                -
                valid_rows["net_profit"]
            )
            /
            valid_rows["profit_before_tax"]
        ) * 100

        valid_rows["difference"] = (
            valid_rows["calculated_tax"]
            -
            valid_rows["tax_percentage"]
        ).abs()

        invalid_rows = valid_rows[
            valid_rows["difference"] > tolerance
        ]

        for index, row in invalid_rows.iterrows():

            self.add_failure(
                "DQ-08",
                "WARNING",
                table_name,
                "tax_percentage",
                self.get_record_id(row, index),
                (
                    f"Stored={row['tax_percentage']:.2f}%, "
                    f"Calculated="
                    f"{row['calculated_tax']:.2f}%"
                )
            )

        if invalid_rows.empty:

            print("✓ DQ-08 PASSED")

        else:

            print(
                f"⚠ DQ-08 WARNING: "
                f"{len(invalid_rows)} mismatches"
            )

    # =========================================================
    # DQ-09: DIVIDEND PAYOUT CAP
    # =========================================================

    def validate_dividend_payout(
        self,
        df,
        table_name="profitandloss",
        min_value=0,
        max_value=100
    ):

        if "dividend_payout" not in df.columns:

            print("WARNING: DQ-09 skipped.")

            return

        temp = df.copy()

        temp["dividend_payout"] = pd.to_numeric(
            temp["dividend_payout"],
            errors="coerce"
        )

        invalid_rows = temp[
            temp["dividend_payout"].isna()
            |
            (temp["dividend_payout"] < min_value)
            |
            (temp["dividend_payout"] > max_value)
        ]

        for index, row in invalid_rows.iterrows():

            self.add_failure(
                "DQ-09",
                "WARNING",
                table_name,
                "dividend_payout",
                self.get_record_id(row, index),
                (
                    f"Invalid dividend payout: "
                    f"{row['dividend_payout']}"
                )
            )

        if invalid_rows.empty:

            print("✓ DQ-09 PASSED")

        else:

            print(
                f"⚠ DQ-09 WARNING: "
                f"{len(invalid_rows)} invalid values"
            )

    # =========================================================
    # DQ-10: URL VALIDATION
    # =========================================================

    def validate_urls(
        self,
        df,
        table_name,
        url_columns
    ):

        existing_columns = [
            column
            for column in url_columns
            if column in df.columns
        ]

        if not existing_columns:

            print(
                f"WARNING: DQ-10 skipped for "
                f"{table_name}."
            )

            return

        invalid_count = 0

        for column in existing_columns:

            for index, row in df.iterrows():

                value = row[column]

                if pd.isna(value):

                    continue

                value = str(value).strip()

                if value == "":

                    continue

                try:

                    parsed = urlparse(value)

                    is_valid = (
                        parsed.scheme in ["http", "https"]
                        and bool(parsed.netloc)
                    )

                except Exception:

                    is_valid = False

                if not is_valid:

                    invalid_count += 1

                    self.add_failure(
                        "DQ-10",
                        "WARNING",
                        table_name,
                        column,
                        self.get_record_id(row, index),
                        f"Invalid URL: {value}"
                    )

        if invalid_count == 0:

            print(
                f"✓ DQ-10 PASSED: "
                f"{table_name}"
            )

        else:

            print(
                f"⚠ DQ-10 WARNING: "
                f"{invalid_count} invalid URLs "
                f"in {table_name}"
            )

    # =========================================================
    # DQ-11: EPS SIGN VALIDATION
    # =========================================================

    def validate_eps_sign(
        self,
        df,
        table_name="profitandloss"
    ):

        required = [
            "net_profit",
            "eps"
        ]

        if not all(
            column in df.columns
            for column in required
        ):

            print("WARNING: DQ-11 skipped.")

            return

        temp = df.copy()

        temp["net_profit"] = pd.to_numeric(
            temp["net_profit"],
            errors="coerce"
        )

        temp["eps"] = pd.to_numeric(
            temp["eps"],
            errors="coerce"
        )

        valid_rows = temp.dropna(
            subset=required
        )

        invalid_rows = valid_rows[
            (
                (valid_rows["net_profit"] > 0)
                &
                (valid_rows["eps"] < 0)
            )
            |
            (
                (valid_rows["net_profit"] < 0)
                &
                (valid_rows["eps"] > 0)
            )
        ]

        for index, row in invalid_rows.iterrows():

            self.add_failure(
                "DQ-11",
                "WARNING",
                table_name,
                "eps",
                self.get_record_id(row, index),
                (
                    f"EPS sign inconsistent. "
                    f"Net Profit={row['net_profit']}, "
                    f"EPS={row['eps']}"
                )
            )

        if invalid_rows.empty:

            print("✓ DQ-11 PASSED")

        else:

            print(
                f"⚠ DQ-11 WARNING: "
                f"{len(invalid_rows)} sign mismatches"
            )

    # =========================================================
    # DQ-12: BALANCE SHEET COMPONENT CHECK
    # =========================================================

    def validate_balance_components(
        self,
        df,
        table_name="balancesheet",
        tolerance=0.01
    ):

        required = [
            "equity_capital",
            "reserves",
            "borrowings",
            "other_liabilities",
            "total_liabilities"
        ]

        if not all(
            column in df.columns
            for column in required
        ):

            print("WARNING: DQ-12 skipped.")

            return

        temp = df.copy()

        for column in required:

            temp[column] = pd.to_numeric(
                temp[column],
                errors="coerce"
            )

        valid_rows = temp.dropna(
            subset=required
        ).copy()

        valid_rows["calculated_total"] = (
            valid_rows["equity_capital"]
            +
            valid_rows["reserves"]
            +
            valid_rows["borrowings"]
            +
            valid_rows["other_liabilities"]
        )

        valid_rows = valid_rows[
            valid_rows["total_liabilities"] != 0
        ]

        valid_rows["difference"] = (
            (
                valid_rows["calculated_total"]
                -
                valid_rows["total_liabilities"]
            ).abs()
            /
            valid_rows["total_liabilities"].abs()
        )

        invalid_rows = valid_rows[
            valid_rows["difference"] > tolerance
        ]

        for index, row in invalid_rows.iterrows():

            self.add_failure(
                "DQ-12",
                "WARNING",
                table_name,
                "total_liabilities",
                self.get_record_id(row, index),
                (
                    f"Stored={row['total_liabilities']}, "
                    f"Calculated="
                    f"{row['calculated_total']}"
                )
            )

        if invalid_rows.empty:

            print("✓ DQ-12 PASSED")

        else:

            print(
                f"⚠ DQ-12 WARNING: "
                f"{len(invalid_rows)} mismatches"
            )

    # =========================================================
    # DQ-13: YEAR VALIDITY
    # =========================================================

    def validate_year_range(
        self,
        df,
        table_name,
        year_column="year",
        min_year=1990,
        max_year=2030
    ):

        if year_column not in df.columns:

            print(
                f"WARNING: DQ-13 skipped for "
                f"{table_name}."
            )

            return

        temp = df.copy()

        temp[year_column] = pd.to_numeric(
            temp[year_column],
            errors="coerce"
        )

        invalid_rows = temp[
            temp[year_column].isna()
            |
            (temp[year_column] < min_year)
            |
            (temp[year_column] > max_year)
        ]

        for index, row in invalid_rows.iterrows():

            self.add_failure(
                "DQ-13",
                "WARNING",
                table_name,
                year_column,
                self.get_record_id(row, index),
                (
                    f"Invalid year: "
                    f"{row[year_column]}"
                )
            )

        if invalid_rows.empty:

            print(
                f"✓ DQ-13 PASSED: "
                f"{table_name}"
            )

        else:

            print(
                f"⚠ DQ-13 WARNING: "
                f"{len(invalid_rows)} invalid years"
            )

    # =========================================================
    # DQ-14: REQUIRED FIELD CHECK
    # =========================================================

    def validate_required_fields(
        self,
        df,
        table_name,
        required_columns
    ):

        existing_columns = [
            column
            for column in required_columns
            if column in df.columns
        ]

        if not existing_columns:

            print(
                f"WARNING: DQ-14 skipped for "
                f"{table_name}."
            )

            return

        invalid_count = 0

        for column in existing_columns:

            null_rows = df[
                df[column].isna()
                |
                (
                    df[column]
                    .astype(str)
                    .str.strip()
                    .eq("")
                )
            ]

            for index, row in null_rows.iterrows():

                invalid_count += 1

                self.add_failure(
                    "DQ-14",
                    "WARNING",
                    table_name,
                    column,
                    self.get_record_id(row, index),
                    "Required field is missing."
                )

        if invalid_count == 0:

            print(
                f"✓ DQ-14 PASSED: "
                f"{table_name}"
            )

        else:

            print(
                f"⚠ DQ-14 WARNING: "
                f"{invalid_count} missing values"
            )

    # =========================================================
    # DQ-15: NUMERIC VALUE VALIDATION
    # =========================================================

    def validate_numeric_columns(
        self,
        df,
        table_name,
        numeric_columns
    ):

        existing_columns = [
            column
            for column in numeric_columns
            if column in df.columns
        ]

        if not existing_columns:

            print(
                f"WARNING: DQ-15 skipped for "
                f"{table_name}."
            )

            return

        invalid_count = 0

        for column in existing_columns:

            converted = pd.to_numeric(
                df[column],
                errors="coerce"
            )

            invalid_rows = df[
                df[column].notna()
                &
                converted.isna()
            ]

            for index, row in invalid_rows.iterrows():

                invalid_count += 1

                self.add_failure(
                    "DQ-15",
                    "WARNING",
                    table_name,
                    column,
                    self.get_record_id(row, index),
                    (
                        f"Non-numeric value: "
                        f"{row[column]}"
                    )
                )

        if invalid_count == 0:

            print(
                f"✓ DQ-15 PASSED: "
                f"{table_name}"
            )

        else:

            print(
                f"⚠ DQ-15 WARNING: "
                f"{invalid_count} invalid numeric values"
            )

    # =========================================================
    # DQ-16: COMPANY YEAR COVERAGE
    # =========================================================

    def validate_company_coverage(
        self,
        df,
        table_name,
        company_column="company_id",
        year_column="year",
        minimum_years=5
    ):

        required = [
            company_column,
            year_column
        ]

        if not all(
            column in df.columns
            for column in required
        ):

            print(
                f"WARNING: DQ-16 skipped for "
                f"{table_name}."
            )

            return

        coverage = (
            df.groupby(company_column)[year_column]
            .nunique()
        )

        insufficient = coverage[
            coverage < minimum_years
        ]

        for company_id, year_count in insufficient.items():

            self.add_failure(
                "DQ-16",
                "WARNING",
                table_name,
                year_column,
                company_id,
                (
                    f"Only {year_count} years available. "
                    f"Minimum required: {minimum_years}."
                )
            )

        if insufficient.empty:

            print(
                f"✓ DQ-16 PASSED: "
                f"{table_name}"
            )

        else:

            print(
                f"⚠ DQ-16 WARNING: "
                f"{len(insufficient)} companies "
                f"have fewer than "
                f"{minimum_years} years."
            )

    # =========================================================
    # GET FAILURES
    # =========================================================

    def get_failures(self):

        columns = [
            "timestamp",
            "rule_id",
            "severity",
            "table",
            "column",
            "record_identifier",
            "message"
        ]

        return pd.DataFrame(
            self.failures,
            columns=columns
        )

    # =========================================================
    # SAVE FAILURES
    # =========================================================

    def save_failures(
        self,
        output_path="output/validation_failures.csv"
    ):

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        failures_df = self.get_failures()

        failures_df.to_csv(
            output_path,
            index=False
        )

        print(
            f"\nValidation failures saved to: "
            f"{output_path}"
        )

        return failures_df