from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_shark_trajectory(async_client: AsyncClient):
    # 1. Przygotuj dane
    shark_id = "SHARK-001"
    mock_db_data = [
        {
            "name": "Deep Blue",
            "species": "White Shark",
            "timestamp": "2026-05-18T08:00:00",
            "lat": 25.0,
            "lon": -80.0,
            "zone": "ZONE_25_-80",
        }
    ]

    # 2. Skonfiguruj mocki dla asynchronicznej sesji Neo4j
    mock_session = MagicMock()
    mock_result = MagicMock()

    # Neo4j w async zwraca wynik przez metodę .data()
    mock_result.data.return_value = mock_db_data
    mock_session.run.return_value = mock_result

    # Kluczowe: __aenter__ dla async with driver.session()
    mock_session.__aenter__.return_value = mock_session

    # 3. Patchuj ścieżkę do drivera w pliku z trasami
    with patch("src.backend.app.routes.sharks.driver.session", return_value=mock_session):
        response = await async_client.get(f"/api/sharks/{shark_id}/trajectory")

    # 4. Asercje
    assert response.status_code == 200
    data = response.json()
    assert data["sharkId"] == shark_id
    assert data["name"] == "Deep Blue"


# @pytest.mark.asyncio
# async def test_get_shark_not_found(async_client: AsyncClient):
#     """
#     Test the behavior when a requested shark ID does not exist in the database (empty results).
#     """
#     shark_id = "UNKNOWN-999"

#     # Mocking empty database response result list
#     mock_session = MagicMock()
#     mock_session.run.return_value = []
#     mock_session.__enter__.return_value = mock_session

#     # Patch the driver object directly inside the sharks route package destination
#     with patch("backend.app.routes.sharks.driver.session", return_value=mock_session):
#         response = await async_client.get(f"/api/sharks/{shark_id}/trajectory")

#     # Assert correct HTTP status code for unmapped tracking entities
#     assert response.status_code == 404
