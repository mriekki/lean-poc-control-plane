#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REQUEST_PREFIX = "[generate-poc]"
FOUNDATIONAL_REPOSITORIES = {
    "mriekki/lean-agentic-core",
    "mriekki/lean-poc-bootstrap",
    "mriekki/lean-workspace-adoption-kit",
    "mriekki/family-meal-planner",
    "mriekki/lean-poc-control-plane",
}


class RequestError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RequestError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RequestError(f"Invalid JSON in {path}: {exc}") from exc


def load_allowed_owners(path: Path) -> set[str]:
    data = read_json(path)
    if data.get("schemaVersion") != 1:
        raise RequestError("Unsupported allowed-owner schemaVersion")
    owners = data.get("owners")
    if not isinstance(owners, list) or not owners:
        raise RequestError("allowed owners must be a non-empty list")
    normalized: set[str] = set()
    for owner in owners:
        value = str(owner or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", value):
            raise RequestError(f"Invalid allowed GitHub owner: {value!r}")
        normalized.add(value.lower())
    return normalized


def parse_request(event: dict[str, Any], allowed_owners: set[str]) -> dict[str, str]:
    issue = event.get("issue")
    if not isinstance(issue, dict):
        raise RequestError("Generation requires a GitHub issue event")

    body = str(issue.get("body") or "")
    if body.strip():
        raise RequestError(
            "Generation request body must be empty; keep the approved POC_BOOTSTRAP.json private in the target repository"
        )

    author = str((issue.get("user") or {}).get("login") or "").strip()
    title = str(issue.get("title") or "").strip()
    match = re.fullmatch(r"\[generate-poc\]\s+([^/\s]+)/([^/\s]+)", title)
    if not match:
        raise RequestError("Issue title must be exactly '[generate-poc] owner/repository'")

    owner, repository_name = match.groups()
    if author.lower() != owner.lower():
        raise RequestError(
            f"Generation request author must own the target repository ({owner}); found {author or 'unknown'}"
        )
    if owner.lower() not in allowed_owners:
        raise RequestError(f"Target owner is not enabled for this control plane: {owner}")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", repository_name):
        raise RequestError(f"Invalid target repository name: {repository_name!r}")

    repository = f"{owner}/{repository_name}"
    if repository.lower() in {value.lower() for value in FOUNDATIONAL_REPOSITORIES}:
        raise RequestError(f"Refusing foundational repository as generation target: {repository}")

    number = str(issue.get("number") or "")
    if not number.isdigit():
        raise RequestError("Issue number is missing or invalid")

    return {
        "target_owner": owner,
        "target_name": repository_name,
        "target_repository": repository,
        "request_author": author,
        "issue_number": number,
    }


def write_github_output(values: dict[str, str]) -> None:
    destination = os.getenv("GITHUB_OUTPUT")
    if not destination:
        return
    with Path(destination).open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            if "\n" in value or "\r" in value:
                raise RequestError(f"Unsafe multiline output: {key}")
            handle.write(f"{key}={value}\n")


def extract_command(args: argparse.Namespace) -> int:
    allowed = load_allowed_owners(args.allowed_owners)
    values = parse_request(read_json(args.event), allowed)
    write_github_output(values)
    print(f"Validated public generation request for {values['target_repository']}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Lean POC control-plane requests")
    sub = parser.add_subparsers(dest="command", required=True)

    extract = sub.add_parser("extract", help="Validate an issue request and emit target metadata")
    extract.add_argument("--event", required=True, type=Path)
    extract.add_argument("--allowed-owners", required=True, type=Path)
    extract.set_defaults(func=extract_command)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return args.func(args)
    except RequestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
