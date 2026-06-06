#!/usr/bin/env python3
"""Generate a skill health report and a reversible disable script."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


@dataclass
class SkillRow:
    name: str
    description: str
    calls_7d: int
    calls_30d: int
    calls_90d: int
    last_used_days: int
    failure_rate: float
    corrections: int
    token_share: float
    covered_by: list[str]


def _load_dataset(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if "skills" not in data or not isinstance(data["skills"], list):
        raise ValueError("dataset must include a `skills` list")
    return data


def _parse_skill(row: dict[str, Any]) -> SkillRow:
    return SkillRow(
        name=str(row.get("name", "unknown")),
        description=str(row.get("description", "")),
        calls_7d=int(row.get("calls_7d", 0) or 0),
        calls_30d=int(row.get("calls_30d", 0) or 0),
        calls_90d=int(row.get("calls_90d", 0) or 0),
        last_used_days=int(row.get("last_used_days", 9999) or 9999),
        failure_rate=float(row.get("failure_rate", 0.0) or 0.0),
        corrections=int(row.get("corrections", 0) or 0),
        token_share=float(row.get("token_share", 0.0) or 0.0),
        covered_by=[str(x) for x in (row.get("covered_by") or [])],
    )


def _recommendation_bucket(skill: SkillRow) -> str:
    protected_keywords = ["vetter", "security", "incident", "compliance", "emergency"]
    if any(k in skill.name.lower() for k in protected_keywords):
        if skill.calls_30d == 0:
            return "confirm"

    if skill.calls_30d == 0 and skill.last_used_days >= 60 and skill.covered_by:
        return "delete"

    if skill.calls_7d > 0 or skill.calls_30d >= 3:
        return "keep"

    if skill.calls_90d <= 1 and skill.last_used_days >= 45 and skill.covered_by:
        return "delete"

    return "confirm"


def _reason_for_skill(skill: SkillRow, bucket: str) -> str:
    if bucket == "delete":
        if skill.last_used_days >= 60:
            if skill.covered_by:
                return f"{skill.last_used_days} 天未调用，且被「{skill.covered_by[0]}」覆盖"
            return f"{skill.last_used_days} 天未调用"
        if skill.covered_by:
            return f"低频且可被「{skill.covered_by[0]}」覆盖"
        return "长期低频且无明显独特价值"

    if bucket == "keep":
        if skill.calls_7d > 0:
            return f"本周调用 {skill.calls_7d} 次"
        return f"30 天调用 {skill.calls_30d} 次，保留活跃价值"

    if bucket == "confirm":
        if "vetter" in skill.name.lower() or "security" in skill.name.lower():
            return "60 天未用，但属于安全/风控类，可能是低频高价值"
        return "证据不足以自动删除，建议人工确认"

    return "可合并候选"


def _estimate_benefit(total: int, delete_count: int, group_count: int) -> tuple[int, int]:
    if total <= 0:
        return 0, 0
    context_reduction = int(round((delete_count / total) * 25))
    accuracy_gain = int(round(min(12, delete_count * 0.3 + group_count * 0.8)))
    return context_reduction, accuracy_gain


def _render_report(
    scan_date: str,
    total_count: int,
    active_month: int,
    long_unused: list[tuple[SkillRow, str]],
    merge_groups: list[dict[str, Any]],
    keep_list: list[tuple[SkillRow, str]],
    confirm_list: list[tuple[SkillRow, str]],
    context_reduction: int,
    accuracy_gain: int,
) -> str:
    long_unused_pct = int(round((len(long_unused) / total_count) * 100)) if total_count else 0

    lines = [
        f"📊 Skill 健康报告（{scan_date} 扫描）",
        f"总安装：{total_count} 个",
        f"本月被使用：{active_month} 个",
        f"长期未用：{len(long_unused)} 个（{long_unused_pct}%）",
        f"冗余重复：{len(merge_groups)} 组",
        f"预计清理收益：context -{context_reduction}%, 选择准确率 +{accuracy_gain}%",
        "---",
        f"🟢 强烈建议删除（{len(long_unused)}个）",
    ]

    for skill, reason in long_unused:
        lines.append(f"- 「{skill.name}」：{reason}")

    lines.append(f"🟡 建议合并（{len(merge_groups)} 组）")
    for group in merge_groups:
        skills = group.get("skills", [])
        reason = group.get("reason", "功能重叠")
        if len(skills) >= 2:
            joined = "」+「".join(skills)
            lines.append(f"- 「{joined}」：{reason}")

    lines.append(f"🟢 建议保留（{len(keep_list)} 个）")
    for skill, reason in keep_list:
        lines.append(f"- 「{skill.name}」：{reason}")

    lines.append(f"❓ 需要你确认（{len(confirm_list)} 个）")
    for skill, reason in confirm_list:
        lines.append(f"- 「{skill.name}」：{reason} → 保留？")

    return "\n".join(lines) + "\n"


def _render_disable_script(skills_dir: Path, delete_rows: list[SkillRow]) -> str:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        f'SKILLS_DIR="{skills_dir}"',
        'BACKUP_DIR="$SKILLS_DIR/.disabled-$(date +%Y%m%d-%H%M%S)"',
        'mkdir -p "$BACKUP_DIR"',
        'echo "Backup dir: $BACKUP_DIR"',
        "",
    ]

    for row in delete_rows:
        lines.extend(
            [
                f'if [ -d "$SKILLS_DIR/{row.name}" ]; then',
                f'  mv "$SKILLS_DIR/{row.name}" "$BACKUP_DIR/"',
                f'  echo "Disabled: {row.name}"',
                "else",
                f'  echo "Skip: {row.name} (not found)"',
                "fi",
                "",
            ]
        )

    lines.append('echo "Done. To rollback, move folders from $BACKUP_DIR back to $SKILLS_DIR"')
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate skill health report")
    parser.add_argument("--skills-dir", required=True, help="Installed skills root directory")
    parser.add_argument("--logs", required=True, help="JSON dataset with skill usage signals")
    parser.add_argument("--scan-date", default=str(date.today()), help="Report scan date")
    parser.add_argument("--output-report", required=True, help="Output report path")
    parser.add_argument("--output-disable-script", required=True, help="Output disable script path")
    args = parser.parse_args()

    skills_dir = Path(args.skills_dir)
    dataset_path = Path(args.logs)
    report_path = Path(args.output_report)
    disable_script_path = Path(args.output_disable_script)

    dataset = _load_dataset(dataset_path)
    rows = [_parse_skill(x) for x in dataset["skills"]]
    merge_groups = dataset.get("redundancy_groups", [])

    delete_rows: list[SkillRow] = []
    keep_rows: list[SkillRow] = []
    confirm_rows: list[SkillRow] = []

    delete_with_reason: list[tuple[SkillRow, str]] = []
    keep_with_reason: list[tuple[SkillRow, str]] = []
    confirm_with_reason: list[tuple[SkillRow, str]] = []

    for row in rows:
        bucket = _recommendation_bucket(row)
        reason = _reason_for_skill(row, bucket)
        if bucket == "delete":
            delete_rows.append(row)
            delete_with_reason.append((row, reason))
        elif bucket == "keep":
            keep_rows.append(row)
            keep_with_reason.append((row, reason))
        else:
            confirm_rows.append(row)
            confirm_with_reason.append((row, reason))

    total_count = len(rows)
    active_month = sum(1 for row in rows if row.calls_30d > 0)

    context_reduction, accuracy_gain = _estimate_benefit(
        total=total_count,
        delete_count=len(delete_rows),
        group_count=len(merge_groups),
    )

    report_text = _render_report(
        scan_date=args.scan_date,
        total_count=total_count,
        active_month=active_month,
        long_unused=delete_with_reason,
        merge_groups=merge_groups,
        keep_list=keep_with_reason,
        confirm_list=confirm_with_reason,
        context_reduction=context_reduction,
        accuracy_gain=accuracy_gain,
    )

    disable_script = _render_disable_script(skills_dir=skills_dir, delete_rows=delete_rows)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    disable_script_path.parent.mkdir(parents=True, exist_ok=True)

    report_path.write_text(report_text)
    disable_script_path.write_text(disable_script)
    os.chmod(disable_script_path, 0o755)

    print(f"Report written to: {report_path}")
    print(f"Disable script written to: {disable_script_path}")
    print(
        "Summary: "
        f"total={total_count}, active_30d={active_month}, delete={len(delete_rows)}, "
        f"merge_groups={len(merge_groups)}, keep={len(keep_rows)}, confirm={len(confirm_rows)}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
