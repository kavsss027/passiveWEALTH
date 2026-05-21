import os
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import logging
import re
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.corporate_actions_repo import corporate_actions_repo
from app.database.models.raw_corporate_actions import RawCorporateAction
from app.database.models.corporate_actions import CorporateAction
from app.pipeline.ingestion.nse import fetch_nse_corporate_actions
from app.pipeline.ingestion.yahoo_finance import fetch_yahoo_finance_data, get_historical_close_price

from app.pipeline.normalization.action_normalizer import normalize_corporate_actions, parse_nse_purpose
from app.reconstruction.engine import ReconstructionEngine, ReconstructionResult
from app.corporate_actions.split import StockSplitHandler
from app.corporate_actions.bonus import BonusIssueHandler
from app.corporate_actions.dividend import CashDividendHandler
from app.corporate_actions.sequencer import CorporateActionSequencer

logger = logging.getLogger(__name__)

def parse_nse_date(date_str: str) -> date:
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        pass
    raise ValueError(f"Unknown date format: {date_str}")


async def ensure_corporate_actions_ingested(session: AsyncSession, ticker: str, exchange: str) -> list[CorporateAction]:
    ticker = ticker.upper()
    exchange = exchange.upper()
    
    # 1. Check if corporate actions exist in PostgreSQL for the ticker
    actions = await corporate_actions_repo.get_by_ticker(session, ticker, exchange)
    if actions:
        return actions

    logger.info(f"No corporate actions found in DB for {ticker} on {exchange}. Triggering data pipeline ingestion...")
    raw_actions_to_add = []

    # A. Fetch from Yahoo Finance (Extremely robust for structured splits & dividends)
    try:
        yf_data = await fetch_yahoo_finance_data(ticker, date(1990, 1, 1), date.today())
        
        splits = yf_data.get("splits")
        dividends = yf_data.get("dividends")
        
        # Parse splits
        if splits is not None and not splits.empty:
            for item_date, ratio in splits.items():
                action_date = item_date.date()
                ratio_dec = Decimal(str(ratio))
                if ratio_dec >= 1:
                    num = ratio_dec
                    den = Decimal("1")
                else:
                    num = Decimal("1")
                    den = Decimal("1") / ratio_dec
                    
                raw_actions_to_add.append(RawCorporateAction(
                    ticker=ticker, exchange=exchange, action_date=action_date,
                    action_type_raw="SPLIT", numerator=num, denominator=den,
                    data_source="yahoo_finance"
                ))
                
        # Parse dividends
        if dividends is not None and not dividends.empty:
            for item_date, amount in dividends.items():
                action_date = item_date.date()
                amount_dec = Decimal(str(amount))
                if amount_dec > 0:
                    raw_actions_to_add.append(RawCorporateAction(
                        ticker=ticker, exchange=exchange, action_date=action_date,
                        action_type_raw="DIVIDEND", numerator=amount_dec, denominator=Decimal("1"),
                        data_source="yahoo_finance"
                    ))
    except Exception as e:
        logger.error(f"Failed to fetch Yahoo Finance corporate actions for {ticker}: {e}")

    # B. Fetch from NSE
    try:
        nse_data = await fetch_nse_corporate_actions(ticker)
        for action in nse_data:
            ex_date_str = action.get("exDate")
            purpose = action.get("subject", action.get("purpose", ""))
            if ex_date_str:
                try:
                    action_date = parse_nse_date(ex_date_str)
                    act_type, num, den = parse_nse_purpose(purpose)
                    if act_type == "OTHER":
                        continue
                    raw_actions_to_add.append(RawCorporateAction(
                        ticker=ticker, exchange=exchange, action_date=action_date,
                        action_type_raw=act_type, numerator=num, denominator=den,
                        data_source="nse"
                    ))
                except Exception as date_err:
                    logger.warning(f"Failed to parse NSE exDate '{ex_date_str}' or purpose '{purpose}': {date_err}")
    except Exception as e:
        logger.error(f"Failed to fetch NSE corporate actions for {ticker}: {e}")

    # 2. Save raw actions to raw table
    if raw_actions_to_add:
        await session.execute(
            delete(RawCorporateAction).filter(
                RawCorporateAction.ticker == ticker,
                RawCorporateAction.exchange == exchange
            )
        )
        session.add_all(raw_actions_to_add)
        await session.flush()
        
        # 3. Call normalization to fetch, resolve, and store them
        actions = await normalize_corporate_actions(session, ticker, exchange)
    
    # Check if this ticker has historical overrides defined
    overrides_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "core",
        "historical_overrides.json"
    )
    overrides = {}
    if os.path.exists(overrides_path):
        try:
            with open(overrides_path, "r", encoding="utf-8") as f:
                overrides = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load historical overrides: {e}")

    ticker_upper = ticker.upper()
    if ticker_upper in overrides:
        logger.info(f"Applying authoritative overrides post-normalization for {ticker_upper}")
        ticker_overrides = overrides[ticker_upper]
        
        # Delete any normalized splits/bonuses from DB for this ticker
        await session.execute(
            delete(CorporateAction).filter(
                CorporateAction.ticker == ticker_upper,
                CorporateAction.exchange == exchange,
                CorporateAction.action_type.in_(["SPLIT", "BONUS"])
            )
        )
        
        # Build override corporate actions
        override_actions = []
        for ov in ticker_overrides:
            ov_date = date.fromisoformat(ov["action_date"])
            ov_type = ov["action_type"]
            ov_num = Decimal(str(ov["numerator"]))
            ov_den = Decimal(str(ov["denominator"]))
            
            override_actions.append(
                CorporateAction(
                    ticker=ticker_upper,
                    exchange=exchange,
                    action_date=ov_date,
                    action_type=ov_type,
                    numerator=ov_num,
                    denominator=ov_den,
                    confidence="HIGH",
                    data_source="override",
                    notes=ov.get("notes", "Authoritative historical override")
                )
            )
        session.add_all(override_actions)
        await session.flush()
        
        # Re-fetch all actions
        actions = await corporate_actions_repo.get_by_ticker(session, ticker_upper, exchange)
    
    # Filter out future corporate actions
    today = date.today()
    actions = [act for act in actions if act.action_date <= today]
    
    return actions


