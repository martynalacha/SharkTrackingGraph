from neo4j import GraphDatabase

from src.backend.app.config import settings

# Inicjalizacja oficjalnego sterownika Neo4j
driver = GraphDatabase.driver(
    settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
)


def get_db_session():
    """Context manager providing a secure database session."""
    with driver.session() as session:
        yield session


def close_driver():
    """Closes the database driver connection pool."""
    driver.close()
