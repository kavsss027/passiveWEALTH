import pytest
from datetime import date
from decimal import Decimal
from app.corporate_actions.base import PortfolioState
from app.corporate_actions.dividend import CashDividendHandler
from app.core.exceptions import ValidationError

def test_dividend_handler_eligibility():
    handler = CashDividendHandler()
    assert handler.is_eligible(date(2020, 1, 1), date(2020, 1, 2)) is True
    assert handler.is_eligible(date(2020, 1, 2), date(2020, 1, 2)) is False
    assert handler.is_eligible(date(2020, 1, 3), date(2020, 1, 2)) is False

def test_dividend_handler_apply_success():
    handler = CashDividendHandler()
    state = PortfolioState(
        date=date(2020, 1, 1),
        quantity=Decimal("100"),
        cost_basis_per_share=Decimal("10.00"),
        total_invested=Decimal("1000.00"),
        cumulative_dividends_received=Decimal("0.00")
    )
    action = {
        "action_date": date(2020, 1, 2),
        "numerator": Decimal("2.50")
    }
    
    result = handler.apply(state, action)
    assert result.event_type == "DIVIDEND"
    assert result.financial_impact == Decimal("250.0000")
    assert result.impact_type == "REALIZED"
    assert result.new_state.quantity == Decimal("100")
    assert result.new_state.cumulative_dividends_received == Decimal("250.0000")

def test_dividend_handler_validation():
    handler = CashDividendHandler()
    state = PortfolioState(
        date=date(2020, 1, 1),
        quantity=Decimal("100"),
        cost_basis_per_share=Decimal("10.00"),
        total_invested=Decimal("1000.00"),
        cumulative_dividends_received=Decimal("0.00")
    )
    
    # Zero/negative dividend
    with pytest.raises(ValidationError):
        handler.apply(state, {"action_date": date(2020, 1, 2), "numerator": 0})
