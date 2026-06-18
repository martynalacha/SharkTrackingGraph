from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

# ===========================================================================
# GRID  —  GET /api/zones/markers
# ===========================================================================


@pytest.mark.asyncio
async def test_get_zone_markers(async_client: AsyncClient):
    """Returns aggregated map-marker data for all ocean grid nodes."""
    mock_records = [
        {
            "zoneName": "Gulf Of Mexico",
            "lat": 25.0,
            "lon": -90.0,
            "uniqueSharks": 5,
            "sampleSharks": ["Deep Blue", "Brutus"],
        },
        {
            "zoneName": "Great Barrier Reef",
            "lat": -18.0,
            "lon": 147.0,
            "uniqueSharks": 3,
            "sampleSharks": ["Jaws"],
        },
    ]

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.data = AsyncMock(return_value=mock_records)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.grid.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/zones/markers")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["zoneName"] == "Gulf Of Mexico"
    assert data[0]["uniqueSharksCount"] == 5
    assert "Deep Blue" in data[0]["presentSharks"]


@pytest.mark.asyncio
async def test_get_zone_markers_empty(async_client: AsyncClient):
    """Returns an empty list when no grid nodes have telemetry data."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.data = AsyncMock(return_value=[])
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.grid.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/zones/markers")

    assert response.status_code == 200
    assert response.json() == []


# ===========================================================================
# CLUSTERS  —  GET /api/zones/analysis/clusters
# ===========================================================================


@pytest.mark.asyncio
async def test_get_zone_clusters(async_client: AsyncClient):
    """Returns ranked hot-spot zones within the default time window."""
    mock_records = [
        {
            "gridId": "Gulf Of Mexico",
            "centerLat": 25.0,
            "centerLon": -90.0,
            "totalPings": 812,
            "uniqueSharksCount": 14,
        },
        {
            "gridId": "Cape Cod, MA",
            "centerLat": 41.9,
            "centerLon": -70.0,
            "totalPings": 430,
            "uniqueSharksCount": 7,
        },
    ]

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.data = AsyncMock(return_value=mock_records)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.clusters.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/zones/analysis/clusters?limit=2")

    assert response.status_code == 200
    data = response.json()
    assert data["requestedLimit"] == 2
    assert data["totalClustersReturned"] == 2
    assert data["clusters"][0]["gridId"] == "Gulf Of Mexico"
    assert data["clusters"][0]["totalPings"] == 812


@pytest.mark.asyncio
async def test_get_zone_clusters_with_time_filter(async_client: AsyncClient):
    """Accepts ISO 8601 start/end parameters and forwards them to the query."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.data = AsyncMock(return_value=[])
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.clusters.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get(
            "/api/zones/analysis/clusters" "?start_time=2024-01-01T00:00:00&end_time=2024-12-31T23:59:59&limit=5"
        )

    assert response.status_code == 200
    data = response.json()
    assert data["requestedLimit"] == 5
    assert data["clusters"] == []
    # Verify the filter period was correctly parsed
    assert "2024-01-01" in data["filterPeriod"]["start"]


@pytest.mark.asyncio
async def test_get_zone_clusters_empty(async_client: AsyncClient):
    """Returns an empty clusters list when no pings exist in the period."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.data = AsyncMock(return_value=[])
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.clusters.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/zones/analysis/clusters")

    assert response.status_code == 200
    assert response.json()["totalClustersReturned"] == 0
