from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = re.compile(r"(?i)(?:\bpocs?\b|poc[-_])")
TEXT_SUFFIXES = {".md", ".json", ".py", ".yml", ".yaml", ".txt"}
EXCLUDED = {
    "CHANGELOG.md",
    "tests/test_project_terminology.py",
}


class ProjectTerminologyTests(unittest.TestCase):
    def test_active_tree_uses_project_namespace(self) -> None:
        violations: list[str] = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            relative = path.relative_to(ROOT).as_posix()
            if relative in EXCLUDED:
                continue
            if FORBIDDEN.search(relative):
                violations.append(f"path: {relative}")
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                if FORBIDDEN.search(line):
                    violations.append(f"{relative}:{line_number}: {line.strip()}")
        self.assertEqual(
            violations,
            [],
            "Active predecessor Project terminology remains:\n" + "\n".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
