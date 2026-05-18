import pytest
from datetime import date
from decimal import Decimal
from app.corporate_actions.base import PortfolioState
from app.corporate_actions.split import StockSplitHandler
from app.core.exceptions import ValidationError

def test_split_handler_eligibility():
    handler = StockSplitHandler()
    assert handler.is_eligible(date(2020, 1, 1), date(2020, 1, 2)) is True
    assert handler.is_eligible(date(2020, 1, 2), date(2020, 1, 2)) is False
    assert handler.is_eligible(date(2020, 1, 3), date(2020, 1, 2)) is False

def test_split_handler_apply_success():
    handler = StockSplitHandler()
    state = PortfolioState(
        date=date(2020, 1, 1),
        quantity=Decimal("100"),
        cost_basis_per_share=Decimal("10.00"),
        total_invested=Decimal("1000.00"),
        cumulative_dividends_received=Decimal("0.00")
    )
    action = {
        "action_date": date(2020, 1, 2),
        "numerator": Decimal("2"),
        "denominator": Decimal("1")
    }
    
    result = handler.apply(state, action)
    assert result.event_type == "SPLIT"
    assert result.financial_impact == Decimal("0")
    assert result.impact_type == "STRUCTURAL"
    assert result.new_state.quantity == Decimal("200")
    assert result.new_state.cost_basis_per_share == Decimal("5.00")
    assert result.new_state.total_invested == Decimal("1000.00")

def test_split_handler_validation():
    handler = StockSplitHandler()
    state = PortfolioState(
        date=date(2020, 1, 1),
        quantity=Decimal("100"),
        cost_basis_per_share=Decimal("10.00"),
        total_invested=Decimal("1000.00"),
        cumulative_dividends_received=Decimal("0.00")
    )
    
    # Numerator equal to denominator
    with pytest.raises(ValidationError):
        handler.apply(state, {"action_date": date(2020, 1, 2), "numerator": 1, "denominator": 1})
        
    # Negative/zero values
    with pytest.raises(ValidationError):
        handler.apply(state, {"action_date": date(2020, 1, 2), "numerator": -1, "denominator": 1})

def test_split_handler_reverse_split():
    handler = StockSplitHandler()
    state = PortfolioState(
        date=date(2020, 1, 1),
        quantity=Decimal("100"),
        cost_basis_per_share=Decimal("10.00"),
        total_invested=Decimal("1000.00"),
        cumulative_dividends_received=Decimal("0.00")
    )
    # Reverse split 1:2
    action = {
        "action_date": date(2020, 1, 2),
        "numerator": Decimal("1"),
        "denominator": Decimal("2")
    }
    result = handler.apply(state, action)
    assert result.new_state.quantity == Decimal("50")
    assert result.new_state.cost_basis_per_share == Decimal("20.00")
