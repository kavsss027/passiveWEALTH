import httpx
from typing import Dict, Any, List
from app.core.exceptions import DataIngestionError
from app.core.config import settings

async def fetch_bse_corporate_actions(bse_code: str) -> List[Dict[str, Any]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        try:
            response = await client.get(
                f"https://api.bseindia.com/BseIndiaAPI/api/CorporateAction/w",
                params={"scripcode": bse_code, "type": "CA"},
                timeout=settings.NSE_REQUEST_TIMEOUT
            )
            if response.status_code != 200:
                raise DataIngestionError(f"BSE API returned {response.status_code}")
            
            data = response.json()
            if isinstance(data, dict) and "Table" in data:
                return data["Table"]
            elif isinstance(data, list):
                return data
            return []
        except Exception as e:
            raise DataIngestionError(f"Failed to fetch BSE data for {bse_code}: {str(e)}")
