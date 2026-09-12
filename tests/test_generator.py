"""Tests for the private deployment renderer."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generate_deployment", ROOT / "scripts/generate_deployment.py")
assert SPEC and SPEC.loader
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class GeneratorTest(unittest.TestCase):
    def test_renders_working_battery_defaults_and_preserves_base_cameras(self) -> None:
        inventory = GENERATOR.read_inventory(ROOT / "config/inventory.example.yaml")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "generated"
            base = Path(temporary) / "frigate-base.yaml"
            base.write_text("cameras:\n  non_arlo:\n    enabled: true\n    detect:\n      fps: 3\n")
            GENERATOR.generate(inventory, output, "entry_123", base)

            mediamtx = yaml.safe_load((output / "camera-host/mediamtx/mediamtx.yml").read_text())
            path = mediamtx["paths"]["camera_1"]
            self.assertTrue(path["sourceOnDemand"])
            self.assertEqual(path["maxReaders"], 1)
            self.assertEqual(path["sourceOnDemandCloseAfter"], "1s")

            api = yaml.safe_load((output / "camera-host/arlo-cam-api/config.yaml").read_text())
            self.assertTrue(api["NotifyOnMotionTimeoutAlert"])
            self.assertTrue(api["MotionTimeoutWebHookUrl"].endswith("_motion_timeout"))

            merged = yaml.safe_load((output / "frigate/config.yml").read_text())
            self.assertTrue(merged["cameras"]["non_arlo"]["enabled"])
            self.assertFalse(merged["cameras"]["camera_1"]["enabled"])
            self.assertEqual(merged["cameras"]["camera_1"]["detect"]["fps"], 5)

    def test_deep_merge_replaces_scalars_and_recursively_merges_mappings(self) -> None:
        self.assertEqual(
            GENERATOR.deep_merge({"a": {"old": 1, "shared": 1}, "list": [1]}, {"a": {"new": 2, "shared": 2}, "list": [2]}),
            {"a": {"old": 1, "shared": 2, "new": 2}, "list": [2]},
        )


if __name__ == "__main__":
    unittest.main()
