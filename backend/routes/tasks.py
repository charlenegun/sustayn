"""
backend/routes/tasks.py — GET /tasks
"""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/tasks")
def list_tasks(request: Request):
    """Return all synthetic open tasks."""
    return request.app.state.tasks
