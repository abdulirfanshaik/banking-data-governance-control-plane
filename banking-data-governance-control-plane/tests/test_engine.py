from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from governance_control.engine import assess_governance
from governance_control.generator import generate_catalog
from governance_control.io_utils import read_csv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class GovernanceEngineTests(unittest.TestCase):
    def test_expected_negative_controls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inputs, outputs = root / "input", root / "output"
            generate_catalog(inputs)
            summary = assess_governance(inputs, outputs, PROJECT_ROOT / "config" / "policies.json")
            self.assertEqual(summary["certification_status"], "NON_COMPLIANT")
            self.assertEqual(summary["violations"], {"total": 11, "critical": 1, "high": 9, "medium": 1})
            self.assertEqual(summary["access_review"], {"keep": 7, "review": 1, "revoke": 4})
            self.assertEqual(summary["coverage"]["dataset_ownership_pct"], 91.67)
            self.assertEqual(summary["coverage"]["restricted_masking_pct"], 75.0)

    def test_findings_are_traceable_and_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inputs, outputs = root / "input", root / "output"
            generate_catalog(inputs)
            assess_governance(inputs, outputs, PROJECT_ROOT / "config" / "policies.json")
            violations = read_csv(outputs / "policy_violations.csv")
            self.assertEqual(len(violations), 11)
            self.assertTrue(all(row["object_name"] and row["remediation"] for row in violations))
            connection = sqlite3.connect(outputs / "governance_controls.db")
            try:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM policy_violations").fetchone()[0], 11)
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM policy_violations WHERE rule_id = 'GOV-MASK-001'").fetchone()[0],
                    3,
                )
            finally:
                connection.close()

    def test_every_grant_receives_a_review_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inputs, outputs = root / "input", root / "output"
            generate_catalog(inputs)
            assess_governance(inputs, outputs, PROJECT_ROOT / "config" / "policies.json")
            decisions = read_csv(outputs / "access_review.csv")
            self.assertEqual(len(decisions), 12)
            self.assertTrue(all(row["decision"] in {"KEEP", "REVIEW", "REVOKE"} for row in decisions))


if __name__ == "__main__":
    unittest.main()

