from pathlib import Path
import sqlite3
import pandas as pd


# ============================================================
# DAY 17 - COMPANY LEVEL RANKING
# ============================================================

DB_PATH = Path("db/nifty100.db")
OUTPUT_PATH = Path("output/top_companies.csv")


class CompanyRanking:

    def __init__(self, database_path=DB_PATH):
        self.database_path = Path(database_path)

        if not self.database_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.database_path}"
            )

    # ========================================================
    # DATABASE CONNECTION
    # ========================================================

    def get_connection(self):
        return sqlite3.connect(
            self.database_path
        )

    # ========================================================
    # LOAD DATA
    # ========================================================

    def load_data(self):

        connection = self.get_connection()

        try:

            ratios = pd.read_sql_query(
                "SELECT * FROM financial_ratios",
                connection
            )

            companies = pd.read_sql_query(
                "SELECT * FROM companies",
                connection
            )

        finally:

            connection.close()

        ratios.columns = [
            str(c).strip().lower()
            for c in ratios.columns
        ]

        companies.columns = [
            str(c).strip().lower()
            for c in companies.columns
        ]

        # ----------------------------------------------------
        # Company ID
        # ----------------------------------------------------

        if "company_id" not in companies.columns:

            if "id" in companies.columns:

                companies = companies.rename(
                    columns={
                        "id": "company_id"
                    }
                )

            else:

                raise ValueError(
                    "companies table has neither "
                    "'company_id' nor 'id'."
                )

        # ----------------------------------------------------
        # Normalize IDs
        # ----------------------------------------------------

        ratios["company_id"] = (
            ratios["company_id"]
            .astype(str)
            .str.strip()
            .str.upper()
            .str.replace(".NS", "", regex=False)
            .str.replace(".BO", "", regex=False)
        )

        companies["company_id"] = (
            companies["company_id"]
            .astype(str)
            .str.strip()
            .str.upper()
            .str.replace(".NS", "", regex=False)
            .str.replace(".BO", "", regex=False)
        )

        # ----------------------------------------------------
        # Company name
        # ----------------------------------------------------

        if "company_name" in companies.columns:

            lookup_columns = [
                "company_id",
                "company_name"
            ]

            # Add sector if available
            if "broad_sector" in companies.columns:
                lookup_columns.append(
                    "broad_sector"
                )

            lookup = (
                companies[lookup_columns]
                .drop_duplicates(
                    subset=["company_id"]
                )
            )

            ratios = ratios.merge(
                lookup,
                on="company_id",
                how="left"
            )

        else:

            ratios["company_name"] = (
                ratios["company_id"]
            )

        # ----------------------------------------------------
        # If sector missing
        # ----------------------------------------------------

        if "broad_sector" not in ratios.columns:

            ratios["broad_sector"] = (
                "Unknown"
            )

        return ratios

    # ========================================================
    # CONVERT NUMERIC
    # ========================================================

    def numeric(self, df, columns):

        for column in columns:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        return df

    # ========================================================
    # SELECT LATEST YEAR
    # ========================================================

    def latest_year_per_company(
        self,
        df
    ):

        if "year" not in df.columns:

            raise ValueError(
                "financial_ratios does not contain "
                "'year' column."
            )

        df["year_numeric"] = pd.to_numeric(
            df["year"],
            errors="coerce"
        )

        # Remove rows where company/year is unavailable
        df = df.dropna(
            subset=[
                "company_id",
                "year_numeric"
            ]
        ).copy()

        # Sort newest first
        df = df.sort_values(
            [
                "company_id",
                "year_numeric"
            ],
            ascending=[
                True,
                False
            ]
        )

        # One latest row per company
        latest = (
            df.drop_duplicates(
                subset=["company_id"],
                keep="first"
            )
            .copy()
        )

        latest.drop(
            columns=["year_numeric"],
            inplace=True,
            errors="ignore"
        )

        return latest

    # ========================================================
    # VALIDATE KPI COLUMNS
    # ========================================================

    def validate_columns(self, df):

        required = [
            "return_on_equity_pct",
            "net_profit_margin_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
            "interest_coverage"
        ]

        missing = [
            column
            for column in required
            if column not in df.columns
        ]

        if missing:

            raise ValueError(
                "Missing required KPI columns:\n"
                + "\n".join(
                    f" - {column}"
                    for column in missing
                )
            )

    # ========================================================
    # CALCULATE SCORE
    # ========================================================

    @staticmethod
    def roe_score(value):

        if pd.isna(value):
            return 0

        if value >= 20:
            return 25

        if value >= 15:
            return 20

        if value >= 10:
            return 12

        return 5

    @staticmethod
    def npm_score(value):

        if pd.isna(value):
            return 0

        if value >= 20:
            return 20

        if value >= 10:
            return 15

        if value >= 5:
            return 10

        return 5

    @staticmethod
    def de_score(
        value,
        sector
    ):

        if pd.isna(value):
            return 0

        # Financial companies have structurally
        # higher leverage.
        if (
            isinstance(sector, str)
            and sector.strip().lower()
            == "financials"
        ):

            if value < 2:
                return 20

            if value < 4:
                return 15

            if value < 6:
                return 10

            return 5

        if value < 0.5:
            return 20

        if value < 1:
            return 15

        if value < 2:
            return 10

        return 5

    @staticmethod
    def growth_score(value):

        if pd.isna(value):
            return 0

        if value >= 15:
            return 20

        if value >= 10:
            return 15

        if value >= 5:
            return 10

        return 5

    @staticmethod
    def icr_score(value):

        if pd.isna(value):
            return 0

        if value >= 5:
            return 15

        if value >= 3:
            return 12

        if value >= 1.5:
            return 8

        return 3

    # ========================================================
    # CALCULATE COMPANY SCORE
    # ========================================================

    def calculate_score(
        self,
        df
    ):

        self.validate_columns(
            df
        )

        numeric_columns = [
            "return_on_equity_pct",
            "net_profit_margin_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
            "interest_coverage"
        ]

        df = self.numeric(
            df,
            numeric_columns
        )

        # ----------------------------------------------------
        # Individual scores
        # ----------------------------------------------------

        df["roe_score"] = (
            df["return_on_equity_pct"]
            .apply(
                self.roe_score
            )
        )

        df["npm_score"] = (
            df["net_profit_margin_pct"]
            .apply(
                self.npm_score
            )
        )

        df["de_score"] = df.apply(
            lambda row:
            self.de_score(
                row["debt_to_equity"],
                row["broad_sector"]
            ),
            axis=1
        )

        df["growth_score"] = (
            df["revenue_cagr_5yr"]
            .apply(
                self.growth_score
            )
        )

        df["icr_score"] = (
            df["interest_coverage"]
            .apply(
                self.icr_score
            )
        )

        # ----------------------------------------------------
        # Composite score
        # ----------------------------------------------------

        df["composite_score"] = (
            df["roe_score"]
            + df["npm_score"]
            + df["de_score"]
            + df["growth_score"]
            + df["icr_score"]
        )

        # ----------------------------------------------------
        # Quality category
        # ----------------------------------------------------

        def quality(score):

            if score >= 80:
                return "Excellent"

            if score >= 65:
                return "Good"

            if score >= 50:
                return "Average"

            return "Weak"

        df["quality_rating"] = (
            df["composite_score"]
            .apply(quality)
        )

        return df

    # ========================================================
    # RANK COMPANIES
    # ========================================================

    def rank_companies(
        self,
        df
    ):

        df = df.sort_values(
            [
                "composite_score",
                "return_on_equity_pct"
            ],
            ascending=[
                False,
                False
            ]
        ).copy()

        df["rank"] = range(
            1,
            len(df) + 1
        )

        return df

    # ========================================================
    # PREPARE OUTPUT
    # ========================================================

    def prepare_output(
        self,
        df
    ):

        columns = [
            "rank",
            "company_id",
            "company_name",
            "broad_sector",
            "year",

            "return_on_equity_pct",
            "roe_score",

            "net_profit_margin_pct",
            "npm_score",

            "debt_to_equity",
            "de_score",

            "revenue_cagr_5yr",
            "growth_score",

            "interest_coverage",
            "icr_score",

            "composite_score",
            "quality_rating"
        ]

        available = [
            column
            for column in columns
            if column in df.columns
        ]

        return df[
            available
        ].copy()

    # ========================================================
    # SAVE OUTPUT
    # ========================================================

    def save_output(
        self,
        df,
        output_path=OUTPUT_PATH
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

        print(
            f"\n✓ Output saved: "
            f"{output_path}"
        )

        print(
            f"✓ Companies saved: "
            f"{len(df)}"
        )

    # ========================================================
    # RUN
    # ========================================================

    def run(self):

        print("=" * 70)
        print(
            "SPRINT 3 - DAY 17"
        )
        print(
            "COMPANY LEVEL RANKING"
        )
        print("=" * 70)

        # ----------------------------------------------------
        # Load
        # ----------------------------------------------------

        df = self.load_data()

        print(
            f"\nFinancial ratio rows: "
            f"{len(df)}"
        )

        # ----------------------------------------------------
        # Latest year
        # ----------------------------------------------------

        latest = (
            self.latest_year_per_company(
                df
            )
        )

        print(
            f"Latest company rows: "
            f"{len(latest)}"
        )

        # ----------------------------------------------------
        # Calculate score
        # ----------------------------------------------------

        scored = (
            self.calculate_score(
                latest
            )
        )

        # ----------------------------------------------------
        # Rank
        # ----------------------------------------------------

        ranked = (
            self.rank_companies(
                scored
            )
        )

        # ----------------------------------------------------
        # Output
        # ----------------------------------------------------

        output = (
            self.prepare_output(
                ranked
            )
        )

        # ----------------------------------------------------
        # Display top 20
        # ----------------------------------------------------

        print("\n" + "=" * 70)
        print("TOP 20 COMPANIES")
        print("=" * 70)

        print(
            output.head(20).to_string(
                index=False
            )
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        self.save_output(
            output
        )

        return output


# ============================================================
# MAIN
# ============================================================

def main():

    ranking = CompanyRanking()

    ranking.run()

    print("\n" + "=" * 70)
    print(
        "✓ DAY 17 COMPLETED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()