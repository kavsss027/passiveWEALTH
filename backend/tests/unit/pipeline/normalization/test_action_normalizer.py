import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.raw_corporate_actions import RawCorporateAction
from app.database.models.corporate_actions import CorporateAction
from app.pipeline.normalization.action_normalizer import normalize_corporate_actions
from app.core.constants import ActionType, ConfidenceLevel

@pytest.mark.asyncio
async def test_action_normalizer_agreement(db_session: AsyncSession):
    # Both sources agree on split ratio and date
    db_session.add(RawCorporateAction(
        ticker="INFY",
        exchange="NSE",
        action_date=date(2020, 1, 1),
        action_type_raw="SPLIT",
        numerator=Decimal("2"),
        denominator=Decimal("1"),
        data_source="nse"
    ))
    db_session.add(RawCorporateAction(
        ticker="INFY",
        exchange="NSE",
        action_date=date(2020, 1, 1),
        action_type_raw="SPLIT",
        numerator=Decimal("2"),
        denominator=Decimal("1"),
        data_source="yahoo_finance"
    ))
    await db_session.flush()
    
    normalized = await normalize_corporate_actions(db_session, "INFY", "NSE")
    assert len(normalized) == 1
    assert normalized[0].action_type == ActionType.SPLIT.value
    assert normalized[0].numerator == Decimal("2")
    assert normalized[0].denominator == Decimal("1")
    assert normalized[0].confidence == ConfidenceLevel.HIGH.value

@pytest.mark.asyncio
async def test_action_normalizer_bonus_vs_split_nse_wins(db_session: AsyncSession):
    # Yahoo says SPLIT, NSE says BONUS. NSE wins!
    db_session.add(RawCorporateAction(
        ticker="INFY",
        exchange="NSE",
        action_date=date(2020, 6, 1),
        action_type_raw="BONUS",
        numerator=Decimal("1"),
        denominator=Decimal("1"),
        data_source="nse"
    ))
    db_session.add(RawCorporateAction(
        ticker="INFY",
        exchange="NSE",
        action_date=date(2020, 6, 1),
        action_type_raw="SPLIT",
        numerator=Decimal("1"),
        denominator=Decimal("1"),
        data_source="yahoo_finance"
    ))
    await db_session.flush()
    
    normalized = await normalize_corporate_actions(db_session, "INFY", "NSE")
    assert len(normalized) == 1
    assert normalized[0].action_type == ActionType.BONUS.value
    assert normalized[0].confidence == ConfidenceLevel.HIGH.value

@pytest.mark.asyncio
async def test_action_normalizer_ratio_disagreement(db_session: AsyncSession):
    # Disagreement on ratio: NSE says 2:1, Yahoo says 3:1. NSE wins but confidence is LOW.
    db_session.add(RawCorporateAction(
        ticker="INFY",
        exchange="NSE",
        action_date=date(2020, 12, 1),
        action_type_raw="SPLIT",
        numerator=Decimal("2"),
        denominator=Decimal("1"),
        data_source="nse"
    ))
    db_session.add(RawCorporateAction(
        ticker="INFY",
        exchange="NSE",
        action_date=date(2020, 12, 1),
        action_type_raw="SPLIT",
        numerator=Decimal("3"),
        denominator=Decimal("1"),
        data_source="yahoo_finance"
    ))
    await db_session.flush()
    
    normalized = await normalize_corporate_actions(db_session, "INFY", "NSE")
    target = [n for n in normalized if n.action_date == date(2020, 12, 1)][0]
    assert target.action_type == ActionType.SPLIT.value
    assert target.numerator == Decimal("2")
    assert target.confidence == ConfidenceLevel.LOW.value

