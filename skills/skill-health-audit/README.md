# Skill Health Audit

`skill-health-audit` helps you prune, merge, and retain skills using evidence instead of gut feel.

It targets requests such as:

- `audit my skills`
- `@bot 帮我清理 skills`
- "Which skills are unused or redundant?"

## What It Produces

A report in this shape:

- install/usage summary
- long-unused skills
- redundancy groups
- keep/delete/merge/confirm buckets
- estimated cleanup benefit
- reversible disable script

Example headline format:

```text
📊 Skill 健康报告（2026-06-06 扫描）
总安装：42 个
本月被使用：18 个
长期未用：24 个（57%）
冗余重复：3 组
预计清理收益：context -15%, 选择准确率 +8%
```

## Core Modules

1. 使用频率分析（7d/30d/90d）
2. 效果评估（失败率、纠正迹象、token 占比）
3. 冗余检测（描述相似度、共现、关键词重叠）
4. 清理建议生成（带理由和风险标记）
5. 一键执行（先生成脚本，确认后执行）

## Suggested CLI

```bash
python3 skills/skill-health-audit/scripts/generate_skill_health_report.py \
  --skills-dir skills \
  --logs skills/skill-health-audit/examples/sample-skill-usage.json \
  --scan-date 2026-06-06 \
  --output-report /tmp/skill-health-report.md \
  --output-disable-script /tmp/disable-skills.sh
```

## Output Policy

- Never auto-delete skills during analysis.
- Disable script must be reversible (move to backup folder).
- Execute disable script only after explicit user confirmation.

## Repository Layout

```text
skill-health-audit/
├── README.md
├── SKILL.md
├── evals/
│   └── evals.json
├── examples/
│   ├── sample-skill-usage.json
│   └── sample-report.md
├── references/
│   └── methodology.md
└── scripts/
    └── generate_skill_health_report.py
```

## Verification

Run:

```bash
python3 skills/skill-health-audit/scripts/generate_skill_health_report.py \
  --skills-dir skills \
  --logs skills/skill-health-audit/examples/sample-skill-usage.json \
  --scan-date 2026-06-06 \
  --output-report /tmp/skill-health-report.md \
  --output-disable-script /tmp/disable-skills.sh
```

Expected:

- report file exists and includes four recommendation buckets
- disable script exists and includes backup move operations
- all recommendation rows include reasons
