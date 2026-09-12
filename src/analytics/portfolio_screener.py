from pathlib import Path
import sqlite3
import pandas as pd


DB_PATH = Path("db/nifty100.db")
OUTPUT_PATH = Path("output/portfolio_candidates.csv")


class PortfolioScreener:

    def __init__(self, database_path=DB_PATH):
        self.database_path = Path(database_path)

        if not self.database_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.database_path}"
            )

    # ========================================================
    # LOAD DATA
    # ========================================================

    def load_data(self):

        connection = sqlite3.connect(
            self.database_path
        )

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
        # Company ID compatibility
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
            .str.replace(
                ".NS",
                "",
                regex=False
            )
            .str.replace(
                ".BO",
                "",
                regex=False
            )
        )

        companies["company_id"] = (
            companies["company_id"]
            .astype(str)
            .str.strip()
            .str.upper()
            .str.replace(
                ".NS",
                "",
                regex=False
            )
            .str.replace(
                ".BO",
                "",
                regex=False
            )
        )

        # ----------------------------------------------------
        # Company information
        # ----------------------------------------------------

        lookup_columns = [
            "company_id"
        ]

        if "company_name" in companies.columns:
            lookup_columns.append(
                "company_name"
            )

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

        df = ratios.merge(
            lookup,
            on="company_id",
            how="left"
        )

        if "company_name" not in df.columns:
            df["company_name"] = df["company_id"]

        if "broad_sector" not in df.columns:
            df["broad_sector"] = "Unknown"

        return df

    # ========================================================
    # LATEST YEAR
    # ========================================================

    def latest_year(
        self,
        df
    ):

        df["year_numeric"] = pd.to_numeric(
            df["year"],
            errors="coerce"
        )

        df = df.dropna(
            subset=[
                "company_id",
                "year_numeric"
            ]
        ).copy()

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

        df = (
            df.drop_duplicates(
                subset=["company_id"],
                keep="first"
            )
            .copy()
        )

        df.drop(
            columns=["year_numeric"],
            inplace=True,
            errors="ignore"
        )

        return df

    # ========================================================
    # NUMERIC COLUMNS
    # ========================================================

    def convert_numeric(
        self,
        df
    ):

        columns = [
            "return_on_equity_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
            "interest_coverage",
            "net_profit_margin_pct",
            "composite_score"
        ]

        for column in columns:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        return df

    # ========================================================
    # SCORE
    # ========================================================

    def calculate_score(
        self,
        df
    ):

        required = [
            "return_on_equity_pct",
            "debt_to_equity",
            "revenue_cagr_5yr"
        ]

        missing = [
            column
            for column in required
            if column not in df.columns
        ]

        if missing:

            raise ValueError(
                "Missing columns:\n"
                + "\n".join(
                    f" - {c}"
                    for c in missing
                )
            )

        # ----------------------------------------------------
        # If Day 17 score exists, use it
        # ----------------------------------------------------

        if "composite_score" not in df.columns:

            df["composite_score"] = 0

            df["composite_score"] += (
                df["return_on_equity_pct"]
                .fillna(0)
                .clip(lower=0, upper=25)
            )

            df["composite_score"] += (
                df["revenue_cagr_5yr"]
                .fillna(0)
                .clip(lower=0, upper=20)
            )

            df["composite_score"] += (
                (df["debt_to_equity"] < 1)
                .astype(int) * 20
            )

        return df

    # ========================================================
    # APPLY SCREEN
    # ========================================================

    def apply_screen(
        self,
        df
    ):

        # ----------------------------------------------------
        # Core filters
        # ----------------------------------------------------

        roe_condition = (
            df["return_on_equity_pct"] > 15
        )

        debt_condition = (
            df["debt_to_equity"] < 1
        )

        growth_condition = (
            df["revenue_cagr_5yr"] > 5
        )

        # ----------------------------------------------------
        # Interest coverage
        #
        # Debt-free companies have ICR = NULL.
        # These should not automatically fail.
        # ----------------------------------------------------

        if "interest_coverage" in df.columns:

            icr_condition = (
                df["interest_coverage"].isna()
                |
                (
                    df["interest_coverage"]
                    > 1.5
                )
            )

        else:

            icr_condition = True

        # ----------------------------------------------------
        # Final filter
        # ----------------------------------------------------

        candidates = df[
            roe_condition
            & debt_condition
            & growth_condition
            & icr_condition
        ].copy()

        return candidates

    # ========================================================
    # RANK
    # ========================================================

    def rank_candidates(
        self,
        df
    ):

        df = df.sort_values(
            [
                "composite_score",
                "return_on_equity_pct",
                "revenue_cagr_5yr"
            ],
            ascending=[
                False,
                False,
                False
            ]
        ).copy()

        df["portfolio_rank"] = range(
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
            "portfolio_rank",
            "company_id",
            "company_name",
            "broad_sector",
            "year",

            "return_on_equity_pct",
            "net_profit_margin_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
            "interest_coverage",

            "composite_score",
            "quality_rating"
        ]

        available = [
            c
            for c in columns
            if c in df.columns
        ]

        return df[
            available
        ].copy()

    # ========================================================
    # SAVE
    # ========================================================

    def save(
        self,
        df
    ):

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        df.to_csv(
            OUTPUT_PATH,
            index=False
        )

        print(
            f"\n✓ Saved: {OUTPUT_PATH}"
        )

        print(
            f"✓ Candidates: {len(df)}"
        )

    # ========================================================
    # RUN
    # ========================================================

    def run(self):

        print("=" * 70)
        print("SPRINT 3 - DAY 19")
        print("PORTFOLIO SCREENING")
        print("=" * 70)

        # Load
        df = self.load_data()

        print(
            f"\nFinancial ratio rows: {len(df)}"
        )

        # Latest year
        df = self.latest_year(
            df
        )

        print(
            f"Latest companies: {len(df)}"
        )

        # Numeric
        df = self.convert_numeric(
            df
        )

        # Score
        df = self.calculate_score(
            df
        )

        # Screen
        candidates = self.apply_screen(
            df
        )

        print(
            f"Companies passing screen: "
            f"{len(candidates)}"
        )

        # Rank
        candidates = self.rank_candidates(
            candidates
        )

        # Output
        output = self.prepare_output(
            candidates
        )

        print("\n" + "=" * 70)
        print("PORTFOLIO CANDIDATES")
        print("=" * 70)

        if output.empty:

            print(
                "⚠ No companies passed all filters."
            )

        else:

            print(
                output.head(20).to_string(
                    index=False
                )
            )

        # Save
        self.save(
            output
        )

        return output


# ============================================================
# MAIN
# ============================================================

def main():

    screener = PortfolioScreener()

    screener.run()

    print("\n" + "=" * 70)
    print("✓ DAY 19 COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
    