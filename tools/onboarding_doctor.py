#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import invitation

DOCTOR_PREFIX = "[lean-doctor]"


class DoctorError(RuntimeError):
    pass


def extract_request(event: dict[str, Any], registry: dict[str, Any]) -> dict[str, str]:
    issue = invitation.issue_from_event(event)
    title = str(issue.get("title") or "").strip()

    # Preserve the existing invitation-issue doctor path exactly.
    if title.startswith(f"{invitation.INVITE_PREFIX} "):
        try:
            return invitation.extract_doctor(event, registry)
        except invitation.InvitationError as exc:
            raise DoctorError(str(exc)) from exc

    if not title.startswith(f"{DOCTOR_PREFIX} "):
        raise DoctorError(
            f"Doctor issue title must be '{DOCTOR_PREFIX} github-owner' or an existing invitation issue"
        )

    try:
        invitation.require_empty_body(issue, "Doctor")
        target = invitation.parse_title(issue, DOCTOR_PREFIX)
        record = invitation.developer(registry, target)
        if not record or record["status"] != "active":
            raise invitation.InvitationError(f"Developer is not ACTIVE: {target}")

        comment = event.get("comment")
        if comment is None:
            # Opening a standalone doctor issue is itself the request.
            actor = invitation.issue_author(issue)
        else:
            if not isinstance(comment, dict):
                raise invitation.InvitationError("Doctor comment is invalid")
            if str(comment.get("body") or "").strip() != invitation.DOCTOR_COMMAND:
                raise invitation.InvitationError(
                    f"Doctor comment must be exactly '{invitation.DOCTOR_COMMAND}'"
                )
            actor = invitation.normalize_login((comment.get("user") or {}).get("login"))

        if actor.lower() != target.lower():
            invitation.require_capability(registry, actor, "invite-developer")

        return {
            "target_owner": target,
            "request_author": actor,
            "issue_number": invitation.issue_number(issue),
        }
    except invitation.InvitationError as exc:
        raise DoctorError(str(exc)) from exc


def extract_command(args: argparse.Namespace) -> int:
    event = invitation.read_json(args.event)
    registry = invitation.load_registry(args.registry)
    if not isinstance(event, dict):
        raise DoctorError("Expected a GitHub event object")
    values = extract_request(event, registry)
    invitation.write_github_output(values)
    print(f"Validated Lean onboarding doctor request for {values['target_owner']}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Lean onboarding doctor requests")
    sub = parser.add_subparsers(dest="command", required=True)
    extract = sub.add_parser("extract")
    extract.add_argument("--event", type=Path, required=True)
    extract.add_argument("--registry", type=Path, required=True)
    extract.set_defaults(func=extract_command)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return args.func(args)
    except (DoctorError, invitation.InvitationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
