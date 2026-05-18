# EXPLAINABILITY_RULES.md
# Explainability Rules — Narrative Templates and Labeling Standards

---

## Purpose

The explainability layer converts raw calculation results into human-readable event descriptions. Every rupee in the final output must be traceable to a specific event with a clear explanation of what happened.

This is not a formatting concern. The specific language used has financial implications. Use the exact templates defined here.

---

## Core Labeling Rules

### impact_type Values and When to Use Them

| impact_type | When to use | Example |
|---|---|---|
| INVESTED | The original buy event | User invested ₹50,000 |
| STRUCTURAL | Split or bonus — no cash impact | Holdings doubled after split |
| REALIZED | Dividend received — cash in hand | ₹1,500 dividend credited |
| UNREALIZED | Market appreciation — conditional | Current paper gain at market price |

**Never classify a split or bonus as REALIZED or UNREALIZED.**
**Never classify a dividend as STRUCTURAL.**
These are not style guidelines — they are financial accuracy requirements.

---

## Event Description Templates

### BUY Event

```python
def format_buy_event(quantity: Decimal, ticker: str, price: Decimal, total: Decimal) -> str:
    return (
        f"Purchased {int(quantity)} shares of {ticker} "
        f"at ₹{price} per share. "
        f"Total invested: ₹{total}."
    )
```

Example output:
```
Purchased 100 shares of INFY at ₹500.00 per share. Total invested: ₹50,000.00.
```

---

### SPLIT Event

```python
def format_split_event(
    numerator: int,
    denominator: int,
    quantity_before: Decimal,
    quantity_after: Decimal,
    cost_before: Decimal,
    cost_after: Decimal
) -> str:
    return (
        f"Stock split {numerator}:{denominator}. "
        f"Holdings changed from {int(quantity_before)} to {int(quantity_after)} shares. "
        f"Cost basis adjusted from ₹{cost_before} to ₹{cost_after} per share."
    )
```

Example output:
```
Stock split 2:1. Holdings changed from 100 to 200 shares. Cost basis adjusted from ₹500.00 to ₹250.00 per share.
```

---

### BONUS Event

```python
def format_bonus_event(
    numerator: int,
    denominator: int,
    additional_shares: Decimal,
    quantity_before: Decimal,
    quantity_after: Decimal
) -> str:
    return (
        f"Bonus issue {numerator}:{denominator}. "
        f"{int(additional_shares)} additional shares issued. "
        f"Holdings increased from {int(quantity_before)} to {int(quantity_after)} shares."
    )
```

Example output:
```
Bonus issue 1:1. 200 additional shares issued. Holdings increased from 200 to 400 shares.
```

---

### DIVIDEND Event

```python
def format_dividend_event(
    dividend_per_share: Decimal,
    quantity: Decimal,
    dividend_received: Decimal
) -> str:
    return (
        f"Dividend of ₹{dividend_per_share} per share received on "
        f"{int(quantity)} shares. "
        f"₹{dividend_received} credited."
    )
```

Example output:
```
Dividend of ₹7.50 per share received on 200 shares. ₹1,500.00 credited.
```

---

## Wealth Summary Labels — Mandatory Language

### Unrealized Gain Label

**This exact string must be used. No variation.**

```python
UNREALIZED_GAIN_LABEL = "if sold at current market price"
```

The API response field `unrealized_gain_label` must always contain this exact string. Never use:
- "current profit"
- "market gain"
- "paper profit"
- "potential gain"
- "estimated return"

The reason is financial accuracy. Unrealized gains are conditional. The specific phrasing "if sold at current market price" makes the conditionality explicit and unambiguous.

---

### Total Wealth Label

When combining realized dividends and unrealized appreciation:

```python
def format_wealth_summary(
    total_dividends: Decimal,
    unrealized_gain: Decimal,
    current_market_value: Decimal
) -> dict:
    return {
        "total_dividends_received": str(total_dividends),
        "unrealized_gain": str(unrealized_gain),
        "unrealized_gain_label": "if sold at current market price",
        "total_wealth_if_sold": str(total_dividends + current_market_value),
        "total_wealth_label": "total wealth if all shares sold today including dividends received"
    }
```

---

## Narrative Builder — Assembling the Full Timeline

The narrative builder takes all ActionResult objects from the reconstruction engine and assembles them into the timeline array that the API returns.

Rules:
1. The first entry in the timeline is always the BUY event
2. Events are sorted chronologically ascending
3. Each entry includes cumulative_dividends at that point in time
4. quantity_before for the first entry is 0
5. quantity_before for all subsequent entries equals quantity_after of the previous entry

```python
def build_timeline(
    buy_event: dict,
    action_results: list[ActionResult]
) -> list[dict]:
    timeline = []

    # Always add buy event first
    timeline.append({
        "event_date": str(buy_event["date"]),
        "event_type": "BUY",
        "description": format_buy_event(...),
        "quantity_before": 0,
        "quantity_after": int(buy_event["quantity"]),
        "financial_impact": str(buy_event["total_invested"]),
        "impact_type": "INVESTED",
        "cumulative_dividends": "0.0000"
    })

    # Add each corporate action event in order
    cumulative_dividends = Decimal("0")
    prev_quantity = buy_event["quantity"]

    for result in action_results:
        if result.event_type == "DIVIDEND":
            cumulative_dividends += result.financial_impact

        timeline.append({
            "event_date": str(result.new_state.date),
            "event_type": result.event_type,
            "description": result.description,
            "quantity_before": int(prev_quantity),
            "quantity_after": int(result.new_state.quantity),
            "financial_impact": str(result.financial_impact),
            "impact_type": result.impact_type,
            "cumulative_dividends": str(cumulative_dividends)
        })

        prev_quantity = result.new_state.quantity

    return timeline
```

---

## What the Explainability Layer Must Never Do

- Never present unrealized gains without the "if sold at current market price" qualifier
- Never add realized and unrealized together without clearly labeling the total as conditional
- Never round Decimal values before passing them to the formatter — format as strings, let the client handle display rounding
- Never suppress events from the timeline for cosmetic reasons — every corporate action must appear
