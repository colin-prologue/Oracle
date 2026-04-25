"""Tests for scripts/test-hooks.py.

The harness reads installed settings.json files, finds configured hooks, and
runs them against synthesized stdin payloads. These tests exercise the harness
itself with controlled fixture settings, not against the user's real config.

Stdlib-only (unittest); the Hindsight project has no third-party test framework.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HARNESS = Path(__file__).resolve().parent.parent / "scripts" / "test-hooks.py"


def run_harness(settings_files):
    cmd = ["python3", str(HARNESS)]
    for p in settings_files:
        cmd.extend(["--settings", str(p)])
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return proc.returncode, proc.stdout, proc.stderr


class HarnessTests(unittest.TestCase):
    def test_empty_settings_yields_no_cases(self):
        with tempfile.TemporaryDirectory() as td:
            settings = Path(td) / "settings.json"
            settings.write_text(json.dumps({}))
            code, out, err = run_harness([settings])
            self.assertEqual(code, 0, msg=f"stderr={err}")
            self.assertTrue(
                "0 cases" in out or "no hooks" in out.lower(),
                msg=f"unexpected output: {out}",
            )

    def test_command_hook_runs_with_synthesized_payload(self):
        with tempfile.TemporaryDirectory() as td:
            sentinel = Path(td) / "fired.txt"
            settings = Path(td) / "settings.json"
            settings.write_text(json.dumps({
                "hooks": {
                    "PreToolUse": [{
                        "matcher": "Bash",
                        "hooks": [{
                            "type": "command",
                            "command": f"cat > {sentinel}",
                        }],
                    }],
                },
            }))
            code, out, err = run_harness([settings])
            self.assertEqual(code, 0, msg=f"stderr={err}")
            self.assertTrue(sentinel.exists(), "hook command did not run")
            payload = json.loads(sentinel.read_text())
            self.assertEqual(payload["tool_name"], "Bash")
            self.assertIn("command", payload["tool_input"])


if __name__ == "__main__":
    unittest.main()
