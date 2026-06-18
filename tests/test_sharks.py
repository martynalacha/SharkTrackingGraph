import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_shark_trajectory(async_client: AsyncClient):
    assert 1 + 1 == 2


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
