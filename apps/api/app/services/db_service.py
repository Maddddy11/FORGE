"""Read-only DuckDB queries for analytics endpoints."""
import logging
from pathlib import Path

import duckdb

logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).parents[4] / "data" / "imam_lite.duckdb"


def _connect() -> duckdb.DuckDBPyConnection:
    if not _DB_PATH.exists():
        raise FileNotFoundError(
            f"Analytics database not found at {_DB_PATH}. "
            "Run: python data/synthetic/seed.py"
        )
    return duckdb.connect(str(_DB_PATH), read_only=True)


def get_asset_health() -> list[dict]:
    """Query mart_asset_health (built by dbt) or fall back to raw aggregation."""
    con = _connect()
    try:
        # Try dbt mart first (available after `dbt run`)
        rows = con.execute("""
            select asset_id, name, type, location,
                   total_readings, drift_flagged_count,
                   avg_temp_c, avg_vib_mms, avg_pressure_bar,
                   health_score, last_reading_at
            from mart_asset_health
            order by health_score asc
        """).fetchall()
        cols = ["asset_id", "name", "type", "location", "total_readings",
                "drift_flagged_count", "avg_temp_c", "avg_vib_mms",
                "avg_pressure_bar", "health_score", "last_reading_at"]
    except duckdb.CatalogException:
        # Fall back to raw table before dbt has run
        rows = con.execute("""
            select
                sr.asset_id,
                a.name,
                a.type,
                a.location,
                count(*)                                            as total_readings,
                sum(case when sr.is_anomaly_true then 1 else 0 end) as drift_flagged_count,
                round(avg(sr.temperature_c), 2)                     as avg_temp_c,
                round(avg(sr.vibration_mms), 3)                     as avg_vib_mms,
                round(avg(sr.pressure_bar), 2)                      as avg_pressure_bar,
                round(1.0 - sum(case when sr.is_anomaly_true then 1 else 0 end)
                    * 1.0 / count(*), 3)                            as health_score,
                max(sr.timestamp)                                   as last_reading_at
            from sensor_readings sr
            join assets a using (asset_id)
            group by sr.asset_id, a.name, a.type, a.location
            order by health_score asc
        """).fetchall()
        cols = ["asset_id", "name", "type", "location", "total_readings",
                "drift_flagged_count", "avg_temp_c", "avg_vib_mms",
                "avg_pressure_bar", "health_score", "last_reading_at"]
    finally:
        con.close()

    return [dict(zip(cols, row)) for row in rows]


def get_incident_kpis() -> list[dict]:
    """Daily KPI roll-up — tries dbt mart, falls back to raw."""
    con = _connect()
    try:
        rows = con.execute("""
            select incident_date, incident_count, high_risk_count,
                   medium_risk_count, low_risk_count, avg_risk_score,
                   avg_mttd_high_risk_hrs, avg_resolution_hrs, approval_required_count
            from mart_incident_kpis
            order by incident_date
        """).fetchall()
        cols = ["incident_date", "incident_count", "high_risk_count",
                "medium_risk_count", "low_risk_count", "avg_risk_score",
                "avg_mttd_high_risk_hrs", "avg_resolution_hrs", "approval_required_count"]
    except duckdb.CatalogException:
        rows = con.execute("""
            select
                cast(created_at as date)                                as incident_date,
                count(*)                                                as incident_count,
                sum(case when risk_label='high'   then 1 else 0 end)   as high_risk_count,
                sum(case when risk_label='medium' then 1 else 0 end)   as medium_risk_count,
                sum(case when risk_label='low'    then 1 else 0 end)   as low_risk_count,
                round(avg(risk_score), 3)                               as avg_risk_score,
                round(avg(case when risk_label='high'
                               then time_to_resolve_hrs end), 2)        as avg_mttd_high_risk_hrs,
                round(avg(time_to_resolve_hrs), 2)                     as avg_resolution_hrs,
                sum(case when risk_score >= 0.70 then 1 else 0 end)    as approval_required_count
            from incidents
            group by cast(created_at as date)
            order by incident_date
        """).fetchall()
        cols = ["incident_date", "incident_count", "high_risk_count",
                "medium_risk_count", "low_risk_count", "avg_risk_score",
                "avg_mttd_high_risk_hrs", "avg_resolution_hrs", "approval_required_count"]
    finally:
        con.close()

    return [dict(zip(cols, row)) for row in rows]
