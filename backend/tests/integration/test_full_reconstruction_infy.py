import pytest
from datetime import date
from decimal import Decimal
from app.reconstruction.engine import ReconstructionEngine
from app.corporate_actions.split import StockSplitHandler
from app.corporate_actions.bonus import BonusIssueHandler
from app.corporate_actions.dividend import CashDividendHandler
from app.corporate_actions.sequencer import CorporateActionSequencer

@pytest.mark.asyncio
async def test_full_reconstruction_infy():
    engine = ReconstructionEngine(
        split_handler=StockSplitHandler(),
        bonus_handler=BonusIssueHandler(),
        dividend_handler=CashDividendHandler(),
        sequencer=CorporateActionSequencer()
    )
    
    # INFY Scenario:
    # Buy: 100 shares on 1999-01-01
    # 1999 split 2:1
    # 2004 split 2:1
    # 2014 bonus 1:1
    # 2018 bonus 1:1
    
    corporate_actions = [
        {
            "action_date": date(1999, 11, 29),
            "action_type": "SPLIT",
            "numerator": Decimal("2"),
            "denominator": Decimal("1")
        },
        {
            "action_date": date(2004, 7, 2),
            "action_type": "SPLIT",
            "numerator": Decimal("2"),
            "denominator": Decimal("1")
        },
        {
            "action_date": date(2014, 12, 3),
            "action_type": "BONUS",
            "numerator": Decimal("1"),
            "denominator": Decimal("1")
        },
        {
            "action_date": date(2018, 9, 4),
            "action_type": "BONUS",
            "numerator": Decimal("1"),
            "denominator": Decimal("1")
        }
    ]
    
    result = await engine.reconstruct(
        ticker="INFY",
        exchange="NSE",
        buy_date=date(1999, 1, 1),
        quantity=Decimal("100"),
        buy_price_per_share=Decimal("150.00"),
        corporate_actions=corporate_actions
    )
    
    # Gate condition verification:
    # 1. Final quantity must be exactly 1600 shares
    assert result.final_state.quantity == Decimal("1600")
    
    # 2. Total invested remains unchanged
    assert result.final_state.total_invested == Decimal("100") * Decimal("150.00")
    
    # 3. Cost basis is adjusted correctly
    expected_cost_basis = (Decimal("100") * Decimal("150.00")) / Decimal("1600")
    assert result.final_state.cost_basis_per_share == expected_cost_basis
