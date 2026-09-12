from pathlib import Path

from src.etl.loader import load_and_normalize


def main():

    # Load both files
    companies = load_and_normalize(
        Path("data/raw/companies.xlsx")
    )

    analysis = load_and_normalize(
        Path("data/raw/analysis.xlsx")
    )

    print("\n" + "=" * 70)
    print("COMPANY ID CHECK")
    print("=" * 70)

    print("\nCompanies IDs:")
    print(sorted(companies["id"].astype(str).unique()))

    print("\nAnalysis company IDs:")
    print(sorted(analysis["company_id"].astype(str).unique()))

    # Find IDs in analysis that do not exist in companies
    company_ids = set(
        companies["id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    analysis_ids = set(
        analysis["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    missing_ids = analysis_ids - company_ids

    print("\n" + "=" * 70)
    print("FOREIGN KEY MISMATCHES")
    print("=" * 70)

    if missing_ids:

        print(
            f"\nFound {len(missing_ids)} missing company IDs:"
        )

        for company_id in sorted(missing_ids):
            print(f"✗ {company_id}")

    else:

        print(
            "\n✓ All analysis.company_id values "
            "exist in companies.id"
        )


if __name__ == "__main__":
    main()