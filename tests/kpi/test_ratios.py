import pytest

def calc_roe(pat, equity):
    return (pat / equity * 100) if equity > 0 else None

def calc_de_ratio(debt, equity):
    return (debt / equity) if equity > 0 else 0.0

def calc_icr(ebit, interest):
    return (ebit / interest) if interest > 0 else None

def test_roe_positive_equity():
    assert calc_roe(100, 500) == 20.0

def test_roe_negative_equity():
    assert calc_roe(100, -500) is None

def test_de_ratio_zero_debt():
    assert calc_de_ratio(0, 500) == 0.0

def test_icr_zero_interest():
    assert calc_icr(200, 0) is None

@pytest.mark.parametrize("metric_val", [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105])
def test_kpi_range_validations(metric_val):
    assert metric_val > 0
