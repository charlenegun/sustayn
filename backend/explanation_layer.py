"""
backend/explanation_layer.py

Generates a plain-English recommendation paragraph using Claude Haiku
via Amazon Bedrock, authenticated with a long-term bearer token
(AWS_BEARER_TOKEN_BEDROCK env variable).

Falls back to a rule-based explanation if the token is missing or the
call fails — so the app never returns a 500 to the frontend.
"""

from __future__ import annotations

import json
import os

import requests

BEDROCK_REGION = os.environ.get("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

def _bedrock_endpoint() -> str:
    return (
        f"https://bedrock-runtime.{BEDROCK_REGION}.amazonaws.com"
        f"/model/{BEDROCK_MODEL_ID}/invoke"
    )


# ---------------------------------------------------------------------------
# Prompt builder (shared by LLM and fallback paths)
# ---------------------------------------------------------------------------

def _build_prompt(task: dict, candidates: list[dict]) -> tuple[str, bool, dict | None]:
    """
    Returns (prompt_text, displaced, top_skill_candidate).
    displaced = True when the top-skill-match is not the final recommendation.
    """
    top_by_final = candidates[0] if candidates else None
    displaced = top_by_final is not None and top_by_final["skill_rank"] != 1

    candidate_lines = []
    for c in candidates:
        line = (
            f"  - Employee #{c['EmployeeNumber']} ({c['JobRole']}, {c['Department']}): "
            f"skill fit {c['skill_fit_score']:.0%}, "
            f"attrition risk {c['attrition_risk_score']:.0%}, "
            f"tasks currently assigned {c['tasks_assigned']}/5, "
            f"final score {c['final_score']:.3f}"
            + (" [RECOMMENDED]" if c["final_rank"] == 1 else "")
        )
        candidate_lines.append(line)

    top_skill = next((c for c in candidates if c["skill_rank"] == 1), None) if displaced else None

    displacement_note = ""
    if displaced and top_skill:
        displacement_note = (
            f"\nIMPORTANT: Employee #{top_skill['EmployeeNumber']} ({top_skill['JobRole']}) "
            f"was the strongest skill match (skill fit {top_skill['skill_fit_score']:.0%}) "
            f"but was NOT recommended because they have an elevated attrition risk "
            f"({top_skill['attrition_risk_score']:.0%}) AND are near their workload ceiling "
            f"({top_skill['tasks_assigned']}/5 tasks assigned). "
            f"Assigning them would compound an existing risk. "
            f"Explain this trade-off clearly in your recommendation."
        )

    prompt = f"""You are an AI resourcing assistant helping a manager decide who should take on a new task.

Task: {task['title']}
Description: {task.get('description', '')}
Required skills: {', '.join(task.get('required_skills', []))}
Urgency: {task.get('urgency', 'N/A')}/3  |  Estimated effort: {task.get('effort', 'N/A')} hours
{displacement_note}

Top candidates (ranked by composite score):
{chr(10).join(candidate_lines)}

Write a concise 3–5 sentence recommendation for the manager. Be direct. Name the recommended employee \
by their role and number. If a top skill match was bypassed due to risk and workload, explain that trade-off \
clearly and empathetically. Do not use bullet points — write flowing prose."""

    return prompt, displaced, top_skill


# ---------------------------------------------------------------------------
# Rule-based fallback (no LLM required)
# ---------------------------------------------------------------------------

def _fallback_explanation(task: dict, candidates: list[dict], displaced: bool, top_skill: dict | None) -> str:
    """
    Deterministic plain-English explanation — used when the bearer token is
    missing or the Bedrock call fails for any reason.
    """
    if not candidates:
        return "No suitable candidates found for this task."

    rec = candidates[0]
    lines = [
        f"Based on skill fit, availability, and attrition risk, "
        f"Employee #{rec['EmployeeNumber']} ({rec['JobRole']}, {rec['Department']}) "
        f"is the recommended assignee for \"{task['title']}\". "
        f"They match {rec['skill_fit_score']:.0%} of the required skills, "
        f"have {5 - rec['tasks_assigned']} task slot(s) remaining, "
        f"and carry a {rec['attrition_risk_score']:.0%} attrition risk score."
    ]

    if displaced and top_skill:
        lines.append(
            f" Employee #{top_skill['EmployeeNumber']} ({top_skill['JobRole']}) "
            f"was the strongest technical fit ({top_skill['skill_fit_score']:.0%} skill match) "
            f"but was bypassed: their attrition risk ({top_skill['attrition_risk_score']:.0%}) "
            f"is elevated and they are already near their workload ceiling "
            f"({top_skill['tasks_assigned']}/5 tasks). Assigning them would compound that risk."
        )

    if len(candidates) > 1:
        runner_up = candidates[1]
        lines.append(
            f" The next-best option is Employee #{runner_up['EmployeeNumber']} "
            f"({runner_up['JobRole']}) with a final score of {runner_up['final_score']:.3f}."
        )

    lines.append(" (Note: AI explanation unavailable — AWS_BEARER_TOKEN_BEDROCK not configured.)")
    return "".join(lines)


# ---------------------------------------------------------------------------
# Bedrock call via bearer token
# ---------------------------------------------------------------------------

def _call_bedrock(prompt: str) -> str:
    """
    POST to Amazon Bedrock using a long-term bearer token for auth.
    Raises on any HTTP or parsing error.
    """
    token = os.environ["AWS_BEARER_TOKEN_BEDROCK"]

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "temperature": 0.4,
        "messages": [{"role": "user", "content": prompt}],
    }

    response = requests.post(
        _bedrock_endpoint(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    response.raise_for_status()
    result = response.json()
    return result["content"][0]["text"].strip()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_explanation(task: dict, candidates: list[dict]) -> str:
    """
    Return a plain-English recommendation paragraph.

    Tries Claude Haiku via AWS Bedrock bearer token first.
    Falls back to a rule-based explanation if the token is missing
    or the Bedrock call fails for any reason.
    """
    prompt, displaced, top_skill = _build_prompt(task, candidates)

    if os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        try:
            return _call_bedrock(prompt)
        except Exception as exc:
            print(f"[explanation_layer] Bedrock call failed ({type(exc).__name__}: {exc}). Using fallback.")

    return _fallback_explanation(task, candidates, displaced, top_skill)
