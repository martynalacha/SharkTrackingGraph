from fastapi import APIRouter, BackgroundTasks, Depends

from src.backend.app.database.connection import driver
from src.backend.app.database.seeding import (
    get_recalibration_status,
    remap_telemetry_relations,
    set_recalibration_status,
)
from src.backend.app.dependencies.auth import verify_admin_credentials
from src.backend.app.schemas.common import RecalibrationResponse, TelemetryDateRangeResponse

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])


@router.get(
    "/verify",
    dependencies=[Depends(verify_admin_credentials)],
)
async def verify_admin():
    """
    Lightweight credential-check endpoint for the admin login form.
    The verify_admin_credentials dependency raises 401 on bad credentials,
    so reaching this body at all means the supplied Basic Auth was valid.
    """
    return {"status": "ok"}


@router.post(
    "/recalibrate",
    response_model=RecalibrationResponse,
    dependencies=[Depends(verify_admin_credentials)],
)
async def trigger_recalibration(background_tasks: BackgroundTasks):
    """
    Admin-only endpoint to trigger dynamic spatial re-mapping whenever the
    OceanGrid architecture is modified. Always recalibrates against the
    telemetry currently stored in Neo4j — it does not depend on any CSV
    file on disk, so it works the same whether or not a seeding file exists.
    The status flips to "running" synchronously here, before the response is
    sent, so a client polling /recalibrate/status right away never sees a
    stale "done" from a previous run.
    """
    set_recalibration_status("running")
    background_tasks.add_task(remap_telemetry_relations)

    return {"status": "processing", "message": "Spatial relationship recalibration started in background."}


@router.get(
    "/recalibrate/status",
    dependencies=[Depends(verify_admin_credentials)],
)
async def get_recalibrate_status():
    """
    Returns the in-memory status of the most recent recalibration run, so the
    admin panel can poll for completion instead of guessing with a fixed delay.
    """
    return get_recalibration_status()


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
