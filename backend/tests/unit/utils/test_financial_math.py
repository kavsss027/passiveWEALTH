from decimal import Decimal
from app.utils.financial_math import get_decimal, round_monetary, calculate_adjusted_cost_basis, calculate_shares_after_action

def test_get_decimal():
    assert get_decimal(10) == Decimal("10")
    assert get_decimal("10.5") == Decimal("10.5")
    assert get_decimal(10.5) == Decimal("10.5")

def test_round_monetary():
    assert round_monetary(Decimal("10.12345")) == Decimal("10.1235")
    assert round_monetary(Decimal("10.12344")) == Decimal("10.1234")

def test_calculate_adjusted_cost_basis():
    assert calculate_adjusted_cost_basis(Decimal("500"), Decimal("2")) == Decimal("250.0000")

def test_calculate_shares_after_action():
    assert calculate_shares_after_action(Decimal("100"), Decimal("2")) == Decimal("200.0000")
