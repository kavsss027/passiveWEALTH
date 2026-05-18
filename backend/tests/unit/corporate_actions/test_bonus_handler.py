import pytest
from datetime import date
from decimal import Decimal
from app.corporate_actions.base import PortfolioState
from app.corporate_actions.bonus import BonusIssueHandler
from app.core.exceptions import ValidationError

def test_bonus_handler_eligibility():
    handler = BonusIssueHandler()
    assert handler.is_eligible(date(2020, 1, 1), date(2020, 1, 2)) is True
    assert handler.is_eligible(date(2020, 1, 2), date(2020, 1, 2)) is False
    assert handler.is_eligible(date(2020, 1, 3), date(2020, 1, 2)) is False

def test_bonus_handler_apply_success():
    handler = BonusIssueHandler()
    state = PortfolioState(
        date=date(2020, 1, 1),
        quantity=Decimal("100"),
        cost_basis_per_share=Decimal("10.00"),
        total_invested=Decimal("1000.00"),
        cumulative_dividends_received=Decimal("0.00")
    )
    action = {
        "action_date": date(2020, 1, 2),
        "numerator": Decimal("1"),
        "denominator": Decimal("1")
    }
    
    result = handler.apply(state, action)
    assert result.event_type == "BONUS"
    assert result.financial_impact == Decimal("0")
    assert result.impact_type == "STRUCTURAL"
    assert result.new_state.quantity == Decimal("200")
    assert result.new_state.cost_basis_per_share == Decimal("5.00")
    assert result.new_state.total_invested == Decimal("1000.00")

def test_bonus_handler_validation():
    handler = BonusIssueHandler()
    state = PortfolioState(
        date=date(2020, 1, 1),
        quantity=Decimal("100"),
        cost_basis_per_share=Decimal("10.00"),
        total_invested=Decimal("1000.00"),
        cumulative_dividends_received=Decimal("0.00")
    )
    
    # Zero or negative values
    with pytest.raises(ValidationError):
        handler.apply(state, {"action_date": date(2020, 1, 2), "numerator": 0, "denominator": 1})
