import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

# Import the actual FastAPI application instance
from src.backend.app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """
    Creates an instance of the default asyncio event loop for the whole test session.
    Provides isolation and fixes closed event loop runtime errors.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
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
