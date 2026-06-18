import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

# ===========================================================================
# Helpers
# ===========================================================================


def _override_auth(app):
    """Bypass admin credential check for testing."""
    from src.backend.app.dependencies.auth import verify_admin_credentials

    app.dependency_overrides[verify_admin_credentials] = lambda: None


# ===========================================================================
# ADMIN SHARKS  —  /api/admin/sharks
# ===========================================================================


@pytest.mark.asyncio
async def test_create_shark(async_client: AsyncClient):
    """POST /api/admin/sharks/  creates a new shark node and returns its profile."""
    from src.backend.app.main import app

    _override_auth(app)

    shark_payload = {
        "sharkId": "SHARK-NEW",
        "name": "Finley",
        "gender": "Male",
        "species": "Bull Shark",
        "weight": 180.0,
        "length": 2.4,
        "speciesImage": "",
    }
    db_record = {**shark_payload, "speciesImage": "https://wiki.example.com/bull.jpg"}

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=db_record)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("src.backend.app.routes.admin_sharks.driver") as mock_driver,
        patch(
            "src.backend.app.routes.admin_sharks.WikiService.get_species_image_url",
            new_callable=AsyncMock,
            return_value="https://wiki.example.com/bull.jpg",
        ),
    ):
        mock_driver.session.return_value = mock_session
        response = await async_client.post("/api/admin/sharks/", json=shark_payload)

    assert response.status_code == 201
    data = response.json()
    assert data["sharkId"] == "SHARK-NEW"
    assert data["name"] == "Finley"


@pytest.mark.asyncio
async def test_create_shark_duplicate(async_client: AsyncClient):
    """POST /api/admin/sharks/  returns 400 when a constraint violation occurs."""
    from src.backend.app.main import app

    _override_auth(app)

    shark_payload = {
        "sharkId": "SHARK-001",
        "name": "Deep Blue",
        "gender": "Female",
        "species": "White Shark",
        "weight": 2200.0,
        "length": 6.1,
        "speciesImage": "",
    }

    mock_session = MagicMock()
    mock_session.run = AsyncMock(side_effect=Exception("ConstraintError"))
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("src.backend.app.routes.admin_sharks.driver") as mock_driver,
        patch(
            "src.backend.app.routes.admin_sharks.WikiService.get_species_image_url",
            new_callable=AsyncMock,
            return_value="",
        ),
    ):
        mock_driver.session.return_value = mock_session
        response = await async_client.post("/api/admin/sharks/", json=shark_payload)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_shark(async_client: AsyncClient):
    """PUT /api/admin/sharks/{id}  updates mutable shark fields."""
    from src.backend.app.main import app

    _override_auth(app)

    db_record = {
        "sharkId": "SHARK-001",
        "name": "Deep Blue Updated",
        "gender": "Female",
        "species": "White Shark",
        "weight": 2300.0,
        "length": 6.2,
        "speciesImage": "",
    }

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=db_record)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.admin_sharks.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.put(
            "/api/admin/sharks/SHARK-001",
            json={"name": "Deep Blue Updated", "weight": 2300.0},
        )

    assert response.status_code == 200
    assert response.json()["name"] == "Deep Blue Updated"
    assert response.json()["weight"] == 2300.0


