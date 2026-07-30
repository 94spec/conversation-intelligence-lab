from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ci_lab.quality import validate_record  # noqa: E402
from ci_lab.report import build_report, load_deals, summarize  # noqa: E402


class ConversationIntelligenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = load_deals(ROOT / "data" / "synthetic_deals.jsonl")
        cls.summary = summarize(cls.records)

    def test_all_fixture_records_are_valid(self) -> None:
        self.assertEqual(sum(bool(validate_record(item)) for item in self.records), 0)

    def test_monthly_denominators_are_explicit(self) -> None:
        self.assertEqual(self.summary["dataset"]["total_deals"], 18)
        self.assertEqual(
            [month["n"] for month in self.summary["monthly"].values()],
            [6, 6, 6],
        )

    def test_expected_directional_change(self) -> None:
        changes = self.summary["change_first_to_last_pp"]
        self.assertLess(changes["high_readiness_pct"], 0)
        self.assertGreater(changes["next_step_pct"], 0)

    def test_objection_handling_uses_objection_bearing_deals(self) -> None:
        months = list(self.summary["monthly"].values())
        self.assertEqual(
            [month["deals_with_objections"] for month in months],
            [5, 5, 5],
        )
        self.assertEqual(
            [month["full_objection_handling_count"] for month in months],
            [2, 1, 0],
        )
        self.assertEqual(
            [month["full_objection_handling_pct"] for month in months],
            [40.0, 20.0, 0.0],
        )

    def test_objection_handling_is_na_without_objections(self) -> None:
        record = dict(self.records[0])
        record["deal_id"] = "SYN-999"
        record["objections"] = []
        record["objection_handling"] = "not_applicable"

        summary = summarize([record])
        month = summary["monthly"][record["month"]]
        self.assertEqual(month["deals_with_objections"], 0)
        self.assertEqual(month["full_objection_handling_count"], 0)
        self.assertIsNone(month["full_objection_handling_pct"])
        self.assertIn("N/A (0/0)", build_report(summary))

    def test_empty_dataset_has_clear_error(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "dataset must contain at least one deal",
        ):
            summarize([])

    def test_inconsistent_record_is_flagged(self) -> None:
        invalid = dict(self.records[0])
        invalid["readiness"] = "low"
        self.assertIn(
            "low readiness conflicts with purchase_status=buying",
            validate_record(invalid),
        )

    def test_report_contains_causal_boundary(self) -> None:
        report = build_report(self.summary)
        self.assertIn("descriptive, not causal", report)
        self.assertIn("traceable", report)


if __name__ == "__main__":
    unittest.main()
