import os

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from src.backend.app.database.connection import driver
from src.backend.app.database.seeding import remap_telemetry_relations
from src.backend.app.dependencies.auth import verify_admin_credentials
from src.backend.app.schemas.common import RecalibrationResponse, TelemetryDateRangeResponse

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])


@router.post(
    "/recalibrate",
    response_model=RecalibrationResponse,
    dependencies=[Depends(verify_admin_credentials)],
)
async def trigger_recalibration(background_tasks: BackgroundTasks):
    """
    Admin-only endpoint to trigger dynamic spatial re-mapping
    whenever the OceanGrid architecture is modified.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    clean_csv_path = os.path.join(base_dir, "data", "sharks_data_clean.csv")

    if not os.path.exists(clean_csv_path):
        raise HTTPException(status_code=404, detail="Cleaned source telemetry file missing. Cannot recalibrate.")

    # Read the historical data from file to match against new database state
    df = pd.read_csv(clean_csv_path)

    # Execute the heavy query in a background task to prevent blocking the REST API response
    background_tasks.add_task(remap_telemetry_relations, df)

    return {"status": "processing", "message": "Spatial relationship recalibration started in background."}


@router.get("/telemetry/date-range", response_model=TelemetryDateRangeResponse)
async def get_telemetry_date_range():
    """Returns the global min and max timestamp across all PINGED_AT relations."""
    query = """
    MATCH ()-[r:PINGED_AT]->()
    RETURN min(r.timestamp) AS minDate, max(r.timestamp) AS maxDate
    """
    async with driver.session() as session:
        result = await session.run(query)
        record = await result.single()

        if not record:
            return {"minDate": None, "maxDate": None}

        return {"minDate": record["minDate"], "maxDate": record["maxDate"]}
