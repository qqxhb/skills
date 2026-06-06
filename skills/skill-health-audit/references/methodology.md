# Skill Health Audit Methodology

This document defines how `skill-health-audit` derives recommendations.

## Signals

### Usage signal

For each skill, compute call counts in windows:

- 7 days
- 30 days
- 90 days

Also compute:

- `last_used_days`
- active flag in current month

### Effectiveness signal

From invocation outcomes and nearby turns:

- failure count and failure rate
- correction count (post-invocation correction or retry)
- token usage share

### Redundancy signal

Pairwise/group signal using:

1. description similarity
2. keyword overlap
3. co-invocation frequency in same session

## Recommendation Buckets

### 强烈建议删除

Typical criteria:

- no usage in 60+ days
- low unique capability evidence
- covered by stronger frequently used skill(s)
- low risk if disabled

### 建议合并

Typical criteria:

- high overlap with 1+ neighbors
- often co-invoked in same session
- user can gain from one unified interface skill

### 建议保留

Typical criteria:

- stable usage in 30d or 7d
- high effectiveness signal
- unique capability not covered elsewhere

### 需要确认

Typical criteria:

- low recent usage but potentially critical when needed
- emergency/security/compliance/incident classes
- insufficient telemetry to decide safely

## Confidence

- high: all major signals available
- medium: one dimension partial
- low: sparse logs; mostly static analysis

## Execution Safety

Cleanup execution should be reversible:

- move target skill folders into a timestamped backup directory
- never permanently delete without a second explicit confirmation
