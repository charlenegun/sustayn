# Sustayn — Build Plan
### IBM AI Builders Challenge: Intelligent Systems for the Future of Work

---

## Overview

**Goal:** Build a working proof-of-concept for *Retention-Aware Resourcing* — an AI assistant that recommends who should take on a new task by balancing skill fit with sustainability (workload + attrition risk).

**Stack:**
- Backend: Python + FastAPI
- Frontend: Python + Streamlit
- ML: scikit-learn (logistic regression → gradient boosting)
- LLM: OpenAI GPT-4o via `openai` SDK
- Data: IBM HR Attrition dataset (real) + synthetic skills/tasks overlays

**Approach:** Five sequential sub-tasks, each with a clear checkpoint. Each sub-task is independently reviewable before moving to the next.

---

## Sub-Tasks

---

### Sub-Task 1 — Repo Scaffolding & File Structure

**Intent:**
Set up the full repository skeleton before any code is written. This establishes the directory layout, base config files, and the development environment. Everything downstream depends on this structure existing.

**Expected Outcomes:**
- All directories and placeholder files exist as per the project plan
- `requirements.txt` lists all confirmed dependencies
- `.env.example` documents the required `OPENAI_API_KEY`
- `.gitignore` excludes all the right files
- `README.md` is updated with the project title and a "work in progress" note
- A Python virtual environment can be created and all packages installed with no errors

**Todo List:**
1. Create the full directory tree: `data/raw/`, `data/synthetic/`, `data/processed/`, `model/`, `backend/routes/`, `backend/tests/`, `frontend/`, `docs/`, `video/`
2. Create `requirements.txt` with: `fastapi`, `uvicorn`, `scikit-learn`, `pandas`, `numpy`, `openai`, `streamlit`, `python-dotenv`, `joblib`, `imbalanced-learn`, `matplotlib`, `seaborn`, `ipykernel`
3. Create `.env.example` with `OPENAI_API_KEY=your-key-here`
4. Create `.gitignore` covering: `venv/`, `__pycache__/`, `.env`, `data/raw/`, `.DS_Store`, `*.ipynb_checkpoints`
5. Create stub files (empty or with a single comment) for: `backend/app.py`, `backend/matching_engine.py`, `backend/explanation_layer.py`, `backend/routes/tasks.py`, `backend/routes/employees.py`, `backend/routes/recommendations.py`, `backend/tests/test_matching_engine.py`, `model/train_attrition_model.py`, `frontend/app.py`, `docs/demo_script.md`, `video/demo_link.md`
6. Update `README.md` with project title, one-line tagline, and a note that the README will be completed in Sub-Task 5

**Relevant Context:**
- `.env` must never be committed — `.gitignore` entry is critical
- `data/raw/` is also gitignored to avoid committing the CSV; the README will document how to obtain it

**Status:** [ ] pending

---

### Sub-Task 2 — Data Pipeline & Attrition Model

**Intent:**
Process the IBM HR Attrition dataset, train an attrition-risk classifier, build the synthetic skills taxonomy and open-tasks dataset, and produce the merged employee profile store. This is the data foundation every other component reads from.

**Expected Outcomes:**
- `data/raw/ibm_hr_attrition.csv` is present (already downloaded from Kaggle)
- `data/synthetic/skills_taxonomy.json` maps all ~15 unique `JobRole` values to 3–5 skill tags each
- `data/synthetic/open_tasks.json` contains 15–20 tasks, each with: `task_id`, `title`, `required_skills` (list), `urgency` (1–3), `effort` (integer, estimated hours), `description`
- `model/train_attrition_model.py` runs end-to-end and saves `model/attrition_model.pkl`
- `data/processed/employee_profiles.csv` contains: original IBM columns + `attrition_risk_score` (0–1 float) + `skill_tags` (comma-separated string) + `tasks_assigned` (synthetic int 0–5)
- Model AUC ≥ 0.75 on held-out test split
- `model/evaluation_notebook.ipynb` documents AUC, confusion matrix, and top feature importances

**Todo List:**
1. Place `ibm_hr_attrition.csv` at `data/raw/ibm_hr_attrition.csv`
2. In `train_attrition_model.py`: load CSV, drop constant columns (`EmployeeCount`, `Over18`, `StandardHours`), encode categoricals with `LabelEncoder` or `pd.get_dummies`, split train/test 80/20 stratified on `Attrition`
3. Train logistic regression baseline; evaluate AUC; if AUC < 0.75 switch to `GradientBoostingClassifier`
4. Extract `.predict_proba()` scores for the full dataset as `attrition_risk_score`
5. Save trained model to `model/attrition_model.pkl` using `joblib.dump`
6. Build `data/synthetic/skills_taxonomy.json`: iterate over all unique `JobRole` values in the dataset and assign 3–5 realistic skill tags per role (e.g. "Sales Executive" → ["negotiation", "CRM", "client communication", "pipeline management"])
7. Build `data/synthetic/open_tasks.json`: 15–20 tasks varied across departments and urgency levels; each task's `required_skills` must reference tags that exist in the taxonomy
8. Merge into `data/processed/employee_profiles.csv`: attach `attrition_risk_score`, attach `skill_tags` via taxonomy lookup on `JobRole`, generate synthetic `tasks_assigned` counter (0–5, weighted by `OverTime` + `JobInvolvement` to make it plausible)
9. Create `model/evaluation_notebook.ipynb` with AUC score, confusion matrix plot, and feature importance bar chart

