-- Daily KPI roll-up: incident counts, risk distribution, MTTD proxy.
with incidents as (
    select * from {{ ref('stg_incidents') }}
)

select
    cast(created_at as date)                                            as incident_date,
    count(*)                                                            as incident_count,
    sum(case when risk_label = 'high'   then 1 else 0 end)             as high_risk_count,
    sum(case when risk_label = 'medium' then 1 else 0 end)             as medium_risk_count,
    sum(case when risk_label = 'low'    then 1 else 0 end)             as low_risk_count,
    round(avg(risk_score), 3)                                           as avg_risk_score,
    -- MTTD proxy: average resolution time for high-risk incidents (hours)
    round(
        avg(case when risk_label = 'high' then time_to_resolve_hrs end), 2
    )                                                                   as avg_mttd_high_risk_hrs,
    round(avg(time_to_resolve_hrs), 2)                                  as avg_resolution_hrs,
    sum(case when requires_approval then 1 else 0 end)                  as approval_required_count
from incidents
group by cast(created_at as date)
order by incident_date
