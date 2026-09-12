from pathlib import Path
import sqlite3
import re
import pandas as pd


# ============================================================
# SPRINT 3 - DAY 15
# FINANCIAL SCREENER ENGINE
# ============================================================

DEFAULT_DB_PATH = "db/nifty100.db"
DEFAULT_OUTPUT_PATH = "output/screener_results.csv"


class FinancialScreener:
    """
    Financial company screener based on the financial_ratios
    and companies tables.

    Default screening conditions:

        ROE > 15%
        Debt-to-Equity < 1
        Net Profit Margin > 10%
        Interest Coverage > 3
        Asset Turnover > 0.5
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        database_path=DEFAULT_DB_PATH
    ):

        self.database_path = Path(
            database_path
        )

        if not self.database_path.exists():

            raise FileNotFoundError(
                f"Database not found: "
                f"{self.database_path}"
            )

    # ========================================================
    # DATABASE CONNECTION
    # ========================================================

    def get_connection(self):

        connection = sqlite3.connect(
            self.database_path
        )

        return connection

    # ========================================================
    # NORMALIZE COLUMN NAME
    # ========================================================

    @staticmethod
    def normalize_column_name(column):

        return (
            re.sub(
                r"[^a-z0-9]+",
                "_",
                str(column)
                .strip()
                .lower()
            )
            .strip("_")
        )

    # ========================================================
    # NORMALIZE COMPANY ID
    # ========================================================

    @staticmethod
    def normalize_company_id(value):

        if pd.isna(value):
            return None

        value = str(value).strip().upper()

        if value in {
            "",
            "NAN",
            "NONE",
            "NULL"
        }:
            return None

        # Remove NSE/BSE suffixes
        value = re.sub(
            r"\.(NS|BO)$",
            "",
            value
        )

        return value

    # ========================================================
    # FIND COLUMN
    # ========================================================

    def find_column(
        self,
        columns,
        candidates
    ):
        """
        Find a column using several possible names.
        """

        normalized = {}

        for column in columns:

            normalized[
                self.normalize_column_name(column)
            ] = column

        for candidate in candidates:

            candidate_normalized = (
                self.normalize_column_name(
                    candidate
                )
            )

            if candidate_normalized in normalized:

                return normalized[
                    candidate_normalized
                ]

        return None

    # ========================================================
    # LOAD DATA
    # ========================================================

    def load_data(self):

        connection = self.get_connection()

        try:

            # ------------------------------------------------
            # Load financial ratios
            # ------------------------------------------------

            ratios = pd.read_sql_query(
                "SELECT * FROM financial_ratios",
                connection
            )

            # ------------------------------------------------
            # Load companies
            # ------------------------------------------------

            companies = pd.read_sql_query(
                "SELECT * FROM companies",
                connection
            )

        finally:

            connection.close()

        # ====================================================
        # NORMALIZE COLUMN NAMES
        # ====================================================

        ratios.columns = [
            self.normalize_column_name(
                column
            )
            for column in ratios.columns
        ]

        companies.columns = [
            self.normalize_column_name(
                column
            )
            for column in companies.columns
        ]

        print("\nDATABASE TABLES LOADED")
        print("-" * 70)

        print(
            f"financial_ratios rows : "
            f"{len(ratios)}"
        )

        print(
            f"companies rows        : "
            f"{len(companies)}"
        )

        # ====================================================
        # FINANCIAL RATIOS COMPANY ID
        # ====================================================

        ratios_id_column = self.find_column(
            ratios.columns,
            [
                "company_id",
                "id",
                "ticker",
                "symbol"
            ]
        )

        if ratios_id_column is None:

            raise ValueError(
                "Could not find company ID in "
                "financial_ratios table.\n\n"
                "Available columns:\n"
                + "\n".join(
                    f"  - {column}"
                    for column in ratios.columns
                )
            )

        # ====================================================
        # COMPANIES COMPANY ID
        # ====================================================

        companies_id_column = self.find_column(
            companies.columns,
            [
                "company_id",
                "id",
                "ticker",
                "symbol"
            ]
        )

        if companies_id_column is None:

            raise ValueError(
                "Could not find company ID in "
                "companies table.\n\n"
                "Available columns:\n"
                + "\n".join(
                    f"  - {column}"
                    for column in companies.columns
                )
            )

        print(
            f"Ratios ID column     : "
            f"{ratios_id_column}"
        )

        print(
            f"Companies ID column  : "
            f"{companies_id_column}"
        )

        # ====================================================
        # STANDARDIZE COMPANY IDS
        # ====================================================

        ratios["company_id"] = (
            ratios[ratios_id_column]
            .map(
                self.normalize_company_id
            )
        )

        companies["company_id"] = (
            companies[companies_id_column]
            .map(
                self.normalize_company_id
            )
        )

        # ====================================================
        # COMPANY NAME
        # ====================================================

        company_name_column = self.find_column(
            companies.columns,
            [
                "company_name",
                "name",
                "company"
            ]
        )

        if company_name_column is not None:

            company_lookup = (
                companies[
                    [
                        "company_id",
                        company_name_column
                    ]
                ]
                .dropna(
                    subset=["company_id"]
                )
                .drop_duplicates(
                    subset=["company_id"]
                )
                .rename(
                    columns={
                        company_name_column:
                            "company_name"
                    }
                )
            )

            ratios = ratios.merge(
                company_lookup,
                on="company_id",
                how="left"
            )

        else:

            ratios["company_name"] = (
                ratios["company_id"]
            )

        return ratios

    # ========================================================
    # VALIDATE REQUIRED KPI COLUMNS
    # ========================================================

    def validate_columns(self, df):

        print("\nKPI COLUMN VALIDATION")
        print("-" * 70)

        # ----------------------------------------------------
        # Possible names for every required KPI
        # ----------------------------------------------------

        column_candidates = {

            "roe": [
                "return_on_equity_pct",
                "return_on_equity_percentage",
                "roe_pct",
                "roe_percentage",
                "roe"
            ],

            "de": [
                "debt_to_equity",
                "debt_equity",
                "de_ratio",
                "de"
            ],

            "npm": [
                "net_profit_margin_pct",
                "net_profit_margin_percentage",
                "net_profit_margin",
                "npm_pct",
                "npm"
            ],

            "icr": [
                "interest_coverage",
                "interest_coverage_ratio",
                "interest_coverage_pct",
                "icr"
            ],

            "asset_turnover": [
                "asset_turnover",
                "asset_turnover_ratio"
            ]
        }

        detected = {}

        missing = []

        for logical_name, candidates in (
            column_candidates.items()
        ):

            column = self.find_column(
                df.columns,
                candidates
            )

            if column is None:

                missing.append(
                    logical_name
                )

                print(
                    f"✗ {logical_name}"
                )

            else:

                detected[
                    logical_name
                ] = column

                print(
                    f"✓ {logical_name:<20} "
                    f"-> {column}"
                )

        if missing:

            print(
                "\nAvailable financial_ratios "
                "columns:"
            )

            for column in df.columns:

                print(
                    f"  - {column}"
                )

            raise ValueError(
                "\nMissing required KPI columns: "
                + ", ".join(missing)
            )

        return detected

    # ========================================================
    # CLEAN NUMERIC VALUES
    # ========================================================

    def clean_numeric_columns(
        self,
        df,
        detected
    ):

        for column in detected.values():

            df[column] = (
                pd.to_numeric(
                    df[column],
                    errors="coerce"
                )
            )

        return df

    # ========================================================
    # DEFAULT SCREEN
    # ========================================================

    def screen(
        self,
        roe_min=15,
        de_max=1,
        npm_min=10,
        icr_min=3,
        asset_turnover_min=0.5
    ):

        df = self.load_data()

        detected = self.validate_columns(
            df
        )

        df = self.clean_numeric_columns(
            df,
            detected
        )

        roe_column = detected["roe"]
        de_column = detected["de"]
        npm_column = detected["npm"]
        icr_column = detected["icr"]
        asset_column = detected[
            "asset_turnover"
        ]

        # ====================================================
        # APPLY SCREENING CONDITIONS
        # ====================================================

        mask = (

            (df[roe_column] > roe_min)

            &

            (df[de_column] < de_max)

            &

            (df[npm_column] > npm_min)

            &

            (df[icr_column] > icr_min)

            &

            (df[asset_column] > asset_turnover_min)
        )

        filtered = df[
            mask
        ].copy()

        return filtered

    # ========================================================
    # ROE + D/E SCREEN
    # ========================================================

    def screen_roe_de(
        self,
        roe_min=15,
        de_max=1
    ):

        df = self.load_data()

        detected = self.validate_columns(
            df
        )

        df = self.clean_numeric_columns(
            df,
            detected
        )

        filtered = df[
            (
                df[detected["roe"]]
                > roe_min
            )
            &
            (
                df[detected["de"]]
                < de_max
            )
        ].copy()

        return filtered

    # ========================================================
    # CUSTOM SCREEN
    # ========================================================

    def custom_screen(
        self,
        roe_min=None,
        de_max=None,
        npm_min=None,
        icr_min=None,
        asset_turnover_min=None
    ):

        df = self.load_data()

        detected = self.validate_columns(
            df
        )

        df = self.clean_numeric_columns(
            df,
            detected
        )

        mask = pd.Series(
            True,
            index=df.index
        )

        if roe_min is not None:

            mask &= (
                df[detected["roe"]]
                > roe_min
            )

        if de_max is not None:

            mask &= (
                df[detected["de"]]
                < de_max
            )

        if npm_min is not None:

            mask &= (
                df[detected["npm"]]
                > npm_min
            )

        if icr_min is not None:

            mask &= (
                df[detected["icr"]]
                > icr_min
            )

        if asset_turnover_min is not None:

            mask &= (
                df[
                    detected["asset_turnover"]
                ]
                > asset_turnover_min
            )

        return df[
            mask
        ].copy()

    # ========================================================
    # PREPARE OUTPUT
    # ========================================================

    def prepare_output(
        self,
        df
    ):

        detected = self.validate_columns(
            df
        )

        output = pd.DataFrame()

        # ----------------------------------------------------
        # Company
        # ----------------------------------------------------

        if "company_id" in df.columns:

            output["company_id"] = (
                df["company_id"]
            )

        if "company_name" in df.columns:

            output["company_name"] = (
                df["company_name"]
            )

        # ----------------------------------------------------
        # Year
        # ----------------------------------------------------

        year_column = self.find_column(
            df.columns,
            [
                "year",
                "financial_year",
                "fy"
            ]
        )

        if year_column:

            output["year"] = (
                df[year_column]
            )

        # ----------------------------------------------------
        # KPIs
        # ----------------------------------------------------

        output[
            "return_on_equity_pct"
        ] = df[
            detected["roe"]
        ]

        output[
            "debt_to_equity"
        ] = df[
            detected["de"]
        ]

        output[
            "net_profit_margin_pct"
        ] = df[
            detected["npm"]
        ]

        output[
            "interest_coverage"
        ] = df[
            detected["icr"]
        ]

        output[
            "asset_turnover"
        ] = df[
            detected["asset_turnover"]
        ]

        # ----------------------------------------------------
        # Sort
        # ----------------------------------------------------

        sort_columns = []

        if "company_id" in output.columns:

            sort_columns.append(
                "company_id"
            )

        if "year" in output.columns:

            sort_columns.append(
                "year"
            )

        if sort_columns:

            output = output.sort_values(
                sort_columns
            )

        return output.reset_index(
            drop=True
        )

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    def save_results(
        self,
        df,
        output_path=DEFAULT_OUTPUT_PATH
    ):

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        df.to_csv(
            output_path,
            index=False
        )

        print("\nOUTPUT")
        print("-" * 70)

        print(
            f"✓ Saved: {output_path}"
        )

        print(
            f"✓ Rows : {len(df)}"
        )

        return output_path

    # ========================================================
    # PRINT RESULTS
    # ========================================================

    def print_results(
        self,
        df
    ):

        print("\n" + "=" * 70)
        print(
            "FINANCIAL SCREENER RESULTS"
        )
        print("=" * 70)

        print("\nFILTERS")
        print("-" * 70)

        print(
            "ROE              > 15%"
        )

        print(
            "Debt-to-Equity   < 1"
        )

        print(
            "Net Profit Margin > 10%"
        )

        print(
            "Interest Coverage > 3"
        )

        print(
            "Asset Turnover   > 0.5"
        )

        print("\nRESULTS")
        print("-" * 70)

        if df.empty:

            print(
                "⚠ No rows matched all filters."
            )

            return

        output = self.prepare_output(
            df
        )

        print(
            output.to_string(
                index=False
            )
        )

        print("\n" + "-" * 70)

        print(
            f"Matching rows    : "
            f"{len(output)}"
        )

        if "company_id" in output.columns:

            print(
                f"Unique companies : "
                f"{output['company_id'].nunique()}"
            )

    # ========================================================
    # DATABASE SUMMARY
    # ========================================================

    def print_database_summary(self):

        connection = self.get_connection()

        try:

            ratios_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM financial_ratios
                """
            ).fetchone()[0]

            companies_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM companies
                """
            ).fetchone()[0]

        finally:

            connection.close()

        print("\nDATABASE SUMMARY")
        print("-" * 70)

        print(
            f"Companies         : "
            f"{companies_count}"
        )

        print(
            f"Financial ratios  : "
            f"{ratios_count}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SPRINT 3 - DAY 15")
    print("FINANCIAL SCREENER ENGINE")
    print("=" * 70)

    try:

        screener = FinancialScreener()

        # ----------------------------------------------------
        # Database summary
        # ----------------------------------------------------

        screener.print_database_summary()

        # ----------------------------------------------------
        # Run screener
        # ----------------------------------------------------

        results = screener.screen()

        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        screener.print_results(
            results
        )

        # ----------------------------------------------------
        # Prepare final CSV
        # ----------------------------------------------------

        output = screener.prepare_output(
            results
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        screener.save_results(
            output
        )

        # ----------------------------------------------------
        # Final status
        # ----------------------------------------------------

        print("\n" + "=" * 70)
        print(
            "✓ DAY 15 SCREENER COMPLETED"
        )
        print("=" * 70)

    except Exception as error:

        print("\n" + "=" * 70)
        print(
            "✗ DAY 15 SCREENER FAILED"
        )
        print("=" * 70)

        print(
            f"\nError: {error}"
        )

        raise


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()