-- Sensor readings with per-asset rolling stats for anomaly context.
-- The ML model (train.py) writes its scores back to the DB after this view exists;
-- this fact table is the analytical foundation for mart_asset_health.
with readings as (
    select * from {{ ref('stg_sensor_readings') }}
),

with_stats as (
    select
        reading_id,
        asset_id,
        timestamp,
        temperature_c,
        vibration_mms,
        pressure_bar,
        is_anomaly_true,
        temp_zscore,
        vib_zscore,
        pres_zscore,
        -- Rolling 2-hour window stats (8 intervals × 15 min)
        avg(temperature_c) over (
            partition by asset_id
            order by timestamp
            rows between 8 preceding and current row
        ) as rolling_temp_avg,
        avg(vibration_mms) over (
            partition by asset_id
            order by timestamp
            rows between 8 preceding and current row
        ) as rolling_vib_avg,
        -- Simple composite drift score: normalised Euclidean distance from rolling mean
        sqrt(
            power(temp_zscore, 2) +
            power(vib_zscore,  2) +
            power(pres_zscore, 2)
        ) as drift_score
    from readings
)

select
    *,
    drift_score >= 2.0 as flagged_by_drift
from with_stats
