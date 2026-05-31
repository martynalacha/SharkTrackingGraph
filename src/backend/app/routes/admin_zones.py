from fastapi import APIRouter, Depends, HTTPException, status

from src.backend.app.database.connection import driver
from src.backend.app.dependencies.auth import verify_admin_credentials
from src.backend.app.schemas.grid import OceanGridCreate, OceanGridResponse

router = APIRouter(
    prefix="/api/admin/zones", tags=["Admin Zone Management"], dependencies=[Depends(verify_admin_credentials)]
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=OceanGridResponse)
def create_ocean_zone(zone: OceanGridCreate):
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
    with driver.session() as session:
        try:
            result = session.run(query, **zone.dict())
            return result.single()["zone_data"]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.put("/{grid_id}", response_model=OceanGridResponse)
def update_ocean_zone(grid_id: str, zone_data: OceanGridCreate):
    """
    Updates the coordinates or properties of an existing OceanGrid node.
    """
    query = """
    MATCH (g:OceanGrid {gridId: $grid_id})
    SET g.centerLat = toFloat($centerLat),
        g.centerLon = toFloat($centerLon)
    RETURN g {.*} AS zone_data
    """
    with driver.session() as session:
        result = session.run(query, grid_id=grid_id, centerLat=zone_data.centerLat, centerLon=zone_data.centerLon)
        record = result.single()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"OceanGrid node with ID '{grid_id}' not found."
            )
        return record["zone_data"]


@router.delete("/{grid_id}", status_code=status.HTTP_200_OK)
def delete_ocean_zone(grid_id: str):
    """
    Performs a cascading DETACH DELETE to safely remove an OceanGrid node and its topology edges.
    """
    query = """
    MATCH (g:OceanGrid {gridId: $grid_id})
    DETACH DELETE g
    RETURN count(g) AS deleted_count
    """
    with driver.session() as session:
        result = session.run(query, grid_id=grid_id)
        record = result.single()
        if record["deleted_count"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"OceanGrid node with ID '{grid_id}' not found."
            )
        return {"detail": f"OceanGrid zone '{grid_id}' and all associated path edges successfully deleted."}
