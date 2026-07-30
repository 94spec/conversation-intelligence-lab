"""Contract tests: the validation rules and the CLI surface.

test_report.py covers the aggregation maths. These tests cover the two other
things a consumer of this package depends on: that an invalid record is
rejected with a message naming the problem, and that the CLI reports failure
through its exit code rather than only in prose.
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ci_lab.cli import main  # noqa: E402
from ci_lab.quality import validate_dataset, validate_record  # noqa: E402
from ci_lab.report import load_deals  # noqa: E402

VALID = {
    "deal_id": "SYN-001",
    "month": "2026-03",
    "customer_need": "career_change",
    "readiness": "high",
    "purchase_status": "buying",
    "objections": ["price"],
    "objection_handling": "full",
    "competitor_mentioned": False,
    "next_step": True,
}


def record(**overrides: object) -> dict:
    item = dict(VALID)
    item.update(overrides)
    return item


class ValidationContractTests(unittest.TestCase):
    def test_reference_record_is_accepted(self) -> None:
        self.assertEqual(validate_record(record()), [])

    def test_missing_fields_are_listed_by_name(self) -> None:
        incomplete = record()
        del incomplete["readiness"]
        del incomplete["objections"]
        errors = validate_record(incomplete)
        self.assertEqual(len(errors), 1, "missing fields report once, not per rule")
        self.assertIn("readiness", errors[0])
        self.assertIn("objections", errors[0])

    def test_deal_id_must_stay_synthetic(self) -> None:
        # The prefix is the guard that keeps real deal identifiers out of a
        # public repository, so it is a contract, not a formatting preference.
        errors = validate_record(record(deal_id="00000000"))
        self.assertTrue(any("SYN-" in error for error in errors))

    def test_unsupported_enum_value_names_the_field(self) -> None:
        errors = validate_record(record(readiness="very high"))
        self.assertTrue(any(error.startswith("readiness has unsupported value") for error in errors))

    def test_objection_handling_must_match_objection_presence(self) -> None:
        no_objections = validate_record(record(objections=[], objection_handling="full"))
        self.assertTrue(any("not_applicable when no objection" in error for error in no_objections))

        with_objections = validate_record(record(objection_handling="not_applicable"))
        self.assertTrue(any("cannot be not_applicable" in error for error in with_objections))

    def test_outcome_contradictions_are_rejected(self) -> None:
        self.assertTrue(validate_record(record(purchase_status="buying", readiness="low")))
        self.assertTrue(validate_record(record(purchase_status="next_step", next_step=False)))

    def test_dataset_failures_are_keyed_by_deal(self) -> None:
        failures = validate_dataset([record(), record(deal_id="SYN-002", readiness="unknown")])
        self.assertEqual(list(failures), ["SYN-002"])


class LoaderTests(unittest.TestCase):
    def test_blank_lines_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deals.jsonl"
            path.write_text(json.dumps(VALID) + "\n\n", encoding="utf-8")
            self.assertEqual(len(load_deals(path)), 1)

    def test_broken_json_reports_the_line_number(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deals.jsonl"
            path.write_text(json.dumps(VALID) + "\n{oops\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "line 2"):
                load_deals(path)


class CommandLineTests(unittest.TestCase):
    def _run(self, argv: list[str]) -> tuple[int, str]:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(argv)
        return code, buffer.getvalue()

    def test_validate_passes_on_the_shipped_dataset(self) -> None:
        code, output = self._run(["validate", str(ROOT / "data" / "synthetic_deals.jsonl")])
        self.assertEqual(code, 0)
        self.assertIn("passed validation", output)

    def test_validate_fails_with_a_non_zero_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deals.jsonl"
            path.write_text(json.dumps(record(readiness="unknown")) + "\n", encoding="utf-8")
            code, output = self._run(["validate", str(path)])
        self.assertEqual(code, 1, "a failing dataset must be detectable by CI")
        self.assertIn("SYN-001", json.loads(output))

    def test_report_writes_a_file_and_json_alternative(self) -> None:
        source = str(ROOT / "data" / "synthetic_deals.jsonl")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "report.md"
            code, _ = self._run(["report", source, "--output", str(target)])
            self.assertEqual(code, 0)
            self.assertIn("|", target.read_text(encoding="utf-8"))

        code, output = self._run(["report", source, "--json"])
        self.assertEqual(code, 0)
        self.assertIn("monthly", json.loads(output))


if __name__ == "__main__":
    unittest.main()
