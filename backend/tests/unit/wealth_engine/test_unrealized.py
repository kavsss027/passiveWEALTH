from decimal import Decimal
from app.wealth_engine.unrealized import calculate_unrealized_gain

def test_calculate_unrealized_gain():
    gain = calculate_unrealized_gain(
        current_price=Decimal("150.00"),
        adjusted_cost_basis=Decimal("100.00"),
        current_quantity=Decimal("10")
    )
    assert gain == Decimal("500.00")
