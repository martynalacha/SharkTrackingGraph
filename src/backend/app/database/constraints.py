import logging

from src.backend.app.database.connection import driver

logger = logging.getLogger("uvicorn.error")


async def setup_database_constraints():
    """Creates UNIQUE constraints and supporting indexes in Neo4j if they do not exist."""

    query_shark_constraint = """
    CREATE CONSTRAINT shark_id_unique IF NOT EXISTS
    FOR (s:Shark) REQUIRE s.sharkId IS UNIQUE
    """

    query_grid_constraint = """
    CREATE CONSTRAINT grid_id_unique IF NOT EXISTS
    FOR (g:OceanGrid) REQUIRE g.gridId IS UNIQUE
    """

    query_species_index = """
    CREATE INDEX shark_species_idx IF NOT EXISTS
    FOR (s:Shark) ON (s.species)
    """

    query_name_index = """
    CREATE INDEX shark_name_idx IF NOT EXISTS
    FOR(s:Shark) ON (s.name)
    """

    query_timesptamp_index = """
    CREATE INDEX pinged_at_timestamp_idx IF NOT EXISTS
    FOR ()-[r:PINGED_AT]-() ON (r.timestamp)
    """

    try:
        async with driver.session() as session:
            await session.run(query_shark_constraint)
            await session.run(query_grid_constraint)
            await session.run(query_species_index)
            await session.run(query_name_index)
            await session.run(query_timesptamp_index)
            logger.info("Database constraints and indexes verified/created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database constraints: {e}")
