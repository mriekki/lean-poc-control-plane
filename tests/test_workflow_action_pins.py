from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
FLOATING_ACTION = re.compile(r"uses:\s+actions/[^\s]+@v\d+\b")
PINNED_ACTION = re.compile(r"uses:\s+actions/[^\s]+@[0-9a-f]{40}(?:\s+#\s+v\d+)?$")


class WorkflowActionPinTests(unittest.TestCase):
    def test_first_party_actions_are_pinned_to_exact_commits(self) -> None:
        floating: list[str] = []
        malformed: list[str] = []
        seen = 0
        for path in sorted(WORKFLOWS.glob("*.yml")):
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if "uses: actions/" not in line:
                    continue
                seen += 1
                if FLOATING_ACTION.search(line):
                    floating.append(f"{path.name}:{line_number}:{line.strip()}")
                if not PINNED_ACTION.search(line.strip()):
                    malformed.append(f"{path.name}:{line_number}:{line.strip()}")
        self.assertGreater(seen, 0)
        self.assertEqual(floating, [])
        self.assertEqual(malformed, [])


if __name__ == "__main__":
    unittest.main()
