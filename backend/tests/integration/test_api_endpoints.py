import pytest
from httpx import AsyncClient
from app.main import app
from app.database.connection import get_db
from datetime import date
from decimal import Decimal

@pytest.mark.asyncio
async def test_reconstruct_portfolio_success(db_session):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "ticker": "INFY",
            "exchange": "NSE",
            "buy_date": "1999-01-01",
            "quantity": 100,
            "total_amount_invested": 50000.00
        }
        response = await ac.post("/api/v1/portfolio/reconstruct", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["ticker"] == "INFY"
        assert data["exchange"] == "NSE"
        assert data["timeline"][0]["event_type"] == "BUY"
        assert data["wealth_summary"]["unrealized_gain_label"] == "if sold at current market price"
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_reconstruct_portfolio_auto_fetch(db_session):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "ticker": "INFY",
            "exchange": "NSE",
            "buy_date": "1999-01-01",
            "quantity": 100
        }
        response = await ac.post("/api/v1/portfolio/reconstruct", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["ticker"] == "INFY"
        assert data["exchange"] == "NSE"
        assert data["timeline"][0]["event_type"] == "BUY"
        # Since no total_amount_invested was provided, a warning should be added
        assert len(data["data_quality"]["warnings"]) > 0
        assert "Buy price auto-fetched" in data["data_quality"]["warnings"][0]
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_reconstruct_portfolio_invalid_ticker(db_session):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "ticker": "INVALID_TICKER",
            "exchange": "NSE",
            "buy_date": "1999-01-01",
            "quantity": 100,
            "total_amount_invested": 50000.00
        }
        response = await ac.post("/api/v1/portfolio/reconstruct", json=payload)
        assert response.status_code == 422
        
        data = response.json()
        assert data["error"]["code"] == "INVALID_TICKER"
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_reconstruct_portfolio_future_date(db_session):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "ticker": "INFY",
            "exchange": "NSE",
            "buy_date": "2030-01-01",
            "quantity": 100,
            "total_amount_invested": 50000.00
        }
        response = await ac.post("/api/v1/portfolio/reconstruct", json=payload)
        assert response.status_code == 422
        
        data = response.json()
        assert data["error"]["code"] == "INVALID_BUY_DATE"
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_reconstruct_portfolio_invalid_quantity(db_session):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "ticker": "INFY",
            "exchange": "NSE",
            "buy_date": "1999-01-01",
            "quantity": 0,
            "total_amount_invested": 50000.00
        }
        response = await ac.post("/api/v1/portfolio/reconstruct", json=payload)
        assert response.status_code == 422
        
        data = response.json()
        assert data["error"]["code"] == "INVALID_QUANTITY"
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_corporate_actions(db_session):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/corporate-actions/INFY?exchange=NSE")
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "INFY"
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_market_data_not_found(db_session):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/market-data/INFY?exchange=NSE&from_date=2000-01-01&to_date=2000-01-02")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NO_DATA_AVAILABLE"
    app.dependency_overrides.clear()
