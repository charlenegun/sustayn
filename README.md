# Sustayn — Retention-Aware Resourcing
### IBM AI Builders Challenge · Wildcard: Intelligent Systems for the Future of Work

> *Match the work to the person who can do it well — and can afford to.*

---

## Problem Statement

Managers assign work based on memory and availability, not on a systematic view of skill fit or sustainability. The best, most visible performers become the default assignee for every new task — quietly accumulating workload and burnout risk that nobody tracks until they resign.

Replacing an employee costs **50–200% of their annual salary** (Gallup, SHRM). Voluntary turnover costs U.S. businesses an estimated **$1 trillion per year**. A large share of that is preventable — driven by exactly this kind of invisible over-allocation, not compensation.

**The gap:** organisations have skill data (who can do what) and attrition-risk signals (who's likely to leave) sitting in separate systems, and nobody combines them at the moment a resourcing decision is actually made.

---

## Solution

Sustayn is an AI-powered resourcing assistant that recommends who should take on a new task by balancing two signals that are normally considered separately:

1. **Skill fit** — who is best qualified for this work
2. **Sustainability** — who has headroom, and who is already over-allocated and at elevated attrition risk

Instead of a single ranked name, it returns a **reasoned recommendation** — including cases where it deliberately recommends *against* the top skill match because assigning them would compound an existing risk — and a team-level view that surfaces employees who have quietly become the "default assignee" for repeated tasks.

---

## AI Approach & Architecture

![Architecture Diagram](docs/architecture_diagram.svg)

### Scoring Formula

```
score(employee, task) =
    skill_fit_score                          (0–1: % of required skills matched)
    − risk_penalty                           (only if risk > 0.6 AND tasks ≥ 4)
    + availability_bonus × 0.3              (headroom: remaining tasks / ceiling)

where:
    risk_penalty = attrition_risk_score × 0.4
    availability_bonus = (5 − tasks_assigned) / 5
```

The risk penalty only activates when **both** conditions are true: elevated attrition risk **and** high current workload. A high-risk employee with spare capacity is not penalised — the problem is compounding risk onto someone already stretched, not risk in isolation. This conditional logic is the core defensibility argument of the scoring design.

### Model Details

- **Dataset:** [IBM HR Analytics Employee Attrition & Performance](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset) — IBM's illustrative/synthetic HR dataset (1,470 records, 35 features)
- **Model:** Logistic Regression (scikit-learn), trained on 80/20 stratified split
- **Validation:** AUC = 0.7929 on held-out test set; see `model/evaluation_notebook.ipynb` for full evaluation
- **LLM:** Claude Haiku via Amazon Bedrock generates the plain-English recommendation paragraph, including narrating the "bypass" case. Falls back to a rule-based explanation if credentials are not configured.

---

## Data Sources

| File | Type | Description |
|---|---|---|
| `data/raw/ibm_hr_attrition.csv` | **Real data** | IBM HR Attrition dataset from Kaggle — untouched original |
| `data/synthetic/skills_taxonomy.json` | **Synthetic** | Role → skill tags mapping constructed for this demo |
| `data/synthetic/open_tasks.json` | **Synthetic** | 18 open tasks with required skills, urgency, and effort |
| `data/processed/employee_profiles.csv` | **Derived** | IBM dataset + model risk scores + synthetic skills/workload |

The skills taxonomy and open-tasks dataset are synthetic overlays, not real data. This is a deliberate, transparent design choice — the IBM dataset contains no skills field or live workload data. The approach is described clearly rather than implied as real.

---

## How to Run

### Prerequisites

- Python 3.10+
- AWS credentials with Bedrock access (Claude Haiku model enabled in your region)

### Setup

```bash
# Clone the repo
git clone https://github.com/charlenegunawanteguh/sustayn.git
cd sustayn

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure your AWS credentials
cp .env.example .env
# Edit .env and add your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
```

### Train the model (run once)

```bash
# Place ibm_hr_attrition.csv in data/raw/ first
python model/train_attrition_model.py
```

### Start the backend

```bash
uvicorn backend.app:app --reload
# API docs available at http://localhost:8000/docs
```

### Build and serve the frontend

```bash
# Build the React app (run once, or after any frontend changes)
cd frontend_react && npm install && npm run build && cd ..

# The React dashboard is now served by FastAPI at http://localhost:8000
# No separate frontend server needed
```

### Run tests

```bash
pytest backend/tests/test_matching_engine.py -v
```

---

## How IBM Bob Was Used

IBM Bob was used throughout every phase of this build:

1. **Repo scaffolding** — Bob generated the full directory structure, `requirements.txt`, `.env.example`, and all stub files in a single pass
2. **Data pipeline** — Bob wrote `model/train_attrition_model.py`, including the LabelEncoder pipeline, train/test split strategy, AUC evaluation, and the synthetic `tasks_assigned` counter weighted by `OverTime` + `JobInvolvement`
3. **Synthetic data design** — Bob constructed all 9 role → skill-tag mappings in `skills_taxonomy.json` and all 18 tasks in `open_tasks.json`, ensuring consistent tag strings across both files
4. **Matching engine** — Bob implemented the conditional risk-penalty scoring formula, including the critical boundary logic (penalty fires only on elevated risk AND high workload, not either alone), and structured the `rank_candidates` function to expose both `final_rank` and `skill_rank` for displacement detection
5. **API layer** — Bob generated all FastAPI routes, CORS middleware, lifespan data-loading pattern, and the SPA static file serving setup
6. **Unit tests** — Bob wrote 18 tests covering all four risk-penalty boundary quadrants, skill-fit edge cases, and the displacement scenario
7. **Explanation prompt engineering** — Bob designed and iterated the Claude Haiku (AWS Bedrock) prompt in `explanation_layer.py` to explicitly narrate the "bypassed top match" case when it occurs, and added a rule-based fallback so the app never crashes when credentials are unavailable
8. **React frontend** — Bob scaffolded the full React + Vite + Tailwind CSS frontend with three pages (Dashboard, Recommendations, Team Overview), the displaced-top-match warning banner, colour-coded risk/workload indicators, interactive score breakdown, and all API integration
9. **Architecture decisions** — Bob recommended replacing Streamlit with React for competition-quality polish, designed the FastAPI static-file serving pattern so both API and frontend run on one port, and debugged the AWS Bedrock model ID to the correct `us.anthropic.claude-haiku-4-5-20251001-v1:0`
10. **Documentation** — Bob wrote this README, the demo script, and the full build plan

---

## Challenge Theme

**Wildcard Challenge: Intelligent Systems for the Future of Work**
Category: Decision Intelligence / Operations & Productivity

Sustayn addresses the challenge by making invisible over-allocation visible at the exact moment a resourcing decision is made — combining skill fit and attrition-risk signals that are normally kept separate.

---

## Business Case

Worked example for a 200-person organisation (average salary $75K, 15% annual voluntary turnover):

- 30 departures/year × 50% of salary (low estimate) = **~$1.1M/year** in replacement cost
- If even 15% of those departures were preventable over-allocation cases, that's a plausible **~$165K/year** Sustayn could help avoid

These are illustrative, sourced estimates (Gallup, SHRM) — not a guaranteed outcome.

---

## Known Caveats

- **Attrition model is illustrative, not validated.** It is trained on IBM's synthetic/illustrative dataset and should be treated as a proof-of-concept methodology, not a production-grade risk model.
- **Skills and workload data are synthetic overlays.** The IBM dataset contains no skills field or live workload data. These were constructed deliberately and transparently for the demo.
- **Scoring formula is intentionally simple.** The conditional risk-penalty logic is the key design decision — a judge asking "isn't this just weighted sorting?" can be answered by explaining that the penalty only fires on the compound condition, not either factor alone.

---

## Submission Checklist

- [x] Working prototype built primarily with IBM Bob
- [ ] Completed required IBM SkillsBuild learning activity
- [x] Public GitHub repo with README meeting challenge structure
- [ ] Project page submitted on challenge platform
- [ ] Public demo video (max 3 minutes) — see `video/demo_link.md`
- [ ] Submitted by 11:59pm ET on the deadline date

---

## License

MIT — see [LICENSE](LICENSE)
