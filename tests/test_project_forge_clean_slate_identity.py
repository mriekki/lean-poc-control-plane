from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


class ProjectForgeCleanSlateIdentityTests(unittest.TestCase):
    def test_current_tree_has_no_retired_product_identity(self) -> None:
        root = Path(__file__).resolve().parents[1]

        lower = "le" + "an"
        title = lower.title()
        upper = lower.upper()

        pattern = re.compile(
            rf"(?<![A-Za-z0-9])"
            rf"(?:{lower}|{title}|{upper})"
            rf"(?:(?=[^A-Za-z0-9]|$)|(?=[A-Z]))"
            rf"|{title}(?=[A-Z])"
        )

        retired_generation = "generate-" + "p" + "oc"

        result = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        hits: list[str] = []

        for rel in result.stdout.splitlines():
            if not rel:
                continue

            if pattern.search(rel) or retired_generation in rel:
                hits.append(f"PATH:{rel}")

            path = root / rel
            if not path.is_file():
                continue

            try:
                lines = path.read_text(
                    encoding="utf-8",
                ).splitlines()
            except (UnicodeDecodeError, OSError):
                continue

            for number, line in enumerate(lines, 1):
                if pattern.search(line) or retired_generation in line:
                    hits.append(
                        f"{rel}:{number}:{line.strip()}"
                    )

        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
