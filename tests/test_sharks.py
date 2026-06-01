from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_shark_trajectory(async_client: AsyncClient):
    """
    Test the endpoint returning a shark's trajectory based on its ID by mocking Neo4j driver session.
    """
    shark_id = "SHARK-001"

    # Prepared mock raw data matching the exact database row record structure
    mock_db_response = [
        {
            "name": "Deep Blue",
            "species": "White Shark",
            "image": "https://example.com/image.jpg",
            "timestamp": "2026-05-18T08:00:00",
            "lat": 25.0,
            "lon": -80.0,
            "zone": "ZONE_25_-80",
        },
        {
            "name": "Deep Blue",
            "species": "White Shark",
            "image": "https://example.com/image.jpg",
            "timestamp": "2026-05-19T10:30:00",
            "lat": 25.5,
            "lon": -81.0,
            "zone": "ZONE_25_-81",
        },
    ]

    # Mocking the context manager execution chain for driver.session().run()
    mock_session = MagicMock()
    mock_session.run.return_value = mock_db_response
    mock_session.__enter__.return_value = mock_session

    # Patch the driver object directly inside the sharks route package destination
    with patch("backend.app.routes.sharks.driver.session", return_value=mock_session):
        # Execute GET request
        response = await async_client.get(f"/api/sharks/{shark_id}/trajectory")

    # Assert response validation parameters
    assert response.status_code == 200

    data = response.json()
    assert data["sharkId"] == shark_id
    assert data["name"] == "Deep Blue"
    assert len(data["trajectory"]) == 2
    assert data["trajectory"][0]["zone"] == "ZONE_25_-80"


@pytest.mark.asyncio
async def test_get_shark_not_found(async_client: AsyncClient):
    """
    Test the behavior when a requested shark ID does not exist in the database (empty results).
    """
    shark_id = "UNKNOWN-999"

    # Mocking empty database response result list
    mock_session = MagicMock()
    mock_session.run.return_value = []
    mock_session.__enter__.return_value = mock_session

    # Patch the driver object directly inside the sharks route package destination
    with patch("backend.app.routes.sharks.driver.session", return_value=mock_session):
        response = await async_client.get(f"/api/sharks/{shark_id}/trajectory")

    # Assert correct HTTP status code for unmapped tracking entities
    assert response.status_code == 404
