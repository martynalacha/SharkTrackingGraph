from fastapi import APIRouter, HTTPException, Query

from src.backend.app.database.connection import driver

router = APIRouter(prefix="/api/sharks", tags=["Sharks"])


@router.get("/")
async def get_sharks(species: str = Query(None, description="Filter sharks by exact species name")):
    """
    Returns a list of all sharks in the database.
    If a species query parameter is provided, filters the result by that species.
    """
    if species:
        query = """
        MATCH (s:Shark)
        WHERE s.species = $species
        RETURN s {.*} AS shark_data
        ORDER BY s.name ASC
        """
        params = {"species": species}
    else:
        query = """
        MATCH (s:Shark)
        RETURN s {.*} AS shark_data
        ORDER BY s.name ASC
        """
        params = {}

    async with driver.session() as session:
        result = await session.run(query, **params)
        records = await result.data()
        return [record["shark_data"] for record in records]


@router.get("/search")
async def search_shark(q: str = Query(..., description="Search term matching sharkId or shark name")):
    """
    Finds a specific shark's full profile by performing a case-insensitive search
    on both its name and sharkId.
    """
    query = """
    MATCH (s:Shark)
    WHERE s.sharkId = $q OR toLower(s.name) = toLower($q)
    RETURN s {.*} AS shark_data
    """
    async with driver.session() as session:
        result = await session.run(query, q=q)
        record = await result.single()
        if not record:
            raise HTTPException(status_code=404, detail=f"Shark with identifier '{q}' not found")
        return record["shark_data"]


@router.get("/{shark_id}/trajectory")
async def get_shark_trajectory(shark_id: str):
    """
    Returns the chronological history of geographic points pinged by a specific shark,
    including zone coordinates and entity metadata for map visualization.
    """
    # Uwaga: poprawiłem właściwości r.timestamp, r.lat, r.lon oraz g.gridId
    # tak, aby odpowiadały dokładnie nazwom kluczy, które zapisały się w bazie w poprzednich krokach
    query = """
    MATCH (s:Shark {sharkId: $shark_id})-[r:PINGED_AT]->(g:OceanGrid)
    RETURN s.name AS name, s.species AS species, s.speciesImage AS image,
           r.timestamp AS timestamp, r.lat AS lat, r.lon AS lon, g.gridId AS zone
    ORDER BY r.timestamp ASC
    """
    async with driver.session() as session:
        result = await session.run(query, shark_id=shark_id)
        records = await result.data()

        if not records:
            raise HTTPException(status_code=404, detail="Shark tracking data not found")

        trajectory = []
        for rec in records:
            trajectory.append(
                {"timestamp": rec["timestamp"], "lat": rec["lat"], "lon": rec["lon"], "zone": rec["zone"]}
            )

        return {
            "sharkId": shark_id,
            "name": records[0]["name"],
            "species": records[0]["species"],
            "image": records[0]["image"],
            "trajectory": trajectory,
        }
