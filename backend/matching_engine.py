"""
backend/matching_engine.py

Scoring formula (from project plan Section 5):

    final_score = skill_fit_score
                  - risk_penalty          # only if risk > 0.6 AND tasks_assigned >= 4
                  + availability_bonus * 0.3

Thresholds (locked in plan):
    - Risk elevated:        attrition_risk_score > 0.6
    - Overallocation floor: tasks_assigned >= 4
    - Workload ceiling:     5 tasks
"""

from __future__ import annotations

from typing import Any

import pandas as pd

RISK_THRESHOLD = 0.6
OVERALLOCATION_FLOOR = 4
WORKLOAD_CEILING = 5
AVAILABILITY_WEIGHT = 0.3
RISK_PENALTY_FACTOR = 0.4


def _skill_fit(employee_skills: list[str], required_skills: list[str]) -> float:
    """Fraction of required skills the employee possesses (0.0 – 1.0)."""
    if not required_skills:
        return 1.0  # no requirements = any employee is a perfect match
    matches = sum(1 for s in required_skills if s in employee_skills)
    return matches / len(required_skills)


def _availability_bonus(tasks_assigned: int) -> float:
    """Headroom fraction: (ceiling - assigned) / ceiling."""
    return max(0.0, (WORKLOAD_CEILING - tasks_assigned) / WORKLOAD_CEILING)


def _risk_penalty(attrition_risk: float, tasks_assigned: int) -> float:
    """
    Penalty fires ONLY when employee is BOTH elevated-risk AND near workload ceiling.
    A high-risk employee with spare capacity is NOT penalised.
    """
    if attrition_risk > RISK_THRESHOLD and tasks_assigned >= OVERALLOCATION_FLOOR:
        return attrition_risk * RISK_PENALTY_FACTOR
    return 0.0


def score(employee: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    """
    Compute the composite score for one (employee, task) pair.
    Returns a dict with all score components for transparency.
    """
    emp_skills = [s.strip() for s in str(employee.get("skill_tags", "")).split(",") if s.strip()]
    required = task.get("required_skills", [])
    risk = float(employee.get("attrition_risk_score", 0))
    assigned = int(employee.get("tasks_assigned", 0))

    sfit = _skill_fit(emp_skills, required)
    avail = _availability_bonus(assigned)
    penalty = _risk_penalty(risk, assigned)
    final = sfit - penalty + avail * AVAILABILITY_WEIGHT

    return {
        "skill_fit_score": round(sfit, 4),
        "availability_bonus": round(avail, 4),
        "risk_penalty": round(penalty, 4),
        "final_score": round(final, 4),
    }


def rank_candidates(task: dict[str, Any], employees_df: pd.DataFrame, top_n: int = 3) -> list[dict[str, Any]]:
    """
    Rank all employees for a given task and return the top N.

    Also computes `skill_rank` (rank by skill-fit alone) so the frontend
    can detect when the top-skill-match was displaced by the penalty.
    """
    results = []
    for _, row in employees_df.iterrows():
        emp = row.to_dict()
        scores = score(emp, task)
        results.append({
            "EmployeeNumber": emp.get("EmployeeNumber"),
            "JobRole": emp.get("JobRole"),
            "Department": emp.get("Department"),
            "attrition_risk_score": emp.get("attrition_risk_score"),
            "tasks_assigned": emp.get("tasks_assigned"),
            "skill_tags": emp.get("skill_tags", ""),
            **scores,
        })

    # Sort by final_score descending
    results.sort(key=lambda x: x["final_score"], reverse=True)
    for i, r in enumerate(results):
        r["final_rank"] = i + 1

    # Also compute skill-only ranking
    results_by_skill = sorted(results, key=lambda x: x["skill_fit_score"], reverse=True)
    skill_rank_map = {r["EmployeeNumber"]: i + 1 for i, r in enumerate(results_by_skill)}
    for r in results:
        r["skill_rank"] = skill_rank_map[r["EmployeeNumber"]]

    return results[:top_n]
