# runtime-observability Trigger Eval Report

## Summary
- Passed: 5/5
- Failed: 0/5

## Results
| ID | Expected | Predicted | Passed | Notes |
|----|----------|-----------|--------|-------|
| 1 | True | True | True | positive_hits=['runtime-observability', 'session log', 'execution timeline', 'token breakdown', 'redundant tool']; negative_hits=['none'] |
| 2 | True | True | True | positive_hits=['runtime-observability', 'session id', 'session_logs']; negative_hits=['none'] |
| 3 | True | True | True | positive_hits=['agent trace', 'token spike', 'redundant tool']; negative_hits=['none'] |
| 4 | False | False | True | positive_hits=['none']; negative_hits=['opentelemetry', 'grafana', 'metrics'] |
| 5 | False | False | True | positive_hits=['none']; negative_hits=['opentelemetry', 'metrics', '埋点', '监控平台', 'metrics 方案'] |

## Failure Details
- None
