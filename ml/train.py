"""
Train and evaluate ML models for IMAM Lite.

Run from repo root after seeding the database:
    python ml/train.py

Produces:
    ml/models/anomaly_detector.joblib   — IsolationForest on sensor readings
    ml/models/risk_classifier.joblib    — TF-IDF + LogisticRegression on incident text
    ml/models/feature_meta.joblib       — per-asset feature scaling parameters
    ml/models/rul_predictor.joblib      — GradientBoosting RUL regressor (all 100 FD001 engines)
"""
from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    mean_absolute_error,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DB_PATH    = Path(__file__).parent.parent / "data" / "imam_lite.duckdb"
MODELS_DIR = Path(__file__).parent / "models"
CMAPSS_FD001 = Path(__file__).parent.parent / "data" / "cmapss" / "raw" / "train_FD001.txt"
MODELS_DIR.mkdir(exist_ok=True)

_CMAPSS_COLS = ["unit", "cycle", "op1", "op2", "op3"] + [f"s{i}" for i in range(1, 22)]
# Sensors with non-trivial variance in FD001 (constant sensors excluded)
_FD001_FEATURES = ["s2", "s3", "s4", "s7", "s8", "s9", "s11", "s12", "s13", "s14", "s15", "s17", "s20", "s21"]


# ── Helpers ────────────────────────────────────────────────────────────────

def _open_db() -> duckdb.DuckDBPyConnection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. Run: python data/synthetic/seed.py"
        )
    return duckdb.connect(str(DB_PATH), read_only=True)


# ── 1. Anomaly Detection ───────────────────────────────────────────────────

def train_anomaly_detector(con: duckdb.DuckDBPyConnection) -> None:
    print("\n=== Anomaly Detector (IsolationForest) ===")

    df = con.execute("""
        select asset_id, temperature_c, vibration_mms, pressure_bar, is_anomaly_true
        from sensor_readings
        order by asset_id, timestamp
    """).df()

    print(f"Loaded {len(df):,} sensor readings across {df['asset_id'].nunique()} assets")
    print(f"True anomaly rate: {df['is_anomaly_true'].mean():.2%}")

    # Compute per-asset z-scores so the model sees normalised features
    feature_meta = {}
    scaled_rows = []
    for asset_id, group in df.groupby("asset_id"):
        means = group[["temperature_c", "vibration_mms", "pressure_bar"]].mean()
        stds  = group[["temperature_c", "vibration_mms", "pressure_bar"]].std().clip(lower=1e-6)
        feature_meta[asset_id] = {"mean": means.to_dict(), "std": stds.to_dict()}
        normed = (group[["temperature_c", "vibration_mms", "pressure_bar"]] - means) / stds
        normed["is_anomaly_true"] = group["is_anomaly_true"].values
        scaled_rows.append(normed)

    import pandas as pd
    scaled = pd.concat(scaled_rows, ignore_index=True)

    X = scaled[["temperature_c", "vibration_mms", "pressure_bar"]].values
    y = scaled["is_anomaly_true"].values

    # Train on normal readings only (contamination estimate from data)
    contamination = float(y.mean())
    X_normal = X[~y]

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_normal)

    # Evaluate on full dataset
    raw_scores = model.decision_function(X)
    # Map to [0, 1]: higher = more anomalous
    anomaly_scores = 1 / (1 + np.exp(raw_scores * 5))

    preds = (model.predict(X) == -1).astype(int)
    auc = roc_auc_score(y.astype(int), anomaly_scores)

    print(f"ROC-AUC: {auc:.3f}")
    print(classification_report(y.astype(int), preds, target_names=["normal", "anomaly"]))

    joblib.dump(model,        MODELS_DIR / "anomaly_detector.joblib")
    joblib.dump(feature_meta, MODELS_DIR / "feature_meta.joblib")
    print(f"Saved → {MODELS_DIR}/anomaly_detector.joblib")
    print(f"Saved → {MODELS_DIR}/feature_meta.joblib")


# ── 2. Risk Text Classifier ────────────────────────────────────────────────

def train_risk_classifier(con: duckdb.DuckDBPyConnection) -> None:
    print("\n=== Risk Classifier (TF-IDF + LogisticRegression) ===")

    df = con.execute("""
        select summary, risk_label
        from incidents
    """).df()

    print(f"Loaded {len(df)} incident descriptions")
    print(f"Label distribution:\n{df['risk_label'].value_counts().to_string()}")

    # Binary: high-risk vs not
    y = (df["risk_label"] == "high").astype(int).values
    X = df["summary"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=2000,
            sublinear_tf=True,
        )),
        ("clf", LogisticRegression(
            C=1.0,
            max_iter=500,
            class_weight="balanced",
            random_state=42,
        )),
    ])
    pipeline.fit(X_train, y_train)

    y_pred  = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_proba)

    print(f"ROC-AUC: {auc:.3f}")
    print(classification_report(y_test, y_pred, target_names=["not-high", "high"]))

    joblib.dump(pipeline, MODELS_DIR / "risk_classifier.joblib")
    print(f"Saved → {MODELS_DIR}/risk_classifier.joblib")


# ── 3. RUL Predictor (CMAPSS FD001) ───────────────────────────────────────

def train_rul_predictor() -> None:
    print("\n=== RUL Predictor (GradientBoosting — NASA CMAPSS FD001) ===")

    if not CMAPSS_FD001.exists():
        print(f"  CMAPSS data not found at {CMAPSS_FD001}")
        print("  Run: python data/cmapss/fetch.py — then re-run training.")
        return

    df = pd.read_csv(CMAPSS_FD001, sep=r"\s+", header=None, names=_CMAPSS_COLS)
    df = df.dropna(axis=1, how="all")

    # Compute RUL label per row (run-to-failure: max cycle minus current)
    df["rul"] = df.groupby("unit")["cycle"].transform("max") - df["cycle"]

    # Clip RUL at 125 — standard CMAPSS convention: anything > 125 is "healthy"
    df["rul"] = df["rul"].clip(upper=125)

    X = df[_FD001_FEATURES].values
    y = df["rul"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    print(f"Loaded {len(df):,} rows from FD001 ({df['unit'].nunique()} engines)")
    print(f"MAE: {mae:.1f} cycles  (lower = better)")

    joblib.dump(model, MODELS_DIR / "rul_predictor.joblib")
    print(f"Saved → {MODELS_DIR}/rul_predictor.joblib")
    print("  Feature importance (top 5):")
    top5 = sorted(zip(_FD001_FEATURES, model.feature_importances_), key=lambda x: -x[1])[:5]
    for name, imp in top5:
        print(f"    {name}: {imp:.3f}")


# ── Entry point ────────────────────────────────────────────────────────────

def main() -> None:
    con = _open_db()
    train_anomaly_detector(con)
    train_risk_classifier(con)
    con.close()
    train_rul_predictor()
    print("\nAll models trained successfully.")


if __name__ == "__main__":
    main()
