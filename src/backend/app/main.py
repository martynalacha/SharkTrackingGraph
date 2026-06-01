import os

from backend.app.routes import admin_sharks
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.backend.app.database.connection import close_driver
from src.backend.app.database.constraints import setup_database_constraints
from src.backend.app.database.seeding import seed_database
from src.backend.app.routes import admin_zones, analytics, clusters, grid, sharks, zones

app = FastAPI(title="SharkTrackingGraph API")

# Register application routing structures
app.include_router(sharks.router)
app.include_router(grid.router)
app.include_router(zones.router)
app.include_router(analytics.router)
app.include_router(admin_sharks.router)
app.include_router(admin_zones.router)
app.include_router(clusters.router)


@app.on_event("startup")
async def on_startup():
    """
    Handles sequential validation, constraint setting, and database seeding on system startup.
    """
    # 1. Setup Neo4j Schema constraints (Indexes and Uniqueness)
    setup_database_constraints()

    # 2. Define operational file paths for the clean data pipeline
    base_dir = os.path.dirname(__file__)
    clean_csv_path = os.path.join(base_dir, "data", "sharks_data_clean.csv")

    # 3. Trigger seeding logic sequentially to ensure database consistency before accepting requests
    if os.path.exists(clean_csv_path):
        # Await completion so the UI doesn't fetch empty graph structures on cold start
        await seed_database(clean_csv_path)
    else:
        # Log a structural warning if the configuration pipeline is broken
        import logging

        logger = logging.getLogger("uvicorn.error")
        logger.warning(f"Startup data binding aborted: Clean data file missing at {clean_csv_path}")


@app.on_event("shutdown")
def on_shutdown():
    """
    Ensures safe termination of database driver connection pools.
    """
    close_driver()


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "database": "connected"}


# Serwowanie frontendu
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")

app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")


@app.get("/")
def serve_frontend():
    index_path = os.path.join(frontend_dir, "index.html")
    return FileResponse(index_path)
