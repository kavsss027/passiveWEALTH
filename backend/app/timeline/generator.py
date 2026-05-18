from decimal import Decimal
from datetime import date
from typing import List, Dict, Any
from app.corporate_actions.base import ActionResult, PortfolioState
from app.wealth_engine.realized import calculate_realized_dividends
from app.wealth_engine.unrealized import calculate_unrealized_gain
from app.wealth_engine.aggregator import aggregate_wealth_summary
from app.explainability.narrative_builder import build_timeline

class TimelineGenerator:
    def generate(
        self,
        ticker: str,
        exchange: str,
        buy_date: date,
        original_quantity: Decimal,
        buy_price: Decimal,
        current_price: Decimal,
        action_results: List[ActionResult],
        warnings: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generates the raw dictionary response data, combining:
        - Reconstruction states
        - Wealth calculations
        - Timeline narrative building
        """
        if action_results:
            final_portfolio_state = action_results[-1].new_state
        else:
            final_portfolio_state = PortfolioState(
                date=buy_date,
                quantity=original_quantity,
                cost_basis_per_share=buy_price,
                total_invested=original_quantity * buy_price,
                cumulative_dividends_received=Decimal("0.0000")
            )

        # 1. Realized Dividends
        total_dividends = calculate_realized_dividends(action_results)

        # 2. Unrealized Gains
        unrealized_gain = calculate_unrealized_gain(
            current_price=current_price,
            adjusted_cost_basis=final_portfolio_state.cost_basis_per_share,
            current_quantity=final_portfolio_state.quantity
        )

        # 3. Wealth Summary
        wealth_summary = aggregate_wealth_summary(
            total_dividends=total_dividends,
            unrealized_gain=unrealized_gain,
            current_quantity=final_portfolio_state.quantity,
            current_price=current_price
        )

        # Calculate wealth multiple
        original_investment = original_quantity * buy_price
        total_wealth_if_sold = Decimal(wealth_summary["total_wealth_if_sold"])
        if original_investment > 0:
            wealth_multiple = total_wealth_if_sold / original_investment
        else:
            wealth_multiple = Decimal("0.0000")
        
        wealth_summary["wealth_multiple"] = f"{wealth_multiple:.2f}x"

        # 4. Timeline
        buy_event = {
            "date": buy_date,
            "ticker": ticker,
            "quantity": original_quantity,
            "price": buy_price,
            "total_invested": original_investment
        }
        timeline = build_timeline(buy_event, action_results)

        # 5. Current State
        current_state = {
            "quantity": int(final_portfolio_state.quantity),
            "current_price_per_share": str(current_price),
            "current_market_value": str(final_portfolio_state.quantity * current_price),
            "adjusted_cost_basis_per_share": str(final_portfolio_state.cost_basis_per_share),
            "total_invested": str(final_portfolio_state.total_invested)
        }

        # 6. Data Quality
        data_quality = {
            "confidence": "HIGH",
            "sources_used": ["NSE", "YahooFinance"],
            "warnings": warnings or []
        }

        return {
            "ticker": ticker,
            "exchange": exchange,
            "buy_date": buy_date,
            "original_quantity": int(original_quantity),
            "original_investment": str(original_investment),
            "current_state": current_state,
            "wealth_summary": wealth_summary,
            "timeline": timeline,
            "data_quality": data_quality
        }

