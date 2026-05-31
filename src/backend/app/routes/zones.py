from fastapi import APIRouter, HTTPException, Query

from src.backend.app.database.connection import driver

router = APIRouter(prefix="/api/zones", tags=["Ocean Zones"])


@router.get("/{grid_id}")
def get_zone_analysis(
    grid_id: str,
    start_time: str = Query("2000-01-01 00:00:00", description="Start timestamp filter (YYYY-MM-DD HH:MM:SS)"),
    end_time: str = Query("2030-12-31 23:59:59", description="End timestamp filter (YYYY-MM-DD HH:MM:SS)"),
):
    """
    Returns the details of a specific ocean sector along with a list of all
    unique sharks recorded within this zone inside the specified time range.
    """
    query = """
    MATCH (g:OceanGrid {gridId: $grid_id})
    OPTIONAL MATCH (s:Shark)-[r:PINGED_AT]->(g)
    WHERE r.timestamp >= $start_time AND r.timestamp <= $end_time
    RETURN g.gridId AS gridId, g.centerLat AS centerLat, g.centerLon AS centerLon,
           collect(DISTINCT s { .sharkId, .name, .species, .speciesImage }) AS unique_sharks
    """
    with driver.session() as session:
        result = session.run(query, grid_id=grid_id, start_time=start_time, end_time=end_time)
        record = result.single()

        if not record or record["gridId"] is None:
            raise HTTPException(status_code=404, detail=f"Ocean zone sector '{grid_id}' not found in the database.")

        return {
            "gridId": record["gridId"],
            "centerLat": record["centerLat"],
            "centerLon": record["centerLon"],
            "filterPeriod": {"start": start_time, "end": end_time},
            "totalUniqueSharksDetected": len(record["unique_sharks"]),
            "sharks": record["unique_sharks"],
        }


@router.get("/analysis/clusters")
def get_zone_clusters(
    start_time: str = Query("2000-01-01 00:00:00", description="Start timestamp filter (YYYY-MM-DD HH:MM:SS)"),
    end_time: str = Query("2030-12-31 23:59:59", description="End timestamp filter (YYYY-MM-DD HH:MM:SS)"),
    limit: int = Query(10, description="Number of top hot-spots to return"),
):
    """
    Returns a ranked list of ocean zones with the highest traffic intensity (pings)
    within a specified time range, effectively detecting biological hot-spots/clusters.
    """
    query = """
    MATCH (s:Shark)-[r:PINGED_AT]->(g:OceanGrid)
    WHERE r.timestamp >= $start_time AND r.timestamp <= $end_time
    RETURN g.gridId AS gridId, g.centerLat AS centerLat, g.centerLon AS centerLon,
           count(r) AS totalPings,
           count(DISTINCT s) AS uniqueSharksCount
    ORDER BY totalPings DESC
    LIMIT $limit
    """
    with driver.session() as session:
        result = session.run(query, start_time=start_time, end_time=end_time, limit=limit)

        clusters = []
        for rec in result:
            clusters.append(
                {
                    "gridId": rec["gridId"],
                    "centerLat": rec["centerLat"],
                    "centerLon": rec["centerLon"],
                    "totalPings": rec["totalPings"],
                    "uniqueSharksCount": rec["uniqueSharksCount"],
                }
            )

        return {
            "filterPeriod": {"start": start_time, "end": end_time},
            "requestedLimit": limit,
            "totalClustersReturned": len(clusters),
            "clusters": clusters,
        }


@router.get("/analysis/degree-centrality")
def get_zones_degree_centrality(limit: int = Query(10, description="Number of top ecological corridors to return")):
    """
    Executes a graph centrality analysis (Degree Centrality) to calculate
    the mathematical importance of each OceanGrid node based on incoming telemetry connections.
    """
    query = """
    MATCH (g:OceanGrid)
    OPTIONAL MATCH (s:Shark)-[r:PINGED_AT]->(g)
    WITH g, count(r) AS degreeScore
    RETURN g.gridId AS gridId, g.centerLat AS centerLat, g.centerLon AS centerLon, degreeScore
    ORDER BY degreeScore DESC
    LIMIT $limit
    """
    with driver.session() as session:
        result = session.run(query, limit=limit)

        centrality_report = []
        for rec in result:
            centrality_report.append(
                {
                    "gridId": rec["gridId"],
                    "centerLat": rec["centerLat"],
                    "centerLon": rec["centerLon"],
                    "centralityDegreeScore": rec["degreeScore"],
                }
            )

        return {
            "algorithm": "Degree Centrality (In-Degree Spatial Traversal)",
            "targetLabels": ["Shark", "OceanGrid"],
            "relationshipType": "PINGED_AT",
            "results": centrality_report,
        }
