from unittest.mock import patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_shark_trajectory(async_client: AsyncClient):
    """
    Test the endpoint returning a shark's trajectory based on its ID.
    """
    shark_id = "SHARK-001"

    # Mock data representing Neo4j database response
    mock_db_response = [
        {"grid": "ZONE_25_-80", "time": "2026-05-18T08:00:00"},
        {"grid": "ZONE_25_-81", "time": "2026-05-19T10:30:00"},
    ]

    # Target the queries module object imported inside the sharks route
    with patch("backend.app.routes.sharks.queries.get_shark_trajectory_from_db") as mock_db_call:
        mock_db_call.return_value = mock_db_response

        # Execute GET request
        response = await async_client.get(f"/api/sharks/{shark_id}/trajectory")

    # Assert response parameters
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert data[0]["grid"] == "ZONE_25_-80"
    assert data[1]["time"] == "2026-05-19T10:30:00"


@pytest.mark.asyncio
async def test_get_shark_not_found(async_client: AsyncClient):
    """
    Test the behavior when a requested shark ID does not exist in the database.
    """
    shark_id = "UNKNOWN-999"

    # Target the queries module object imported inside the sharks route
    with patch("backend.app.routes.sharks.queries.get_shark_trajectory_from_db") as mock_db_call:
        # Return empty list simulating no records found
        mock_db_call.return_value = []

        response = await async_client.get(f"/api/sharks/{shark_id}/trajectory")

    # Assert correct HTTP status for not found resource
    assert response.status_code == 404