@pytest.mark.asyncio
async def test_action_normalizer_nse_only(db_session: AsyncSession):
    # NSE only data for different raw types: BONUS, SPLIT, DIVIDEND, unknown
    db_session.add(RawCorporateAction(
        ticker="INFY",
        exchange="NSE",
        action_date=date(2021, 1, 1),
        action_type_raw="BONUS issue",
        numerator=Decimal("1"),
        denominator=Decimal("1"),
        data_source="nse"
    ))
    db_session.add(RawCorporateAction(
        ticker="INFY",
        exchange="NSE",
        action_date=date(2021, 2, 1),
        action_type_raw="SPLIT to 5",
        numerator=Decimal("2"),
        denominator=Decimal("1"),
        data_source="nse"
    ))
    db_session.add(RawCorporateAction(
        ticker="INFY",
        exchange="NSE",
        action_date=date(2021, 3, 1),
        action_type_raw="DIVIDEND rs 5",
        numerator=Decimal("5"),
        denominator=Decimal("1"),
        data_source="nse"
    ))
    db_session.add(RawCorporateAction(
        ticker="INFY",
        exchange="NSE",
        action_date=date(2021, 4, 1),
        action_type_raw="SOME_UNKNOWN_ACTION",
        numerator=Decimal("1"),
        denominator=Decimal("1"),
        data_source="nse"
    ))
    await db_session.flush()
    
    normalized = await normalize_corporate_actions(db_session, "INFY", "NSE")
    
    bonus_act = [n for n in normalized if n.action_date == date(2021, 1, 1)][0]
    assert bonus_act.action_type == ActionType.BONUS.value
    assert bonus_act.confidence == ConfidenceLevel.MEDIUM.value
    
    split_act = [n for n in normalized if n.action_date == date(2021, 2, 1)][0]
    assert split_act.action_type == ActionType.SPLIT.value
    assert split_act.confidence == ConfidenceLevel.MEDIUM.value
    
    div_act = [n for n in normalized if n.action_date == date(2021, 3, 1)][0]
    assert div_act.action_type == ActionType.DIVIDEND.value
    assert div_act.confidence == ConfidenceLevel.LOW.value # Dividend gets LOW when only NSE has it
    
    unknown_act = [n for n in normalized if n.action_date == date(2021, 4, 1)][0]
    assert unknown_act.action_type == ActionType.SPLIT.value # default fallback

@pytest.mark.asyncio
async def test_action_normalizer_yahoo_only(db_session: AsyncSession):
    # Yahoo Finance only data (always splits)
    db_session.add(RawCorporateAction(
        ticker="INFY",
        exchange="NSE",
        action_date=date(2022, 1, 1),
        action_type_raw="SPLIT",
        numerator=Decimal("2"),
        denominator=Decimal("1"),
        data_source="yahoo_finance"
    ))
    await db_session.flush()
    
    normalized = await normalize_corporate_actions(db_session, "INFY", "NSE")
    yahoo_act = [n for n in normalized if n.action_date == date(2022, 1, 1)][0]
    assert yahoo_act.action_type == ActionType.SPLIT.value
    assert yahoo_act.confidence == ConfidenceLevel.MEDIUM.value

@pytest.mark.asyncio
async def test_action_normalizer_empty_and_disagreement_mapping(db_session: AsyncSession):
    # NSE and Yahoo agree on dividend, mapping check
    db_session.add(RawCorporateAction(
        ticker="INFY",
        exchange="NSE",
        action_date=date(2023, 1, 1),
        action_type_raw="DIVIDEND",
        numerator=Decimal("10"),
        denominator=Decimal("1"),
        data_source="nse"
    ))
    db_session.add(RawCorporateAction(
        ticker="INFY",
        exchange="NSE",
        action_date=date(2023, 1, 1),
        action_type_raw="DIVIDEND",
        numerator=Decimal("10"),
        denominator=Decimal("1"),
        data_source="yahoo_finance"
    ))
    await db_session.flush()
    
    normalized = await normalize_corporate_actions(db_session, "INFY", "NSE")
    div_act = [n for n in normalized if n.action_date == date(2023, 1, 1)][0]
    assert div_act.action_type == ActionType.DIVIDEND.value
    assert div_act.confidence == ConfidenceLevel.HIGH.value
