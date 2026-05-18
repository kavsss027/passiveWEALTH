# RECONSTRUCTION_ENGINE.md
# Reconstruction Engine — State Machine Design and Implementation Guide

---

## What the Reconstruction Engine Does

The reconstruction engine takes an initial portfolio state and a sorted list of corporate actions, then walks through each event in order, applying it to produce the next state. The result is a complete history of how the portfolio evolved from buy date to today.

---

## The State Machine Model

```
Initial State
     │
     ▼
Apply Event 1 → State 1
     │
     ▼
Apply Event 2 → State 2
     │
     ▼
    ...
     │
     ▼
Apply Event N → Final State
```

Each state transition is deterministic. The same initial state and the same ordered list of events always produce the same final state. This is not a simulation — it is a mathematical replay.

---

## Module Responsibilities

### `quantity_tracker.py`

Maintains the authoritative share quantity at every point in time. This is the most critical piece of state in the entire engine.

```python
from decimal import Decimal
from datetime import date
from dataclasses import dataclass, field

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
```

**Why quantity_tracker.py must be built before dividend.py:**
Dividend calculation requires knowing the exact quantity on the ex-dividend date. Without a quantity tracker that can answer "how many shares did the investor hold on date X", dividend calculations will use the wrong quantity.

---

### `state_machine.py`

The state machine holds and transitions the portfolio state. It is stateful during a single reconstruction run but does not persist anything.

```python
from decimal import Decimal
from datetime import date

class PortfolioStateMachine:
    def __init__(
        self,
        buy_date: date,
        quantity: Decimal,
        buy_price_per_share: Decimal
    ):
        self.current_state = PortfolioState(
            date=buy_date,
            quantity=quantity,
            cost_basis_per_share=buy_price_per_share,
            total_invested=quantity * buy_price_per_share,
            cumulative_dividends_received=Decimal("0")
        )
        self.state_history: list[PortfolioState] = [self.current_state]
        self.event_log: list[ActionResult] = []

    def apply(self, handler: CorporateActionHandler, action: dict) -> ActionResult:
        if not handler.is_eligible(self.current_state.date, action["action_date"]):
            return None  # Skip ineligible actions silently

        result = handler.apply(self.current_state, action)
        self.current_state = result.new_state
        self.state_history.append(result.new_state)
        self.event_log.append(result)
        return result

    def final_state(self) -> PortfolioState:
        return self.current_state

    def full_event_log(self) -> list[ActionResult]:
        return self.event_log
```

---

### `engine.py`

The engine orchestrates the entire reconstruction. It is the only component in this module that external code (services) should call.

```python
class ReconstructionEngine:
    def __init__(
        self,
        split_handler: SplitHandler,
        bonus_handler: BonusHandler,
        dividend_handler: DividendHandler,
        sequencer: CorporateActionSequencer
    ):
        self._handlers = {
            "SPLIT": split_handler,
            "BONUS": bonus_handler,
            "DIVIDEND": dividend_handler
        }
        self._sequencer = sequencer

    async def reconstruct(
        self,
        ticker: str,
        exchange: str,
        buy_date: date,
        quantity: Decimal,
        buy_price_per_share: Decimal,
        corporate_actions: list[dict]
    ) -> ReconstructionResult:

        # Sort all actions chronologically with same-date priority rules
        sorted_actions = self._sequencer.sort_and_filter(
            actions=corporate_actions,
            buy_date=buy_date
        )

        # Initialise the state machine
        machine = PortfolioStateMachine(
            buy_date=buy_date,
            quantity=quantity,
            buy_price_per_share=buy_price_per_share
        )

        # Walk through every event in order
        for action in sorted_actions:
            action_type = action["action_type"]
            handler = self._handlers.get(action_type)

            if handler is None:
                # Unknown action type — log and skip
                log.warning("unknown_action_type",
                    ticker=ticker,
                    action_type=action_type,
                    action_date=str(action["action_date"]))
                continue

            machine.apply(handler, action)

        return ReconstructionResult(
            final_state=machine.final_state(),
            event_log=machine.full_event_log()
        )
```

---

## What the Engine Does Not Do

The reconstruction engine handles state transitions only. It does not:

- Fetch data from any external source
- Query the database
- Calculate unrealized gains (that is the wealth engine's job)
- Format output for the API response (that is the explainability layer's job)
- Handle HTTP concerns of any kind

Keeping the engine pure means it can be tested completely independently of databases and APIs using only plain Python objects.

---

## Testing the Reconstruction Engine

Every test for the reconstruction engine must use a fixed, known sequence of events and verify the exact output state.

**Template for a reconstruction test:**

```python
import pytest
from decimal import Decimal
from datetime import date

def test_split_doubles_quantity():
    engine = build_test_engine()

    result = engine.reconstruct(
        ticker="TEST",
        exchange="NSE",
        buy_date=date(2000, 1, 1),
        quantity=Decimal("100"),
        buy_price_per_share=Decimal("500"),
        corporate_actions=[
            {
                "action_date": date(2004, 6, 1),
                "action_type": "SPLIT",
                "numerator": Decimal("2"),
                "denominator": Decimal("1")
            }
        ]
    )

    assert result.final_state.quantity == Decimal("200")
    assert result.final_state.total_invested == Decimal("50000")
    assert result.final_state.cost_basis_per_share == Decimal("250")
    assert len(result.event_log) == 1
    assert result.event_log[0].event_type == "SPLIT"
    assert result.event_log[0].financial_impact == Decimal("0")
    assert result.event_log[0].impact_type == "STRUCTURAL"
```

Use real historical events from real Indian stocks as the primary test cases. INFY, TCS, and Wipro have well-documented split and bonus histories that are easy to verify against public records.
