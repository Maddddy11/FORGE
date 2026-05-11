"""
Generates a realistic synthetic dataset and loads it into DuckDB.

Run from the repo root:
    python data/synthetic/seed.py

Creates data/imam_lite.duckdb with tables:
    assets, sensor_readings, anomaly_scores, work_orders, incidents
"""
import math
import random
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb
import numpy as np

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

DB_PATH = Path(__file__).parents[2] / "data" / "imam_lite.duckdb"

ASSETS = [
    {"asset_id": "PUMP-101", "name": "Centrifugal Pump P-101", "type": "pump",
     "location": "Process Area A", "oem": "Flowserve"},
    {"asset_id": "PUMP-102", "name": "Centrifugal Pump P-102", "type": "pump",
     "location": "Process Area A", "oem": "Flowserve"},
    {"asset_id": "COMP-201", "name": "Reciprocating Compressor C-201", "type": "compressor",
     "location": "Compression Bay", "oem": "Dresser-Rand"},
    {"asset_id": "HEX-301", "name": "Shell-and-Tube Heat Exchanger E-301", "type": "heat_exchanger",
     "location": "Utilities Row", "oem": "Alfa Laval"},
    {"asset_id": "VALVE-401", "name": "Control Valve V-401", "type": "valve",
     "location": "Feed Header", "oem": "Emerson"},
]

# Normal operating envelopes per asset type: (mean, std) for (temp_c, vib_mms, pressure_bar)
NORMAL_PARAMS = {
    "pump":          {"temp": (72, 4),   "vib": (3.5, 0.8),  "pres": (4.5, 0.5)},
    "compressor":    {"temp": (92, 6),   "vib": (5.5, 1.2),  "pres": (11.0, 1.5)},
    "heat_exchanger":{"temp": (58, 5),   "vib": (1.8, 0.4),  "pres": (3.0, 0.4)},
    "valve":         {"temp": (32, 4),   "vib": (1.0, 0.3),  "pres": (2.0, 0.3)},
}

DAYS = 30
INTERVAL_MINUTES = 15


def _reading_timestamp_range() -> list[datetime]:
    start = datetime.now(UTC) - timedelta(days=DAYS)
    start = start.replace(minute=0, second=0, microsecond=0)
    steps = (DAYS * 24 * 60) // INTERVAL_MINUTES
    return [start + timedelta(minutes=i * INTERVAL_MINUTES) for i in range(steps)]


def _inject_anomaly_windows(n_readings: int) -> list[tuple[int, int]]:
    """Return 2 non-overlapping anomaly windows (start_idx, end_idx)."""
    window_size = 12  # 3 hours at 15-min intervals
    windows = []
    attempts = 0
    while len(windows) < 2 and attempts < 100:
        start = random.randint(window_size, n_readings - window_size - 1)
        end = start + window_size
        if not any(s - window_size <= start <= e + window_size for s, e in windows):
            windows.append((start, end))
        attempts += 1
    return windows


def generate_sensor_readings() -> list[dict]:
    timestamps = _reading_timestamp_range()
    rows = []
    for asset in ASSETS:
        params = NORMAL_PARAMS[asset["type"]]
        anomaly_windows = _inject_anomaly_windows(len(timestamps))

        for i, ts in enumerate(timestamps):
            in_anomaly = any(s <= i <= e for s, e in anomaly_windows)

            # Ramp factor — gradual drift into anomaly, spike at peak
            ramp = 0.0
            for s, e in anomaly_windows:
                if s <= i <= e:
                    mid = (s + e) / 2
                    ramp = max(ramp, 1.0 - abs(i - mid) / ((e - s) / 2 + 1e-9))

            temp_mul  = 1 + ramp * 0.35 if in_anomaly else 1.0
            vib_mul   = 1 + ramp * 0.60 if in_anomaly else 1.0
            pres_mul  = 1 + ramp * 0.20 if in_anomaly else 1.0

            temp = np.random.normal(params["temp"][0] * temp_mul, params["temp"][1])
            vib  = abs(np.random.normal(params["vib"][0]  * vib_mul,  params["vib"][1]))
            pres = abs(np.random.normal(params["pres"][0] * pres_mul, params["pres"][1]))

            rows.append({
                "reading_id":      str(uuid.uuid4()),
                "asset_id":        asset["asset_id"],
                "timestamp":       ts,
                "temperature_c":   round(float(temp), 2),
                "vibration_mms":   round(float(vib),  3),
                "pressure_bar":    round(float(pres),  2),
                "is_anomaly_true": in_anomaly,
            })
    return rows


INCIDENT_TEMPLATES = [
    # (template, risk_label)
    ("Scheduled PM on {asset}. Replaced filter element. No issues found.", "low"),
    ("Routine lubrication check on {asset}. Grease levels topped up.", "low"),
    ("Calibration check on pressure transmitter for {asset}. Values within spec.", "low"),
    ("Visual inspection of {asset}. All readings nominal. Log updated.", "low"),
    ("Operator reported minor noise on {asset}. Inspection found loose fastener. Torqued to spec.", "low"),
    ("Preventive replacement of mechanical seal on {asset} per PM schedule.", "low"),
    ("Unusual vibration observed on {asset}. Levels slightly above baseline.", "medium"),
    ("Temperature trending upward on {asset} over past 12 hours. Possible fouling.", "medium"),
    ("Oil seepage detected at shaft seal of {asset}. Monitoring initiated.", "medium"),
    ("Flow rate reduction on {asset}. Possible partial blockage in suction line.", "medium"),
    ("Pressure differential across {asset} higher than normal. Filter replacement scheduled.", "medium"),
    ("Bearing temperature elevated on {asset}. Lubrication checked; root cause under investigation.", "medium"),
    ("Fire alarm triggered near {asset}. Possible gas leak detected. Area evacuated.", "high"),
    ("Rupture disk indicator showing possible overpressure event on {asset}.", "high"),
    ("Emergency shutdown triggered on {asset}. Loss of containment suspected.", "high"),
    ("Significant process fluid leak observed at flange connection on {asset}.", "high"),
    ("Operator attempting to bypass safety interlock to restart {asset}.", "high"),
    ("Trip signal received on {asset}. High vibration protection activated.", "high"),
    ("Smoke observed near {asset}. Fire suppression system activated.", "high"),
    ("Catastrophic bearing failure on {asset}. Equipment taken offline immediately.", "high"),
]