**Relevant Context:**
- `tasks_assigned` ceiling is **5** — this is the overallocation threshold used in the scoring formula in Sub-Task 3
- Skill tag strings must be consistent across `skills_taxonomy.json` and `open_tasks.json` — they are matched by exact string equality in the matching engine
- Keep `OverTime` and `JobInvolvement` columns in `employee_profiles.csv`; the matching engine uses them as supplementary workload signals

**Status:** [ ] pending

---

### Sub-Task 3 — Matching Engine & FastAPI Backend

**Intent:**
Build the core scoring logic (skill-fit + availability + conditional risk penalty) and expose it through FastAPI REST endpoints. This is the computational heart of the project.

**Expected Outcomes:**
- `backend/matching_engine.py` implements the scoring formula exactly — risk penalty only fires when attrition risk is elevated AND workload is near ceiling
- `backend/explanation_layer.py` calls GPT-4o and returns a plain-English recommendation paragraph, including the "against the top match" case
- FastAPI app starts cleanly with `uvicorn backend.app:app --reload`
- Four working endpoints:
  - `GET /tasks` — returns list of open tasks from `open_tasks.json`
  - `GET /employees` — returns list of employees from `employee_profiles.csv`
  - `POST /recommendations/{task_id}` — returns top-3 ranked candidates with scores + GPT-4o explanation
  - `GET /team-overview` — returns all employees sorted by `tasks_assigned` descending with their `attrition_risk_score`
- Unit tests in `backend/tests/test_matching_engine.py` pass, covering the four risk-penalty boundary cases

**Todo List:**
1. Implement `score(employee, task)` in `matching_engine.py` using this exact formula:
   - `skill_fit_score` = count of matching skills / total required skills (0.0–1.0)
   - `availability_bonus` = `(5 - tasks_assigned) / 5`
   - `risk_penalty` = `attrition_risk_score * 0.4` — but **only** if `attrition_risk_score > 0.6` AND `tasks_assigned >= 4`; otherwise `risk_penalty = 0`
   - `final_score` = `skill_fit_score - risk_penalty + availability_bonus * 0.3`
2. Implement `rank_candidates(task, employees_df)` returning top-N rows sorted by `final_score` descending
3. Implement `generate_explanation(task, ranked_candidates)` in `explanation_layer.py`:
   - Build a structured prompt including task details, top 3 candidates with scores, and a flag if the top-skill-match was displaced
   - Call `openai.chat.completions.create` with model `gpt-4o`
   - Return the explanation string
4. In `backend/app.py`: initialize FastAPI app, load `employee_profiles.csv` and `open_tasks.json` at startup using lifespan context, register all routers
5. Implement `backend/routes/tasks.py` — `GET /tasks`
6. Implement `backend/routes/employees.py` — `GET /employees`
7. Implement `backend/routes/recommendations.py` — `POST /recommendations/{task_id}` (calls matching engine → explanation layer)
8. Add `GET /team-overview` to `backend/routes/employees.py`
9. Write unit tests covering: (a) high risk + high workload → penalty fires, (b) high risk + low workload → no penalty, (c) low risk + high workload → no penalty, (d) zero required skills edge case
10. Verify all endpoints via FastAPI's auto-generated Swagger UI at `http://localhost:8000/docs`

**Relevant Context:**
- The conditional risk penalty is the core defensibility argument — preserve exact semantics: penalty fires on BOTH conditions, never on either alone
- The explanation prompt must explicitly describe the "displaced top-match" scenario so GPT-4o can narrate it — this is the key demo moment
- `OPENAI_API_KEY` is loaded from `.env` via `python-dotenv`; load it in `app.py` at startup

**Status:** [ ] pending

---

### Sub-Task 4 — Streamlit Frontend

**Intent:**
Build the Streamlit dashboard presenting two views: the task recommendation view (pick a task → ranked candidates + reasoning) and the team risk view (who's the default assignee, who's accumulating risk).

**Expected Outcomes:**
- `frontend/app.py` runs cleanly with `streamlit run frontend/app.py`
- **Task View:** dropdown of open tasks → shows top-3 ranked candidates with scores and GPT-4o explanation
- **Team View:** table of all employees sorted by `tasks_assigned` descending, with `attrition_risk_score` colour-coded
- The "displaced top match" scenario is visually prominent when it occurs
- Frontend calls the FastAPI backend at `http://localhost:8000` (configurable)

