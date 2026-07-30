from __future__ import annotations

import argparse
import json
from pathlib import Path

from .quality import validate_dataset
from .report import build_report, load_deals, summarize


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ci-lab",
        description="Validate and summarize synthetic deal-level conversation data.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate", help="run schema-like quality checks")
    validate.add_argument("input", type=Path)

    report = subcommands.add_parser("report", help="generate a traceable report")
    report.add_argument("input", type=Path)
    report.add_argument("--output", type=Path)
    report.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    records = load_deals(args.input)

    if args.command == "validate":
        failures = validate_dataset(records)
        if failures:
            print(json.dumps(failures, ensure_ascii=False, indent=2))
            return 1
        print(f"OK: {len(records)} records passed validation")
        return 0

    summary = summarize(records)
    output = (
        json.dumps(summary, ensure_ascii=False, indent=2)
        if args.as_json
        else build_report(summary)
    )
    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(output)
    return 0
