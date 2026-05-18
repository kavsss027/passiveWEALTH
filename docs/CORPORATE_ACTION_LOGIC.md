# CORPORATE_ACTION_LOGIC.md
# Corporate Action Logic — Exact Mathematical Rules and Edge Cases

---

## This Document Is the Source of Truth for Financial Calculation Logic

Any ambiguity between this document and code means the code is wrong. Fix the code.

---

## Abstract Base — All Action Handlers Must Implement

Every corporate action handler must implement this interface:

```python
from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import date
from dataclasses import dataclass

@dataclass
class PortfolioState:
    date: date
    quantity: Decimal
    cost_basis_per_share: Decimal
    total_invested: Decimal
    cumulative_dividends_received: Decimal

@dataclass
class ActionResult:
    new_state: PortfolioState
    event_type: str
    description: str
    financial_impact: Decimal
    impact_type: str   # STRUCTURAL, REALIZED, UNREALIZED

class CorporateActionHandler(ABC):
    @abstractmethod
    def apply(self, state: PortfolioState, action: dict) -> ActionResult:
        pass

    @abstractmethod
    def is_eligible(self, buy_date: date, action_date: date) -> bool:
        pass
```

---

## Handler 1 — Stock Split

### Eligibility Rule

The investor must have held shares before the split ex-date. Eligibility check:

```python
def is_eligible(self, buy_date: date, action_date: date) -> bool:
    return buy_date < action_date
```

Strictly less than. If buy_date equals action_date, not eligible.

### Calculation

```python
def apply(self, state: PortfolioState, action: dict) -> ActionResult:
    numerator = Decimal(str(action["numerator"]))
    denominator = Decimal(str(action["denominator"]))

    split_ratio = numerator / denominator

    new_quantity = state.quantity * split_ratio

    # Total invested never changes for structural events
    new_cost_basis = state.total_invested / new_quantity

    new_state = PortfolioState(
        date=action["action_date"],
        quantity=new_quantity,
        cost_basis_per_share=new_cost_basis,
        total_invested=state.total_invested,
        cumulative_dividends_received=state.cumulative_dividends_received
    )

    description = (
        f"Stock split {int(numerator)}:{int(denominator)}. "
        f"Holdings changed from {state.quantity} to {new_quantity} shares. "
        f"Cost basis adjusted from ₹{state.cost_basis_per_share} to ₹{new_cost_basis} per share."
    )

    return ActionResult(
        new_state=new_state,
        event_type="SPLIT",
        description=description,
        financial_impact=Decimal("0"),
        impact_type="STRUCTURAL"
    )
```

### Validation Rules

- numerator must be greater than denominator for a split (e.g., 2:1, 5:1, 10:1)
- If numerator equals denominator — invalid, log error, skip action
- If numerator is less than denominator — this is a reverse split, log warning, process normally

---

## Handler 2 — Bonus Issue

### Eligibility Rule

Same as split — investor must hold shares before bonus ex-date:

```python
def is_eligible(self, buy_date: date, action_date: date) -> bool:
    return buy_date < action_date
```

### Calculation

```python
def apply(self, state: PortfolioState, action: dict) -> ActionResult:
    numerator = Decimal(str(action["numerator"]))
    denominator = Decimal(str(action["denominator"]))

    # Bonus ratio: numerator shares issued FOR EVERY denominator shares held
    # 1:1 bonus means 1 new share for every 1 existing share → quantity doubles
    # 1:2 bonus means 1 new share for every 2 existing shares → quantity * 1.5
    additional_shares = state.quantity * (numerator / denominator)
    new_quantity = state.quantity + additional_shares

    # Total invested does not change — bonus shares are free
    new_cost_basis = state.total_invested / new_quantity

    new_state = PortfolioState(
        date=action["action_date"],
        quantity=new_quantity,
        cost_basis_per_share=new_cost_basis,
        total_invested=state.total_invested,
        cumulative_dividends_received=state.cumulative_dividends_received
    )

    description = (
        f"Bonus issue {int(numerator)}:{int(denominator)}. "
        f"{additional_shares} additional shares issued. "
        f"Holdings increased from {state.quantity} to {new_quantity} shares."
    )

    return ActionResult(
        new_state=new_state,
        event_type="BONUS",
        description=description,
        financial_impact=Decimal("0"),
        impact_type="STRUCTURAL"
    )
```

