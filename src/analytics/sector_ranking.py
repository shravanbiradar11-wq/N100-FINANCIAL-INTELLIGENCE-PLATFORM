from pathlib import Path
import sqlite3
import pandas as pd


DB_PATH = Path("db/nifty100.db")
OUTPUT_PATH = Path("output/sector_ranking.csv")


class SectorRanking:

    def __init__(self, database_path=DB_PATH):
        self.database_path = Path(database_path)

        if not self.database_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.database_path}"
            )

    # ========================================================
    # DATABASE
    # ========================================================

    def get_connection(self):
        return sqlite3.connect(self.database_path)

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
        # Companies ID
        # ----------------------------------------------------

        if "company_id" not in companies.columns:

            if "id" in companies.columns:
                companies = companies.rename(
                    columns={"id": "company_id"}
                )

            else:
                raise ValueError(
                    "companies table has neither "
                    "company_id nor id."
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

    def latest_year_per_company(
        self,
        df
    ):

        if "year" not in df.columns:
            raise ValueError(
                "financial_ratios does not contain year."
            )

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
    # NUMERIC CONVERSION
    # ========================================================

    def convert_numeric(
        self,
        df
    ):

        columns = [
            "return_on_equity_pct",
            "net_profit_margin_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
            "interest_coverage"
        ]

        for column in columns:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        return df

    # ========================================================
    # SECTOR BENCHMARKS
    # ========================================================

    def calculate_sector_benchmarks(
        self,
        df
    ):

        benchmark = (
            df.groupby(
                "broad_sector",
                dropna=False
            )
            .agg(
                sector_avg_roe=(
                    "return_on_equity_pct",
                    "mean"
                ),
                sector_avg_npm=(
                    "net_profit_margin_pct",
                    "mean"
                ),
                sector_avg_de=(
                    "debt_to_equity",
                    "mean"
                ),
                sector_avg_revenue_cagr=(
                    "revenue_cagr_5yr",
                    "mean"
                ),
                sector_avg_icr=(
                    "interest_coverage",
                    "mean"
                )
            )
            .reset_index()
        )

        return benchmark

    # ========================================================
    # ADD BENCHMARK COMPARISON
    # ========================================================

    def add_comparison(
        self,
        df
    ):

        benchmark = (
            self.calculate_sector_benchmarks(
                df
            )
        )

        df = df.merge(
            benchmark,
            on="broad_sector",
            how="left"
        )

        # ----------------------------------------------------
        # Difference from sector average
        # ----------------------------------------------------

        df["roe_vs_sector_pct"] = (
            df["return_on_equity_pct"]
            - df["sector_avg_roe"]
        )

        df["npm_vs_sector_pct"] = (
            df["net_profit_margin_pct"]
            - df["sector_avg_npm"]
        )

        df["de_vs_sector"] = (
            df["debt_to_equity"]
            - df["sector_avg_de"]
        )

        df["revenue_cagr_vs_sector_pct"] = (
            df["revenue_cagr_5yr"]
            - df["sector_avg_revenue_cagr"]
        )

        df["icr_vs_sector"] = (
            df["interest_coverage"]
            - df["sector_avg_icr"]
        )

        # ----------------------------------------------------
        # Sector performance score
        # ----------------------------------------------------

        df["sector_relative_score"] = (
            (df["roe_vs_sector_pct"] > 0)
            .astype(int)

            +

            (df["npm_vs_sector_pct"] > 0)
            .astype(int)

            +

            (df["de_vs_sector"] < 0)
            .astype(int)

            +

            (df["revenue_cagr_vs_sector_pct"] > 0)
            .astype(int)

            +

            (df["icr_vs_sector"] > 0)
            .astype(int)
        )

        return df

    # ========================================================
    # RANK WITHIN SECTOR
    # ========================================================

    def rank_sector(
        self,
        df
    ):

        df["sector_rank"] = (
            df.groupby(
                "broad_sector"
            )[
                "sector_relative_score"
            ]
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

    def prepare_output(
        self,
        df
    ):

        columns = [

            "sector_rank",

            "company_id",
            "company_name",
            "broad_sector",
            "year",

            "return_on_equity_pct",
            "sector_avg_roe",
            "roe_vs_sector_pct",

            "net_profit_margin_pct",
            "sector_avg_npm",
            "npm_vs_sector_pct",

            "debt_to_equity",
            "sector_avg_de",
            "de_vs_sector",

            "revenue_cagr_5yr",
            "sector_avg_revenue_cagr",
            "revenue_cagr_vs_sector_pct",

            "interest_coverage",
            "sector_avg_icr",
            "icr_vs_sector",

            "sector_relative_score"
        ]

        available = [
            c for c in columns
            if c in df.columns
        ]

        output = df[
            available
        ].copy()

        return output.sort_values(
            [
                "broad_sector",
                "sector_rank",
                "company_id"
            ]
        )

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
            f"✓ Rows: {len(df)}"
        )

    # ========================================================
    # RUN
    # ========================================================

    def run(self):

        print("=" * 70)
        print("SPRINT 3 - DAY 18")
        print("SECTOR-WISE COMPANY RANKING")
        print("=" * 70)

        # Load
        df = self.load_data()

        print(
            f"\nFinancial ratio rows: {len(df)}"
        )

        # Latest year
        df = self.latest_year_per_company(
            df
        )

        print(
            f"Latest company rows: {len(df)}"
        )

        # Numeric
        df = self.convert_numeric(
            df
        )

        # Benchmark
        df = self.add_comparison(
            df
        )

        # Rank
        df = self.rank_sector(
            df
        )

        # Output
        output = self.prepare_output(
            df
        )

        print("\nTOP COMPANIES BY SECTOR")
        print("-" * 70)

        for sector in output[
            "broad_sector"
        ].dropna().unique():

            print(
                f"\n{sector}"
            )

            sector_data = output[
                output["broad_sector"]
                == sector
            ].head(5)

            print(
                sector_data[
                    [
                        "sector_rank",
                        "company_name",
                        "sector_relative_score"
                    ]
                ].to_string(
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

    ranking = SectorRanking()

    ranking.run()

    print("\n" + "=" * 70)
    print("✓ DAY 18 COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()