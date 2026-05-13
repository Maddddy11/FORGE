"""
Seed DuckDB sensor_readings from NASA CMAPSS FD001 (real turbofan degradation data).

Run from repo root after fetching the data:
    python data/cmapss/fetch.py          # one-time download
    python data/cmapss/seed_cmapss.py    # replaces synthetic sensor_readings

What this does:
  - Maps 5 FD001 engines to the 5 existing assets
  - Scales raw sensor channels to industrial-looking units (°C, mm/s, bar)
  - Sets is_anomaly_true = True when RUL < 30 cycles (degradation zone)
  - Adds a rul column (remaining useful life in cycles) to sensor_readings
  - Keeps assets, incidents, and work_orders tables untouched
"""
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

RAW_DIR = Path(__file__).parent / "raw"
FD001_TRAIN = RAW_DIR / "train_FD001.txt"
DB_PATH = Path(__file__).parents[2] / "data" / "imam_lite.duckdb"

# FD001 has 26 space-separated columns, no header
COLUMNS = ["unit", "cycle", "op1", "op2", "op3"] + [f"s{i}" for i in range(1, 22)]

# Map 5 FD001 engine IDs to our existing asset IDs
ASSET_MAPPING = {
    1: "PUMP-101",
    2: "PUMP-102",
    10: "COMP-201",
    50: "HEX-301",
    80: "VALVE-401",
}

# Sensors to use as the 3 DB columns and their target physical ranges
# s4  = T30 (HPC outlet temperature) → temperature_c [60, 120]
# s11 = Ps30 (static pressure HPC outlet) → pressure_bar [3, 14]
# s7  = P30 (total pressure HPC outlet) → vibration_mms [1.5, 9]
SENSOR_MAP = {
    "temperature_c": ("s4",  60.0, 120.0),
    "pressure_bar":  ("s11", 3.0,  14.0),
    "vibration_mms": ("s7",  1.5,   9.0),
}

# Cycle timestep: 1 hour per cycle
CYCLE_HOURS = 1


def _load_fd001() -> pd.DataFrame:
    if not FD001_TRAIN.exists():
        raise FileNotFoundError(
            f"CMAPSS data not found at {FD001_TRAIN}\n"
            "Run:  python data/cmapss/fetch.py"
        )
    df = pd.read_csv(FD001_TRAIN, sep=r"\s+", header=None, names=COLUMNS)
    # Drop trailing NaN columns that sometimes appear
    df = df.dropna(axis=1, how="all")
    return df


def _minmax_scale(series: pd.Series, lo: float, hi: float) -> pd.Series:
    s_min, s_max = series.min(), series.max()
    if s_max - s_min < 1e-9:
        return pd.Series(np.full(len(series), (lo + hi) / 2), index=series.index)
    return lo + (series - s_min) / (s_max - s_min) * (hi - lo)


def build_readings(df: pd.DataFrame) -> list[dict]:
    rows = []
    # Anchor: place the last cycle of each engine at "now - 1 hour"
    anchor = datetime.now(UTC) - timedelta(hours=1)

    for engine_id, asset_id in ASSET_MAPPING.items():
        engine_df = df[df["unit"] == engine_id].copy().reset_index(drop=True)
        if engine_df.empty:
            print(f"  WARNING: engine {engine_id} not found in FD001, skipping")
            continue

        max_cycle = engine_df["cycle"].max()

        # Compute RUL for each row
        engine_df["rul"] = max_cycle - engine_df["cycle"]

        # Scale the 3 sensor channels per-engine (normalise against this engine's range)
        for col, (sensor, lo, hi) in SENSOR_MAP.items():
            engine_df[col] = _minmax_scale(engine_df[sensor], lo, hi).round(3)

        # Add small Gaussian noise so readings look real at inspection time
        rng = np.random.default_rng(seed=engine_id)
        for col, (_, lo, hi) in SENSOR_MAP.items():
            noise_std = (hi - lo) * 0.005
            engine_df[col] = (engine_df[col] + rng.normal(0, noise_std, len(engine_df))).clip(lo * 0.9, hi * 1.1).round(3)

        # Timestamps: work backwards from anchor (last cycle = anchor)
        n = len(engine_df)
        engine_df["timestamp"] = [
            anchor - timedelta(hours=(n - 1 - i) * CYCLE_HOURS)
            for i in range(n)
        ]

        for _, row in engine_df.iterrows():
            rows.append({
                "reading_id":      str(uuid.uuid4()),
                "asset_id":        asset_id,
                "timestamp":       row["timestamp"],
                "temperature_c":   float(row["temperature_c"]),
                "vibration_mms":   float(row["vibration_mms"]),
                "pressure_bar":    float(row["pressure_bar"]),
                "is_anomaly_true": bool(row["rul"] < 30),
                "rul":             int(row["rul"]),
            })

    return rows


def seed(db_path: Path = DB_PATH) -> None:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}\n"
            "Run the base seed first:  python data/synthetic/seed.py"
        )

    df = _load_fd001()
    print(f"Loaded FD001: {len(df):,} rows, {df['unit'].nunique()} engines")

    readings = build_readings(df)

    con = duckdb.connect(str(db_path))

    # Add rul column if it doesn't exist yet
    existing_cols = {row[0] for row in con.execute("DESCRIBE sensor_readings").fetchall()}
    if "rul" not in existing_cols:
        con.execute("ALTER TABLE sensor_readings ADD COLUMN rul INTEGER")

    con.execute("DELETE FROM sensor_readings WHERE asset_id IN (SELECT asset_id FROM assets)")

    con.executemany(
        "INSERT INTO sensor_readings VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            [r["reading_id"], r["asset_id"], r["timestamp"],
             r["temperature_c"], r["vibration_mms"], r["pressure_bar"],
             r["is_anomaly_true"], r["rul"]]
            for r in readings
        ],
    )

    con.close()

    anomaly_count = sum(1 for r in readings if r["is_anomaly_true"])
    print(f"Loaded {len(readings):,} CMAPSS sensor readings ({anomaly_count:,} anomalous, RUL < 30)")
    print(f"  Engines used: {list(ASSET_MAPPING.keys())} → {list(ASSET_MAPPING.values())}")
    print(f"  DB: {db_path}")


if __name__ == "__main__":
    seed()
