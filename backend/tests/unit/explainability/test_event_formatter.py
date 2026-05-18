from decimal import Decimal
from app.explainability.event_formatter import (
    format_buy_event,
    format_split_event,
    format_bonus_event,
    format_dividend_event
)

def test_event_formatters():
    # Buy
    buy_str = format_buy_event(Decimal("100"), "INFY", Decimal("500.00"), Decimal("50000.00"))
    assert buy_str == "Purchased 100 shares of INFY at ₹500.00 per share. Total invested: ₹50000.00."
    
    # Split
    split_str = format_split_event(2, 1, Decimal("100"), Decimal("200"), Decimal("500.00"), Decimal("250.00"))
    assert split_str == "Stock split 2:1. Holdings changed from 100 to 200 shares. Cost basis adjusted from ₹500.00 to ₹250.00 per share."
    
    # Bonus
    bonus_str = format_bonus_event(1, 1, Decimal("200"), Decimal("200"), Decimal("400"))
    assert bonus_str == "Bonus issue 1:1. 200 additional shares issued. Holdings increased from 200 to 400 shares."
    
    # Dividend
    div_str = format_dividend_event(Decimal("7.50"), Decimal("200"), Decimal("1500.00"))
    assert div_str == "Dividend of ₹7.50 per share received on 200 shares. ₹1500.00 credited."

def test_narrative_builder_validations():
    import pytest
    from app.explainability.narrative_builder import build_timeline
    from app.corporate_actions.base import ActionResult, PortfolioState
    from datetime import date
    
    buy_event = {
        "date": date(2020, 1, 1),
        "ticker": "INFY",
        "quantity": Decimal("100"),
        "price": Decimal("500.00"),
        "total_invested": Decimal("50000.00")
    }
    
    # 1. Dividend with impact_type STRUCTURAL should raise ValueError
    state = PortfolioState(date(2020, 1, 2), Decimal("100"), Decimal("500.00"), Decimal("50000.00"), Decimal("0.00"))
    res_div_bad = ActionResult(state, "DIVIDEND", "div", Decimal("10"), "STRUCTURAL")
    with pytest.raises(ValueError):
        build_timeline(buy_event, [res_div_bad])
        
    # 2. Split with impact_type REALIZED should raise ValueError
    res_split_bad = ActionResult(state, "SPLIT", "split", Decimal("0"), "REALIZED")
    with pytest.raises(ValueError):
        build_timeline(buy_event, [res_split_bad])
