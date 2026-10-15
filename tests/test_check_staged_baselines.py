from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.check_staged_baselines import StagedBaselineError, validate_staged_baselines


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def make_repo(root: Path, attributes: str) -> tuple[bytes, str]:
    git(root, "init")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "core.autocrlf", "false")

    managed = b"line one\r\nline two\r\n"
    expected_hash = hashlib.sha256(managed).hexdigest()

    (root / ".gitattributes").write_text(attributes, encoding="utf-8")
    (root / "managed.txt").write_bytes(managed)

    write_json(
        root / "POC_BOOTSTRAP.json",
        {
            "generation": {
                "lean": {
                    "package": "@mriekki/lean",
                    "version": "0.1.0",
                    "profile": "greenfield-poc",
                    "integrity": "sha512-test",
                }
            }
        },
    )
    write_json(
        root / "LEAN_BASELINE.json",
        {
            "schemaVersion": 1,
            "package": "@mriekki/lean",
            "version": "0.1.0",
            "profile": "greenfield-poc",
            "components": {
                "core": {
                    "repository": "mriekki/lean-agentic-core",
                    "commit": "a" * 40,
                    "version": "1.10.0",
                    "distribution": "greenfield-workspace",
                }
            },
        },
    )
    write_json(
        root / "CORE_BASELINE.json",
        {
            "schemaVersion": 1,
            "coreRepository": "mriekki/lean-agentic-core",
            "coreCommit": "a" * 40,
            "coreVersion": "1.10.0",
            "distribution": "greenfield-workspace",
            "managedPaths": [
                {
                    "source": "managed.txt",
                    "path": "managed.txt",
                    "sha256": expected_hash,
                }
            ],
        },
    )

    git(root, "add", "-A")
    return managed, expected_hash


class StagedBaselineTests(unittest.TestCase):
    def test_rejects_git_normalized_managed_blob(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            managed, _ = make_repo(root, "* text=auto eol=lf\n")

            staged = subprocess.run(
                ["git", "-C", str(root), "show", ":managed.txt"],
                check=True,
                capture_output=True,
            ).stdout
            self.assertNotEqual(managed, staged)

            with self.assertRaisesRegex(StagedBaselineError, "Staged managed file drift: managed.txt"):
                validate_staged_baselines(root)

    def test_accepts_byte_preserved_managed_blob(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            managed, _ = make_repo(root, "* text=auto eol=lf\nmanaged.txt -text\n")

            staged = subprocess.run(
                ["git", "-C", str(root), "show", ":managed.txt"],
                check=True,
                capture_output=True,
            ).stdout
            self.assertEqual(managed, staged)
            self.assertEqual(1, validate_staged_baselines(root))


class GenerateWorkflowContractTests(unittest.TestCase):
    def test_generation_checks_staged_managed_baselines_before_commit(self):
        workflow = Path(".github/workflows/generate-poc.yml").read_text(encoding="utf-8")
        staged_check = 'python tools/check_staged_baselines.py --root "$target"'
        commit = 'git -C "$target" commit -m "Generate ${PROJECT_SLUG} workspace baseline"'

        self.assertIn(staged_check, workflow)
        self.assertIn(commit, workflow)
        self.assertLess(workflow.index(staged_check), workflow.index(commit))


if __name__ == "__main__":
    unittest.main()
