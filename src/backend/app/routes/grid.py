from fastapi import APIRouter

from src.backend.app.database.connection import driver

router = APIRouter(prefix="/api/zones", tags=["Ocean Zones"])


@router.get("/markers")
def get_zone_markers():
    """
    Returns aggregate map marker data for all registered ocean grids,
    including unique shark counts and the latest registered activities.
    """
    query = """
    MATCH (s:Shark)-[r:PINGED_AT]->(g:OceanGrid)
    WITH g, count(DISTINCT s) AS uniqueSharks, collect(s.name)[0..5] AS sampleSharks
    RETURN g.name AS zoneName, g.centerLat AS lat, g.centerLon AS lon,
           uniqueSharks, sampleSharks
    """
    with driver.session() as session:
        result = session.run(query)
        markers = []
        for rec in result:
            markers.append(
                {
                    "zoneName": rec["zoneName"],
                    "lat": rec["lat"],
                    "lon": rec["lon"],
                    "uniqueSharksCount": rec["uniqueSharks"],
                    "presentSharks": rec["sampleSharks"],
                }
            )
        return markers
