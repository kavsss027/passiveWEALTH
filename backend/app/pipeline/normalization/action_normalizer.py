import logging
import re
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

def parse_nse_purpose(purpose_str: str) -> tuple[str, Decimal, Decimal]:
    if not purpose_str or not purpose_str.strip():
        return "OTHER", Decimal("1"), Decimal("1")
        
    p_upper = purpose_str.upper()
    
    # Skip clear non-actions
    if any(x in p_upper for x in ["ANNUAL GENERAL MEETING", "AGM", "BOOK CLOSURE", "EXTRAORDINARY GENERAL MEETING", "EGM", "INTEREST PAYMENT"]):
        if not any(x in p_upper for x in ["DIVIDEND", "BONUS", "SPLIT"]):
            return "OTHER", Decimal("1"), Decimal("1")
    
    # 1. Dividend
    if any(x in p_upper for x in ["DIVIDEND", "INTERIM", "FINAL", "SPECIAL DIV"]):
        # Try to find all rupee amounts
        matches = re.findall(r"(?:RS|RE|RUPEES)[\s\.]*([\d\.]+)", p_upper)
        if matches:
            try:
                total = sum(Decimal(x) for x in matches)
                return "DIVIDEND", total, Decimal("1")
            except Exception:
                pass
        
        # Fallback to any standalone decimals
        matches = re.findall(r"\b(\d+\.\d+|\d+)\b", p_upper)
        if matches:
            try:
                vals = []
                for x in matches:
                    val = Decimal(x)
                    if val < 500: # unlikely to have > 500 Rs dividend
                        vals.append(val)
                if vals:
                    return "DIVIDEND", sum(vals), Decimal("1")
            except Exception:
                pass
                
        return "DIVIDEND", Decimal("0"), Decimal("1")
        
    # 2. Bonus
    if "BONUS" in p_upper:
        # Look for ratio X:Y
        match = re.search(r"(\d+)\s*:\s*(\d+)", p_upper)
        if match:
            return "BONUS", Decimal(match.group(1)), Decimal(match.group(2))
        match = re.search(r"(\d+)\s*TO\s*(\d+)", p_upper)
        if match:
            return "BONUS", Decimal(match.group(1)), Decimal(match.group(2))
        return "BONUS", Decimal("1"), Decimal("1")
        
    # 3. Split
    if any(x in p_upper for x in ["SPLIT", "SUB-DIVISION", "SUB DIVISION", "SUB_DIVISION"]):
        match = re.search(r"FROM\s*RS\s*(\d+)\s*TO\s*RS\s*(\d+)", p_upper)
        if match:
            old = Decimal(match.group(1))
            new = Decimal(match.group(2))
            if new > 0:
                return "SPLIT", old / new, Decimal("1")
        match = re.search(r"RS\s*(\d+)/?-\s*TO\s*RS\s*(\d+)/?-", p_upper)
        if match:
            old = Decimal(match.group(1))
            new = Decimal(match.group(2))
            if new > 0:
                return "SPLIT", old / new, Decimal("1")
        # Try custom match pattern
        match = re.search(r"FROM\s*RS\.?\s*(\d+).*?TO\s*RS\.?\s*(\d+)", p_upper)
        if match:
            old = Decimal(match.group(1))
            new = Decimal(match.group(2))
            if new > 0:
                return "SPLIT", old / new, Decimal("1")
                
        # Secondary parsing path if regex didn't match directly but we have FROM/TO and RS
        if re.search(r"FROM\s*RS\.?\s*", p_upper) and re.search(r"TO\s*RS\.?\s*", p_upper):
            nums = re.findall(r'[\d.]+', purpose_str)
            if len(nums) >= 2:
                try:
                    old = Decimal(nums[0])
                    new = Decimal(nums[1])
                    if new > 0:
                        return "SPLIT", old / new, Decimal("1")
                except Exception:
                    pass
                    
        match = re.search(r"(\d+)\s*:\s*(\d+)", p_upper)
        if match:
            return "SPLIT", Decimal(match.group(1)), Decimal(match.group(2))
        return "SPLIT", Decimal("2"), Decimal("1")
        
    return "OTHER", Decimal("1"), Decimal("1")

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
