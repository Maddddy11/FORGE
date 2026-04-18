# Evaluation Plan

## Dataset
- 20 historical incident replay cases with known outcomes.

## Metrics
- MTTD reduction percentage
- Top-2 recommendation relevance
- Compliance violation recall
- Audit completion rate for high-risk outputs

## Method
- Offline replay harness from `packages/eval/datasets`
- Compare baseline decision workflow vs IMAM Lite workflow
