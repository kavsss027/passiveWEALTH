import pytest
from datetime import date
from decimal import Decimal
from app.corporate_actions.sequencer import CorporateActionSequencer
from app.core.exceptions import ValidationError

def test_sequencer_filtering_and_sorting():
    sequencer = CorporateActionSequencer()
    
    actions = [
        # Action before buy date - should be filtered out
        {
            "action_date": date(2019, 12, 31),
            "action_type": "SPLIT",
            "numerator": Decimal("2"),
            "denominator": Decimal("1")
        },
        # Action on buy date - should be filtered out
        {
            "action_date": date(2020, 1, 1),
            "action_type": "SPLIT",
            "numerator": Decimal("2"),
            "denominator": Decimal("1")
        },
        # Action after buy date - eligible
        {
            "action_date": date(2020, 2, 1),
            "action_type": "BONUS",
            "numerator": Decimal("1"),
            "denominator": Decimal("1")
        },
        # Same-date action with lower priority (DIVIDEND) - should be processed after SPLIT
        {
            "action_date": date(2020, 3, 1),
            "action_type": "DIVIDEND",
            "numerator": Decimal("2.50"),
            "denominator": Decimal("1")
        },
        # Same-date action with higher priority (SPLIT)
        {
            "action_date": date(2020, 3, 1),
            "action_type": "SPLIT",
            "numerator": Decimal("2"),
            "denominator": Decimal("1")
        }
    ]
    
    results = sequencer.process_timeline(
        buy_date=date(2020, 1, 1),
        initial_quantity=Decimal("100"),
        buy_price=Decimal("10.00"),
        actions=actions
    )
    
    # 1. Verification of Filtering:
    # 5 actions total, 2 are before/on buy_date -> only 3 actions should be executed
    assert len(results) == 3
    
    # 2. Verification of Sequencing:
    # First action: BONUS on 2020-02-01
    assert results[0].event_type == "BONUS"
    assert results[0].new_state.quantity == Decimal("200") # 100 + 100
    
    # Second action: SPLIT on 2020-03-01 (should execute BEFORE dividend on same date)
    assert results[1].event_type == "SPLIT"
    assert results[1].new_state.quantity == Decimal("400") # 200 * 2
    
    # Third action: DIVIDEND on 2020-03-01 (should execute AFTER split on same date, so gets dividend on 400 shares!)
    assert results[2].event_type == "DIVIDEND"
    assert results[2].new_state.quantity == Decimal("400")
    assert results[2].financial_impact == Decimal("1000.0000") # 400 shares * 2.50
    assert results[2].new_state.cumulative_dividends_received == Decimal("1000.0000")

def test_sequencer_invalid_action_type():
    sequencer = CorporateActionSequencer()
    with pytest.raises(ValidationError):
        sequencer.process_timeline(
            buy_date=date(2020, 1, 1),
            initial_quantity=Decimal("100"),
            buy_price=Decimal("10.00"),
            actions=[{"action_date": date(2020, 1, 2), "action_type": "UNKNOWN"}]
        )
