"""
backend/routes/recommendations.py — GET /recommendations/{task_id}
"""

from fastapi import APIRouter, HTTPException, Request

from backend.explanation_layer import generate_explanation
from backend.matching_engine import rank_candidates

router = APIRouter()


@router.get("/recommendations/{task_id}")
def get_recommendations(task_id: str, request: Request):
    """
    Return ranked top-3 candidates for a given task, with a Claude Haiku explanation.
    """
    tasks = request.app.state.tasks
    employees_df = request.app.state.employees

    # Find the task
    task = next((t for t in tasks if t["task_id"] == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    candidates = rank_candidates(task, employees_df, top_n=3)
    explanation = generate_explanation(task, candidates)

    return {
        "task": task,
        "candidates": candidates,
        "explanation": explanation,
        "displaced_top_match": (
            bool(candidates) and candidates[0]["skill_rank"] != 1
        ),
    }
