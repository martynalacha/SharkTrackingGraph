from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from src.backend.app.database.connection import driver

router = APIRouter(prefix="/api/zones", tags=["Ocean Zones"])


@router.get("/{grid_id}/bounds")
async def get_zone_time_bounds(grid_id: str):
    """
    Returns the absolute earliest and latest ping timestamps recorded within
    a specific ocean zone or globally for all zones combined.
    """
    if grid_id == "ALL_ZONES":
        # Globalne zapytanie o MIN i MAX ze wszystkich pingów w bazie
        query = """
        OPTIONAL MATCH (:Shark)-[r:PINGED_AT]->(:OceanGrid)
        RETURN "ALL_ZONES" AS gridId,
               min(r.timestamp) AS absolute_start,
               max(r.timestamp) AS absolute_end
        """
    else:
        # Dotychczasowe zapytanie o konkretną strefę
        query = """
        MATCH (g:OceanGrid {gridId: $grid_id})
        OPTIONAL MATCH (:Shark)-[r:PINGED_AT]->(g)
        RETURN g.gridId AS gridId,
               min(r.timestamp) AS absolute_start,
               max(r.timestamp) AS absolute_end
        """

    async with driver.session() as session:
        result = await session.run(query, grid_id=grid_id)
        record = await result.single()

        if not record or (grid_id != "ALL_ZONES" and record["gridId"] is None):
            raise HTTPException(status_code=404, detail="Zone or global bounds data not found.")

        return {
            "gridId": record["gridId"],
            "start": record["absolute_start"] if record["absolute_start"] else "2018-01-01 00:00:00",
            "end": record["absolute_end"] if record["absolute_end"] else "2026-12-31 23:59:00",
        }


@router.get("/{grid_id}")
async def get_zone_analysis(
    grid_id: str,
    start_time: Annotated[datetime, Query(description="Start timestamp filter (ISO 8601)")] = datetime(2000, 1, 1, 0, 0, 0),
    end_time: Annotated[datetime, Query(description="End timestamp filter (ISO 8601)")] = datetime(2030, 12, 31, 23, 59, 59),
):
    """
    Returns the details of a specific ocean sector along with a list of all
    unique sharks recorded within this zone inside the specified time range.
    """
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

    query = """
    MATCH (g:OceanGrid {gridId: $grid_id})
    OPTIONAL MATCH (s:Shark)-[r:PINGED_AT]->(g)
    WHERE r.timestamp >= $start_time AND r.timestamp <= $end_time
    RETURN g.gridId AS gridId, g.centerLat AS centerLat, g.centerLon AS centerLon,
           collect(DISTINCT s { .sharkId, .name, .species, .speciesImage }) AS unique_sharks
    """
    async with driver.session() as session:
        result = await session.run(query, grid_id=grid_id, start_time=start_str, end_time=end_str)
        record = await result.single()

        if not record or record["gridId"] is None:
            raise HTTPException(status_code=404, detail=f"Ocean zone sector '{grid_id}' not found in the database.")

        return {
            "gridId": record["gridId"],
            "centerLat": record["centerLat"],
            "centerLon": record["centerLon"],
            "filterPeriod": {"start": start_str, "end": end_str},
            "totalUniqueSharksDetected": len(record["unique_sharks"]),
            "sharks": record["unique_sharks"],
        }


# @router.get("/{grid_id}")
# async def get_zone_analysis(
#     grid_id: str,
#     start_time: str = Query("2000-01-01 00:00:00", description="Start timestamp filter (YYYY-MM-DD HH:MM:SS)"),
#     end_time: str = Query("2030-12-31 23:59:59", description="End timestamp filter (YYYY-MM-DD HH:MM:SS)"),
# ):
#     """
#     Returns the details of a specific ocean sector along with a list of all
#     unique sharks recorded within this zone inside the specified time range.
#     It also returns the absolute min and max ping timestamps for calendar limits.
#     """
#     query = """
#     MATCH (g:OceanGrid {gridId: $grid_id})

#     # 1. Pobieramy bezwzględne, rzeczywiste ramy czasowe dla tej strefy
#     OPTIONAL MATCH (:Shark)-[all_r:PINGED_AT]->(g)
#     WITH g, min(all_r.timestamp) AS absolute_start, max(all_r.timestamp) AS absolute_end

#     # 2. Wyciągamy rekiny pasujące do filtrów czasowych użytkownika
#     OPTIONAL MATCH (s:Shark)-[r:PINGED_AT]->(g)
#     WHERE r.timestamp >= $start_time AND r.timestamp <= $end_time

#     RETURN g.gridId AS gridId, g.centerLat AS centerLat, g.centerLon AS centerLon,
#            absolute_start, absolute_end,
#            collect(DISTINCT s { .sharkId, .name, .species, .speciesImage }) AS unique_sharks
#     """
#     async with driver.session() as session:
#         result = await session.run(query, grid_id=grid_id, start_time=start_time, end_time=end_time)
#         record = result.single()

#         if not record or record["gridId"] is None:
#             raise HTTPException(status_code=404, detail=f"Ocean zone sector '{grid_id}' not found in the database.")

#         return {
#             "gridId": record["gridId"],
#             "centerLat": record["centerLat"],
#             "centerLon": record["centerLon"],
#             # Rzeczywiste ramy czasowe z bazy (przekazujemy je do zablokowania kalendarzy)
#             "zoneBounds": {
#                 "start": record["absolute_start"] if record["absolute_start"] else "2018-01-01 00:00:00",
#                 "end": record["absolute_end"] if record["absolute_end"] else "2026-12-31 23:59:00",
#             },
#             "filterPeriod": {"start": start_time, "end": end_time},
#             "totalUniqueSharksDetected": len(record["unique_sharks"]),
#             "sharks": record["unique_sharks"],
#         }


@router.get("/analysis/degree-centrality")
async def get_zones_degree_centrality(
    limit: Annotated[int, Query(description="Number of top ecological corridors to return")] = 10,
):
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
    async with driver.session() as session:
        result = await session.run(query, limit=limit)
        records = await result.data()

        centrality_report = []
        for rec in records:
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


@router.get("/{grid_id}/trajectories")
async def get_zone_sharks_trajectories(
    grid_id: str,
    start_time: Annotated[datetime, Query(description="Start timestamp filter (ISO 8601)")] = datetime(2000, 1, 1, 0, 0, 0),
    end_time: Annotated[datetime, Query(description="End timestamp filter (ISO 8601)")] = datetime(2030, 12, 31, 23, 59, 59),
):
    """
    Returns telemetry points for all sharks, but ONLY the PINGED_AT relationships
    that occurred strictly within this specific zone and time range.
    """
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

    query = """
    MATCH (g:OceanGrid {gridId: $grid_id})
    MATCH (s:Shark)-[r:PINGED_AT]->(g)
    WHERE r.timestamp >= $start_time AND r.timestamp <= $end_time
    RETURN s.sharkId AS sharkId, s.name AS name,
           collect({
               lat: r.lat,
               lon: r.lon,
               timestamp: r.timestamp
           }) AS points
    """
    async with driver.session() as session:
        result = await session.run(query, grid_id=grid_id, start_time=start_str, end_time=end_str)
        records = await result.data()
        output = []
        for rec in records:
            sorted_points = sorted(rec["points"], key=lambda x: x["timestamp"])
            output.append({"sharkId": rec["sharkId"], "name": rec["name"], "trajectory": sorted_points})

        return output
