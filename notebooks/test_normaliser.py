import pandas as pd

from src.etl.normaliser import (
    normalize_year,
    normalize_ticker,
    normalize_text,
    normalize_dataframe
)


print("YEAR TESTS")
print("-" * 40)

print(normalize_year(2024))
print(normalize_year("2024"))
print(normalize_year("FY2024"))
print(normalize_year("FY 2024"))
print(normalize_year(2024.0))
print(normalize_year("ABC"))


print("\nTICKER TESTS")
print("-" * 40)

print(normalize_ticker("reliance"))
print(normalize_ticker(" RELIANCE "))
print(normalize_ticker("ReLiAnCe"))
print(normalize_ticker(""))


print("\nTEXT TESTS")
print("-" * 40)

print(normalize_text(" Reliance Industries "))
print(normalize_text(""))
print(normalize_text(None))


print("\nDATAFRAME TEST")
print("-" * 40)

df = pd.DataFrame({
    " Company Name ": ["Reliance Industries"],
    "Ticker": [" reliance "],
    "Year": ["FY2024"]
})

print("Before:")
print(df)

result = normalize_dataframe(df)

print("\nAfter:")
print(result)