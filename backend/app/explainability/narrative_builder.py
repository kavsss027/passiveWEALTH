from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any
from app.corporate_actions.base import ActionResult
from app.explainability.event_formatter import format_buy_event

def build_timeline(
    buy_event: Dict[str, Any],
    action_results: List[ActionResult]
) -> List[Dict[str, Any]]:
    """
    Assembles the timeline list starting from the BUY event.
    """
    timeline = []

    # Always add buy event first
    total_invested_q = Decimal(str(buy_event["total_invested"])).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    timeline.append({
        "event_date": str(buy_event["date"]),
        "event_type": "BUY",
        "description": format_buy_event(
            quantity=Decimal(str(buy_event["quantity"])),
            ticker=buy_event["ticker"],
            price=Decimal(str(buy_event["price"])),
            total=Decimal(str(buy_event["total_invested"]))
        ),
        "quantity_before": 0,
        "quantity_after": int(buy_event["quantity"]),
        "financial_impact": str(total_invested_q),
        "impact_type": "INVESTED",
        "cumulative_dividends": "0.0000"
    })

    # Add each corporate action event in order
    cumulative_dividends = Decimal("0")
    prev_quantity = buy_event["quantity"]

    for result in action_results:
        # Validate critical rules
        if result.event_type == "DIVIDEND" and result.impact_type == "STRUCTURAL":
            raise ValueError("Dividend cannot be labeled STRUCTURAL")
        if result.event_type in ("SPLIT", "BONUS") and result.impact_type in ("REALIZED", "UNREALIZED"):
            raise ValueError(f"{result.event_type} cannot be labeled REALIZED or UNREALIZED")

        if result.event_type == "DIVIDEND":
            cumulative_dividends += result.financial_impact

        financial_impact_q = Decimal(str(result.financial_impact)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        cumulative_dividends_q = Decimal(str(cumulative_dividends)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        timeline.append({
            "event_date": str(result.new_state.date),
            "event_type": result.event_type,
            "description": result.description,
            "quantity_before": int(prev_quantity),
            "quantity_after": int(result.new_state.quantity),
            "financial_impact": str(financial_impact_q),
            "impact_type": result.impact_type,
            "cumulative_dividends": str(cumulative_dividends_q)
        })

        prev_quantity = result.new_state.quantity

    return timeline
