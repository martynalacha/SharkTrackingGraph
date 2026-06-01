from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_hub_identification(async_client: AsyncClient):
    """
    Test the endpoint returning telemetry date range by mocking the Neo4j driver session.
    """
    # Prepared mock records matching the exact expected keys returned by the query
    mock_record = {"minDate": "2026-01-01T00:00:00", "maxDate": "2026-06-01T00:00:00"}

    # Mocking the context manager execution chain for driver.session().run().single()
    mock_session = MagicMock()
    mock_result = MagicMock()

    mock_result.single.return_value = mock_record
    mock_session.run.return_value = mock_result
    mock_session.__enter__.return_value = mock_session

    # Patch the driver object directly inside the analytics route package destination
    with patch("backend.app.routes.analytics.driver.session", return_value=mock_session):
        # Execute GET request to the real defined endpoint
        response = await async_client.get("/api/telemetry/date-range")

    # Assert response validation parameters
    assert response.status_code == 200

    data = response.json()
    assert data["minDate"] == "2026-01-01T00:00:00"
    assert data["maxDate"] == "2026-06-01T00:00:00"
