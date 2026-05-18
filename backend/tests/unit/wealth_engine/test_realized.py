from decimal import Decimal
from datetime import date
from app.corporate_actions.base import ActionResult, PortfolioState
from app.wealth_engine.realized import calculate_realized_dividends

def test_calculate_realized_dividends():
    state = PortfolioState(
        date=date(2020, 1, 1),
        quantity=Decimal("100"),
        cost_basis_per_share=Decimal("10.00"),
        total_invested=Decimal("1000.00"),
        cumulative_dividends_received=Decimal("0.00")
    )
    
    event_log = [
        # Structural event
        ActionResult(
            new_state=state,
            event_type="SPLIT",
            description="split",
            financial_impact=Decimal("0"),
            impact_type="STRUCTURAL"
        ),
        # Realized event 1
        ActionResult(
            new_state=state,
            event_type="DIVIDEND",
            description="div 1",
            financial_impact=Decimal("150.00"),
            impact_type="REALIZED"
        ),
        # Realized event 2
        ActionResult(
            new_state=state,
            event_type="DIVIDEND",
            description="div 2",
            financial_impact=Decimal("200.00"),
            impact_type="REALIZED"
        )
    ]
    
    total = calculate_realized_dividends(event_log)
    assert total == Decimal("350.00")
