import pytest

# Import your FastAPI app instance
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def async_client():
    """
    Provide an asynchronous client for FastAPI testing.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# Mocking database dependencies
async def mock_get_db_session():
    """
    Mock function to replace the actual Neo4j session generator.
    """
    yield None


@pytest.fixture(autouse=True)
def override_dependencies():
    """
    Override actual database dependencies with mocks before each test.
    """
    # Assuming get_db_session is used in your FastAPI endpoints
    # app.dependency_overrides[get_db_session] = mock_get_db_session
    yield
    app.dependency_overrides.clear()
