import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.backend.app.database.connection import driver
from src.backend.app.database.seeding import attach_pings_to_grid
from src.backend.app.dependencies.auth import verify_admin_credentials
from src.backend.app.schemas.common import DetailResponse, TelemetryImportResponse
from src.backend.app.schemas.shark import SharkCreate, SharkResponse, SharkUpdate
from src.backend.app.services.wiki_service import WikiService

router = APIRouter(
    prefix="/api/admin/sharks",
    tags=["Admin Shark Management"],
    dependencies=[Depends(verify_admin_credentials)],  # noqa: B008
)


@router.post("/", response_model=SharkResponse, status_code=status.HTTP_201_CREATED)
async def create_new_shark(shark_data: SharkCreate):
    """
    Creates a single new Shark node in the database and dynamically fetches
    its specific species image from Wikipedia without reloading any other data.
    Rejects the request if a Shark with the given sharkId already exists.
    """
    image_url = await WikiService.get_species_image_url(shark_data.species)

    query = """
    CREATE (s:Shark {
        sharkId: $sharkId,
        name: $name,
        gender: $gender,
        species: $species,
        weight: toFloat($weight),
        length: toFloat($length),
        speciesImage: $image_url
    })
    RETURN s.sharkId AS sharkId, s.name AS name, s.gender AS gender,
           s.species AS species, s.weight AS weight, s.length AS length,
           s.speciesImage AS speciesImage
    """

    async with driver.session() as session:
        try:
            result = await session.run(
                query,
                sharkId=shark_data.sharkId,
                name=shark_data.name,
                gender=shark_data.gender,
                species=shark_data.species,
                weight=shark_data.weight,
                length=shark_data.length,
                image_url=image_url,
            )
            record = await result.single()
            return dict(record)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.put("/{shark_id}", response_model=SharkResponse)
async def update_shark_profile(shark_id: str, shark_data: SharkUpdate):
    """
    Updates the structural profile parameters of an existing Shark node by its sharkId.
    Pola nieprzekazane w body (None) zostają bez zmian — nie są zerowane.
    """
    query = """
    MATCH (s:Shark {sharkId: $shark_id})
    SET s.name = coalesce($name, s.name),
        s.species = coalesce($species, s.species),
        s.gender = coalesce($gender, s.gender),
        s.length = coalesce(toFloat($length), s.length),
        s.weight = coalesce(toFloat($weight), s.weight)
    RETURN s.sharkId AS sharkId, s.name AS name, s.gender AS gender,
           s.species AS species, s.weight AS weight, s.length AS length,
           s.speciesImage AS speciesImage
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            shark_id=shark_id,
            name=shark_data.name,
            species=shark_data.species,
            gender=shark_data.gender,
            length=shark_data.length,
            weight=shark_data.weight,
        )
        record = await result.single()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Shark node with ID '{shark_id}' not found."
            )
        return dict(record)


@router.delete("/{shark_id}", status_code=status.HTTP_200_OK, response_model=DetailResponse)
async def delete_shark_profile(shark_id: str):
    """
    Performs a cascading DETACH DELETE operation to purge a Shark node
    and all its associated telemetry relations.
    """
    query = """
    MATCH (s:Shark {sharkId: $shark_id})
    DETACH DELETE s
    RETURN count(s) AS deleted_count
    """
    async with driver.session() as session:
        result = await session.run(query, shark_id=shark_id)
        record = await result.single()
        if record["deleted_count"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Shark node with ID '{shark_id}' not found."
            )
        return {"detail": f"Shark '{shark_id}' and all connected topology edges successfully deleted."}


@router.post("/import/telemetry", response_model=TelemetryImportResponse)
async def import_telemetry_csv(file: UploadFile = File(...)):  # noqa: B008
    """
    Ingests raw telemetry data from an uploaded CSV file, resolving spatial references
    and binding Shark nodes directly to the nearest OceanGrid nodes via PINGED_AT relations.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file extension. Only CSV allowed.")

    try:
        df = pd.read_csv(file.file)

        required_cols = {"sharkId", "datetime", "lat", "lon"}
        if not required_cols.issubset(df.columns):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"CSV must contain headers: {required_cols}"
            )

        df = df.fillna("")

        pings_payload = []
        for _, row in df.iterrows():
            pings_payload.append(
                {
                    "sharkId": str(row["sharkId"]),
                    "datetime": str(row["datetime"]),
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                }
            )

        total_pings = await attach_pings_to_grid(pings_payload, chunk_size=1000)

        return {
            "status": "Success",
            "message": "Telemetry matrix integrated successfully.",
            "recordsProcessed": total_pings,
            "relationsCreated": total_pings,
        }

    except Exception as e:
        # Added 'from e' to resolve the B904 error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal ingestion pipeline error: {str(e)}"
        ) from e
