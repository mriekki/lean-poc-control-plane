#!/usr/bin/env python3
"""Resolve public Project Forge generation provenance for Control Plane workflows."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_DESCRIPTOR_URL = (
    "https://raw.githubusercontent.com/mriekki/project-forge-platform/main/chatgpt/current.json"
)
EXPECTED_BOOTSTRAP_REPOSITORY = "mriekki/project-forge-bootstrap"
_SHA_RE = re.compile(r"[0-9a-f]{40}")


class ProjectForgeContractError(RuntimeError):
    """Raised when public Project Forge generation provenance is invalid."""


def _load_json_source(source: str) -> dict[str, Any]:
    if source.startswith("https://"):
        with urllib.request.urlopen(source, timeout=20) as response:
            raw = response.read().decode("utf-8")
    elif source.startswith("http://"):
        raise ProjectForgeContractError("Remote Project Forge descriptors must use HTTPS")
    else:
        raw = Path(source).read_text(encoding="utf-8")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ProjectForgeContractError("Project Forge descriptor must be a JSON object")
    return value


def resolve_bootstrap_generation(descriptor: dict[str, Any]) -> dict[str, Any]:
    generation = descriptor.get("generation")
    if not isinstance(generation, dict):
        raise ProjectForgeContractError("Project Forge descriptor generation must be an object")

    bootstrap = generation.get("bootstrap")
    if bootstrap is None:
        raise ProjectForgeContractError(
            "Project Forge descriptor generation.bootstrap pin is required"
        )
    if not isinstance(bootstrap, dict):
        raise ProjectForgeContractError("generation.bootstrap must be an object")

    repository = bootstrap.get("repository")
    commit = bootstrap.get("commit")
    protocol_version = bootstrap.get("protocolVersion")
    catalog_version = bootstrap.get("catalogVersion")

    if repository != EXPECTED_BOOTSTRAP_REPOSITORY:
        raise ProjectForgeContractError(
            "generation.bootstrap.repository must be "
            f"{EXPECTED_BOOTSTRAP_REPOSITORY!r}; found {repository!r}"
        )
    if not isinstance(commit, str) or not _SHA_RE.fullmatch(commit):
        raise ProjectForgeContractError(
            "generation.bootstrap.commit must be an exact lowercase 40-character Git SHA"
        )
    if not isinstance(protocol_version, int) or isinstance(protocol_version, bool) or protocol_version < 1:
        raise ProjectForgeContractError("generation.bootstrap.protocolVersion must be a positive integer")
    if not isinstance(catalog_version, int) or isinstance(catalog_version, bool) or catalog_version < 1:
        raise ProjectForgeContractError("generation.bootstrap.catalogVersion must be a positive integer")

    return {
        "repository": repository,
        "commit": commit,
        "protocolVersion": protocol_version,
        "catalogVersion": catalog_version,
    }


def verify_bootstrap_catalog(
    root: Path,
    *,
    repository: str,
    protocol_version: int,
    catalog_version: int,
) -> dict[str, Any]:
    if repository != EXPECTED_BOOTSTRAP_REPOSITORY:
        raise ProjectForgeContractError(
            f"Unexpected accepted Bootstrap repository: {repository!r}"
        )

    catalog_path = root / "catalog" / "CATALOG.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict):
        raise ProjectForgeContractError("Bootstrap catalog must be a JSON object")

    actual_repository = catalog.get("repository")
    actual_protocol = (catalog.get("protocol") or {}).get("version")
    actual_catalog = catalog.get("catalogVersion")

    if actual_repository != repository:
        raise ProjectForgeContractError(
            f"Bootstrap repository mismatch: expected {repository!r}, found {actual_repository!r}"
        )
    if actual_protocol != protocol_version:
        raise ProjectForgeContractError(
            "Bootstrap protocol mismatch: "
            f"expected {protocol_version!r}, found {actual_protocol!r}"
        )
    if actual_catalog != catalog_version:
        raise ProjectForgeContractError(
            "Bootstrap catalog mismatch: "
            f"expected {catalog_version!r}, found {actual_catalog!r}"
        )
    return catalog


def _write_github_output(values: dict[str, str]) -> None:
    destination = os.getenv("GITHUB_OUTPUT")
    if not destination:
        return
    with Path(destination).open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            if "\n" in value or "\r" in value:
                raise ProjectForgeContractError(f"Unsafe multiline GitHub output: {key}")
            handle.write(f"{key}={value}\n")


def _resolve_command(args: argparse.Namespace) -> int:
    descriptor = _load_json_source(args.descriptor)
    bootstrap = resolve_bootstrap_generation(descriptor)
    values = {
        "bootstrap_repository": str(bootstrap["repository"]),
        "bootstrap_commit": str(bootstrap["commit"]),
        "bootstrap_protocol_version": str(bootstrap["protocolVersion"]),
        "bootstrap_catalog_version": str(bootstrap["catalogVersion"]),
    }
    _write_github_output(values)
    print(json.dumps(values, sort_keys=True))
    return 0


def _verify_command(args: argparse.Namespace) -> int:
    verify_bootstrap_catalog(
        args.root,
        repository=args.repository,
        protocol_version=args.protocol_version,
        catalog_version=args.catalog_version,
    )
    print("Accepted Bootstrap catalog matches public generation provenance")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project_forge_contract.py")
    commands = parser.add_subparsers(dest="command", required=True)

    resolve = commands.add_parser("resolve-bootstrap")
    resolve.add_argument("--descriptor", default=DEFAULT_DESCRIPTOR_URL)
    resolve.set_defaults(func=_resolve_command)

    verify = commands.add_parser("verify-bootstrap")
    verify.add_argument("--root", type=Path, required=True)
    verify.add_argument("--repository", required=True)
    verify.add_argument("--protocol-version", type=int, required=True)
    verify.add_argument("--catalog-version", type=int, required=True)
    verify.set_defaults(func=_verify_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, ValueError, ProjectForgeContractError) as exc:
        print(f"Project Forge contract error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
