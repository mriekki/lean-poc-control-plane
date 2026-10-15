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
    def event(
        self,
        *,
        author: str = "mriekki",
        title: str = "[generate-poc] mriekki/example-poc",
        body: str = "",
    ) -> dict:
        return {
            "issue": {
                "number": 42,
                "title": title,
                "body": body,
                "user": {"login": author},
            }
        }

    def test_valid_owner_request(self) -> None:
        values = request.parse_request(self.event(), {"mriekki"})
        self.assertEqual(values["target_repository"], "mriekki/example-poc")
        self.assertEqual(values["request_author"], "mriekki")

    def test_valid_core_sync_request(self) -> None:
        event = self.event(title="[sync-core] mriekki/example-poc")
        values = request.parse_sync_request(event, {"mriekki"})
        self.assertEqual(values["target_repository"], "mriekki/example-poc")
        self.assertEqual(values["request_author"], "mriekki")

    def test_public_issue_body_must_be_empty(self) -> None:
        for body in (
            '{"state":"approved"}',
            "private product definition",
        ):
            with self.subTest(body=body):
                with self.assertRaises(request.RequestError):
                    request.parse_request(self.event(body=body), {"mriekki"})
                with self.assertRaises(request.RequestError):
                    request.parse_sync_request(
                        self.event(title="[sync-core] mriekki/example-poc", body=body),
                        {"mriekki"},
                    )

        values = request.parse_request(self.event(body="  \n"), {"mriekki"})
        self.assertEqual(values["target_repository"], "mriekki/example-poc")

    def test_author_must_match_target_owner(self) -> None:
        with self.assertRaises(request.RequestError):
            request.parse_request(self.event(author="someone-else"), {"mriekki", "someone-else"})
        with self.assertRaises(request.RequestError):
            request.parse_sync_request(
                self.event(author="someone-else", title="[sync-core] mriekki/example-poc"),
                {"mriekki", "someone-else"},
            )

    def test_owner_must_be_allowlisted(self) -> None:
        event = self.event(author="kyle", title="[generate-poc] kyle/example-poc")
        with self.assertRaises(request.RequestError):
            request.parse_request(event, {"mriekki"})

        sync_event = self.event(author="kyle", title="[sync-core] kyle/example-poc")
        with self.assertRaises(request.RequestError):
            request.parse_sync_request(sync_event, {"mriekki"})

    def test_foundational_repository_is_rejected(self) -> None:
        for title, parser in (
            ("[generate-poc] mriekki/lean-poc-bootstrap", request.parse_request),
            ("[sync-core] mriekki/family-meal-planner", request.parse_sync_request),
            ("[sync-core] mriekki/lean-agentic-core", request.parse_sync_request),
        ):
            with self.subTest(title=title):
                with self.assertRaises(request.RequestError):
                    parser(self.event(title=title), {"mriekki"})

    def test_title_must_be_exact_owner_repo_shape(self) -> None:
        for title in (
            "generate-poc mriekki/example-poc",
            "[generate-poc] example-poc",
            "[generate-poc] mriekki/example-poc extra",
        ):
            with self.subTest(title=title):
                with self.assertRaises(request.RequestError):
                    request.parse_request(self.event(title=title), {"mriekki"})

        for title in (
            "sync-core mriekki/example-poc",
            "[sync-core] example-poc",
            "[sync-core] mriekki/example-poc extra",
        ):
            with self.subTest(title=title):
                with self.assertRaises(request.RequestError):
                    request.parse_sync_request(self.event(title=title), {"mriekki"})

    def test_allowed_owner_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "owners.json"
            path.write_text(json.dumps({"schemaVersion": 1, "owners": ["mriekki", "Kyle-Example"]}), encoding="utf-8")
            self.assertEqual(request.load_allowed_owners(path), {"mriekki", "kyle-example"})

    def test_generation_workflow_uses_github_app_target_isolation_and_private_seed_manifest(self) -> None:
        workflow = (ROOT / ".github/workflows/generate-poc.yml").read_text(encoding="utf-8")
        self.assertIn("actions/create-github-app-token@v3", workflow)
        self.assertIn("APP_PRIVATE_KEY", workflow)
        self.assertIn("APP_CLIENT_ID", workflow)
        self.assertIn("POC_BOOTSTRAP.json", workflow)
        self.assertIn("remote_generation.py validate-manifest", workflow)
        self.assertIn("generate_snapshot.py", workflow)
        self.assertIn("permission-workflows: write", workflow)
        self.assertIn("repositories: lean-poc-bootstrap", workflow)
        self.assertNotIn("LEAN_POC_AUTOMATION_TOKEN", workflow)
        self.assertNotIn("--force", workflow)

    def test_generation_workflow_uses_exact_public_lean_artifact(self) -> None:
        workflow = (ROOT / ".github/workflows/generate-poc.yml").read_text(encoding="utf-8")
        self.assertIn("actions/setup-node@v6", workflow)
        self.assertIn("steps.manifest.outputs.lean_package", workflow)
        self.assertIn("steps.manifest.outputs.lean_version", workflow)
        self.assertIn("steps.manifest.outputs.lean_profile", workflow)
        self.assertIn("steps.manifest.outputs.lean_integrity", workflow)
        self.assertIn('npm pack "${LEAN_PACKAGE}@${LEAN_VERSION}"', workflow)
        self.assertIn("--ignore-scripts", workflow)
        self.assertIn("lean_package_generation.verify_integrity", workflow)
        self.assertIn("--lean-tarball", workflow)
        self.assertIn("LEAN_BASELINE.json", workflow)
        self.assertIn("check-managed-baselines.py", workflow)
        self.assertIn("CORE_BASELINE.json", workflow)
        self.assertIn("DEPLOYMENT_BASELINE.json", workflow)
        self.assertNotIn("Checkout pinned Lean Core source", workflow)
        self.assertNotIn("Checkout pinned Deployment Kit source", workflow)
        self.assertNotIn("--core-path", workflow)
        self.assertNotIn("--deployment-kit-path", workflow)
        self.assertNotIn("lean-agentic-core", workflow)
        self.assertNotIn("lean-poc-deployment-kit", workflow)
        self.assertNotIn("LEAN_CORE_READ_TOKEN", workflow)
        self.assertNotIn("LEAN_POC_AUTOMATION_TOKEN", workflow)

    def test_core_sync_workflow_is_scoped_and_non_force(self) -> None:
        workflow = (ROOT / ".github/workflows/sync-core.yml").read_text(encoding="utf-8")
        self.assertIn("startsWith(github.event.issue.title, '[sync-core] ')", workflow)
        self.assertIn("--request-type sync-core", workflow)
        self.assertIn("repositories: lean-agentic-core", workflow)
        self.assertIn("permission-contents: write", workflow)
        self.assertIn("permission-workflows: write", workflow)
        self.assertIn("permission-pull-requests: write", workflow)
        self.assertIn("permission-checks: read", workflow)
        self.assertIn("core/tools/package/check_baseline.py --root target", workflow)
        self.assertIn("core/tools/package/sync.py", workflow)
        self.assertIn("--apply", workflow)
        self.assertIn("gh pr create", workflow)
        self.assertIn("pulls/$pr_number", workflow)
        self.assertIn("check-runs?per_page=100", workflow)
        self.assertIn("No consumer PR checks registered within 120 seconds.", workflow)
        self.assertIn("Consumer check failed:", workflow)
        self.assertIn("Consumer PR checks are green and stable", workflow)
        self.assertIn("Consumer PR checks did not settle within 30 minutes.", workflow)
        self.assertNotIn("gh pr checks", workflow)
        self.assertNotIn("headRefOid", workflow)
        self.assertIn("CORE_BASELINE.json", workflow)
        self.assertIn("greenfield-workspace", workflow)
        self.assertNotIn("LEAN_CORE_READ_TOKEN", workflow)
        self.assertNotIn("LEAN_POC_AUTOMATION_TOKEN", workflow)
        self.assertNotIn("--force", workflow)


if __name__ == "__main__":
    unittest.main()
