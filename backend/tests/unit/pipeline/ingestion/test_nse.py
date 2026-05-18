import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.pipeline.ingestion.nse import fetch_nse_corporate_actions, get_nse_session
from app.core.exceptions import DataIngestionError

@pytest.mark.asyncio
@patch("app.pipeline.ingestion.nse.httpx.AsyncClient")
async def test_get_nse_session_success(mock_client_class):
    mock_client = AsyncMock()
    mock_client_class.return_value = mock_client
    
    session = await get_nse_session()
    
    assert session == mock_client
    assert mock_client.get.call_count == 2

@pytest.mark.asyncio
@patch("app.pipeline.ingestion.nse.httpx.AsyncClient")
async def test_get_nse_session_failure(mock_client_class):
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("Connection timeout")
    mock_client_class.return_value = mock_client
    
    with pytest.raises(DataIngestionError) as exc:
        await get_nse_session()
        
    assert "Failed to establish NSE session" in str(exc.value)

@pytest.mark.asyncio
@patch("app.pipeline.ingestion.nse.get_nse_session")
async def test_fetch_nse_corporate_actions_success(mock_get_session):
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"purpose": "BONUS"}]
    mock_client.get.return_value = mock_response
    mock_get_session.return_value = mock_client
    
    result = await fetch_nse_corporate_actions("INFY")
    
    assert len(result) == 1
    assert result[0]["purpose"] == "BONUS"
    mock_client.aclose.assert_called_once()

@pytest.mark.asyncio
@patch("app.pipeline.ingestion.nse.get_nse_session")
async def test_fetch_nse_corporate_actions_failure(mock_get_session):
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("API error")
    mock_get_session.return_value = mock_client
    
    with pytest.raises(DataIngestionError) as exc:
        await fetch_nse_corporate_actions("INFY")
        
    assert "Failed to fetch NSE data for INFY" in str(exc.value)
    mock_client.aclose.assert_called_once()
