from decimal import Decimal
from datetime import date
from app.reconstruction.quantity_tracker import QuantityTracker

def test_quantity_tracker_on_arbitrary_dates():
    tracker = QuantityTracker(date(2020, 1, 1), Decimal("100"))
    
    # Check initial buy quantity
    assert tracker.quantity_on(date(2020, 1, 1)) == Decimal("100")
    assert tracker.quantity_on(date(2020, 1, 15)) == Decimal("100")
    assert tracker.quantity_on(date(2019, 12, 31)) == Decimal("0")
    
    # Record split
    tracker.record_change(date(2020, 2, 1), Decimal("200"), "SPLIT")
    assert tracker.quantity_on(date(2020, 1, 31)) == Decimal("100")
    assert tracker.quantity_on(date(2020, 2, 1)) == Decimal("200")
    assert tracker.quantity_on(date(2020, 2, 15)) == Decimal("200")
    
    # Record bonus
    tracker.record_change(date(2020, 3, 1), Decimal("400"), "BONUS")
    assert tracker.quantity_on(date(2020, 2, 28)) == Decimal("200")
    assert tracker.quantity_on(date(2020, 3, 1)) == Decimal("400")
    assert tracker.quantity_on(date(2020, 3, 15)) == Decimal("400")
    
    # Verify all records order
    records = tracker.all_records()
    assert len(records) == 3
    assert records[0].effective_date == date(2020, 1, 1)
    assert records[1].effective_date == date(2020, 2, 1)
    assert records[2].effective_date == date(2020, 3, 1)
