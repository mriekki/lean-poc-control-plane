#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import invitation

TEST_INVITE_PREFIX = "[test-invite-forge]"


def _test_target(issue: dict) -> str:
    """Resolve the self-test target without requiring the admin to type their login."""
    title = str(issue.get("title") or "").strip()
    author = invitation.issue_author(issue)
    if title == TEST_INVITE_PREFIX:
        return author
    return invitation.parse_title(issue, TEST_INVITE_PREFIX)


def _test_identity(issue: dict, registry: dict) -> tuple[str, str]:
    invitation.require_empty_body(issue, "Onboarding test")
    target = _test_target(issue)
    author = invitation.issue_author(issue)
    record = invitation.require_capability(registry, author, "invite-developer")
    if record.get("role") != "admin":
        raise invitation.InvitationError("Onboarding test may only be started by an active admin")
    if target.lower() != author.lower():
        raise invitation.InvitationError(
            "Onboarding test is self-test only; issue target must match the active admin who opened it"
        )
    return target, author


def extract_test_invite(event: dict, registry: dict) -> dict[str, str]:
    issue = invitation.issue_from_event(event)
    target, author = _test_identity(issue, registry)
    return {
        "target_owner": target,
        "request_author": author,
        "issue_number": invitation.issue_number(issue),
    }


def extract_test_claim(
    event: dict,
    registry: dict,
    *,
    expiry_days: int,
) -> dict[str, str]:
    issue = invitation.issue_from_event(event)
    target, author = _test_identity(issue, registry)
    if invitation.invitation_expired(issue, expiry_days):
        raise invitation.InvitationError(
            "Onboarding test has expired; create a new test issue to continue"
        )

    comment = event.get("comment")
    if not isinstance(comment, dict):
        raise invitation.InvitationError("Onboarding test acceptance requires an issue_comment event")
    body = str(comment.get("body") or "").strip()
    if body != invitation.ACCEPT_COMMAND:
        raise invitation.InvitationError(
            f"Onboarding test acceptance comment must be exactly '{invitation.ACCEPT_COMMAND}'"
        )
    claimant = invitation.normalize_login((comment.get("user") or {}).get("login"))
    if claimant.lower() != target.lower():
        raise invitation.InvitationError(
            f"Onboarding test may only be accepted by {target}; found {claimant}"
        )

    return {
        "target_owner": target,
        "request_author": author,
        "claimant": claimant,
        "issue_number": invitation.issue_number(issue),
    }


def _read_event(path: Path) -> dict:
    value = invitation.read_json(path)
    if not isinstance(value, dict):
        raise invitation.InvitationError("GitHub event payload must be a JSON object")
    return value


def command_extract_invite(args: argparse.Namespace) -> int:
    values = extract_test_invite(
        _read_event(args.event),
        invitation.load_registry(args.registry),
    )
    invitation.write_github_output(values)
    print(json.dumps(values, indent=2))
    return 0


def command_extract_claim(args: argparse.Namespace) -> int:
    expiry_days = invitation.load_policy(args.policy)["expiryDays"]
    values = extract_test_claim(
        _read_event(args.event),
        invitation.load_registry(args.registry),
        expiry_days=expiry_days,
    )
    invitation.write_github_output(values)
    print(json.dumps(values, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Project Forge non-authorizing onboarding test tooling"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    invite_parser = sub.add_parser("extract-invite")
    invite_parser.add_argument("--event", required=True, type=Path)
    invite_parser.add_argument("--registry", required=True, type=Path)
    invite_parser.set_defaults(func=command_extract_invite)

    claim_parser = sub.add_parser("extract-claim")
    claim_parser.add_argument("--event", required=True, type=Path)
    claim_parser.add_argument("--registry", required=True, type=Path)
    claim_parser.add_argument("--policy", required=True, type=Path)
    claim_parser.set_defaults(func=command_extract_claim)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return args.func(args)
    except invitation.InvitationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
