"""Validate the public quick-start demonstration without Claude Code."""
from pathlib import Path
import subprocess
import sys
import unittest

REPO = Path(__file__).resolve().parents[1]
DEMO = REPO / "examples" / "demo_evidence_gate.py"

class PublicQuickDemoTest(unittest.TestCase):
    def test_demonstration_is_reproducible(self):
        result = subprocess.run(
            [sys.executable, str(DEMO)],
            cwd=REPO, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Without Read: DENIED", result.stdout)
        self.assertIn("First results write after Read: ALLOWED", result.stdout)
        self.assertIn("Second results write, no new Read: DENIED", result.stdout)
        self.assertIn("Local hook-accounting demonstration only", result.stdout)

if __name__ == "__main__":
    unittest.main()
