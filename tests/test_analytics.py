from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# GET /api/admin/telemetry/date-range
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_telemetry_date_range(async_client: AsyncClient):
    """Returns global min/max timestamp across all PINGED_AT relations."""
    mock_record = {"minDate": "2026-01-01T00:00:00", "maxDate": "2026-06-01T00:00:00"}

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.analytics.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/admin/telemetry/date-range")

    assert response.status_code == 200
    data = response.json()
    assert data["minDate"] == "2026-01-01T00:00:00"
    assert data["maxDate"] == "2026-06-01T00:00:00"


@pytest.mark.asyncio
async def test_get_telemetry_date_range_no_data(async_client: AsyncClient):
    """Returns null dates when there are no telemetry relations."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=None)
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.backend.app.routes.analytics.driver") as mock_driver:
        mock_driver.session.return_value = mock_session
        response = await async_client.get("/api/admin/telemetry/date-range")

    assert response.status_code == 200
    data = response.json()
    assert data["minDate"] is None
    assert data["maxDate"] is None


# ---------------------------------------------------------------------------
# GET /api/admin/verify
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_admin_valid_credentials(async_client: AsyncClient):
    """Returns 200 with status ok when correct Basic Auth credentials are supplied."""
    from src.backend.app.dependencies.auth import verify_admin_credentials
    from src.backend.app.main import app

    app.dependency_overrides[verify_admin_credentials] = lambda: None

    response = await async_client.get("/api/admin/verify")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_verify_admin_invalid_credentials(async_client: AsyncClient):
    """Returns 401 when no / wrong credentials are provided."""
    response = await async_client.get(
        "/api/admin/verify",
        headers={"Authorization": "Basic d3Jvbmc6Y3JlZHM="},  # wrong:creds
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/admin/recalibrate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_trigger_recalibration(async_client: AsyncClient, tmp_path):
    """Returns 200 and starts background recalibration when clean CSV is present."""
    from src.backend.app.dependencies.auth import verify_admin_credentials
    from src.backend.app.main import app

    # Create a minimal CSV so the path check passes
    clean_csv = tmp_path / "sharks_data_clean.csv"
    clean_csv.write_text("id,datetime,latitude,longitude\n")

    app.dependency_overrides[verify_admin_credentials] = lambda: None

    with (
        patch("src.backend.app.routes.analytics.os.path.exists", return_value=True),
        patch("src.backend.app.routes.analytics.pd.read_csv", return_value=MagicMock(iterrows=lambda: iter([]))),
        patch("src.backend.app.routes.analytics.remap_telemetry_relations", new_callable=AsyncMock),
    ):
        response = await async_client.post("/api/admin/recalibrate")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"


@pytest.mark.asyncio
async def test_trigger_recalibration_missing_csv(async_client: AsyncClient):
    """Returns 404 when the clean CSV file is not present."""
    from src.backend.app.dependencies.auth import verify_admin_credentials
    from src.backend.app.main import app

    app.dependency_overrides[verify_admin_credentials] = lambda: None

    with patch("src.backend.app.routes.analytics.os.path.exists", return_value=False):
        response = await async_client.post("/api/admin/recalibrate")

    assert response.status_code == 404
