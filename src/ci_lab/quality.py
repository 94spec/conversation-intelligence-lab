from __future__ import annotations

from collections.abc import Iterable

ALLOWED = {
    "customer_need": {
        "career_change",
        "career_growth",
        "income_growth",
        "remote_work",
        "exploration",
    },
    "readiness": {"high", "medium", "low"},
    "purchase_status": {"buying", "next_step", "exploring", "refused"},
    "objection_handling": {"full", "partial", "not_handled", "not_applicable"},
}
ALLOWED_OBJECTIONS = {"price", "time", "trust", "needs_comparison"}
REQUIRED = {
    "deal_id",
    "month",
    "customer_need",
    "readiness",
    "purchase_status",
    "objections",
    "objection_handling",
    "competitor_mentioned",
    "next_step",
}


def validate_record(record: dict) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED - record.keys()
    if missing:
        errors.append(f"missing fields: {', '.join(sorted(missing))}")
        return errors

    if not isinstance(record["deal_id"], str) or not record["deal_id"].startswith("SYN-"):
        errors.append("deal_id must use the synthetic SYN- prefix")
    if record["month"] not in {"2026-03", "2026-04", "2026-05"}:
        errors.append("month must be one of the demo periods")

    for field, values in ALLOWED.items():
        if record[field] not in values:
            errors.append(f"{field} has unsupported value: {record[field]!r}")

    objections = record["objections"]
    if not isinstance(objections, list):
        errors.append("objections must be a list")
    elif set(objections) - ALLOWED_OBJECTIONS:
        errors.append("objections contain unsupported values")

    if not isinstance(record["competitor_mentioned"], bool):
        errors.append("competitor_mentioned must be boolean")
    if not isinstance(record["next_step"], bool):
        errors.append("next_step must be boolean")

    if not objections and record["objection_handling"] != "not_applicable":
        errors.append("objection handling must be not_applicable when no objection exists")
    if objections and record["objection_handling"] == "not_applicable":
        errors.append("objection handling cannot be not_applicable when objections exist")
    if record["purchase_status"] == "next_step" and not record["next_step"]:
        errors.append("purchase_status=next_step requires next_step=true")
    if record["purchase_status"] == "buying" and record["readiness"] == "low":
        errors.append("low readiness conflicts with purchase_status=buying")

    return errors


def validate_dataset(records: Iterable[dict]) -> dict[str, list[str]]:
    failures: dict[str, list[str]] = {}
    seen: set[str] = set()
    for index, record in enumerate(records, start=1):
        deal_id = str(record.get("deal_id", f"row-{index}"))
        errors = validate_record(record)
        if deal_id in seen:
            errors.append("duplicate deal_id")
        seen.add(deal_id)
        if errors:
            failures[deal_id] = errors
    return failures
