import pytest
from decimal import Decimal
from datetime import date
from app.reconstruction.engine import ReconstructionEngine
from app.corporate_actions.split import StockSplitHandler
from app.corporate_actions.bonus import BonusIssueHandler
from app.corporate_actions.dividend import CashDividendHandler
from app.corporate_actions.sequencer import CorporateActionSequencer

@pytest.mark.asyncio
async def test_reconstruction_engine():
    engine = ReconstructionEngine(
        split_handler=StockSplitHandler(),
        bonus_handler=BonusIssueHandler(),
        dividend_handler=CashDividendHandler(),
        sequencer=CorporateActionSequencer()
    )
    
    actions = [
        {
            "action_date": date(2020, 2, 1),
            "action_type": "SPLIT",
            "numerator": Decimal("2"),
            "denominator": Decimal("1")
        },
        {
            "action_date": date(2020, 3, 1),
            "action_type": "DIVIDEND",
            "numerator": Decimal("1.5"),
            "denominator": Decimal("1")
        },
        {
            "action_date": date(2020, 4, 1),
            "action_type": "UNKNOWN_ACTION",
            "numerator": Decimal("1"),
            "denominator": Decimal("1")
        }
    ]
    
    result = await engine.reconstruct(
        ticker="TEST",
        exchange="NSE",
        buy_date=date(2020, 1, 1),
        quantity=Decimal("100"),
        buy_price_per_share=Decimal("10.00"),
        corporate_actions=actions
    )
    
    assert result.final_state.quantity == Decimal("200")
    assert result.final_state.total_invested == Decimal("1000.00")
    assert result.final_state.cumulative_dividends_received == Decimal("300.0000") # 200 shares * 1.50
    assert len(result.event_log) == 2
    assert result.event_log[0].event_type == "SPLIT"
    assert result.event_log[1].event_type == "DIVIDEND"
