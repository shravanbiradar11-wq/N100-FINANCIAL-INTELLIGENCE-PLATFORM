"""
Sprint 3 - Day 16
Six Preset Screeners

Implements the six preset screening strategies defined
in the Sprint 3 specification.
"""

from pathlib import Path
import sys

# Allow execution as:
# python -m src.screener.presets
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.screener.engine import ScreenerEngine


# ============================================================
# PRESET DEFINITIONS
# ============================================================

PRESETS = {

    "Quality Compounder": {
        "roe_min": 15,
        "de_max": 1.0,
        "fcf_min": 0,
        "revenue_cagr_5yr_min": 10
    },

    "Value Pick": {
        "pe_max": 20,
        "pb_max": 3.0,
        "de_max": 2.0,
        "dividend_yield_min": 1
    },

    "Growth Accelerator": {
        "pat_cagr_5yr_min": 20,
        "revenue_cagr_5yr_min": 15,
        "de_max": 2.0
    },

    "Dividend Champion": {
        "dividend_yield_min": 2,
        "dividend_payout_max": 80,
        "fcf_min": 0
    },

    "Debt-Free Blue Chip": {
        "de_max": 0,
        "roe_min": 12,
        "sales_min": 5000
    },

    "Turnaround Watch": {
        "revenue_cagr_3yr_min": 10,
        "fcf_min": 0
    }
}


# ============================================================
# PRESET SCREENING CLASS
# ============================================================

class PresetScreener:

    def __init__(self):

        self.engine = ScreenerEngine()

    # ========================================================
    # GET DATA
    # ========================================================

    def load_data(self):

        return self.engine.load_data()

    # ========================================================
    # APPLY PRESET
    # ========================================================

    def run_preset(
        self,
        preset_name,
        df=None
    ):

        if preset_name not in PRESETS:

            raise ValueError(
                f"Unknown preset: {preset_name}"
            )

        if df is None:

            df = self.load_data()

        filters = PRESETS[preset_name]

        print()
        print("=" * 70)
        print(f"PRESET: {preset_name}")
        print("=" * 70)

        for name, value in filters.items():

            print(
                f"  {name} = {value}"
            )

        # ----------------------------------------------------
        # Day 15 engine handles the actual filtering
        # ----------------------------------------------------

        result = self.engine.apply_filters(
            df,
            filters
        )

        # ----------------------------------------------------
        # Add existing/fallback composite score
        # ----------------------------------------------------

        result = self.engine.add_composite_score(
            result
        )

        # ----------------------------------------------------
        # Sort by score
        # ----------------------------------------------------

        result = self.engine.sort_results(
            result
        )

        print()
        print(
            f"Input companies/rows : {len(df)}"
        )

        print(
            f"Matched rows          : {len(result)}"
        )

        return result

    # ========================================================
    # RUN ALL PRESETS
    # ========================================================

    def run_all(self):

        df = self.load_data()

        results = {}

        print()
        print("=" * 70)
        print("SPRINT 3 - DAY 16")
        print("6 PRESET SCREENERS")
        print("=" * 70)

        for preset_name in PRESETS:

            try:

                result = self.run_preset(
                    preset_name,
                    df
                )

                results[preset_name] = result

            except Exception as error:

                print()
                print(
                    f"✗ {preset_name} failed:"
                )

                print(
                    f"  {error}"
                )

                results[preset_name] = None

        return results

    # ========================================================
    # PRINT SUMMARY
    # ========================================================

    def print_summary(
        self,
        results
    ):

        print()
        print("=" * 70)
        print("DAY 16 PRESET SUMMARY")
        print("=" * 70)

        for preset_name, result in results.items():

            if result is None:

                print(
                    f"{preset_name:<25} FAILED"
                )

            else:

                print(
                    f"{preset_name:<25} "
                    f"{len(result)} rows"
                )

        print("=" * 70)

    # ========================================================
    # SHOW TOP RESULTS
    # ========================================================

    def show_top_results(
        self,
        results,
        limit=5
    ):

        for preset_name, result in results.items():

            if result is None or result.empty:
                continue

            print()
            print("-" * 70)
            print(
                f"TOP {min(limit, len(result))}: "
                f"{preset_name}"
            )
            print("-" * 70)

            preferred_columns = [
                "company_id",
                "company_name",
                "broad_sector",
                "return_on_equity_pct",
                "roe_pct",
                "debt_to_equity",
                "free_cash_flow_cr",
                "revenue_cagr_5yr",
                "pat_cagr_5yr",
                "dividend_yield_pct",
                "pe_ratio",
                "pb_ratio",
                "composite_quality_score"
            ]

            columns = [
                column
                for column in preferred_columns
                if column in result.columns
            ]

            if columns:

                print(
                    result[
                        columns
                    ].head(limit).to_string(
                        index=False
                    )
                )

            else:

                print(
                    result.head(limit).to_string(
                        index=False
                    )
                )


# ============================================================
# MAIN
# ============================================================

def main():

    screener = PresetScreener()

    results = screener.run_all()

    screener.print_summary(
        results
    )

    screener.show_top_results(
        results,
        limit=5
    )

    print()
    print("=" * 70)
    print("DAY 16 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":

    main()