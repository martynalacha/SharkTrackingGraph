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
    Performs a cascading DETACH DELETE to safely remove an OceanGrid node and its topology edges.
    """
    query = """
    MATCH (g:OceanGrid {gridId: $grid_id})
    DETACH DELETE g
    RETURN count(g) AS deleted_count
    """
    async with driver.session() as session:
        result = await session.run(query, grid_id=grid_id)
        record = await result.single()
        if record["deleted_count"] == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"OceanGrid node with ID '{grid_id}' not found.")
        return {"detail": f"OceanGrid zone '{grid_id}' and all associated path edges successfully deleted."}
