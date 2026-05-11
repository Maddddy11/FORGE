-- One row per asset: current health score, anomaly summary, latest readings.
with anomalies as (
    select * from {{ ref('fct_anomalies') }}
),

assets as (
    select * from {{ source('raw', 'assets') }}
),

aggregated as (
    select
        asset_id,
        count(*)                                                        as total_readings,
        sum(case when is_anomaly_true   then 1 else 0 end)             as true_anomaly_count,
        sum(case when flagged_by_drift  then 1 else 0 end)             as drift_flagged_count,
        avg(drift_score)                                                as mean_drift_score,
        max(drift_score)                                                as max_drift_score,
        avg(temperature_c)                                              as avg_temp_c,
        avg(vibration_mms)                                              as avg_vib_mms,
        avg(pressure_bar)                                               as avg_pressure_bar,
        max(timestamp)                                                  as last_reading_at,
        -- Health score: 1 = fully healthy, 0 = all readings anomalous
        round(
            1.0 - (
                sum(case when flagged_by_drift then 1 else 0 end) * 1.0
                / nullif(count(*), 0)
            ), 3
        )                                                               as health_score
    from anomalies
    group by asset_id
)

select
    a.asset_id,
    a.name,
    a.type,
    a.location,
    ag.total_readings,
    ag.true_anomaly_count,
    ag.drift_flagged_count,
    ag.mean_drift_score,
    ag.max_drift_score,
    ag.avg_temp_c,
    ag.avg_vib_mms,
    ag.avg_pressure_bar,
    ag.last_reading_at,
    ag.health_score
from aggregated ag
join assets a using (asset_id)
order by ag.health_score asc
