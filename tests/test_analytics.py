from unittest.mock import patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_hub_identification(async_client: AsyncClient):
    """
    Test the endpoint returning aggregated data for ocean hubs (Degree Centrality).
    """
    # Mock data representing analytical Cypher query response
    mock_hub_data = [
        {"grid_id": "ZONE_20_-70", "unique_sharks_count": 45},
        {"grid_id": "ZONE_25_-80", "unique_sharks_count": 32},
        {"grid_id": "ZONE_15_-60", "unique_sharks_count": 12},
    ]

    # Target the queries module object imported inside the analytics route
    with patch("backend.app.routes.analytics.queries.calculate_degree_centrality") as mock_calc:
        mock_calc.return_value = mock_hub_data

        # Execute GET request
        response = await async_client.get("/api/analytics/hubs")

    # Assert response structure
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3

    # Assert correct sorting and data mapping
    assert data[0]["grid_id"] == "ZONE_20_-70"
    assert data[0]["unique_sharks_count"] == 45
    assert data[2]["unique_sharks_count"] == 12
