import logging
from typing import List, Dict, Any
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database.models.corporate_actions import CorporateAction
from app.database.models.raw_corporate_actions import RawCorporateAction
from app.core.constants import ActionType, ConfidenceLevel
from app.core.exceptions import NormalizationError

logger = logging.getLogger(__name__)

def resolve_confidence_and_ratio(nse_action: RawCorporateAction, yahoo_action: RawCorporateAction) -> tuple[Decimal, Decimal, str]:
    """
    Resolve ratio and confidence between NSE and Yahoo.
    If they disagree on ratio by more than 0.01, use NSE but set confidence to LOW.
    """
    nse_ratio = nse_action.numerator / nse_action.denominator
    yahoo_ratio = yahoo_action.numerator / yahoo_action.denominator
    
    if abs(nse_ratio - yahoo_ratio) <= Decimal("0.01"):
        return nse_action.numerator, nse_action.denominator, ConfidenceLevel.HIGH.value
    else:
        logger.warning(
            f"Ratio mismatch for {nse_action.ticker} on {nse_action.action_date}: "
            f"NSE={nse_ratio}, Yahoo={yahoo_ratio}. Using NSE ratio with LOW confidence."
        )
        return nse_action.numerator, nse_action.denominator, ConfidenceLevel.LOW.value

async def normalize_corporate_actions(session: AsyncSession, ticker: str, exchange: str) -> List[CorporateAction]:
    """
    Normalize raw corporate actions from NSE and Yahoo Finance.
    Saves the normalized records to the database.
    """
    # 1. Fetch raw corporate actions
    stmt = select(RawCorporateAction).filter(
        RawCorporateAction.ticker == ticker,
        RawCorporateAction.exchange == exchange,
        RawCorporateAction.deleted_at.is_(None)
    )
    result = await session.execute(stmt)
    raw_actions = list(result.scalars().all())
    
    if not raw_actions:
        return []
    
    # 2. Group raw actions by action_date
    actions_by_date: Dict[date, List[RawCorporateAction]] = {}
    for action in raw_actions:
        actions_by_date.setdefault(action.action_date, []).append(action)
        
    normalized_actions: List[CorporateAction] = []
    
    # 3. Process each date
    for action_date, raw_list in actions_by_date.items():
        # Separate by data source
        nse_actions = [r for r in raw_list if r.data_source == "nse"]
        yahoo_actions = [r for r in raw_list if r.data_source == "yahoo_finance"]
        
        # We only care about splits, bonuses, and dividends.
        # Let's resolve BONUS vs SPLIT
        if nse_actions and yahoo_actions:
            nse_act = nse_actions[0]
            yahoo_act = yahoo_actions[0]
            
            # Map raw nse type to standard ActionType
            raw_type = nse_act.action_type_raw.upper()
            if "BONUS" in raw_type:
                resolved_type = ActionType.BONUS.value
            elif "SPLIT" in raw_type:
                resolved_type = ActionType.SPLIT.value
            elif "DIVIDEND" in raw_type:
                resolved_type = ActionType.DIVIDEND.value
            else:
                # Default to SPLIT if unclear
                resolved_type = ActionType.SPLIT.value
                
            num, den, confidence = resolve_confidence_and_ratio(nse_act, yahoo_act)
            
            normalized_actions.append(
                CorporateAction(
                    ticker=ticker,
                    exchange=exchange,
                    action_date=action_date,
                    action_type=resolved_type,
                    numerator=num,
                    denominator=den,
                    confidence=confidence,
                    data_source="nse+yahoo_finance",
                    notes=f"Resolved from NSE ({nse_act.action_type_raw}) and Yahoo Finance."
                )
            )
            
        elif nse_actions:
            # Only NSE data
            nse_act = nse_actions[0]
            raw_type = nse_act.action_type_raw.upper()
            if "BONUS" in raw_type:
                resolved_type = ActionType.BONUS.value
            elif "SPLIT" in raw_type:
                resolved_type = ActionType.SPLIT.value
            elif "DIVIDEND" in raw_type:
                resolved_type = ActionType.DIVIDEND.value
            else:
                resolved_type = ActionType.SPLIT.value
                
            normalized_actions.append(
                CorporateAction(
                    ticker=ticker,
                    exchange=exchange,
                    action_date=action_date,
                    action_type=resolved_type,
                    numerator=nse_act.numerator,
                    denominator=nse_act.denominator,
                    confidence=ConfidenceLevel.LOW.value if resolved_type == ActionType.DIVIDEND.value else ConfidenceLevel.MEDIUM.value,
                    data_source="nse",
                    notes=f"NSE only record: {nse_act.action_type_raw}"
                )
            )
            
        elif yahoo_actions:
            # Only Yahoo Finance data
            yahoo_act = yahoo_actions[0]
            raw_type = yahoo_act.action_type_raw.upper() if yahoo_act.action_type_raw else ""
            if "DIVIDEND" in raw_type:
                resolved_type = ActionType.DIVIDEND.value
                notes = "Yahoo Finance only record: DIVIDEND"
            elif "BONUS" in raw_type:
                resolved_type = ActionType.BONUS.value
                notes = "Yahoo Finance only record: BONUS"
            else:
                resolved_type = ActionType.SPLIT.value
                notes = "Yahoo Finance only record. Classified as SPLIT by default."
            
            normalized_actions.append(
                CorporateAction(
                    ticker=ticker,
                    exchange=exchange,
                    action_date=action_date,
                    action_type=resolved_type,
                    numerator=yahoo_act.numerator,
                    denominator=yahoo_act.denominator,
                    confidence=ConfidenceLevel.MEDIUM.value,
                    data_source="yahoo_finance",
                    notes=notes
                )
            )

    # 4. Save normalized actions to DB
    if normalized_actions:
        # Delete existing normalized actions for this ticker and exchange to prevent duplicate conflicts
        await session.execute(
            delete(CorporateAction).filter(
                CorporateAction.ticker == ticker,
                CorporateAction.exchange == exchange
            )
        )
        
        session.add_all(normalized_actions)
        await session.flush()
        
    return normalized_actions
