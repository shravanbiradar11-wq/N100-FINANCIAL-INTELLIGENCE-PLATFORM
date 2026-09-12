from pathlib import Path
import sqlite3
import pandas as pd


DB_PATH = Path("db/nifty100.db")
OUTPUT_PATH = Path("output/company_scorecard.csv")


class CompanyScorer:

    def __init__(self, database_path=DB_PATH):
        self.database_path = Path(database_path)

        if not self.database_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.database_path}"
            )

    # ========================================================
    # DATABASE
    # ========================================================

    def load_data(self):

        connection = sqlite3.connect(
            self.database_path
        )

        try:
            df = pd.read_sql_query(
                """
                SELECT *
                FROM financial_ratios
                """,
                connection
            )

            companies = pd.read_sql_query(
                """
                SELECT *
                FROM companies
                """,
                connection
            )

        finally:
            connection.close()

        df.columns = [
            str(c).strip().lower()
            for c in df.columns
        ]

        companies.columns = [
            str(c).strip().lower()
            for c in companies.columns
        ]

        # companies table uses id in your database
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
        # Company ID normalization
        # ----------------------------------------------------

        df["company_id"] = (
            df["company_id"]
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

            lookup = companies[
                [
                    "company_id",
                    "company_name"
                ]
            ].drop_duplicates(
                "company_id"
            )

            df = df.merge(
                lookup,
                on="company_id",
                how="left"
            )

        else:

            df["company_name"] = (
                df["company_id"]
            )

        return df

    # ========================================================
    # NUMERIC CONVERSION
    # ========================================================

    def numeric(self, df, column):

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # ========================================================
    # VALIDATE
    # ========================================================

    def validate(self, df):

        required = [
            "return_on_equity_pct",
            "net_profit_margin_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
            "interest_coverage"
        ]

        missing = [
            c for c in required
            if c not in df.columns
        ]

        if missing:

            raise ValueError(
                "Missing scoring columns:\n"
                + "\n".join(
                    f" - {c}"
                    for c in missing
                )
            )

    # ========================================================
    # ROE SCORE
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

    # ========================================================
    # NPM SCORE
    # ========================================================

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

    # ========================================================
    # DE SCORE
    # ========================================================

    @staticmethod
    def de_score(value):

        if pd.isna(value):
            return 0

        if value < 0.5:
            return 20

        if value < 1:
            return 15

        if value < 2:
            return 10

        return 5

    # ========================================================
    # CAGR SCORE
    # ========================================================

    @staticmethod
    def cagr_score(value):

        if pd.isna(value):
            return 0

        if value >= 15:
            return 20

        if value >= 10:
            return 15

        if value >= 5:
            return 10

        return 5

    # ========================================================
    # ICR SCORE
    # ========================================================

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
    # CALCULATE SCORES
    # ========================================================

    def calculate_scores(self, df):

        self.validate(df)

        self.numeric(
            df,
            "return_on_equity_pct"
        )

        self.numeric(
            df,
            "net_profit_margin_pct"
        )

        self.numeric(
            df,
            "debt_to_equity"
        )

        self.numeric(
            df,
            "revenue_cagr_5yr"
        )

        self.numeric(
            df,
            "interest_coverage"
        )

        # ----------------------------------------------------
        # Individual scores
        # ----------------------------------------------------

        df["roe_score"] = (
            df["return_on_equity_pct"]
            .apply(self.roe_score)
        )

        df["npm_score"] = (
            df["net_profit_margin_pct"]
            .apply(self.npm_score)
        )

        df["de_score"] = (
            df["debt_to_equity"]
            .apply(self.de_score)
        )

        df["growth_score"] = (
            df["revenue_cagr_5yr"]
            .apply(self.cagr_score)
        )

        df["icr_score"] = (
            df["interest_coverage"]
            .apply(self.icr_score)
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
        # Quality classification
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

        # ----------------------------------------------------
        # Rank
        # ----------------------------------------------------

        df["rank"] = (
            df["composite_score"]
            .rank(
                ascending=False,
                method="dense"
            )
            .astype(int)
        )

        return df

    # ========================================================
    # PREPARE OUTPUT
    # ========================================================

    def prepare_output(self, df):

        columns = [
            "rank",
            "company_id",
            "company_name",
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
            c for c in columns
            if c in df.columns
        ]

        output = df[
            available
        ].copy()

        output = output.sort_values(
            [
                "rank",
                "company_id"
            ]
        )

        return output

    # ========================================================
    # SAVE
    # ========================================================

    def save(self, df):

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        df.to_csv(
            OUTPUT_PATH,
            index=False
        )

        print(
            f"\n✓ Scorecard saved: "
            f"{OUTPUT_PATH}"
        )

        print(
            f"✓ Rows saved: {len(df)}"
        )

    # ========================================================
    # RUN
    # ========================================================

    def run(self):

        print("=" * 70)
        print("COMPANY QUALITY SCORING ENGINE")
        print("=" * 70)

        df = self.load_data()

        print(
            f"\nRows loaded: {len(df)}"
        )

        df = self.calculate_scores(
            df
        )

        output = self.prepare_output(
            df
        )

        print("\nTOP COMPANIES")
        print("-" * 70)

        print(
            output.head(20).to_string(
                index=False
            )
        )

        self.save(output)

        return output


# ============================================================
# MAIN
# ============================================================

def main():

    scorer = CompanyScorer()

    scorer.run()

    print("\n" + "=" * 70)
    print("✓ DAY 16 COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()