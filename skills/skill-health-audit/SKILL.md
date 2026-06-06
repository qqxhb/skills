---
name: skill-health-audit
description: Analyze installed skills usage, quality, and redundancy; generate a Skill Health Report and cleanup plan. Trigger when the user says "audit my skills", "clean my skills", "帮我清理 skills", or asks for skill pruning/merging.
---

# Skill Health Audit

Use this skill to audit a skills workspace and produce a cleanup decision report.

Primary triggers include:

- `audit my skills`
- `@bot 帮我清理 skills`
- `帮我看哪些 skill 应该删掉`
- `哪些 skill 冗余，能不能合并`

## Goal

Turn a vague "skills 太多了" request into a concrete action plan:

1. usage frequency analysis
2. quality/effectiveness analysis
3. redundancy detection
4. reasoned cleanup recommendations
5. one-click disable script (execute only after user confirmation)

## Operating Rules

- Never hard-delete skills directly during analysis.
- Generate a reversible disable script first.
- Ask for explicit user confirmation before executing the disable script.
- Every recommendation must include reason and risk annotation.
- Mark uncertain recommendations as `需要确认` rather than forcing deletion.

## Required Inputs

At least one of the following:

1. Skill usage logs (session log JSON/JSONL, transcript, or provider output)
2. Installed skills directory (for total count, description parsing, and overlap detection)
3. Optional keep-list from user (skills that should be protected)

If logs are missing, still produce a structure-only audit with confidence marked as low.

## Core Modules

### 1) Usage Frequency Analysis

- Scan logs and count skill invocations.
- Time windows: 7d / 30d / 90d.
- Output per skill:
  - total calls
  - last-used age (days)
  - active window classification

### 2) Effectiveness Assessment

Assess value, not only frequency:

- correction/failure hints after invocation
- token consumption share
- recent-vs-previous quality trend (if data allows)

If evidence is incomplete, label as `inferred` or `unknown`.

### 3) Redundancy Detection

Use three complementary signals:

1. description text similarity
2. same-session co-invocation frequency
3. keyword overlap

Group likely duplicates into merge candidates, with confidence notes.

### 4) Recommendation Generator

Generate four buckets:

- `强烈建议删除`
- `建议合并`
- `建议保留`
- `需要你确认`

Rules:

- Every row must include a reason.
- Add risk tags for low-frequency but high-value skills (e.g. security, incident, migration, emergency tooling).
- Avoid purely mechanical threshold decisions.

### 5) One-Click Execution

- Generate a disable script for `强烈建议删除` skills.
- Script must be reversible (move to backup folder, not permanent deletion).
- Execute only after user confirms.

## Report Format

Use this output skeleton:

```text
📊 Skill 健康报告（YYYY-MM-DD 扫描）
总安装：X 个
本月被使用：Y 个
长期未用：Z 个（P%）
冗余重复：G 组
预计清理收益：context -A%, 选择准确率 +B%
---
🟢 强烈建议删除（N个）
- 「skill-a」：理由
...
🟡 建议合并（M 组）
- 「skill-x」+「skill-y」：理由
...
🟢 建议保留（K 个）
- 「skill-good」：理由
...
❓ 需要你确认（Q 个）
- 「skill-risky」：原因 + 风险标签
```

## Workflow

1. Load skill catalog from installed skills directory.
2. Load/normalize usage logs.
3. Compute 7/30/90 usage windows.
4. Compute failure/correction/token signals.
5. Detect redundancy groups.
6. Build recommendation buckets with reasons.
7. Render report and generate disable script.
8. Ask user whether to execute the script.

## Confidence Labels

Always disclose confidence:

- `high`: usage + quality + redundancy signals are all present
- `medium`: one of the major dimensions is partial
- `low`: mostly structure-only scan with sparse logs

## Recommended Local Command

```bash
python3 skills/skill-health-audit/scripts/generate_skill_health_report.py \
  --skills-dir skills \
  --output-report /tmp/skill-health-report.md \
  --output-disable-script /tmp/disable-skills.sh
```

## Verification

After edits, validate:

- report can be generated from sample data
- generated disable script is executable and reversible
- recommendation rows all include reasons
- uncertain/risky cases are not auto-deleted
