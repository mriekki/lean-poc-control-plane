#!/usr/bin/env python3
"""Validate staged diff whitespace while allowing intentional Markdown hard-break spaces.

The control plane must reject real staged-diff whitespace errors before publishing.
Markdown, however, legitimately uses trailing spaces to express hard line breaks. This
checker preserves strict `git diff --cached --check` behavior everywhere else and
ignores only the `trailing whitespace.` diagnostic for `.md` files.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

DIAGNOSTIC_RE = re.compile(r"^(.*):([0-9]+): (.+)$")
ALLOWED_MARKDOWN_DIAGNOSTIC = "trailing whitespace."


def filter_diff_check_output(output: str) -> tuple[list[str], list[str]]:
    """Return (errors, ignored) from `git diff --check` output.

    Git prints a diagnostic line followed by the offending added line for trailing
    whitespace. We drop both lines only when the diagnostic is exactly trailing
    whitespace in a Markdown file. Every other diagnostic remains an error.
    """

    lines = output.splitlines()
    errors: list[str] = []
    ignored: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        match = DIAGNOSTIC_RE.match(line)
        if match:
            path, _line_number, message = match.groups()
            if path.lower().endswith(".md") and message == ALLOWED_MARKDOWN_DIAGNOSTIC:
                ignored.append(line)
                index += 1
                if index < len(lines) and lines[index].startswith("+"):
                    ignored.append(lines[index])
                    index += 1
                continue

        errors.append(line)
        index += 1

    return errors, ignored


def check_staged_diff(root: Path) -> int:
    completed = subprocess.run(
        ["git", "-C", str(root), "diff", "--cached", "--check"],
        check=False,
        capture_output=True,
        text=True,
    )

    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    if completed.returncode == 0:
        return 0

    errors, ignored = filter_diff_check_output(output)
    if ignored:
        ignored_diagnostics = sum(1 for line in ignored if DIAGNOSTIC_RE.match(line))
        print(
            f"Allowed {ignored_diagnostics} Markdown trailing-whitespace diagnostic(s) "
            "for intentional Markdown formatting.",
            file=sys.stderr,
        )

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return completed.returncode or 2

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Git worktree root")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return check_staged_diff(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
