#!/usr/bin/env python3
"""Run minimal trigger regression checks for runtime-observability."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


POSITIVE_PATTERNS = [
    "runtime-observability",
    "session log",
    "session id",
    "agent trace",
    "execution timeline",
    "token breakdown",
    "token spike",
    "redundant tool",
    "post-run",
    "执行时间线",
    "session_logs",
    "复盘",
    "执行过程",
    "问题清单",
    "质量评分",
]

NEGATIVE_PATTERNS = [
    "opentelemetry",
    "grafana",
    "apm",
    "instrumentation",
    "metrics",
    "埋点",
    "监控平台",
    "trace 方案",
    "metrics 方案",
]


def load_evals(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def should_trigger(prompt: str) -> tuple[bool, list[str], list[str]]:
    lowered = prompt.lower()
    positive_hits = [pattern for pattern in POSITIVE_PATTERNS if pattern.lower() in lowered]
    negative_hits = [pattern for pattern in NEGATIVE_PATTERNS if pattern.lower() in lowered]

    if negative_hits and not positive_hits:
        return False, positive_hits, negative_hits
    if positive_hits and not negative_hits:
        return True, positive_hits, negative_hits
    if positive_hits and negative_hits:
        return len(positive_hits) > len(negative_hits), positive_hits, negative_hits
    return False, positive_hits, negative_hits


def expected_trigger(eval_case: dict[str, Any]) -> bool:
    expected = str(eval_case.get("expected_output", ""))
    return "should not trigger" not in expected.lower()


def evaluate_case(eval_case: dict[str, Any]) -> dict[str, Any]:
    prompt = str(eval_case["prompt"])
    expected = expected_trigger(eval_case)
    predicted, positive_hits, negative_hits = should_trigger(prompt)
    passed = expected == predicted
    reason = (
        f"positive_hits={positive_hits or ['none']}; negative_hits={negative_hits or ['none']}"
    )
    return {
        "id": eval_case["id"],
        "prompt": prompt,
        "expected_trigger": expected,
        "predicted_trigger": predicted,
        "passed": passed,
        "reason": reason,
    }


def build_markdown(skill_name: str, results: list[dict[str, Any]]) -> str:
    passed = sum(1 for result in results if result["passed"])
    total = len(results)
    lines = [
        f"# {skill_name} Trigger Eval Report",
        "",
        "## Summary",
        f"- Passed: {passed}/{total}",
        f"- Failed: {total - passed}/{total}",
        "",
        "## Results",
        "| ID | Expected | Predicted | Passed | Notes |",
        "|----|----------|-----------|--------|-------|",
    ]
    for result in results:
        lines.append(
            f"| {result['id']} | {result['expected_trigger']} | {result['predicted_trigger']} | "
            f"{result['passed']} | {result['reason']} |"
        )
    lines.extend(["", "## Failure Details"])
    failures = [result for result in results if not result["passed"]]
    if not failures:
        lines.append("- None")
    else:
        for result in failures:
            lines.append(
                f"- Eval {result['id']}: expected {result['expected_trigger']} but predicted "
                f"{result['predicted_trigger']} for prompt `{result['prompt']}`; {result['reason']}"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run minimal trigger regression checks")
    parser.add_argument("--evals", required=True, help="Path to evals.json")
    parser.add_argument("--output-json", required=True, help="Path to JSON results")
    parser.add_argument("--output-md", required=True, help="Path to markdown report")
    args = parser.parse_args()

    evals_path = Path(args.evals)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)

    payload = load_evals(evals_path)
    results = [evaluate_case(eval_case) for eval_case in payload.get("evals", [])]
    report = {
        "skill_name": payload.get("skill_name", "unknown"),
        "passed": sum(1 for result in results if result["passed"]),
        "total": len(results),
        "results": results,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2) + "\n")
    output_md.write_text(build_markdown(report["skill_name"], results))
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
