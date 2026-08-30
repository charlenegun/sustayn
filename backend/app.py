"""
backend/app.py — FastAPI application entrypoint

Run with:
    uvicorn backend.app:app --reload

The built React app (frontend/dist/) is served as static files.
Visit http://localhost:8000 to open the dashboard.
API docs: http://localhost:8000/docs
"""

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.routes.employees import router as employees_router
from backend.routes.recommendations import router as recommendations_router
from backend.routes.tasks import router as tasks_router

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
EMPLOYEES_CSV = REPO_ROOT / "data" / "processed" / "employee_profiles.csv"
TASKS_JSON    = REPO_ROOT / "data" / "synthetic" / "open_tasks.json"
DIST_DIR      = REPO_ROOT / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data once at startup; make it available via app.state."""
    if not EMPLOYEES_CSV.exists():
        raise FileNotFoundError(
            f"Employee profiles not found at {EMPLOYEES_CSV}. "
            "Run: python model/train_attrition_model.py"
        )
    if not TASKS_JSON.exists():
        raise FileNotFoundError(f"Tasks file not found at {TASKS_JSON}")
    app.state.employees = pd.read_csv(EMPLOYEES_CSV)
    with open(TASKS_JSON) as f:
        app.state.tasks = json.load(f)
    yield


app = FastAPI(
    title="Sustayn — Retention-Aware Resourcing API",
    description=(
        "AI-powered resourcing recommendations that balance skill fit with "
        "employee sustainability (workload + attrition risk)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes first (so /docs, /tasks etc. take precedence over static files)
app.include_router(tasks_router)
app.include_router(employees_router)
app.include_router(recommendations_router)

# Serve the built React app from frontend/dist/
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str = ""):
        # Let API routes (/tasks, /employees, /docs, etc.) pass through above.
        # Everything else gets the React index.html (client-side routing).
        index = DIST_DIR / "index.html"
        return FileResponse(index)
