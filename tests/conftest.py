import pytest

# Import the actual FastAPI application instance
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture(scope="session")
def anyio_backend():
    """
    Defines the backend driver for asynchronous operation execution.
    Using anyio allows standard async/await syntax resolution in tests.
    """
    return "asyncio"


@pytest.fixture
async def async_client():
    """
    Provides a contextual isolated asynchronous client for FastAPI integration testing.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
def manage_dependency_overrides():
    """
    Ensures that any lifecycle endpoint overrides are correctly isolated per test
    and thoroughly cleared after execution completes.
    """
    yield
    app.dependency_overrides.clear()