def generate_incidents() -> list[dict]:
    rows = []
    start = datetime.now(UTC) - timedelta(days=DAYS)
    for i in range(180):
        template, risk_label = random.choice(INCIDENT_TEMPLATES)
        asset = random.choice(ASSETS)
        summary = template.format(asset=asset["asset_id"])
        risk_score = {
            "low":    round(random.uniform(0.05, 0.38), 2),
            "medium": round(random.uniform(0.40, 0.68), 2),
            "high":   round(random.uniform(0.72, 0.98), 2),
        }[risk_label]
        created_at = start + timedelta(hours=random.uniform(0, DAYS * 24))
        resolve_hours = random.uniform(0.5, 48) if risk_label != "low" else random.uniform(0.5, 8)
        rows.append({
            "incident_id":         str(uuid.uuid4()),
            "asset_id":            asset["asset_id"],
            "summary":             summary,
            "risk_label":          risk_label,
            "risk_score":          risk_score,
            "created_at":          created_at,
            "time_to_resolve_hrs": round(resolve_hours, 2),
        })
    return rows


def generate_work_orders() -> list[dict]:
    rows = []
    start = datetime.now(UTC) - timedelta(days=DAYS)
    statuses = ["open", "in_progress", "completed", "deferred"]
    for i in range(60):
        asset = random.choice(ASSETS)
        created = start + timedelta(hours=random.uniform(0, DAYS * 24))
        rows.append({
            "wo_id":       str(uuid.uuid4()),
            "asset_id":    asset["asset_id"],
            "title":       f"Maintenance order for {asset['asset_id']}",
            "status":      random.choice(statuses),
            "priority":    random.choice(["low", "medium", "high"]),
            "created_at":  created,
            "planned_hrs": round(random.uniform(1, 16), 1),
        })
    return rows


def seed(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))

    con.execute("DROP TABLE IF EXISTS assets")
    con.execute("DROP TABLE IF EXISTS sensor_readings")
    con.execute("DROP TABLE IF EXISTS incidents")
    con.execute("DROP TABLE IF EXISTS work_orders")

    con.execute("""
        CREATE TABLE assets (
            asset_id    VARCHAR PRIMARY KEY,
            name        VARCHAR,
            type        VARCHAR,
            location    VARCHAR,
            oem         VARCHAR
        )
    """)
    con.executemany(
        "INSERT INTO assets VALUES (?, ?, ?, ?, ?)",
        [[a["asset_id"], a["name"], a["type"], a["location"], a["oem"]] for a in ASSETS],
    )

    readings = generate_sensor_readings()
    con.execute("""
        CREATE TABLE sensor_readings (
            reading_id       VARCHAR PRIMARY KEY,
            asset_id         VARCHAR,
            timestamp        TIMESTAMPTZ,
            temperature_c    DOUBLE,
            vibration_mms    DOUBLE,
            pressure_bar     DOUBLE,
            is_anomaly_true  BOOLEAN
        )
    """)
    con.executemany(
        "INSERT INTO sensor_readings VALUES (?, ?, ?, ?, ?, ?, ?)",
        [[r["reading_id"], r["asset_id"], r["timestamp"],
          r["temperature_c"], r["vibration_mms"], r["pressure_bar"],
          r["is_anomaly_true"]] for r in readings],
    )

    incidents = generate_incidents()
    con.execute("""
        CREATE TABLE incidents (
            incident_id          VARCHAR PRIMARY KEY,
            asset_id             VARCHAR,
            summary              VARCHAR,
            risk_label           VARCHAR,
            risk_score           DOUBLE,
            created_at           TIMESTAMPTZ,
            time_to_resolve_hrs  DOUBLE
        )
    """)
    con.executemany(
        "INSERT INTO incidents VALUES (?, ?, ?, ?, ?, ?, ?)",
        [[i["incident_id"], i["asset_id"], i["summary"], i["risk_label"],
          i["risk_score"], i["created_at"], i["time_to_resolve_hrs"]] for i in incidents],
    )

    work_orders = generate_work_orders()
    con.execute("""
        CREATE TABLE work_orders (
            wo_id       VARCHAR PRIMARY KEY,
            asset_id    VARCHAR,
            title       VARCHAR,
            status      VARCHAR,
            priority    VARCHAR,
            created_at  TIMESTAMPTZ,
            planned_hrs DOUBLE
        )
    """)
    con.executemany(
        "INSERT INTO work_orders VALUES (?, ?, ?, ?, ?, ?, ?)",
        [[w["wo_id"], w["asset_id"], w["title"], w["status"],
          w["priority"], w["created_at"], w["planned_hrs"]] for w in work_orders],
    )

    con.close()

    total_readings = len(readings)
    anomaly_readings = sum(1 for r in readings if r["is_anomaly_true"])
    print(f"Seeded {db_path}")
    print(f"  assets:          {len(ASSETS)}")
    print(f"  sensor_readings: {total_readings:,} ({anomaly_readings:,} anomalous)")
    print(f"  incidents:       {len(incidents)}")
    print(f"  work_orders:     {len(work_orders)}")


if __name__ == "__main__":
    seed()
