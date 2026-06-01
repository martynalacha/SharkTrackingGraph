from fastapi import APIRouter, Query

from src.backend.app.database.connection import driver

router = APIRouter(prefix="/api/zones/analysis/clusters", tags=["Zone Clusters"])


@router.get("")
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
