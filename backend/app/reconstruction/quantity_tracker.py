from decimal import Decimal
from datetime import date
from dataclasses import dataclass

@dataclass
class QuantityRecord:
    effective_date: date
    quantity: Decimal
    reason: str  # "INITIAL_BUY", "SPLIT", "BONUS"

class QuantityTracker:
    def __init__(self, buy_date: date, initial_quantity: Decimal):
        self._records: list[QuantityRecord] = [
            QuantityRecord(
                effective_date=buy_date,
                quantity=initial_quantity,
                reason="INITIAL_BUY"
            )
        ]

    def record_change(self, effective_date: date, new_quantity: Decimal, reason: str):
        self._records.append(QuantityRecord(
            effective_date=effective_date,
            quantity=new_quantity,
            reason=reason
        ))

    def quantity_on(self, target_date: date) -> Decimal:
        """
        Returns the quantity held on a specific date.
        Finds the most recent record with effective_date <= target_date.
        """
        eligible = [r for r in self._records if r.effective_date <= target_date]
        if not eligible:
            return Decimal("0")
        return max(eligible, key=lambda r: r.effective_date).quantity

    def all_records(self) -> list[QuantityRecord]:
        return sorted(self._records, key=lambda r: r.effective_date)
