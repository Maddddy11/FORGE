with source as (
    select * from {{ source('raw', 'incidents') }}
)

select
    incident_id,
    asset_id,
    summary,
    risk_label,
    risk_score,
    created_at,
    time_to_resolve_hrs,
    case
        when risk_label = 'high'   then 2
        when risk_label = 'medium' then 1
        else 0
    end as risk_ordinal,
    risk_score >= 0.70 as requires_approval
from source
