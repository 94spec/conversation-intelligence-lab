from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from .quality import validate_dataset


def load_deals(path: str | Path) -> list[dict]:
    records: list[dict] = []
    with Path(path).open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}: {exc.msg}") from exc
    return records


def _percent(part: int, total: int) -> float:
    return round(part * 100 / total, 1) if total else 0.0


def summarize(records: list[dict]) -> dict:
    if not records:
        raise ValueError("dataset must contain at least one deal")

    failures = validate_dataset(records)
    if failures:
        details = "; ".join(
            f"{deal_id}: {', '.join(errors)}"
            for deal_id, errors in sorted(failures.items())
        )
        raise ValueError(f"quality checks failed: {details}")

    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        grouped[record["month"]].append(record)

    months: dict[str, dict] = {}
    for month, deals in sorted(grouped.items()):
        total = len(deals)
        readiness = Counter(item["readiness"] for item in deals)
        outcomes = Counter(item["purchase_status"] for item in deals)
        needs = Counter(item["customer_need"] for item in deals)
        objections = Counter(
            objection for item in deals for objection in item["objections"]
        )
        objection_deals = [item for item in deals if item["objections"]]
        full_handling = sum(
            1
            for item in objection_deals
            if item["objection_handling"] == "full"
        )
        next_steps = sum(1 for item in deals if item["next_step"])
        competitor_mentions = sum(
            1 for item in deals if item["competitor_mentioned"]
        )

        months[month] = {
            "n": total,
            "high_readiness_pct": _percent(readiness["high"], total),
            "buying_pct": _percent(outcomes["buying"], total),
            "next_step_pct": _percent(next_steps, total),
            "deals_with_objections": len(objection_deals),
            "full_objection_handling_count": full_handling,
            "full_objection_handling_pct": (
                _percent(full_handling, len(objection_deals))
                if objection_deals
                else None
            ),
            "competitor_mention_pct": _percent(competitor_mentions, total),
            "needs": dict(needs.most_common()),
            "objections": dict(objections.most_common()),
            "deal_ids": [item["deal_id"] for item in deals],
        }

    first_month, last_month = min(months), max(months)
    comparisons = {}
    for metric in (
        "high_readiness_pct",
        "buying_pct",
        "next_step_pct",
        "full_objection_handling_pct",
    ):
        first_value = months[first_month][metric]
        last_value = months[last_month][metric]
        comparisons[metric] = (
            round(last_value - first_value, 1)
            if first_value is not None and last_value is not None
            else None
        )

    return {
        "dataset": {
            "total_deals": len(records),
            "months": len(months),
            "synthetic": True,
        },
        "monthly": months,
        "change_first_to_last_pp": comparisons,
        "interpretation_rule": (
            "Changes are observations in a synthetic dataset, not causal estimates."
        ),
    }


def build_report(summary: dict) -> str:
    lines = [
        "# Conversation Intelligence report",
        "",
        "> Dataset scope: synthetic. Metrics are descriptive, not causal.",
        "",
        f"Deals: **{summary['dataset']['total_deals']}**  ",
        f"Periods: **{summary['dataset']['months']}**",
        "",
        "## Monthly indicators",
        "",
        "| Month | N | High readiness | Buying now | Next step | Full objection handling among deals with objections | Competitor mentioned |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for month, data in summary["monthly"].items():
        handling = (
            f"{data['full_objection_handling_pct']:.1f}% "
            f"({data['full_objection_handling_count']}/{data['deals_with_objections']})"
            if data["full_objection_handling_pct"] is not None
            else "N/A (0/0)"
        )
        lines.append(
            "| {month} | {n} | {high:.1f}% | {buying:.1f}% | {next_step:.1f}% | "
            "{handling} | {competitor:.1f}% |".format(
                month=month,
                n=data["n"],
                high=data["high_readiness_pct"],
                buying=data["buying_pct"],
                next_step=data["next_step_pct"],
                handling=handling,
                competitor=data["competitor_mention_pct"],
            )
        )

    lines.extend(["", "## Change from first to last month", ""])
    labels = {
        "high_readiness_pct": "High readiness",
        "buying_pct": "Buying now",
        "next_step_pct": "Agreed next step",
        "full_objection_handling_pct": "Full objection handling",
    }
    for metric, change in summary["change_first_to_last_pp"].items():
        if change is None:
            lines.append(f"- {labels[metric]}: **N/A**")
            continue
        sign = "+" if change > 0 else ""
        lines.append(f"- {labels[metric]}: **{sign}{change:.1f} pp**")

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            summary["interpretation_rule"],
            "",
            "Each aggregate is traceable through `monthly.<month>.deal_ids` in the JSON output.",
        ]
    )
    return "\n".join(lines) + "\n"
