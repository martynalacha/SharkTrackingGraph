import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.backend.app.database.clean_data import clean_csv_data
from src.backend.app.database.connection import close_driver
from src.backend.app.database.constraints import setup_database_constraints
from src.backend.app.database.seeding import seed_database
from src.backend.app.routes import admin_sharks, admin_zones, analytics, clusters, grid, sharks, zones

logger = logging.getLogger("uviconr.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    logger.info("Initializing database constraints...")
    await setup_database_constraints()

    base_dir = os.path.dirname(__file__)
    raw_csv_path = os.path.join(base_dir, "data", "sharks.csv")
    clean_csv_path = os.path.join(base_dir, "data", "sharks_data_clean.csv")

    if not os.path.exists(clean_csv_path):
        if os.path.exists(raw_csv_path):
            logger.info("Clean data missing. Starting automated cleaning process...")
            try:
                clean_csv_data(raw_csv_path, clean_csv_path)
                logger.info("Cleaning complete.")
            except Exception as e:
                logger.error(f"Failed to clean data: {e}")
        else:
            logger.error(f"No source data found at {raw_csv_path}")

    if os.path.exists(clean_csv_path):
        logger.info("Seeding database...")
        await seed_database(clean_csv_path)
    else:
        logger.warning(f"Data file missing at {clean_csv_path}")

    yield

    # --- SHUTDOWN ---
    logger.info("Closing database driver...")
    await close_driver()


app = FastAPI(title="SharkTrackingGraph API", lifespan=lifespan)

# Register application routing structures
app.include_router(sharks.router)
app.include_router(grid.router)
app.include_router(zones.router)
app.include_router(analytics.router)
app.include_router(admin_sharks.router)
app.include_router(admin_zones.router)
app.include_router(clusters.router)


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "database": "connected"}


frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")

app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")


@app.get("/")
def serve_frontend():
    index_path = os.path.join(frontend_dir, "index.html")
    return FileResponse(index_path)
