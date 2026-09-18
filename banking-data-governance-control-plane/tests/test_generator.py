from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from governance_control.generator import generate_catalog
from governance_control.io_utils import read_csv


class CatalogGeneratorTests(unittest.TestCase):
    def test_catalog_population(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = generate_catalog(root)
            self.assertEqual(manifest["datasets"], 12)
            self.assertEqual(manifest["columns"], 96)
            self.assertEqual(len(read_csv(root / "grants.csv")), 12)
            self.assertTrue(manifest["synthetic_data"])

    def test_generation_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_path, second_path = Path(first), Path(second)
            generate_catalog(first_path)
            generate_catalog(second_path)
            for filename in ("datasets.csv", "columns.csv", "lineage.csv", "grants.csv", "identities.csv"):
                self.assertEqual((first_path / filename).read_bytes(), (second_path / filename).read_bytes())


if __name__ == "__main__":
    unittest.main()

