"""
Loads pre-trained ML models and exposes scoring functions.

Models are trained by ml/train.py. If they don't exist the service degrades
gracefully (returns None) so the API stays operational before training.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_MODELS_DIR = Path(__file__).parents[4] / "ml" / "models"

_risk_classifier  = None
_anomaly_detector = None
_feature_meta     = None
_rul_predictor    = None
_models_loaded    = False

# Sensor order expected by the RUL predictor (must match ml/train.py _FD001_FEATURES)
_RUL_FEATURE_NAMES = ["s2", "s3", "s4", "s7", "s8", "s9", "s11", "s12", "s13", "s14", "s15", "s17", "s20", "s21"]


def _load_models() -> None:
    global _risk_classifier, _anomaly_detector, _feature_meta, _rul_predictor, _models_loaded
    if _models_loaded:
        return
    try:
        import joblib
        _risk_classifier  = joblib.load(_MODELS_DIR / "risk_classifier.joblib")
        _anomaly_detector = joblib.load(_MODELS_DIR / "anomaly_detector.joblib")
        _feature_meta     = joblib.load(_MODELS_DIR / "feature_meta.joblib")
        _rul_predictor    = joblib.load(_MODELS_DIR / "rul_predictor.joblib")
        _models_loaded = True
        logger.info("ML models loaded from %s", _MODELS_DIR)
    except FileNotFoundError:
        logger.warning("ML models not found at %s — run ml/train.py to enable ML scoring", _MODELS_DIR)
    except Exception:
        logger.warning("Failed to load ML models", exc_info=True)


_load_models()


def classify_risk(incident_text: str) -> float | None:
    """
    Return probability (0–1) that the incident is high-risk.
    Returns None if the model is unavailable.
    """
    if _risk_classifier is None:
        return None
    try:
        proba = _risk_classifier.predict_proba([incident_text])[0][1]
        return round(float(proba), 3)
    except Exception:
        logger.warning("Risk classifier inference failed", exc_info=True)
        return None


def score_anomaly(asset_id: str, temperature_c: float, vibration_mms: float, pressure_bar: float) -> float | None:
    """
    Return anomaly score (0–1, higher = more anomalous) for a single sensor reading.
    Returns None if the model is unavailable.
    """
    if _anomaly_detector is None or _feature_meta is None:
        return None
    try:
        import numpy as np

        meta = _feature_meta.get(asset_id)
        if meta is None:
            # Unknown asset — use global mean (will be less accurate)
            meta = {
                "mean": {"temperature_c": 65.0, "vibration_mms": 3.5, "pressure_bar": 4.0},
                "std":  {"temperature_c": 10.0, "vibration_mms": 1.5, "pressure_bar": 1.5},
            }

        def _z(val: float, key: str) -> float:
            return (val - meta["mean"][key]) / max(meta["std"][key], 1e-6)

        features = np.array([[
            _z(temperature_c, "temperature_c"),
            _z(vibration_mms, "vibration_mms"),
            _z(pressure_bar,  "pressure_bar"),
        ]])

        raw_score = _anomaly_detector.decision_function(features)[0]
        # Sigmoid mapping: higher score → more anomalous
        score = float(1 / (1 + np.exp(raw_score * 5)))
        return round(score, 3)
    except Exception:
        logger.warning("Anomaly detector inference failed", exc_info=True)
        return None


def predict_rul(sensor_values: dict[str, float]) -> float | None:
    """
    Predict Remaining Useful Life (cycles) from raw CMAPSS sensor readings.

    sensor_values must contain keys matching _RUL_FEATURE_NAMES (s2, s3, …).
    Returns predicted RUL in cycles, or None if the model is unavailable.
    """
    if _rul_predictor is None:
        return None
    try:
        import numpy as np
        features = np.array([[sensor_values.get(k, 0.0) for k in _RUL_FEATURE_NAMES]])
        rul = float(_rul_predictor.predict(features)[0])
        return round(max(0.0, rul), 1)
    except Exception:
        logger.warning("RUL predictor inference failed", exc_info=True)
        return None


def models_available() -> bool:
    return _models_loaded
