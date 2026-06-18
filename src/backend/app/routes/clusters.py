from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query

from src.backend.app.database.connection import driver

router = APIRouter(prefix="/api/zones/analysis/clusters", tags=["Zone Clusters"])


@router.get("")
async def get_zone_clusters(
    start_time: Annotated[datetime, Query(description="Start timestamp filter (ISO 8601)")] = datetime(2000, 1, 1, 0, 0, 0),
    end_time: Annotated[datetime, Query(description="End timestamp filter (ISO 8601)")] = datetime(2030, 12, 31, 23, 59, 59),
    limit: Annotated[int, Query(description="Number of top hot-spots to return")] = 10,
):
    """
    Returns a ranked list of ocean zones with the highest traffic intensity (pings)
    within a specified time range, effectively detecting biological hot-spots/clusters.
    """
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

    query = """
    MATCH (s:Shark)-[r:PINGED_AT]->(g:OceanGrid)
    WHERE r.timestamp >= $start_time AND r.timestamp <= $end_time
    RETURN g.gridId AS gridId, g.centerLat AS centerLat, g.centerLon AS centerLon,
           count(r) AS totalPings,
           count(DISTINCT s) AS uniqueSharksCount
    ORDER BY totalPings DESC
    LIMIT $limit
    """
    async with driver.session() as session:
        result = await session.run(query, start_time=start_str, end_time=end_str, limit=limit)
        records = await result.data()
        clusters = []
        for rec in records:
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
            "filterPeriod": {"start": start_str, "end": end_str},
            "requestedLimit": limit,
            "totalClustersReturned": len(clusters),
            "clusters": clusters,
        }
