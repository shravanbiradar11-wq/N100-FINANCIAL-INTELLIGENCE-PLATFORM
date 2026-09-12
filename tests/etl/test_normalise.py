import pytest

def normalize_year(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        val_int = int(val)
        if 2000 <= val_int <= 2030:
            return val_int
    val_str = str(val).strip()
    if "." in val_str:
        val_str = val_str.split(".")[0]
    if val_str.isdigit() and len(val_str) == 4:
        return int(val_str)
    if "FY" in val_str.upper():
        clean = "".join(filter(str.isdigit, val_str))
        if len(clean) == 2:
            return 2000 + int(clean)
        elif len(clean) == 4:
            return int(clean)
    return None

@pytest.mark.parametrize("input_val, expected", [
    (2024, 2024), ("2023", 2023), ("FY24", 2024), ("FY 2022", 2022),
    ("FY21", 2021), (2020.0, 2020), ("2019", 2019), ("FY 20", 2020),
    (2018, 2018), ("2017", 2017), ("FY 16", 2016), (2015, 2015),
    ("FY14", 2014), ("2013", 2013), ("FY 12", 2012), (2011, 2011),
    ("2010", 2010), ("FY 09", 2009), ("2008", 2008), ("FY07", 2007)
])
def test_normalize_year_variants(input_val, expected):
    assert normalize_year(input_val) == expected
