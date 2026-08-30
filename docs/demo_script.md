# Sustayn Demo Script
### Target: ~3 minutes

---

## Step 1 — Set up the problem (20 seconds)

> "Managers assign work from memory. The best people become the default pick every time — until they burn out and leave. Replacing them costs half to two times their salary. Gallup estimates this costs U.S. businesses a trillion dollars a year. And a meaningful share of it is preventable — it's not compensation, it's invisible over-allocation."

---

## Step 2 — Show the dataset (15 seconds)

> "We're using IBM's own HR Attrition dataset — real data, 1,470 employee records, real attrition patterns. We trained a logistic regression model on it. AUC of 0.79. It gives us a risk score per employee. We layer on synthetic skill tags and a workload counter — and that gives us everything we need."

**On screen:** Show `data/raw/ibm_hr_attrition.csv` briefly, then `data/processed/employee_profiles.csv` showing the added columns (`attrition_risk_score`, `skill_tags`, `tasks_assigned`).

---

## Step 3 — Run the matcher on tasks (60 seconds)

### Task A — standard case (30 sec)
Pick a task like **T002: "Analyse clinical trial data and write summary report"**.

> "Here's a research task that needs data analysis, scientific writing, and statistical modelling. Sustayn ranks the candidates — the top result is a Research Scientist with a 100% skill match, low risk, and plenty of headroom. Straightforward recommendation."

Show the candidate cards — good fit, green risk, low workload.

### Task B — the bypass case (30 sec)
Pick a task where a high-skill-match employee is also high-risk and overloaded. (Pre-identify this task during practice — T001 or T018 may work well.)

> "Now here's the reveal. [Employee X] is the strongest technical fit for this task. But Sustayn is not recommending them."

**Point to the ⚠️ warning banner on screen.**

> "They have a 74% attrition risk score — and they're already at 4 out of 5 tasks. Assigning them would compound an existing risk. So Sustayn recommends [Employee Y] instead — a close second on skills, with more headroom and lower risk. That trade-off is explained right here in plain English."

Read the GPT-4o explanation aloud or show it on screen.

---

## Step 4 — Show the team view (30 seconds)

Navigate to **Team Overview** page.

> "This is the view that managers don't have today. Here's every employee sorted by workload — and their attrition risk colour-coded. Red is elevated. See this cluster at the top? These people have been the default assignee repeatedly. Nobody had visibility into this pattern until now."

**Point to the danger-zone metric** (employees with both elevated risk AND high workload).

> "Three employees are in the danger zone right now — high risk, near capacity. They should not be receiving new tasks."

---

## Step 5 — Close with the number (15 seconds)

> "For a 200-person organisation — $75K average salary, 15% annual voluntary turnover — that's roughly $1.1 million a year in replacement cost. If even 15% of those departures were preventable over-allocation cases, that's $165K a year this tool is built to help avoid. Not by fixing compensation. By making invisible over-allocation visible at the moment the resourcing decision is actually made."

---

## Prep notes

- **Pre-identify the bypass task** before recording. Run `POST /recommendations/{task_id}` for each task ID and find one where `displaced_top_match: true`. This is your Task B.
- **Keep the explanation panel open** for Task B so the GPT-4o text is visible on screen.
- **Practice the transition** from Task A (normal) to Task B (bypass) — the contrast is the demo's key moment.
- Keep the recording under 3 minutes. The numbers are in Step 5 — don't rush past them.
