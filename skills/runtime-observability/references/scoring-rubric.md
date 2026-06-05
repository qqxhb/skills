# Scoring Rubric

Use this rubric to keep analysis consistent and avoid hand-wavy scoring.

## 1. Token And Execution Anomalies

Treat the following as signals, not proof:

- `token spike`: a single model call contributes far more tokens than neighboring calls, or dominates the session total without producing a proportional jump in progress
- `retry storm`: 3 or more retries of the same tool or near-identical model request with little new information
- `loop risk`: repeated browser/search/read patterns that do not materially change the working set
- `idle gap`: long waits between dependent steps with no useful output
- `prompt bloat`: large repeated instructions copied into multiple calls without evidence they were needed

When the baseline is unavailable, judge "normal vs abnormal" using internal relative comparison within the same session:

- compare the largest call with median call size
- compare repeated stages with their first attempt
- compare output size against token input

Never claim an industry benchmark unless the user supplied one or the environment already contains an approved benchmark source.

## 2. Redundancy Heuristic

Mark a tool call as redundant only if at least one condition holds:

1. It repeats a previous call with materially the same query and no new branching reason
2. It happens after the needed evidence was already available
3. It produces no new data and does not serve validation
4. A cheaper already-available source could have answered the same question

Do not mark as redundant:

- a verification step that lowers risk
- a retry after a clear error
- a narrowing search that follows a broad search

## 3. Quality Score Formula

Score out of 100 using this weighted model:

- `output compliance` = 35 points
- `factual grounding` = 40 points
- `scope discipline` = 25 points

### Output Compliance

Ask:

- Did the final output match the expected format?
- Did it include all mandatory sections or fields?
- Did it preserve machine-readability when required?

Suggested deductions:

- missing major section: -10
- wrong format family, such as plain text instead of JSON: -15
- formatting issue that does not block use: -3 to -5

### Factual Grounding

Ask:

- Are URLs, file names, tools, or data points supported by logs or accessible sources?
- Does the answer overstate certainty beyond the evidence?

Suggested deductions:

- confirmed hallucination: -15 each
- suspected unsupported claim: -5 each
- unjustified certainty or fabricated rationale: -5 to -10

### Scope Discipline

Ask:

- Did the run stay within the advertised skill boundary?
- Did it answer adjacent questions the skill was not supposed to answer?
- Did it skip mandatory behavior defined by the skill?

Suggested deductions:

- major out-of-scope behavior: -10
- missed required capability branch: -8
- minor scope drift: -3 to -5

## 4. Confidence Levels

- `high`: the conclusion comes directly from logs or accessible artifacts
- `medium`: the conclusion combines direct evidence with limited inference
- `low`: major fields are missing; the conclusion is plausible but weakly supported

## 5. Missing-Field Scoring

Missing fields should lower confidence before they lower score.

Apply these rules:

- missing `duration_ms`: do not deduct from quality score by itself; instead disclose timing as partial or `unknown`
- missing per-tool token attribution: do not fabricate tool token tables; keep the table and mark values as `unknown`
- missing final artifact body: reduce `output compliance` only when the missing artifact prevents checking a required format detail
- missing model name or tool name: keep the event, label it `unknown`, and lower confidence only if the missing identity affects the conclusion

Only deduct score when the missing field blocks a required judgment, not merely because the dataset is imperfect.

## 6. Severity Levels

Use these labels for issues:

- `high`: likely caused cost blow-up, incorrect output, or major trust loss
- `medium`: materially inefficient or risky, but the run still mostly worked
- `low`: useful cleanup or optimization opportunity with limited impact

## 7. Evidence Style

Every flagged issue should have this shape:

```text
Issue: browser call #3 appears redundant
Severity: medium
Evidence: repeated the same host and query as browser call #2; no new entities or branches followed
Why it matters: added latency and likely token cost without improving coverage
Suggested fix: stop after the second call once the required field is present
Confidence: high
```