@pytest.mark.asyncio
async def test_update_shark_not_found(async_client: AsyncClient):
    """PUT /api/admin/sharks/{id}  returns 404 when shark does not exist."""
    from src.backend.app.main import app

    _override_auth(app)

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=None)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.admin_sharks.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.put(
            "/api/admin/sharks/GHOST-999",
            json={"name": "Nobody"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_shark(async_client: AsyncClient):
    """DELETE /api/admin/sharks/{id}  removes the shark and its edges."""
    from src.backend.app.main import app

    _override_auth(app)

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value={"deleted_count": 1})
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.admin_sharks.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.delete("/api/admin/sharks/SHARK-001")

    assert response.status_code == 200
    assert "SHARK-001" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_shark_not_found(async_client: AsyncClient):
    """DELETE /api/admin/sharks/{id}  returns 404 when the shark is missing."""
    from src.backend.app.main import app

    _override_auth(app)

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value={"deleted_count": 0})
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.admin_sharks.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.delete("/api/admin/sharks/GHOST-999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_import_telemetry_csv(async_client: AsyncClient):
    """POST /api/admin/sharks/import/telemetry  ingests a valid CSV file."""
    from src.backend.app.main import app

    _override_auth(app)

    csv_content = b"sharkId,datetime,lat,lon\nSHARK-001,2026-01-01 08:00:00,25.0,-80.0\n"

    with patch("src.backend.app.routes.admin_sharks.attach_pings_to_grid", new_callable=AsyncMock, return_value=1):
        response = await async_client.post(
            "/api/admin/sharks/import/telemetry",
            files={"file": ("telemetry.csv", io.BytesIO(csv_content), "text/csv")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Success"
    assert data["recordsProcessed"] == 1


@pytest.mark.asyncio
async def test_import_telemetry_wrong_extension(async_client: AsyncClient):
    """POST /api/admin/sharks/import/telemetry  rejects non-CSV files."""
    from src.backend.app.main import app

    _override_auth(app)

    response = await async_client.post(
        "/api/admin/sharks/import/telemetry",
        files={"file": ("data.txt", io.BytesIO(b"not a csv"), "text/plain")},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_import_telemetry_missing_columns(async_client: AsyncClient):
    """POST /api/admin/sharks/import/telemetry  returns 400 for missing required columns."""
    from src.backend.app.main import app

    _override_auth(app)

    csv_content = b"id,date,x,y\n1,2026-01-01,10,20\n"

    response = await async_client.post(
        "/api/admin/sharks/import/telemetry",
        files={"file": ("bad.csv", io.BytesIO(csv_content), "text/csv")},
    )

    assert response.status_code == 400


# ===========================================================================
# ADMIN ZONES  —  /api/admin/zones
# ===========================================================================


@pytest.mark.asyncio
async def test_create_ocean_zone(async_client: AsyncClient):
    """POST /api/admin/zones/  creates a new OceanGrid node."""
    from src.backend.app.main import app

    _override_auth(app)

    zone_payload = {"gridId": "ZONE_TEST", "centerLat": 10.5, "centerLon": -60.2}
    db_record = {"zone_data": {**zone_payload}}

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=db_record)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.admin_zones.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.post("/api/admin/zones/", json=zone_payload)

    assert response.status_code == 201
    assert response.json()["gridId"] == "ZONE_TEST"


@pytest.mark.asyncio
async def test_create_ocean_zone_duplicate(async_client: AsyncClient):
    """POST /api/admin/zones/  returns 400 on constraint violation."""
    from src.backend.app.main import app

    _override_auth(app)

    mock_session = MagicMock()
    mock_session.run = AsyncMock(side_effect=Exception("ConstraintError"))
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.admin_zones.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.post(
            "/api/admin/zones/",
            json={"gridId": "ZONE_DUP", "centerLat": 0.0, "centerLon": 0.0},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_ocean_zone(async_client: AsyncClient):
    """PUT /api/admin/zones/{id}  updates zone coordinates."""
    from src.backend.app.main import app

    _override_auth(app)

    db_record = {"zone_data": {"gridId": "ZONE_TEST", "centerLat": 11.0, "centerLon": -61.0}}

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=db_record)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.admin_zones.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.put(
            "/api/admin/zones/ZONE_TEST",
            json={"centerLat": 11.0, "centerLon": -61.0},
        )

    assert response.status_code == 200
    assert response.json()["centerLat"] == 11.0


@pytest.mark.asyncio
async def test_update_ocean_zone_not_found(async_client: AsyncClient):
    """PUT /api/admin/zones/{id}  returns 404 when zone is missing."""
    from src.backend.app.main import app

    _override_auth(app)

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=None)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.admin_zones.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.put(
            "/api/admin/zones/ZONE_GHOST",
            json={"centerLat": 0.0},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_ocean_zone(async_client: AsyncClient):
    """DELETE /api/admin/zones/{id}  removes the zone and its edges."""
    from src.backend.app.main import app

    _override_auth(app)

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value={"deleted_count": 1})
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.admin_zones.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.delete("/api/admin/zones/ZONE_TEST")

    assert response.status_code == 200
    assert "ZONE_TEST" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_ocean_zone_not_found(async_client: AsyncClient):
    """DELETE /api/admin/zones/{id}  returns 404 when zone does not exist."""
    from src.backend.app.main import app

    _override_auth(app)

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value={"deleted_count": 0})
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.admin_zones.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.delete("/api/admin/zones/ZONE_GHOST")

    assert response.status_code == 404
