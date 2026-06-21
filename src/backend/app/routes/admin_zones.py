from fastapi import APIRouter, Depends, HTTPException, status

from src.backend.app.database.connection import driver
from src.backend.app.dependencies.auth import verify_admin_credentials
from src.backend.app.schemas.common import DetailResponse
from src.backend.app.schemas.grid import OceanGridCreate, OceanGridResponse, OceanGridUpdate

router = APIRouter(prefix="/api/admin/zones", tags=["Admin Zone Management"], dependencies=[Depends(verify_admin_credentials)])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=OceanGridResponse)
async def create_ocean_zone(zone: OceanGridCreate):
    """
    Defines a new ocean sector node (OceanGrid) in the database spatial system.
    """
    query = """
    CREATE (g:OceanGrid {
        gridId: $gridId,
        name: $gridId,
        centerLat: toFloat($centerLat),
        centerLon: toFloat($centerLon)
    })
    RETURN g {.*} AS zone_data
    """
    async with driver.session() as session:
        try:
            result = await session.run(query, **zone.dict())
            record = await result.single()
            return record["zone_data"]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.put("/{grid_id}", response_model=OceanGridResponse)
async def update_ocean_zone(grid_id: str, zone_data: OceanGridUpdate):
    """
    Updates the coordinates of an existing OceanGrid node. Pola nieprzekazane
    w body (None) zostają bez zmian — nie są zerowane.
    """
    query = """
    MATCH (g:OceanGrid {gridId: $grid_id})
    SET g.centerLat = coalesce(toFloat($centerLat), g.centerLat),
        g.centerLon = coalesce(toFloat($centerLon), g.centerLon)
    RETURN g {.*} AS zone_data
    """
    async with driver.session() as session:
        result = await session.run(query, grid_id=grid_id, centerLat=zone_data.centerLat, centerLon=zone_data.centerLon)
        record = await result.single()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"OceanGrid node with ID '{grid_id}' not found.")
        return record["zone_data"]


@router.delete("/{grid_id}", status_code=status.HTTP_200_OK, response_model=DetailResponse)
async def delete_ocean_zone(grid_id: str):
    """
    Removes an OceanGrid node. Any PINGED_AT relations pointing at this zone are
    first re-pointed to the nearest remaining OceanGrid node (by geodesic distance),
    preserving the original timestamp/lat/lon of every ping, so telemetry is never
    silently lost just because its zone got deleted. Refuses to delete the last
    remaining zone in the database, since there would be nowhere to move pings to.
    """
    check_other_zones_query = """
    MATCH (g:OceanGrid {gridId: $grid_id})
    MATCH (other:OceanGrid) WHERE other.gridId <> $grid_id
    RETURN count(other) AS otherZoneCount
    """

    reassign_pings_query = """
    MATCH (target:OceanGrid {gridId: $grid_id})
    MATCH (s:Shark)-[r:PINGED_AT]->(target)
    MATCH (other:OceanGrid) WHERE other.gridId <> $grid_id
    WITH s, r, target, other,
         point({latitude: target.centerLat, longitude: target.centerLon}) AS targetPoint,
         point({latitude: other.centerLat, longitude: other.centerLon}) AS otherPoint
    WITH s, r, other, point.distance(targetPoint, otherPoint) AS distanceMeters
    ORDER BY distanceMeters ASC
    WITH s, r, collect(other)[0] AS nearestZone
    CREATE (s)-[newR:PINGED_AT {
        timestamp: r.timestamp,
        lat: r.lat,
        lon: r.lon
    }]->(nearestZone)
    DELETE r
    """

    delete_zone_query = """
    MATCH (g:OceanGrid {gridId: $grid_id})
    DETACH DELETE g
    RETURN count(g) AS deleted_count
    """

    async with driver.session() as session:
        exists_result = await session.run("MATCH (g:OceanGrid {gridId: $grid_id}) RETURN count(g) AS c", grid_id=grid_id)
        exists_record = await exists_result.single()
        if not exists_record or exists_record["c"] == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"OceanGrid node with ID '{grid_id}' not found.")

        other_result = await session.run(check_other_zones_query, grid_id=grid_id)
        other_record = await other_result.single()
        if not other_record or other_record["otherZoneCount"] == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last remaining zone — its telemetry would have nowhere to go.",
            )

        await session.run(reassign_pings_query, grid_id=grid_id)

        result = await session.run(delete_zone_query, grid_id=grid_id)
        record = await result.single()
        if record["deleted_count"] == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"OceanGrid node with ID '{grid_id}' not found.")
        return {"detail": f"OceanGrid zone '{grid_id}' deleted; its telemetry was reassigned to the nearest remaining zone."}