**Todo List:**
1. In `frontend/app.py`: sidebar with two pages — "Task Recommendations" and "Team Overview"
2. Task Recommendations page:
   - Fetch `GET /tasks` on load; populate a `st.selectbox`
   - On task select, call `POST /recommendations/{task_id}`; display top-3 candidates as `st.columns` cards showing: employee name (use `EmployeeNumber` + `JobRole`), skill fit %, risk score, tasks currently assigned
   - Display the GPT-4o explanation in a `st.info` box below the cards
   - If the top-skill-match candidate was displaced (rank by skill ≠ rank by final score), show a `st.warning` banner: "⚠️ Top skill match bypassed — see explanation below"
3. Team Overview page:
   - Fetch `GET /team-overview`
   - Display as `st.dataframe` with a background gradient on `attrition_risk_score` (red ≥ 0.6, yellow 0.4–0.6, green < 0.4)
   - Add a caption explaining the columns
4. Wrap all API calls in `st.spinner` for loading feedback
5. Wrap all API calls in try/except and show `st.error` on failure

**Relevant Context:**
- FastAPI must be running before Streamlit can fetch data — the README How-to-Run section will document this order
- The displaced-top-match scenario is the centrepiece of the demo script — make it visually impossible to miss

**Status:** [ ] pending

---

### Sub-Task 5 — README, Docs & Demo Prep

**Intent:**
Complete all submission deliverables: the public README (required structure per challenge rules), the architecture diagram, the demo script, and the video placeholder.

**Expected Outcomes:**
- `README.md` fully meets the required structure from the challenge: problem statement, solution description, AI approach and architecture, challenge theme, and specific description of how IBM Bob was used
- `docs/architecture_diagram.png` exists and is embedded in the README
- `docs/demo_script.md` follows the 5-step ~3-minute structure from the project plan
- `video/demo_link.md` is a placeholder ready for the hosted video URL
- All submission checklist items are documented in the README

**Todo List:**
1. Write `README.md` with these sections in order:
   - Project Title & Tagline
   - Problem Statement
   - Solution Description
   - Architecture (embed `docs/architecture_diagram.png`)
   - How to Run (venv setup → `uvicorn` → `streamlit run`)
   - Data Sources (call out IBM HR Attrition as real data; skills taxonomy and open tasks as synthetic)
   - AI Approach (scoring formula, model choice and AUC, LLM role in explanation layer)
   - How IBM Bob Was Used (specific: scaffolded file structure, generated API layer, assisted matching-engine logic, iterated explanation-generation prompt, debugging integration)
   - Challenge Theme: Wildcard — Intelligent Systems for the Future of Work
   - Known Caveats (attrition model is illustrative; skills/workload data are synthetic)
   - License (MIT)
2. Create `docs/architecture_diagram.png` — draw the pipeline (IBM CSV → model → profiles → matching engine → explanation layer → FastAPI → Streamlit); export as PNG
3. Write `docs/demo_script.md` following the 5-step demo structure: problem setup (20s), show dataset (15s), run matcher on 2–3 tasks including the "bypass" reveal (60s), show team view (30s), close with ROI number (15s)
4. Create `video/demo_link.md` as a placeholder with a note to update after recording
5. Add a `LICENSE` file (MIT)
6. Review the full submission checklist and verify each item is addressed

**Relevant Context:**
- The "How IBM Bob was used" section requires concrete specifics — vague claims will be marked down by judges
- Section 10 of the original project plan is the canonical submission checklist — treat it as the definition of done

**Status:** [ ] pending

---

## Build Order

Each sub-task must be complete and verified before starting the next.

```
Sub-Task 1 — Scaffolding
    └── Sub-Task 2 — Data + Model
            └── Sub-Task 3 — Backend + Matching Engine
                    └── Sub-Task 4 — Streamlit Frontend
                            └── Sub-Task 5 — README + Docs
```

---

## Key Design Decisions (locked)

| Decision | Choice | Reason |
|---|---|---|
| Frontend | Streamlit | Faster build, stays in Python, lower timeline risk |
| Backend | FastAPI | Async, auto-OpenAPI docs, pairs well with Streamlit |
| ML baseline | Logistic Regression | Interpretable, fast; upgrade to GBM if AUC < 0.75 |
| LLM | GPT-4o via openai SDK | Best reasoning quality for the explanation layer |
| Risk penalty | Conditional only | Fires only on elevated risk AND high workload — core defensibility |
| Risk threshold | attrition_risk_score > 0.6 | Reasonable "elevated" cutoff for logistic regression output |
| Overallocation ceiling | tasks_assigned >= 4 of 5 | Simple, explainable threshold for the demo |

---

## Known Caveats (state these in README and demo)

- Attrition model is trained on IBM's illustrative/synthetic dataset — proof-of-concept methodology, not a validated production model
- Skills and workload data are synthetic overlays, not real — this is a deliberate, transparent design choice
- The scoring formula's biggest defensibility risk is a judge asking "isn't this just weighted sorting?" — the conditional risk-penalty logic is the answer; have it ready to explain clearly
