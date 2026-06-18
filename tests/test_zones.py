from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# GET /api/zones/{grid_id}/bounds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_zone_bounds(async_client: AsyncClient):
    """Returns absolute time bounds for a specific ocean zone."""
    mock_record = {
        "gridId": "Gulf Of Mexico",
        "absolute_start": "2021-01-01 00:00:00",
        "absolute_end": "2025-12-31 23:59:00",
    }

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.zones.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/zones/Gulf+Of+Mexico/bounds")

    assert response.status_code == 200
    data = response.json()
    assert data["gridId"] == "Gulf Of Mexico"
    assert data["start"] == "2021-01-01 00:00:00"
    assert data["end"] == "2025-12-31 23:59:00"


@pytest.mark.asyncio
async def test_get_all_zones_bounds(async_client: AsyncClient):
    """ALL_ZONES pseudo-ID returns global min/max bounds."""
    mock_record = {
        "gridId": "ALL_ZONES",
        "absolute_start": "2019-03-10 08:00:00",
        "absolute_end": "2026-06-01 12:00:00",
    }

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.zones.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/zones/ALL_ZONES/bounds")

    assert response.status_code == 200
    assert response.json()["gridId"] == "ALL_ZONES"


@pytest.mark.asyncio
async def test_get_zone_bounds_not_found(async_client: AsyncClient):
    """Returns 404 when the zone does not exist."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=None)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.zones.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/zones/NONEXISTENT/bounds")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/zones/{grid_id}  —  zone analysis
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_zone_analysis(async_client: AsyncClient):
    """Returns zone details with detected sharks within the default time range."""
    mock_record = {
        "gridId": "Gulf Of Mexico",
        "centerLat": 25.0,
        "centerLon": -90.0,
        "unique_sharks": [
            {"sharkId": "SHARK-001", "name": "Deep Blue", "species": "White Shark", "speciesImage": ""},
        ],
    }

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.zones.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/zones/Gulf+Of+Mexico")

    assert response.status_code == 200
    data = response.json()
    assert data["gridId"] == "Gulf Of Mexico"
    assert data["totalUniqueSharksDetected"] == 1
    assert data["sharks"][0]["name"] == "Deep Blue"


@pytest.mark.asyncio
async def test_get_zone_analysis_not_found(async_client: AsyncClient):
    """Returns 404 for an unknown zone ID."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=None)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.zones.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/zones/FAKE_ZONE")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/zones/analysis/degree-centrality
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_degree_centrality(async_client: AsyncClient):
    """Returns ranked centrality report for ocean zones."""
    mock_records = [
        {"gridId": "Gulf Of Mexico", "centerLat": 25.0, "centerLon": -90.0, "degreeScore": 540},
        {"gridId": "Great Barrier Reef", "centerLat": -18.0, "centerLon": 147.0, "degreeScore": 310},
    ]

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.data = AsyncMock(return_value=mock_records)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.zones.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/zones/analysis/degree-centrality?limit=2")

    assert response.status_code == 200
    data = response.json()
    assert data["algorithm"].startswith("Degree Centrality")
    assert len(data["results"]) == 2
    assert data["results"][0]["centralityDegreeScore"] == 540


# ---------------------------------------------------------------------------
# GET /api/zones/{grid_id}/trajectories
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_zone_trajectories(async_client: AsyncClient):
    """Returns per-shark trajectory points within a specific zone."""
    mock_records = [
        {
            "sharkId": "SHARK-001",
            "name": "Deep Blue",
            "points": [
                {"lat": 25.0, "lon": -90.0, "timestamp": "2026-01-10 08:00:00"},
                {"lat": 25.1, "lon": -90.1, "timestamp": "2026-01-11 10:00:00"},
            ],
        }
    ]

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.data = AsyncMock(return_value=mock_records)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.zones.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/zones/Gulf+Of+Mexico/trajectories")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["sharkId"] == "SHARK-001"
    assert len(data[0]["trajectory"]) == 2
