#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

INVITE_PREFIX = "[invite-lean]"
REVOKE_PREFIX = "[revoke-lean]"
ACCEPT_COMMAND = "/accept-lean"
DOCTOR_COMMAND = "/lean-doctor"

VALID_ROLES = {"admin", "poc-author"}
VALID_STATUSES = {"active", "revoked"}
VALID_CAPABILITIES = {
    "generate-poc",
    "sync-core",
    "invite-developer",
    "revoke-developer",
}
LOGIN_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})")


class InvitationError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InvitationError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise InvitationError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def normalize_login(value: object) -> str:
    login = str(value or "").strip()
    if not LOGIN_RE.fullmatch(login):
        raise InvitationError(f"Invalid GitHub owner: {login!r}")
    return login


def load_registry(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if data.get("schemaVersion") != 1:
        raise InvitationError("Unsupported developer registry schemaVersion")
    developers = data.get("developers")
    if not isinstance(developers, list) or not developers:
        raise InvitationError("developer registry must contain a non-empty developers list")

    seen: set[str] = set()
    active_admins = 0
    for record in developers:
        if not isinstance(record, dict):
            raise InvitationError("developer records must be objects")
        owner = normalize_login(record.get("githubOwner"))
        key = owner.lower()
        if key in seen:
            raise InvitationError(f"Duplicate developer: {owner}")
        seen.add(key)

        status = record.get("status")
        role = record.get("role")
        channel = record.get("contractChannel")
        capabilities = record.get("capabilities")
        if status not in VALID_STATUSES:
            raise InvitationError(f"Invalid developer status for {owner}: {status!r}")
        if role not in VALID_ROLES:
            raise InvitationError(f"Invalid developer role for {owner}: {role!r}")
        if channel != "stable":
            raise InvitationError(f"Unsupported contract channel for {owner}: {channel!r}")
        if not isinstance(capabilities, list):
            raise InvitationError(f"Capabilities must be a list for {owner}")
        if len(set(capabilities)) != len(capabilities):
            raise InvitationError(f"Duplicate capabilities for {owner}")
        unknown = set(capabilities) - VALID_CAPABILITIES
        if unknown:
            raise InvitationError(f"Unknown capabilities for {owner}: {sorted(unknown)}")
        if status == "revoked" and capabilities:
            raise InvitationError(f"Revoked developer must have no capabilities: {owner}")
        if role == "poc-author" and ({"invite-developer", "revoke-developer"} & set(capabilities)):
            raise InvitationError(f"POC author cannot have admin capabilities: {owner}")
        if status == "active" and role == "admin":
            required = {"generate-poc", "sync-core", "invite-developer", "revoke-developer"}
            if not required <= set(capabilities):
                raise InvitationError(f"Active admin is missing required capabilities: {owner}")
            active_admins += 1

    if active_admins < 1:
        raise InvitationError("Developer registry must retain at least one active admin")
    return data


def developer(data: dict[str, Any], owner: str) -> dict[str, Any] | None:
    key = owner.lower()
    for record in data["developers"]:
        if str(record["githubOwner"]).lower() == key:
            return record
    return None


def require_capability(data: dict[str, Any], owner: str, capability: str) -> dict[str, Any]:
    record = developer(data, owner)
    if not record or record["status"] != "active" or capability not in record["capabilities"]:
        raise InvitationError(f"GitHub owner is not authorized for {capability}: {owner}")
    return record


def load_allowed_owners(path: Path) -> list[str]:
    data = read_json(path)
    if data.get("schemaVersion") != 1:
        raise InvitationError("Unsupported allowed-owner schemaVersion")
    owners = data.get("owners")
    if not isinstance(owners, list):
        raise InvitationError("allowed owners must be a list")
    return [normalize_login(item) for item in owners]


def projected_allowed_owners(data: dict[str, Any]) -> list[str]:
    return [
        record["githubOwner"]
        for record in data["developers"]
        if record["status"] == "active" and "generate-poc" in record["capabilities"]
    ]


def validate_projection(registry: dict[str, Any], allowed_path: Path) -> None:
    actual = [item.lower() for item in load_allowed_owners(allowed_path)]
    expected = [item.lower() for item in projected_allowed_owners(registry)]
    if actual != expected:
        raise InvitationError(
            "config/allowed-owners.json must exactly mirror active generate-poc developers"
        )


def write_projection(registry: dict[str, Any], allowed_path: Path) -> None:
    write_json(
        allowed_path,
        {"schemaVersion": 1, "owners": projected_allowed_owners(registry)},
    )


def issue_from_event(event: dict[str, Any]) -> dict[str, Any]:
    issue = event.get("issue")
    if not isinstance(issue, dict):
        raise InvitationError("Expected a GitHub issue event")
    return issue


def issue_author(issue: dict[str, Any]) -> str:
    return normalize_login((issue.get("user") or {}).get("login"))


def issue_number(issue: dict[str, Any]) -> str:
    number = str(issue.get("number") or "")
    if not number.isdigit():
        raise InvitationError("Issue number is missing or invalid")
    return number


def require_empty_body(issue: dict[str, Any], label: str) -> None:
    if str(issue.get("body") or "").strip():
        raise InvitationError(f"{label} issue body must be empty")


def parse_title(issue: dict[str, Any], prefix: str) -> str:
    title = str(issue.get("title") or "").strip()
    match = re.fullmatch(rf"{re.escape(prefix)}\s+([A-Za-z0-9](?:[A-Za-z0-9-]{{0,38}}))", title)
    if not match:
        raise InvitationError(f"Issue title must be exactly '{prefix} github-owner'")
    return normalize_login(match.group(1))


def extract_invite(event: dict[str, Any], registry: dict[str, Any]) -> dict[str, str]:
    issue = issue_from_event(event)
    require_empty_body(issue, "Invitation")
    target = parse_title(issue, INVITE_PREFIX)
    author = issue_author(issue)
    require_capability(registry, author, "invite-developer")
    existing = developer(registry, target)
    if existing and existing["status"] == "active":
        raise InvitationError(f"Developer is already active: {target}")
    return {
        "target_owner": target,
        "request_author": author,
        "issue_number": issue_number(issue),
    }


def extract_claim(event: dict[str, Any], registry: dict[str, Any]) -> dict[str, str]:
    issue = issue_from_event(event)
    require_empty_body(issue, "Invitation")
    target = parse_title(issue, INVITE_PREFIX)
    inviter = issue_author(issue)
    require_capability(registry, inviter, "invite-developer")

    comment = event.get("comment")
    if not isinstance(comment, dict):
        raise InvitationError("Invitation claim requires an issue_comment event")
    body = str(comment.get("body") or "").strip()
    if body != ACCEPT_COMMAND:
        raise InvitationError(f"Invitation claim comment must be exactly '{ACCEPT_COMMAND}'")
    claimant = normalize_login((comment.get("user") or {}).get("login"))
    if claimant.lower() != target.lower():
        raise InvitationError(
            f"Invitation may only be claimed by {target}; found {claimant}"
        )
    existing = developer(registry, target)
    if existing and existing["status"] == "active":
        raise InvitationError(f"Developer is already active: {target}")
    return {
        "target_owner": target,
        "request_author": inviter,
        "claimant": claimant,
        "issue_number": issue_number(issue),
    }


def active_admin_count(registry: dict[str, Any]) -> int:
    return sum(
        1
        for record in registry["developers"]
        if record["status"] == "active" and record["role"] == "admin"
    )


def extract_revoke(event: dict[str, Any], registry: dict[str, Any]) -> dict[str, str]:
    issue = issue_from_event(event)
    require_empty_body(issue, "Revocation")
    target = parse_title(issue, REVOKE_PREFIX)
    author = issue_author(issue)
    require_capability(registry, author, "revoke-developer")
    existing = developer(registry, target)
    if not existing or existing["status"] != "active":
        raise InvitationError(f"Developer is not active: {target}")
    if existing["role"] == "admin" and active_admin_count(registry) <= 1:
        raise InvitationError("Refusing to revoke the last active Lean admin")
    return {
        "target_owner": target,
        "request_author": author,
        "issue_number": issue_number(issue),
    }


def extract_doctor(event: dict[str, Any], registry: dict[str, Any]) -> dict[str, str]:
    issue = issue_from_event(event)
    target = parse_title(issue, INVITE_PREFIX)
    comment = event.get("comment")
    if not isinstance(comment, dict):
        raise InvitationError("Onboarding doctor requires an issue_comment event")
    if str(comment.get("body") or "").strip() != DOCTOR_COMMAND:
        raise InvitationError(f"Doctor comment must be exactly '{DOCTOR_COMMAND}'")
    actor = normalize_login((comment.get("user") or {}).get("login"))
    if actor.lower() != target.lower():
        require_capability(registry, actor, "invite-developer")
    record = developer(registry, target)
    if not record or record["status"] != "active":
        raise InvitationError(f"Developer is not ACTIVE: {target}")
    return {
        "target_owner": target,
        "request_author": actor,
        "issue_number": issue_number(issue),
    }


def load_registry_from_value(data: dict[str, Any]) -> dict[str, Any]:
    import tempfile
    with tempfile.TemporaryDirectory() as holder:
        path = Path(holder) / "developers.json"
        write_json(path, data)
        return load_registry(path)


def activate(
    registry_path: Path,
    allowed_path: Path,
    *,
    owner: str,
    invited_by: str,
    issue: int,
) -> dict[str, Any]:
    registry = load_registry(registry_path)
    require_capability(registry, invited_by, "invite-developer")
    owner = normalize_login(owner)
    record = developer(registry, owner)
    value = {
        "githubOwner": owner,
        "status": "active",
        "role": "poc-author",
        "contractChannel": "stable",
        "capabilities": ["generate-poc", "sync-core"],
        "invitedBy": invited_by,
        "activationIssue": issue,
    }
    if record is None:
        registry["developers"].append(value)
    else:
        record.clear()
        record.update(value)
    load_registry_from_value(registry)
    write_json(registry_path, registry)
    write_projection(registry, allowed_path)
    validate_projection(registry, allowed_path)
    return value


def revoke(
    registry_path: Path,
    allowed_path: Path,
    *,
    owner: str,
    revoked_by: str,
    issue: int,
) -> dict[str, Any]:
    registry = load_registry(registry_path)
    require_capability(registry, revoked_by, "revoke-developer")
    owner = normalize_login(owner)
    record = developer(registry, owner)
    if not record or record["status"] != "active":
        raise InvitationError(f"Developer is not active: {owner}")
    if record["role"] == "admin" and active_admin_count(registry) <= 1:
        raise InvitationError("Refusing to revoke the last active Lean admin")
    record["status"] = "revoked"
    record["capabilities"] = []
    record["revokedBy"] = revoked_by
    record["revocationIssue"] = issue
    load_registry_from_value(registry)
    write_json(registry_path, registry)
    write_projection(registry, allowed_path)
    validate_projection(registry, allowed_path)
    return record


def write_github_output(values: dict[str, str]) -> None:
    destination = os.getenv("GITHUB_OUTPUT")
    if not destination:
        return
    with Path(destination).open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            if "\n" in value or "\r" in value:
                raise InvitationError(f"Unsafe multiline output: {key}")
            handle.write(f"{key}={value}\n")


def command_extract(args: argparse.Namespace, kind: str) -> int:
    registry = load_registry(args.registry)
    event = read_json(args.event)
    parser = {
        "invite": extract_invite,
        "claim": extract_claim,
        "revoke": extract_revoke,
        "doctor": extract_doctor,
    }[kind]
    values = parser(event, registry)
    write_github_output(values)
    print(json.dumps(values, indent=2))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    registry = load_registry(args.registry)
    validate_projection(registry, args.allowed_owners)
    print("Developer registry and compatibility allowlist are valid")
    return 0


def command_activate(args: argparse.Namespace) -> int:
    value = activate(
        args.registry,
        args.allowed_owners,
        owner=args.owner,
        invited_by=args.invited_by,
        issue=args.issue_number,
    )
    print(f"Activated Lean developer {value['githubOwner']}")
    return 0


def command_revoke(args: argparse.Namespace) -> int:
    value = revoke(
        args.registry,
        args.allowed_owners,
        owner=args.owner,
        revoked_by=args.revoked_by,
        issue=args.issue_number,
    )
    print(f"Revoked Lean developer {value['githubOwner']}")
    return 0


def add_common_extract(sub: argparse._SubParsersAction[argparse.ArgumentParser], name: str) -> None:
    parser = sub.add_parser(name)
    parser.add_argument("--event", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.set_defaults(func=lambda args, kind=name.removeprefix("extract-"): command_extract(args, kind))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lean developer invitation and registry tooling")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("extract-invite", "extract-claim", "extract-revoke", "extract-doctor"):
        add_common_extract(sub, name)

    validate = sub.add_parser("validate-config")
    validate.add_argument("--registry", required=True, type=Path)
    validate.add_argument("--allowed-owners", required=True, type=Path)
    validate.set_defaults(func=command_validate)

    activate_parser = sub.add_parser("activate")
    activate_parser.add_argument("--registry", required=True, type=Path)
    activate_parser.add_argument("--allowed-owners", required=True, type=Path)
    activate_parser.add_argument("--owner", required=True)
    activate_parser.add_argument("--invited-by", required=True)
    activate_parser.add_argument("--issue-number", required=True, type=int)
    activate_parser.set_defaults(func=command_activate)

    revoke_parser = sub.add_parser("revoke")
    revoke_parser.add_argument("--registry", required=True, type=Path)
    revoke_parser.add_argument("--allowed-owners", required=True, type=Path)
    revoke_parser.add_argument("--owner", required=True)
    revoke_parser.add_argument("--revoked-by", required=True)
    revoke_parser.add_argument("--issue-number", required=True, type=int)
    revoke_parser.set_defaults(func=command_revoke)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return args.func(args)
    except InvitationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
