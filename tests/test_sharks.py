from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# GET /api/sharks/  —  list all sharks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_all_sharks(async_client: AsyncClient):
    """Returns a flat list of all shark objects stored in the database."""
    mock_records = [
        {"shark_data": {"sharkId": "SHARK-001", "name": "Deep Blue", "species": "White Shark"}},
        {"shark_data": {"sharkId": "SHARK-002", "name": "Brutus", "species": "Bull Shark"}},
    ]

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.data = AsyncMock(return_value=mock_records)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.sharks.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/sharks/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["sharkId"] == "SHARK-001"
    assert data[1]["name"] == "Brutus"


@pytest.mark.asyncio
async def test_get_sharks_filtered_by_species(async_client: AsyncClient):
    """Passing ?species= filters the result to that species only."""
    mock_records = [
        {"shark_data": {"sharkId": "SHARK-003", "name": "Jaws", "species": "White Shark"}},
    ]

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.data = AsyncMock(return_value=mock_records)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.sharks.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/sharks/?species=White+Shark")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["species"] == "White Shark"


@pytest.mark.asyncio
async def test_get_all_sharks_empty(async_client: AsyncClient):
    """Returns an empty list when the database has no sharks."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.data = AsyncMock(return_value=[])
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.sharks.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/sharks/")

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /api/sharks/search  —  search by name or sharkId
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_shark_found(async_client: AsyncClient):
    """Returns the shark profile when a matching name/ID is found."""
    mock_record = {"shark_data": {"sharkId": "SHARK-001", "name": "Deep Blue", "species": "White Shark"}}

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.sharks.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/sharks/search?q=Deep+Blue")

    assert response.status_code == 200
    assert response.json()["sharkId"] == "SHARK-001"


@pytest.mark.asyncio
async def test_search_shark_not_found(async_client: AsyncClient):
    """Returns 404 when the search term matches no shark."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=None)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.sharks.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/sharks/search?q=GHOST-999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/sharks/{shark_id}/trajectory
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_shark_trajectory(async_client: AsyncClient):
    """Returns ordered trajectory data for a known shark."""
    shark_id = "SHARK-001"
    mock_db_response = [
        {
            "name": "Deep Blue",
            "species": "White Shark",
            "image": "https://example.com/img.jpg",
            "timestamp": "2026-05-18T08:00:00",
            "lat": 25.0,
            "lon": -80.0,
            "zone": "ZONE_25_-80",
        },
        {
            "name": "Deep Blue",
            "species": "White Shark",
            "image": "https://example.com/img.jpg",
            "timestamp": "2026-05-19T10:30:00",
            "lat": 25.5,
            "lon": -81.0,
            "zone": "ZONE_25_-81",
        },
    ]

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.data = AsyncMock(return_value=mock_db_response)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.sharks.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get(f"/api/sharks/{shark_id}/trajectory")

    assert response.status_code == 200
    data = response.json()
    assert data["sharkId"] == shark_id
    assert data["name"] == "Deep Blue"
    assert len(data["trajectory"]) == 2
    assert data["trajectory"][0]["zone"] == "ZONE_25_-80"
    assert data["trajectory"][1]["lat"] == 25.5


@pytest.mark.asyncio
async def test_get_shark_trajectory_not_found(async_client: AsyncClient):
    """Returns 404 when no telemetry records exist for the requested shark."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.data = AsyncMock(return_value=[])
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.sharks.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/sharks/UNKNOWN-999/trajectory")

    assert response.status_code == 404
