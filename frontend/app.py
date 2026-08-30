"""
frontend/app.py — Sustayn Streamlit Dashboard

Run with:
    streamlit run frontend/app.py

Requires the FastAPI backend to be running first:
    uvicorn backend.app:app --reload
"""

import os

import pandas as pd
import requests
import streamlit as st

API_BASE = os.environ.get("SUSTAYN_API_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_tasks() -> list[dict]:
    resp = requests.get(f"{API_BASE}/tasks", timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_recommendations(task_id: str) -> dict:
    resp = requests.post(f"{API_BASE}/recommendations/{task_id}", timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_team_overview() -> list[dict]:
    resp = requests.get(f"{API_BASE}/team-overview", timeout=10)
    resp.raise_for_status()
    return resp.json()


def risk_colour(score: float) -> str:
    if score >= 0.6:
        return "🔴"
    elif score >= 0.4:
        return "🟡"
    return "🟢"


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Sustayn — Retention-Aware Resourcing",
    page_icon="🔄",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

st.sidebar.title("Sustayn")
st.sidebar.caption("Retention-Aware Resourcing")
page = st.sidebar.radio(
    "Navigate",
    ["Task Recommendations", "Team Overview"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**How scores work**\n\n"
    "- **Skill fit:** % of required skills matched\n"
    "- **Availability:** headroom (tasks remaining / ceiling of 5)\n"
    "- **Risk penalty:** only applied when attrition risk > 60% AND tasks ≥ 4\n\n"
    "`score = skill_fit − risk_penalty + availability × 0.3`"
)

# ---------------------------------------------------------------------------
# Page: Task Recommendations
# ---------------------------------------------------------------------------

if page == "Task Recommendations":
    st.title("Task Recommendations")
    st.markdown(
        "Select an open task to see which team members Sustayn recommends — "
        "balancing skill fit with workload sustainability."
    )

    with st.spinner("Loading tasks..."):
        try:
            tasks = fetch_tasks()
        except Exception as e:
            st.error(f"Could not reach the API at `{API_BASE}`. Is the backend running?\n\n`{e}`")
            st.stop()

    task_options = {f"[{t['task_id']}] {t['title']}": t for t in tasks}
    selected_label = st.selectbox("Open tasks", list(task_options.keys()))
    selected_task = task_options[selected_label]

    st.markdown(f"**Description:** {selected_task['description']}")
    meta_cols = st.columns(3)
    meta_cols[0].metric("Required skills", ", ".join(selected_task["required_skills"]))
    meta_cols[1].metric("Urgency", f"{selected_task['urgency']}/3")
    meta_cols[2].metric("Effort", f"{selected_task['effort']} hrs")

    st.markdown("---")

    if st.button("Get Recommendations", type="primary"):
        with st.spinner("Ranking candidates and generating explanation..."):
            try:
                result = fetch_recommendations(selected_task["task_id"])
            except Exception as e:
                st.error(f"Recommendation request failed: `{e}`")
                st.stop()

        candidates = result["candidates"]
        explanation = result["explanation"]
        displaced = result.get("displaced_top_match", False)

        # Displacement banner — the key demo moment
        if displaced:
            st.warning(
                "⚠️ **Top skill match bypassed** — the strongest technical fit "
                "was not recommended due to elevated attrition risk combined with "
                "high workload. See explanation below.",
                icon="⚠️",
            )

        # Candidate cards
        cols = st.columns(len(candidates))
        for col, c in zip(cols, candidates):
            with col:
                rank_label = "✅ Recommended" if c["final_rank"] == 1 else f"#{c['final_rank']}"
                border = True if c["final_rank"] == 1 else False
                with st.container(border=border):
                    st.markdown(f"### {rank_label}")
                    st.markdown(f"**Employee #{c['EmployeeNumber']}**")
                    st.markdown(f"*{c['JobRole']}* · {c['Department']}")
                    st.markdown("---")
                    st.metric("Skill fit", f"{c['skill_fit_score']:.0%}")
                    risk_icon = risk_colour(c["attrition_risk_score"])
                    st.metric("Attrition risk", f"{risk_icon} {c['attrition_risk_score']:.0%}")
                    st.metric("Tasks assigned", f"{c['tasks_assigned']}/5")
                    st.metric("Final score", f"{c['final_score']:.3f}")
                    if c["risk_penalty"] > 0:
                        st.caption(f"⚠️ Risk penalty applied: −{c['risk_penalty']:.3f}")
                    if c.get("skill_rank") == 1 and c["final_rank"] != 1:
                        st.caption("🎯 Strongest skill match — bypassed due to risk+workload")

        # GPT-4o explanation
        st.markdown("---")
        st.subheader("Recommendation")
        st.info(explanation)

        # Score breakdown table
        with st.expander("Score breakdown for all candidates"):
            df_display = pd.DataFrame(candidates)[
                ["EmployeeNumber", "JobRole", "skill_fit_score", "availability_bonus",
                 "risk_penalty", "final_score", "attrition_risk_score", "tasks_assigned",
                 "final_rank", "skill_rank"]
            ]
            st.dataframe(df_display, width="stretch")


# ---------------------------------------------------------------------------
# Page: Team Overview
# ---------------------------------------------------------------------------

elif page == "Team Overview":
    st.title("Team Overview")
    st.markdown(
        "Employees sorted by current task load. "
        "Use this view to spot who has become the *default assignee* — "
        "quietly accumulating workload and burnout risk."
    )

    with st.spinner("Loading team data..."):
        try:
            team = fetch_team_overview()
        except Exception as e:
            st.error(f"Could not reach the API at `{API_BASE}`. Is the backend running?\n\n`{e}`")
            st.stop()

    df = pd.DataFrame(team)

    # Summary metrics
    if not df.empty:
        high_risk = int((df["attrition_risk_score"] >= 0.6).sum())
        overloaded = int((df["tasks_assigned"] >= 4).sum())
        danger_zone = int(((df["attrition_risk_score"] >= 0.6) & (df["tasks_assigned"] >= 4)).sum())

        m1, m2, m3 = st.columns(3)
        m1.metric("Employees at elevated attrition risk (≥60%)", high_risk)
        m2.metric("Employees at/near workload ceiling (≥4 tasks)", overloaded)
        m3.metric("🚨 In danger zone (both)", danger_zone, help="These employees should NOT receive new tasks.")

        st.markdown("---")

        # Colour-code the risk score column
        def highlight_risk(val):
            if val >= 0.6:
                return "background-color: #fde8e8; color: #b91c1c"
            elif val >= 0.4:
                return "background-color: #fef9c3; color: #92400e"
            return "background-color: #dcfce7; color: #166534"

        def highlight_tasks(val):
            if val >= 4:
                return "background-color: #fde8e8; color: #b91c1c"
            elif val >= 3:
                return "background-color: #fef9c3; color: #92400e"
            return ""

        styled = (
            df.style
            .map(highlight_risk, subset=["attrition_risk_score"])
            .map(highlight_tasks, subset=["tasks_assigned"])
            .format({"attrition_risk_score": "{:.1%}"})
        )
        st.dataframe(styled, width="stretch", height=600)

        st.caption(
            "**attrition_risk_score**: probability of voluntary departure predicted by the model "
            "(🔴 ≥60% elevated · 🟡 40–60% moderate · 🟢 <40% low). "
            "**tasks_assigned**: synthetic workload counter (ceiling = 5). "
            "Danger zone = elevated risk AND tasks ≥ 4."
        )
