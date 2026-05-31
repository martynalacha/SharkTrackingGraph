import os

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, HTTPException

from src.backend.app.database.seeding import remap_telemetry_relations

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])


@router.post("/recalibrate")
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
