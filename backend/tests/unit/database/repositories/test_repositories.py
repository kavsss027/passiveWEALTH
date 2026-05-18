import pytest
from datetime import date
from decimal import Decimal
from app.database.repositories.market_data_repo import market_data_repo
from app.database.repositories.corporate_actions_repo import corporate_actions_repo, raw_corporate_actions_repo
from app.database.repositories.raw_dividends_repo import raw_dividends_repo

@pytest.mark.asyncio
async def test_market_data_repo_crud(db_session):
    obj = await market_data_repo.create(db_session, {
        "ticker": "INFY",
        "exchange": "NSE",
        "trade_date": date(2020, 1, 1),
        "open_price": Decimal("100.00"),
        "high_price": Decimal("110.00"),
        "low_price": Decimal("90.00"),
        "close_price": Decimal("105.00"),
        "volume": 1000,
        "data_source": "test"
    })
    
    assert obj.id is not None
    
    records = await market_data_repo.get_by_ticker_and_date_range(
        db_session, "INFY", "NSE", date(2020, 1, 1), date(2020, 1, 1)
    )
    assert len(records) == 1
    assert records[0].close_price == Decimal("105.00")

@pytest.mark.asyncio
async def test_corporate_actions_repo_crud(db_session):
    obj = await corporate_actions_repo.create(db_session, {
        "ticker": "INFY",
        "exchange": "NSE",
        "action_date": date(2020, 1, 1),
        "action_type": "SPLIT",
        "numerator": Decimal("2"),
        "denominator": Decimal("1"),
        "data_source": "test",
        "confidence": "HIGH"
    })
    
    assert obj.id is not None
    records = await corporate_actions_repo.get_by_ticker(db_session, "INFY", "NSE")
    assert len(records) >= 1
    assert any(r.action_type == "SPLIT" for r in records)

@pytest.mark.asyncio
async def test_raw_corporate_actions_repo_crud(db_session):
    obj = await raw_corporate_actions_repo.create(db_session, {
        "ticker": "INFY",
        "exchange": "NSE",
        "action_date": date(2020, 1, 1),
        "action_type_raw": "SPLIT 2:1",
        "numerator": Decimal("2"),
        "denominator": Decimal("1"),
        "data_source": "test",
        "raw_payload": {"hello": "world"}
    })
    assert obj.id is not None
    unprocessed = await raw_corporate_actions_repo.get_unprocessed(db_session)
    assert len(unprocessed) >= 1

@pytest.mark.asyncio
async def test_raw_dividends_repo_crud(db_session):
    obj = await raw_dividends_repo.create(db_session, {
        "ticker": "INFY",
        "exchange": "NSE",
        "ex_date": date(2020, 1, 1),
        "dividend_amount": Decimal("10.50"),
        "data_source": "test"
    })
    
    assert obj.id is not None
    records = await raw_dividends_repo.get_by_ticker(db_session, "INFY", "NSE")
    assert len(records) >= 1
    assert any(r.dividend_amount == Decimal("10.50") for r in records)

@pytest.mark.asyncio
async def test_base_repo_get_by_id(db_session):
    obj = await raw_dividends_repo.create(db_session, {
        "ticker": "INFY",
        "exchange": "NSE",
        "ex_date": date(2020, 1, 1),
        "dividend_amount": Decimal("10.50"),
        "data_source": "test"
    })
    
    fetched = await raw_dividends_repo.get_by_id(db_session, obj.id)
    assert fetched is not None
    assert fetched.id == obj.id

@pytest.mark.asyncio
async def test_base_repo_create_many(db_session):
    objs = await raw_dividends_repo.create_many(db_session, [
        {
            "ticker": "INFY",
            "exchange": "NSE",
            "ex_date": date(2020, 1, 1),
            "dividend_amount": Decimal("1.00"),
            "data_source": "test"
        },
        {
            "ticker": "INFY",
            "exchange": "NSE",
            "ex_date": date(2020, 1, 2),
            "dividend_amount": Decimal("2.00"),
            "data_source": "test"
        }
    ])
    
    assert len(objs) == 2
    assert objs[0].id is not None
    assert objs[1].id is not None