### Critical Distinction From Split

In a bonus ratio, the interpretation is:
- numerator = shares RECEIVED per denominator shares held
- A 1:1 bonus → receive 1 share for every 1 held → quantity doubles → `additional = quantity * (1/1)`
- A 1:2 bonus → receive 1 share for every 2 held → `additional = quantity * (1/2)`

In a split ratio:
- numerator = shares you end up with per 1 original share
- A 2:1 split → 2 shares from every 1 → `new_quantity = quantity * (2/1)`

The formulas look similar but the semantic interpretation of the ratio is different. Verify NSE source data to confirm which ratio format they use before implementing.

---

## Handler 3 — Cash Dividend

### Eligibility Rule

```python
def is_eligible(self, buy_date: date, ex_date: date) -> bool:
    return buy_date < ex_date
```

Strictly less than. Buying on the ex-date does NOT qualify for the dividend.

### Calculation

```python
def apply(self, state: PortfolioState, action: dict) -> ActionResult:
    dividend_per_share = Decimal(str(action["numerator"]))

    # Use quantity AT the ex-date — this is already correctly tracked
    # because the sequencer processes splits and bonuses before dividends
    # when they share the same date
    dividend_received = state.quantity * dividend_per_share
    dividend_received = dividend_received.quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )

    new_cumulative = state.cumulative_dividends_received + dividend_received

    new_state = PortfolioState(
        date=action["action_date"],
        quantity=state.quantity,                         # quantity unchanged by dividend
        cost_basis_per_share=state.cost_basis_per_share, # cost basis unchanged by dividend
        total_invested=state.total_invested,              # total invested unchanged
        cumulative_dividends_received=new_cumulative
    )

    description = (
        f"Dividend of ₹{dividend_per_share} per share received on "
        f"{state.quantity} shares. ₹{dividend_received} credited."
    )

    return ActionResult(
        new_state=new_state,
        event_type="DIVIDEND",
        description=description,
        financial_impact=dividend_received,
        impact_type="REALIZED"
    )
```

---

## The Sequencer — Chronological Event Processing

The sequencer is the component that fetches all applicable corporate actions, sorts them, and feeds them to the reconstruction engine in order.

### Sorting Rule

```python
def sort_actions(actions: list[dict]) -> list[dict]:
    def sort_key(action):
        # Primary sort: date ascending
        # Secondary sort: action type priority for same-date conflicts
        type_priority = {"SPLIT": 0, "BONUS": 1, "DIVIDEND": 2}
        return (action["action_date"], type_priority.get(action["action_type"], 99))

    return sorted(actions, key=sort_key)
```

**Same-date priority rule:** On dates where multiple actions occur, process in this order: SPLIT first, then BONUS, then DIVIDEND.

Rationale: If a split and dividend occur on the same date, the split should be applied first so the dividend calculation uses the post-split quantity. This matches the financial reality of how exchange mechanisms work.

### Filtering Rule

Only process actions where:
```python
action["action_date"] > buy_date
```

Actions that occurred before the buy date are irrelevant to this investor's holdings. Strictly greater than — an action on exactly the buy date is not applied because the investor did not hold shares before that event occurred.

---

## Edge Cases and Their Resolutions

**Edge case 1: Two splits on the same date**
This should not happen but if it appears in data, it indicates a data quality issue. Log a warning, skip the duplicate, flag as LOW confidence.

**Edge case 2: Dividend ex-date equals buy date**
Investor is not eligible. The is_eligible check returns False. Skip the dividend. Do not add to cumulative dividends.

**Edge case 3: Fractional shares from ratio arithmetic**
Keep full Decimal precision throughout all intermediate calculations. Round to 4 decimal places only at the point of persisting to database. Display to user as integer (floor) with a note if fractional.

**Edge case 4: Zero quantity at any point**
If quantity reaches zero through any calculation, raise a QuantityCalculationError. This indicates a data error or logic error. Do not continue the chain.

**Edge case 5: Corporate action data shows ratio of 0**
Reject the action. Log an error with full action details. Skip it in the timeline. Add a warning to the API response.
