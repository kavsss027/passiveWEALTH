import httpx
from typing import Dict, Any, List
from app.core.exceptions import DataIngestionError
from app.core.config import settings

async def get_nse_session() -> httpx.AsyncClient:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    client = httpx.AsyncClient(headers=headers, follow_redirects=True)
    try:
        # Step 1: Hit homepage to establish session cookie
        await client.get("https://www.nseindia.com", timeout=settings.NSE_REQUEST_TIMEOUT)
        # Step 2: Hit the main equities page — some NSE endpoints require this
        await client.get("https://www.nseindia.com/market-data/live-equity-market", timeout=settings.NSE_REQUEST_TIMEOUT)
    except Exception as e:
        await client.aclose()
        raise DataIngestionError(f"Failed to establish NSE session: {str(e)}")
        
    return client

async def fetch_nse_corporate_actions(ticker: str) -> List[Dict[str, Any]]:
    client = await get_nse_session()
    try:
        response = await client.get(
            "https://www.nseindia.com/api/corporates-corporateActions",
            params={"index": "equities", "symbol": ticker},
            timeout=settings.NSE_REQUEST_TIMEOUT
        )
        if response.status_code != 200:
            raise DataIngestionError(f"NSE API returned {response.status_code}")
        
        data = response.json()
        if not isinstance(data, list):
            return []
        return data
    except Exception as e:
        raise DataIngestionError(f"Failed to fetch NSE data for {ticker}: {str(e)}")
    finally:
        await client.aclose()
