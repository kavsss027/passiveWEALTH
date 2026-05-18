from decimal import Decimal
from datetime import date
from app.reconstruction.state_machine import PortfolioStateMachine
from app.corporate_actions.split import StockSplitHandler
from app.corporate_actions.bonus import BonusIssueHandler

def test_state_machine_transitions():
    machine = PortfolioStateMachine(
        buy_date=date(2020, 1, 1),
        quantity=Decimal("100"),
        buy_price_per_share=Decimal("10.00")
    )
    
    assert machine.final_state().quantity == Decimal("100")
    assert machine.final_state().total_invested == Decimal("1000.00")
    
    # Apply split
    split_handler = StockSplitHandler()
    res = machine.apply(split_handler, {
        "action_date": date(2020, 2, 1),
        "numerator": Decimal("2"),
        "denominator": Decimal("1")
    })
    
    assert res is not None
    assert machine.final_state().quantity == Decimal("200")
    assert machine.final_state().total_invested == Decimal("1000.00")
    assert machine.final_state().cost_basis_per_share == Decimal("5.00")
    
    # Ineligible action (before buy date) should be skipped
    res_ineligible = machine.apply(split_handler, {
        "action_date": date(2019, 12, 31),
        "numerator": Decimal("2"),
        "denominator": Decimal("1")
    })
    assert res_ineligible is None
    assert machine.final_state().quantity == Decimal("200")
