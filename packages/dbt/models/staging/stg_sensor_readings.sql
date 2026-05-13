with source as (
    select * from {{ source('raw', 'sensor_readings') }}
),

cleaned as (
    select
        reading_id,
        asset_id,
        timestamp,
        temperature_c,
        vibration_mms,
        pressure_bar,
        is_anomaly_true,
        rul,
        -- Z-scores computed relative to the full dataset for feature inspection
        (temperature_c - avg(temperature_c) over ()) / nullif(stddev(temperature_c) over (), 0) as temp_zscore,
        (vibration_mms - avg(vibration_mms) over ()) / nullif(stddev(vibration_mms) over (), 0) as vib_zscore,
        (pressure_bar  - avg(pressure_bar)  over ()) / nullif(stddev(pressure_bar)  over (), 0) as pres_zscore
    from source
    where temperature_c is not null
      and vibration_mms is not null
      and pressure_bar  is not null
)

select * from cleaned
