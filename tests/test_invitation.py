from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import invitation  # noqa: E402


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
                    "generate-poc",
                    "sync-core",
                    "invite-developer",
                    "revoke-developer",
                ],
            },
            {
                "githubOwner": "kyleriekki-89",
                "status": "active",
                "role": "poc-author",
                "contractChannel": "stable",
                "capabilities": ["generate-poc", "sync-core"],
            },
        ],
    }


def issue_event(title: str, author: str = "mriekki", body: str = "", number: int = 12) -> dict:
    return {
        "issue": {
            "number": number,
            "title": title,
            "body": body,
            "user": {"login": author},
        }
    }


class InvitationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.registry_path = self.root / "developers.json"
        self.allowed_path = self.root / "allowed-owners.json"
        self.registry_path.write_text(json.dumps(registry_value(), indent=2) + "\n", encoding="utf-8")
        self.allowed_path.write_text(
            json.dumps({"schemaVersion": 1, "owners": ["mriekki", "kyleriekki-89"]}, indent=2) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def registry(self) -> dict:
        return invitation.load_registry(self.registry_path)

    def test_config_projection_is_valid(self) -> None:
        value = self.registry()
        invitation.validate_projection(value, self.allowed_path)

    def test_only_active_admin_can_invite(self) -> None:
        event = issue_event("[invite-lean] daniel-example", author="mriekki")
        values = invitation.extract_invite(event, self.registry())
        self.assertEqual(values["target_owner"], "daniel-example")

        with self.assertRaises(invitation.InvitationError):
            invitation.extract_invite(
                issue_event("[invite-lean] daniel-example", author="kyleriekki-89"),
                self.registry(),
            )

    def test_invitation_body_must_be_empty(self) -> None:
        with self.assertRaises(invitation.InvitationError):
            invitation.extract_invite(
                issue_event("[invite-lean] daniel-example", body="private details"),
                self.registry(),
            )

    def test_claimant_identity_must_match_invited_owner(self) -> None:
        event = issue_event("[invite-lean] daniel-example")
        event["comment"] = {"body": "/accept-lean", "user": {"login": "someone-else"}}
        with self.assertRaises(invitation.InvitationError):
            invitation.extract_claim(event, self.registry())

        event["comment"]["user"]["login"] = "daniel-example"
        values = invitation.extract_claim(event, self.registry())
        self.assertEqual(values["claimant"], "daniel-example")

    def test_activation_updates_registry_and_compatibility_allowlist(self) -> None:
        invitation.activate(
            self.registry_path,
            self.allowed_path,
            owner="daniel-example",
            invited_by="mriekki",
            issue=12,
        )
        registry = invitation.load_registry(self.registry_path)
        record = invitation.developer(registry, "daniel-example")
        self.assertEqual(record["status"], "active")
        self.assertEqual(record["role"], "poc-author")
        self.assertEqual(record["capabilities"], ["generate-poc", "sync-core"])
        self.assertEqual(record["activationIssue"], 12)
        allowed = invitation.load_allowed_owners(self.allowed_path)
        self.assertEqual(allowed, ["mriekki", "kyleriekki-89", "daniel-example"])
        invitation.validate_projection(registry, self.allowed_path)

    def test_revocation_removes_future_generation_authorization_only(self) -> None:
        invitation.activate(
            self.registry_path,
            self.allowed_path,
            owner="daniel-example",
            invited_by="mriekki",
            issue=12,
        )
        invitation.revoke(
            self.registry_path,
            self.allowed_path,
            owner="daniel-example",
            revoked_by="mriekki",
            issue=13,
        )
        registry = invitation.load_registry(self.registry_path)
        record = invitation.developer(registry, "daniel-example")
        self.assertEqual(record["status"], "revoked")
        self.assertEqual(record["capabilities"], [])
        self.assertNotIn("daniel-example", invitation.load_allowed_owners(self.allowed_path))

    def test_last_admin_cannot_be_revoked(self) -> None:
        event = issue_event("[revoke-lean] mriekki", author="mriekki")
        with self.assertRaises(invitation.InvitationError):
            invitation.extract_revoke(event, self.registry())

    def test_doctor_is_allowed_for_active_owner_or_admin(self) -> None:
        invitation.activate(
            self.registry_path,
            self.allowed_path,
            owner="daniel-example",
            invited_by="mriekki",
            issue=12,
        )
        registry = invitation.load_registry(self.registry_path)
        event = issue_event("[invite-lean] daniel-example", author="mriekki")
        event["comment"] = {"body": "/lean-doctor", "user": {"login": "daniel-example"}}
        values = invitation.extract_doctor(event, registry)
        self.assertEqual(values["target_owner"], "daniel-example")

        event["comment"]["user"]["login"] = "mriekki"
        values = invitation.extract_doctor(event, registry)
        self.assertEqual(values["request_author"], "mriekki")


if __name__ == "__main__":
    unittest.main()
