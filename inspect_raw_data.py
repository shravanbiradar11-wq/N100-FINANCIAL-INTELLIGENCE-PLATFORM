from pathlib import Path
import pandas as pd

RAW_PATH = Path("data/raw")

for file in RAW_PATH.glob("*.xlsx"):

    print("\n" + "=" * 60)
    print(f"FILE: {file.name}")
    print("=" * 60)

    df = pd.read_excel(file)

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 3 rows:")
    print(df.head(3))