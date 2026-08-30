"""
backend/routes/employees.py — GET /employees, GET /team-overview
"""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/employees")
def list_employees(request: Request):
    """Return all employee profiles."""
    df = request.app.state.employees
    return df.to_dict(orient="records")


@router.get("/team-overview")
def team_overview(request: Request):
    """
    Return employees sorted by tasks_assigned descending.
    Useful for surfacing the 'default assignee' pattern.
    """
    df = request.app.state.employees
    sorted_df = df.sort_values("tasks_assigned", ascending=False)
    cols = [
        "EmployeeNumber", "JobRole", "Department",
        "attrition_risk_score", "tasks_assigned",
        "OverTime", "JobInvolvement",
    ]
    available_cols = [c for c in cols if c in sorted_df.columns]
    return sorted_df[available_cols].to_dict(orient="records")
