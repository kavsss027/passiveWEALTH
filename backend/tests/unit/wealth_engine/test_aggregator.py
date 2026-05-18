from decimal import Decimal
from app.wealth_engine.aggregator import aggregate_wealth_summary

def test_aggregate_wealth_summary():
    summary = aggregate_wealth_summary(
        total_dividends=Decimal("350.00"),
        unrealized_gain=Decimal("500.00"),
        current_quantity=Decimal("10"),
        current_price=Decimal("150.00")
    )
    
    assert summary["total_dividends_received"] == "350.00"
    assert summary["unrealized_gain"] == "500.00"
    assert summary["unrealized_gain_label"] == "if sold at current market price"
    # total_wealth_if_sold = 350.00 + (10 * 150.00) = 1850.00
    assert summary["total_wealth_if_sold"] == "1850.00"
    assert summary["total_wealth_label"] == "total wealth if all shares sold today including dividends received"
