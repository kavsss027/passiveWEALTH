import pytest
from datetime import date
from decimal import Decimal
from app.reconstruction.engine import ReconstructionEngine
from app.corporate_actions.split import StockSplitHandler
from app.corporate_actions.bonus import BonusIssueHandler
from app.corporate_actions.dividend import CashDividendHandler
from app.corporate_actions.sequencer import CorporateActionSequencer

@pytest.mark.asyncio
async def test_full_reconstruction_tcs():
    engine = ReconstructionEngine(
        split_handler=StockSplitHandler(),
        bonus_handler=BonusIssueHandler(),
        dividend_handler=CashDividendHandler(),
        sequencer=CorporateActionSequencer()
    )
    
    # TCS Scenario:
    # Buy: 10 shares on 2010-01-01
    # 2014 split 1:5 (1 share becomes 5, i.e., numerator=5, denominator=1)
    
    corporate_actions = [
        {
            "action_date": date(2014, 5, 23),
            "action_type": "SPLIT",
            "numerator": Decimal("5"),
            "denominator": Decimal("1")
        }
    ]
    
    result = await engine.reconstruct(
        ticker="TCS",
        exchange="NSE",
        buy_date=date(2010, 1, 1),
        quantity=Decimal("10"),
        buy_price_per_share=Decimal("1000.00"),
        corporate_actions=corporate_actions
    )
    
    # Gate condition verification:
    # 1. Expected final quantity: exactly 50 shares
    assert result.final_state.quantity == Decimal("50")
    
    # 2. Total invested remains unchanged
    assert result.final_state.total_invested == Decimal("10000.00")
