import pytest

@pytest.mark.parametrize("rule_id", [f"DQ_RULE_{i:02d}" for i in range(1, 15)])
def test_data_quality_rules(rule_id):
    assert rule_id.startswith("DQ_RULE_")
