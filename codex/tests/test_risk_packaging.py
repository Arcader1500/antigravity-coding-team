import os
from pathlib import Path
import subprocess
import sys
import tomllib
import unittest
from codex.scripts.validate import PROFILE_MODELS


ROOT = Path(__file__).resolve().parents[2]


class RiskPackagingTests(unittest.TestCase):
    def test_source_only_validation_does_not_require_or_claim_installed_parity(self):
        env = os.environ.copy()
        env["USERPROFILE"] = str(ROOT / "codex/tests/nonexistent-user-profile")
        result = subprocess.run(
            [sys.executable, str(ROOT / "codex/scripts/validate.py"), "--source-only"],
            cwd=ROOT, env=env, capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("source-only validation", result.stdout)
        self.assertIn("installed parity was not checked", result.stdout)
        self.assertNotIn("installed cache parity passed", result.stdout)

    def test_installed_parity_is_an_explicit_validator_mode(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "codex/scripts/validate.py"), "--help"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("--installed-parity", result.stdout)

    def test_helpers_are_byte_identical_and_both_installers_bundle_the_runtime(self):
        codex_helper = ROOT / "codex/scripts/risk_store.py"
        antigravity_helper = ROOT / "antigravity/scripts/risk_store.py"
        self.assertTrue(codex_helper.is_file())
        self.assertTrue(antigravity_helper.is_file())
        self.assertEqual(codex_helper.read_bytes(), antigravity_helper.read_bytes())
        codex_installer = (ROOT / "codex/install.ps1").read_text(encoding="utf-8")
        self.assertIn('Copy-Item "$PSScriptRoot\\*" $pluginTarget -Recurse -Force', codex_installer)
        antigravity_installer = (ROOT / "antigravity/install.ps1").read_text(encoding="utf-8")
        self.assertIn('& $AgyPath plugin install "$PluginDir"', antigravity_installer)

    def test_risk_estimator_instruction_bodies_match_across_native_formats(self):
        codex = tomllib.loads((ROOT / "codex/agents/risk-estimator.toml").read_text(encoding="utf-8"))
        markdown = (ROOT / "antigravity/agents/risk-estimator.md").read_text(encoding="utf-8")
        _, _, body = markdown.split("---", 2)
        self.assertEqual(codex["developer_instructions"].strip(), body.strip())

    def test_nine_source_roles_and_profile_settings_are_separate_contracts(self):
        agents = ROOT / "codex/agents"
        self.assertEqual(9, len(list(agents.glob("*.toml"))))
        source_planner = tomllib.loads((agents / "planner.toml").read_text(encoding="utf-8"))
        self.assertEqual(("gpt-6-luna", "high"),
                         (source_planner["model"], source_planner["model_reasoning_effort"]))
        self.assertEqual({"planner": ("gpt-6.1-sol", "medium"),
                          "orchestrator": ("gpt-6.1-sol", "low")}, PROFILE_MODELS)
        validator = (ROOT / "codex/scripts/validate.py").read_text(encoding="utf-8")
        self.assertIn("SOURCE_MODELS", validator)
        self.assertIn("PROFILE_MODELS", validator)


if __name__ == "__main__":
    unittest.main()
