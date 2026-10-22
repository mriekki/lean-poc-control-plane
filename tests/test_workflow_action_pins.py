from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
ACTION_REF = re.compile(r"uses:\s+(actions/[A-Za-z0-9_.-]+)@([^\s#]+)")
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


class WorkflowActionPinTests(unittest.TestCase):
    def test_first_party_actions_are_immutably_pinned(self) -> None:
        failures: list[str] = []
        for path in sorted(WORKFLOWS.glob("*.yml")):
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                match = ACTION_REF.search(line)
                if match and not FULL_SHA.fullmatch(match.group(2)):
                    failures.append(
                        f"{path.relative_to(ROOT)}:{line_number}: {match.group(1)}@{match.group(2)}"
                    )
        self.assertEqual([], failures, "GitHub Actions must use exact commit SHAs")


if __name__ == "__main__":
    unittest.main()
