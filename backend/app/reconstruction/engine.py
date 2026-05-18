from decimal import Decimal
from datetime import date
from dataclasses import dataclass
from typing import List, Dict, Any
import logging
from app.corporate_actions.base import PortfolioState, ActionResult
from app.corporate_actions.sequencer import CorporateActionSequencer
from app.reconstruction.state_machine import PortfolioStateMachine

logger = logging.getLogger(__name__)

@dataclass
class ReconstructionResult:
    final_state: PortfolioState
    event_log: List[ActionResult]

class ReconstructionEngine:
    def __init__(
        self,
        split_handler,
        bonus_handler,
        dividend_handler,
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
        corporate_actions: List[Dict[str, Any]]
    ) -> ReconstructionResult:
        # Sort all actions chronologically with same-date priority rules
        sorted_actions = self._sequencer.sort_and_filter(
            actions=corporate_actions,
            buy_date=buy_date
        )

        # Initialize the state machine
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
                logger.warning(
                    f"Unknown action type {action_type} for {ticker} on {action['action_date']}"
                )
                continue

            machine.apply(handler, action)

        return ReconstructionResult(
            final_state=machine.final_state(),
            event_log=machine.full_event_log()
        )
