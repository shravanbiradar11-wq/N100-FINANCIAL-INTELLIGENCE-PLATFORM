from pathlib import Path

from src.etl.loader import (
    load_and_normalize
)


RAW_PATH = Path("data/raw")

excel_files = list(
    RAW_PATH.glob("*.xlsx")
)


all_data = {}


for file in excel_files:

    print("\n" + "=" * 60)

    print(
        f"PROCESSING: {file.name}"
    )

    print("=" * 60)

    df = load_and_normalize(
        file
    )

    # Store DataFrame
    table_name = file.stem

    all_data[table_name] = df

    print("\nShape:")

    print(df.shape)

    print("\nColumns:")

    print(df.columns.tolist())

    print("\nFirst 3 rows:")

    print(df.head(3))


print("\n" + "=" * 60)

print("ALL FILES LOADED SUCCESSFULLY")

print("=" * 60)


for name, df in all_data.items():

    print(
        f"{name}: "
        f"{df.shape[0]} rows, "
        f"{df.shape[1]} columns"
    )