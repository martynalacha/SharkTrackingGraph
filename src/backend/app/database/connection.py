from neo4j import AsyncGraphDatabase

from src.backend.app.config import settings

# Initialize the official Neo4j driver connection pool.
driver = AsyncGraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))


async def get_db_session():
    """Context manager providing a secure database session."""
    async with driver.session() as session:
        yield session


async def close_driver():
    """Closes the database driver connection pool."""
    await driver.close()
