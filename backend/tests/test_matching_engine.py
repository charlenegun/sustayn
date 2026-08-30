"""
backend/tests/test_matching_engine.py

Unit tests for the scoring logic in matching_engine.py.
Focus: the conditional risk-penalty boundary cases.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.matching_engine import (
    OVERALLOCATION_FLOOR,
    RISK_PENALTY_FACTOR,
    RISK_THRESHOLD,
    _availability_bonus,
    _risk_penalty,
    _skill_fit,
    rank_candidates,
    score,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_employee(risk: float, assigned: int, skills: str = "negotiation,CRM") -> dict:
    return {
        "EmployeeNumber": 1,
        "JobRole": "Sales Executive",
        "Department": "Sales",
        "attrition_risk_score": risk,
        "tasks_assigned": assigned,
        "skill_tags": skills,
    }


def _make_task(required: list[str] | None = None) -> dict:
    return {
        "task_id": "T001",
        "title": "Test Task",
        "required_skills": required or ["negotiation", "CRM"],
        "urgency": 2,
        "effort": 10,
        "description": "A test task.",
    }


# ---------------------------------------------------------------------------
# _risk_penalty boundary cases (the four quadrants)
# ---------------------------------------------------------------------------

class TestRiskPenalty:
    def test_high_risk_high_workload_fires(self):
        """Penalty MUST fire: elevated risk AND near ceiling."""
        penalty = _risk_penalty(attrition_risk=0.75, tasks_assigned=4)
        assert penalty > 0
        assert penalty == pytest.approx(0.75 * RISK_PENALTY_FACTOR)

    def test_high_risk_low_workload_no_penalty(self):
        """Penalty must NOT fire: high risk but spare capacity."""
        penalty = _risk_penalty(attrition_risk=0.75, tasks_assigned=2)
        assert penalty == 0.0

    def test_low_risk_high_workload_no_penalty(self):
        """Penalty must NOT fire: high workload but low risk."""
        penalty = _risk_penalty(attrition_risk=0.3, tasks_assigned=4)
        assert penalty == 0.0

    def test_exactly_at_threshold_no_penalty(self):
        """Risk exactly at threshold (not above) should NOT trigger penalty."""
        penalty = _risk_penalty(attrition_risk=RISK_THRESHOLD, tasks_assigned=OVERALLOCATION_FLOOR)
        assert penalty == 0.0

    def test_just_above_threshold_fires(self):
        """Risk just above threshold with high workload SHOULD fire."""
        penalty = _risk_penalty(attrition_risk=RISK_THRESHOLD + 0.001, tasks_assigned=OVERALLOCATION_FLOOR)
        assert penalty > 0


# ---------------------------------------------------------------------------
# _skill_fit
# ---------------------------------------------------------------------------

class TestSkillFit:
    def test_perfect_match(self):
        assert _skill_fit(["negotiation", "CRM"], ["negotiation", "CRM"]) == 1.0

    def test_partial_match(self):
        assert _skill_fit(["negotiation", "CRM", "B2B sales"], ["negotiation", "CRM", "prospecting"]) == pytest.approx(2 / 3)

    def test_no_match(self):
        assert _skill_fit(["recruiting"], ["negotiation", "CRM"]) == 0.0

    def test_empty_required_skills(self):
        """Edge case: no required skills → 1.0 (any employee is a perfect match)."""
        assert _skill_fit(["negotiation"], []) == 1.0


# ---------------------------------------------------------------------------
# _availability_bonus
# ---------------------------------------------------------------------------

class TestAvailabilityBonus:
    def test_zero_assigned(self):
        assert _availability_bonus(0) == pytest.approx(1.0)

    def test_at_ceiling(self):
        assert _availability_bonus(5) == pytest.approx(0.0)

    def test_mid_assigned(self):
        assert _availability_bonus(3) == pytest.approx(0.4)


# ---------------------------------------------------------------------------
# score (integration)
# ---------------------------------------------------------------------------

class TestScore:
    def test_high_risk_overloaded_gets_penalised(self):
        emp = _make_employee(risk=0.8, assigned=4)
        task = _make_task()
        result = score(emp, task)
        assert result["risk_penalty"] > 0
        assert result["skill_fit_score"] == 1.0

    def test_high_risk_not_overloaded_no_penalty(self):
        emp = _make_employee(risk=0.8, assigned=1)
        task = _make_task()
        result = score(emp, task)
        assert result["risk_penalty"] == 0.0

    def test_final_score_components_sum_correctly(self):
        emp = _make_employee(risk=0.4, assigned=2)
        task = _make_task()
        result = score(emp, task)
        expected = round(result["skill_fit_score"] - result["risk_penalty"] + result["availability_bonus"] * 0.3, 4)
        assert result["final_score"] == pytest.approx(expected, abs=1e-4)


# ---------------------------------------------------------------------------
# rank_candidates
# ---------------------------------------------------------------------------

class TestRankCandidates:
    def test_returns_top_n(self):
        employees = pd.DataFrame([
            _make_employee(risk=0.2, assigned=1),
            {**_make_employee(risk=0.3, assigned=2), "EmployeeNumber": 2},
            {**_make_employee(risk=0.4, assigned=3), "EmployeeNumber": 3},
            {**_make_employee(risk=0.5, assigned=4), "EmployeeNumber": 4},
        ])
        task = _make_task()
        results = rank_candidates(task, employees, top_n=3)
        assert len(results) == 3

    def test_sorted_by_final_score_descending(self):
        employees = pd.DataFrame([
            _make_employee(risk=0.2, assigned=0),
            {**_make_employee(risk=0.9, assigned=5), "EmployeeNumber": 2},
        ])
        task = _make_task()
        results = rank_candidates(task, employees, top_n=2)
        assert results[0]["final_score"] >= results[1]["final_score"]

    def test_displacement_flag_set_when_top_skill_is_not_top_final(self):
        """
        Employee #1: perfect skill match but high risk + overloaded.
        Employee #2: slightly worse skill match but available and low risk.
        Employee #2 should rank #1 by final score; skill_rank of #2 should be > 1.
        """
        emp1 = {
            "EmployeeNumber": 1, "JobRole": "A", "Department": "X",
            "attrition_risk_score": 0.9, "tasks_assigned": 5,
            "skill_tags": "negotiation,CRM",
        }
        emp2 = {
            "EmployeeNumber": 2, "JobRole": "B", "Department": "X",
            "attrition_risk_score": 0.1, "tasks_assigned": 0,
            "skill_tags": "negotiation",
        }
        employees = pd.DataFrame([emp1, emp2])
        task = _make_task(required=["negotiation", "CRM"])
        results = rank_candidates(task, employees, top_n=2)

        # Recommended employee (#1 by final score) should have skill_rank > 1
        assert results[0]["EmployeeNumber"] == 2  # emp2 wins by final score
        assert results[0]["skill_rank"] == 2       # emp2 is #2 by skill fit
