"""
model/train_attrition_model.py

Trains an attrition-risk classifier on the IBM HR Attrition dataset and produces:
  - model/attrition_model.pkl          (trained model)
  - data/processed/employee_profiles.csv (enriched employee store)

Usage:
    python model/train_attrition_model.py
"""

import json
import random
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = REPO_ROOT / "data" / "raw" / "ibm_hr_attrition.csv"
TAXONOMY_JSON = REPO_ROOT / "data" / "synthetic" / "skills_taxonomy.json"
PROCESSED_CSV = REPO_ROOT / "data" / "processed" / "employee_profiles.csv"
MODEL_PKL = REPO_ROOT / "model" / "attrition_model.pkl"

RISK_THRESHOLD = 0.75  # minimum AUC before escalating to gradient boosting

random.seed(42)
np.random.seed(42)


# ---------------------------------------------------------------------------
# 1. Load & clean
# ---------------------------------------------------------------------------

def load_and_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Drop columns that carry no information
    df = df.drop(columns=["EmployeeCount", "Over18", "StandardHours"], errors="ignore")
    return df


# ---------------------------------------------------------------------------
# 2. Encode for modelling (work on a copy, keep originals in df)
# ---------------------------------------------------------------------------

def build_feature_matrix(df: pd.DataFrame):
    """Return X (numeric feature matrix) and y (binary attrition label)."""
    df_enc = df.copy()

    # Binary target
    df_enc["Attrition"] = (df_enc["Attrition"] == "Yes").astype(int)
    y = df_enc["Attrition"].values

    # Encode all remaining object columns with LabelEncoder
    le = LabelEncoder()
    for col in df_enc.select_dtypes(include="object").columns:
        df_enc[col] = le.fit_transform(df_enc[col].astype(str))

    # Drop identifier columns not useful as features
    drop_cols = ["Attrition", "EmployeeNumber"]
    X = df_enc.drop(columns=[c for c in drop_cols if c in df_enc.columns])

    return X, y


# ---------------------------------------------------------------------------
# 3. Train
# ---------------------------------------------------------------------------

def train(X_train, y_train, X_test, y_test):
    print("Training logistic regression baseline...")
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    auc_lr = roc_auc_score(y_test, lr.predict_proba(X_test)[:, 1])
    print(f"  Logistic Regression AUC: {auc_lr:.4f}")

    if auc_lr >= RISK_THRESHOLD:
        print("  AUC meets threshold — using logistic regression.")
        return lr, auc_lr

    print("  AUC below threshold — escalating to Gradient Boosting...")
    gb = GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, max_depth=4, random_state=42)
    gb.fit(X_train, y_train)
    auc_gb = roc_auc_score(y_test, gb.predict_proba(X_test)[:, 1])
    print(f"  Gradient Boosting AUC: {auc_gb:.4f}")
    return gb, auc_gb


# ---------------------------------------------------------------------------
# 4. Synthetic tasks_assigned counter
# ---------------------------------------------------------------------------

def synthetic_tasks_assigned(df: pd.DataFrame) -> pd.Series:
    """
    Generate a plausible tasks_assigned value (0-5) per employee.
    Employees with OverTime=Yes and high JobInvolvement are more likely
    to have a higher task load — mimicking the "default assignee" pattern.
    """
    overtime_flag = (df["OverTime"] == "Yes").astype(int)
    # JobInvolvement is 1-4; normalise to 0-1
    involvement_norm = (df["JobInvolvement"] - 1) / 3

    # Raw score 0-1 (biased toward overloaded employees)
    raw = (0.5 * overtime_flag + 0.5 * involvement_norm)

    # Map to 0-5 integers with some jitter
    tasks = (raw * 5).round().clip(0, 5).astype(int)

    # Add a small random nudge so the distribution isn't perfectly deterministic
    jitter = pd.Series(
        [random.choice([-1, 0, 0, 1]) for _ in range(len(tasks))],
        index=tasks.index,
    )
    return (tasks + jitter).clip(0, 5).astype(int)


# ---------------------------------------------------------------------------
# 5. Build employee profiles
# ---------------------------------------------------------------------------

def build_profiles(df: pd.DataFrame, model, X: pd.DataFrame, taxonomy: dict) -> pd.DataFrame:
    profiles = df.copy()

    # Attrition risk score from model
    risk_scores = model.predict_proba(X)[:, 1]
    profiles["attrition_risk_score"] = np.round(risk_scores, 4)

    # Skill tags from taxonomy
    profiles["skill_tags"] = profiles["JobRole"].map(
        lambda role: ",".join(taxonomy.get(role, {}).get("skills", []))
    )

    # Synthetic workload counter
    profiles["tasks_assigned"] = synthetic_tasks_assigned(df)

    return profiles


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Sustayn — Attrition Model Training ===\n")

    # Load data
    print(f"Loading dataset from {RAW_CSV}...")
    df = load_and_clean(RAW_CSV)
    print(f"  {len(df)} employee records, {len(df.columns)} columns after cleaning.\n")

    # Build features
    X, y = build_feature_matrix(df)

    # Train/test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # Train model
    model, final_auc = train(X_train, y_train, X_test, y_test)
    print(f"\nFinal model AUC on held-out test set: {final_auc:.4f}\n")

    # Save model
    MODEL_PKL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PKL)
    print(f"Model saved to {MODEL_PKL}")

    # Load taxonomy
    with open(TAXONOMY_JSON) as f:
        taxonomy = json.load(f)

    # Build employee profiles (use full X, not just test split)
    profiles = build_profiles(df, model, X, taxonomy)

    # Save profiles
    PROCESSED_CSV.parent.mkdir(parents=True, exist_ok=True)
    profiles.to_csv(PROCESSED_CSV, index=False)
    print(f"Employee profiles saved to {PROCESSED_CSV}")

    # Quick sanity print
    print(f"\nSample risk scores:")
    print(profiles[["EmployeeNumber", "JobRole", "attrition_risk_score", "tasks_assigned"]].head(10).to_string(index=False))

    print(f"\nAttrition distribution in profiles:")
    print(profiles["Attrition"].value_counts().to_string())

    print(f"\nDone. Final AUC = {final_auc:.4f}")


if __name__ == "__main__":
    main()
