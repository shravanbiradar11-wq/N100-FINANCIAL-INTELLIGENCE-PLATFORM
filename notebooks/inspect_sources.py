from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")

files = list(RAW_DIR.glob("*.xlsx"))

print(f"Found {len(files)} Excel files")

for file in files:
    print("\n" + "=" * 80)
    print(f"FILE: {file.name}")
    print("=" * 80)

    try:
        excel = pd.ExcelFile(file)

        print("Sheets:")
        for sheet in excel.sheet_names:
            print(f"  - {sheet}")

            df = pd.read_excel(file, sheet_name=sheet)

            print(f"    Rows: {len(df)}")
            print(f"    Columns: {len(df.columns)}")
            print(f"    Column names: {list(df.columns)}")

            print("\nFirst 3 rows:")
            print(df.head(3))

    except Exception as e:
        print(f"ERROR: {e}")