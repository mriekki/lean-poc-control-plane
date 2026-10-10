from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("request", ROOT / "tools" / "request.py")
assert SPEC and SPEC.loader
request = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(request)


class RequestTests(unittest.TestCase):
    def event(self, *, author: str = "mriekki", title: str = "[generate-poc] mriekki/example-poc") -> dict:
        return {
            "issue": {
                "number": 42,
                "title": title,
                "body": "",
                "user": {"login": author},
            }
        }

    def test_valid_owner_request(self) -> None:
        values = request.parse_request(self.event(), {"mriekki"})
        self.assertEqual(values["target_repository"], "mriekki/example-poc")
        self.assertEqual(values["request_author"], "mriekki")

    def test_author_must_match_target_owner(self) -> None:
        with self.assertRaises(request.RequestError):
            request.parse_request(self.event(author="someone-else"), {"mriekki", "someone-else"})

    def test_owner_must_be_allowlisted(self) -> None:
        event = self.event(author="kyle", title="[generate-poc] kyle/example-poc")
        with self.assertRaises(request.RequestError):
            request.parse_request(event, {"mriekki"})

    def test_foundational_repository_is_rejected(self) -> None:
        event = self.event(title="[generate-poc] mriekki/lean-poc-bootstrap")
        with self.assertRaises(request.RequestError):
            request.parse_request(event, {"mriekki"})

    def test_title_must_be_exact_owner_repo_shape(self) -> None:
        for title in (
            "generate-poc mriekki/example-poc",
            "[generate-poc] example-poc",
            "[generate-poc] mriekki/example-poc extra",
        ):
            with self.subTest(title=title):
                with self.assertRaises(request.RequestError):
                    request.parse_request(self.event(title=title), {"mriekki"})

    def test_allowed_owner_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "owners.json"
            path.write_text(json.dumps({"schemaVersion": 1, "owners": ["mriekki", "Kyle-Example"]}), encoding="utf-8")
            self.assertEqual(request.load_allowed_owners(path), {"mriekki", "kyle-example"})

    def test_workflow_uses_github_app_tokens_and_private_seed_manifest(self) -> None:
        workflow = (ROOT / ".github/workflows/generate-poc.yml").read_text(encoding="utf-8")
        self.assertIn("actions/create-github-app-token@v3", workflow)
        self.assertIn("APP_PRIVATE_KEY", workflow)
        self.assertIn("APP_CLIENT_ID", workflow)
        self.assertIn("POC_BOOTSTRAP.json", workflow)
        self.assertIn("remote_generation.py validate-manifest", workflow)
        self.assertIn("generate_snapshot.py", workflow)
        self.assertIn("permission-workflows: write", workflow)
        self.assertNotIn("LEAN_POC_AUTOMATION_TOKEN", workflow)
        self.assertNotIn("--force", workflow)


if __name__ == "__main__":
    unittest.main()