class ReconstructionService:
    def __init__(self):
        self.engine = ReconstructionEngine(
            split_handler=StockSplitHandler(),
            bonus_handler=BonusIssueHandler(),
            dividend_handler=CashDividendHandler(),
            sequencer=CorporateActionSequencer()
        )

    async def reconstruct_portfolio(
        self,
        session: AsyncSession,
        ticker: str,
        exchange: str,
        buy_date: date,
        quantity: Optional[Decimal],
        total_amount_invested: Optional[Decimal] = None
    ) -> ReconstructionResult:
        # Ingest and retrieve corporate actions
        actions = await ensure_corporate_actions_ingested(session, ticker, exchange)
        
        actions_dict = []
        for action in actions:
            actions_dict.append({
                "action_date": action.action_date,
                "action_type": action.action_type,
                "numerator": action.numerator,
                "denominator": action.denominator
            })

        derived_quantity = quantity
        if quantity is not None and total_amount_invested is not None:
            buy_price = total_amount_invested / quantity
        elif quantity is not None:
            try:
                buy_price = await get_historical_close_price(ticker, exchange, buy_date)
            except Exception:
                buy_price = Decimal("100.00") # absolute fallback
        else:
            # Only total_amount_invested is provided
            try:
                price = await get_historical_close_price(ticker, exchange, buy_date)
            except Exception:
                price = Decimal("100.00") # absolute fallback
            import math
            derived_quantity = Decimal(str(math.floor(total_amount_invested / price)))
            if derived_quantity <= 0:
                derived_quantity = Decimal("1")
            buy_price = total_amount_invested / derived_quantity

        result = await self.engine.reconstruct(
            ticker=ticker,
            exchange=exchange,
            buy_date=buy_date,
            quantity=derived_quantity,
            buy_price_per_share=buy_price,
            corporate_actions=actions_dict
        )
        return result

