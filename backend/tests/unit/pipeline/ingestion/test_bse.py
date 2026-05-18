import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.pipeline.ingestion.bse import fetch_bse_corporate_actions
from app.core.exceptions import DataIngestionError

@pytest.mark.asyncio
@patch("app.pipeline.ingestion.bse.httpx.AsyncClient")
async def test_fetch_bse_corporate_actions_success(mock_client_class):
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Table": [{"purpose": "SPLIT"}]}
    mock_client.get.return_value = mock_response
    
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client_class.return_value = mock_client
    
    result = await fetch_bse_corporate_actions("500209")
    
    assert len(result) == 1
    assert result[0]["purpose"] == "SPLIT"

@pytest.mark.asyncio
@patch("app.pipeline.ingestion.bse.httpx.AsyncClient")
async def test_fetch_bse_corporate_actions_failure(mock_client_class):
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("API error")
    
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client_class.return_value = mock_client
    
    with pytest.raises(DataIngestionError) as exc:
        await fetch_bse_corporate_actions("500209")
        
    assert "Failed to fetch BSE data for 500209" in str(exc.value)
