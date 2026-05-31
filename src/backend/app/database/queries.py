from neo4j import AsyncDriver


async def get_all_sharks(driver: AsyncDriver):
    """
    Retrieve all shark nodes from the database with their full properties.
    """
    query = """
    MATCH (s:Shark)
    RETURN s {.*} AS shark_data
    ORDER BY s.name ASC
    """
    async with driver.session() as session:
        result = await session.run(query)
        records = await result.data()
        return [record["shark_data"] for record in records]


async def get_sharks_by_species(driver: AsyncDriver, species_name: str):
    """
    Filter sharks by their exact species property.
    """
    query = """
    MATCH (s:Shark)
    WHERE toLower(s.species) = toLower($species_name)
    RETURN s {.*} AS shark_data
    ORDER BY s.name ASC
    """
    async with driver.session() as session:
        result = await session.run(query, species_name=species_name)
        records = await result.data()
        return [record["shark_data"] for record in records]


async def get_shark_by_id_or_name(driver: AsyncDriver, search_query: str):
    """
    Find a specific shark by checking both sharkId and name (case-insensitive).
    """
    query = """
    MATCH (s:Shark)
    WHERE s.sharkId = $search_query OR toLower(s.name) = toLower($search_query)
    RETURN s {.*} AS shark_data
    """
    async with driver.session() as session:
        result = await session.run(query, search_query=search_query)
        record = await result.single()
        if record:
            return record["shark_data"]
        return None
