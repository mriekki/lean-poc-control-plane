from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import invitation  # noqa: E402
import onboarding_test  # noqa: E402

NOW = datetime(2026, 10, 18, 22, 0, tzinfo=timezone.utc)


def registry_value() -> dict:
    return {
        "schemaVersion": 1,
        "developers": [
            {
                "githubOwner": "mriekki",
                "status": "active",
                "role": "admin",
                "contractChannel": "stable",
                "capabilities": [
                    "generate-project",
                    "sync-core",
                    "invite-developer",
                    "revoke-developer",
                ],
            },
            {
                "githubOwner": "builder-example",
                "status": "active",
                "role": "project-author",
                "contractChannel": "stable",
                "capabilities": ["generate-project", "sync-core"],
            },
        ],
    }


def issue_event(
    title: str,
    *,
    author: str = "mriekki",
    body: str = "",
    created_at: str = "2026-10-18T20:00:00Z",
) -> dict:
    return {
        "issue": {
            "number": 101,
            "title": title,
            "body": body,
            "created_at": created_at,
            "user": {"login": author},
        }
    }


class OnboardingTestModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.registry_path = self.root / "developers.json"
        self.allowed_path = self.root / "allowed-owners.json"
        self.registry_path.write_text(
            json.dumps(registry_value(), indent=2) + "\n",
            encoding="utf-8",
        )
        self.allowed_path.write_text(
            json.dumps(
                {"schemaVersion": 1, "owners": ["mriekki", "builder-example"]},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def registry(self) -> dict:
        return invitation.load_registry(self.registry_path)

    def test_active_admin_can_start_self_test(self) -> None:
        values = onboarding_test.extract_test_invite(
            issue_event("[test-invite-forge] mriekki"),
            self.registry(),
        )
        self.assertEqual(values["target_owner"], "mriekki")
        self.assertEqual(values["request_author"], "mriekki")

    def test_template_title_infers_active_admin_identity(self) -> None:
        values = onboarding_test.extract_test_invite(
            issue_event("[test-invite-forge]"),
            self.registry(),
        )
        self.assertEqual(values["target_owner"], "mriekki")
        self.assertEqual(values["request_author"], "mriekki")

    def test_self_test_cannot_target_someone_else(self) -> None:
        with self.assertRaisesRegex(invitation.InvitationError, "self-test only"):
            onboarding_test.extract_test_invite(
                issue_event("[test-invite-forge] builder-example"),
                self.registry(),
            )

    def test_non_admin_cannot_start_test_mode(self) -> None:
        with self.assertRaises(invitation.InvitationError):
            onboarding_test.extract_test_invite(
                issue_event(
                    "[test-invite-forge] builder-example",
                    author="builder-example",
                ),
                self.registry(),
            )

    def test_non_admin_cannot_use_template_title_to_start_test_mode(self) -> None:
        with self.assertRaises(invitation.InvitationError):
            onboarding_test.extract_test_invite(
                issue_event(
                    "[test-invite-forge]",
                    author="builder-example",
                ),
                self.registry(),
            )

    def test_test_issue_body_must_be_empty(self) -> None:
        with self.assertRaises(invitation.InvitationError):
            onboarding_test.extract_test_invite(
                issue_event(
                    "[test-invite-forge] mriekki",
                    body="should not be here",
                ),
                self.registry(),
            )

    @patch("onboarding_test.invitation.invitation_expired", return_value=False)
    def test_acceptance_requires_exact_self_identity(self, _expired) -> None:
        event = issue_event("[test-invite-forge] mriekki")
        event["comment"] = {
            "body": "/accept-project-forge",
            "user": {"login": "builder-example"},
        }
        with self.assertRaisesRegex(invitation.InvitationError, "only be accepted"):
            onboarding_test.extract_test_claim(
                event,
                self.registry(),
                expiry_days=30,
            )

        event["comment"]["user"]["login"] = "mriekki"
        values = onboarding_test.extract_test_claim(
            event,
            self.registry(),
            expiry_days=30,
        )
        self.assertEqual(values["claimant"], "mriekki")

    @patch("onboarding_test.invitation.invitation_expired", return_value=False)
    def test_template_title_can_be_accepted_by_same_admin(self, _expired) -> None:
        event = issue_event("[test-invite-forge]")
        event["comment"] = {
            "body": "/accept-project-forge",
            "user": {"login": "mriekki"},
        }
        values = onboarding_test.extract_test_claim(
            event,
            self.registry(),
            expiry_days=30,
        )
        self.assertEqual(values["target_owner"], "mriekki")
        self.assertEqual(values["claimant"], "mriekki")

    @patch("onboarding_test.invitation.invitation_expired", return_value=True)
    def test_expired_test_must_be_recreated(self, _expired) -> None:
        event = issue_event("[test-invite-forge] mriekki")
        event["comment"] = {
            "body": "/accept-project-forge",
            "user": {"login": "mriekki"},
        }
        with self.assertRaisesRegex(invitation.InvitationError, "expired"):
            onboarding_test.extract_test_claim(
                event,
                self.registry(),
                expiry_days=30,
            )

    @patch("onboarding_test.invitation.invitation_expired", return_value=False)
    def test_test_parsers_do_not_mutate_registry_or_allowlist(self, _expired) -> None:
        registry_before = self.registry_path.read_bytes()
        allowed_before = self.allowed_path.read_bytes()
        registry = self.registry()
        registry_value_before = deepcopy(registry)

        onboarding_test.extract_test_invite(
            issue_event("[test-invite-forge] mriekki"),
            registry,
        )
        event = issue_event("[test-invite-forge] mriekki")
        event["comment"] = {
            "body": "/accept-project-forge",
            "user": {"login": "mriekki"},
        }
        onboarding_test.extract_test_claim(event, registry, expiry_days=30)

        self.assertEqual(registry, registry_value_before)
        self.assertEqual(self.registry_path.read_bytes(), registry_before)
        self.assertEqual(self.allowed_path.read_bytes(), allowed_before)


if __name__ == "__main__":
    unittest.main()
