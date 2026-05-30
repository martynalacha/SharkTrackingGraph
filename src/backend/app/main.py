import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.backend.app.database.connection import close_driver
from src.backend.app.database.constraints import setup_database_constraints

app = FastAPI(title="SharkTrackingGraph API")


@app.on_event("startup")
def on_startup():
    # Automatyczna konfiguracja bazy przy podnoszeniu kontenera
    setup_database_constraints()


@app.on_event("shutdown")
def on_shutdown():
    # Bezpieczne zamykanie połączeń
    close_driver()


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "database": "connected"}


# Serwowanie frontendu
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/")
def serve_frontend():
    index_path = os.path.join(frontend_dir, "index.html")
    return FileResponse(index_path)
