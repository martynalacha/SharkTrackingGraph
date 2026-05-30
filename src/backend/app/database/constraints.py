import logging

logger = logging.getLogger("uvicorn.error")


def setup_database_constraints():
    """Creates UNIQUE constraints in Neo4j if they do not exist."""
    from src.backend.app.database.connection import driver

    query_shark = """
    CREATE CONSTRAINT shark_id_unique IF NOT EXISTS
    FOR (s:Shark) REQUIRE s.sharkId IS UNIQUE
    """

    query_grid = """
    CREATE CONSTRAINT grid_id_unique IF NOT EXISTS
    FOR (g:OceanGrid) REQUIRE g.gridId IS UNIQUE
    """

    try:
        with driver.session() as session:
            session.run(query_shark)
            session.run(query_grid)
            logger.info("Database constraints verified/created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database constraints: {e}")