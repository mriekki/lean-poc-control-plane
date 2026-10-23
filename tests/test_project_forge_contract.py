from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "project_forge_contract",
    ROOT / "tools" / "project_forge_contract.py",
)
assert SPEC and SPEC.loader
project_forge_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(project_forge_contract)


class ProjectForgeContractTests(unittest.TestCase):
    def descriptor(self) -> dict:
        return {
            "schemaVersion": 1,
            "generation": {
                "bootstrap": {
                    "repository": "mriekki/project-forge-bootstrap",
                    "commit": "a" * 40,
                    "protocolVersion": 12,
                    "catalogVersion": 11,
                },
                "package": "@mriekki/project-forge",
                "packageVersion": "4.3.0",
                "profile": "greenfield-project",
            },
        }

    def test_resolves_exact_public_generation_bootstrap_pin(self) -> None:
        result = project_forge_contract.resolve_bootstrap_generation(self.descriptor())
        self.assertEqual(
            result,
            {
                "repository": "mriekki/project-forge-bootstrap",
                "commit": "a" * 40,
                "protocolVersion": 12,
                "catalogVersion": 11,
            },
        )

    def test_missing_generation_bootstrap_uses_legacy_compatibility_path(self) -> None:
        descriptor = self.descriptor()
        descriptor["generation"].pop("bootstrap")
        self.assertIsNone(project_forge_contract.resolve_bootstrap_generation(descriptor))

    def test_malformed_or_wrong_bootstrap_provenance_fails_closed(self) -> None:
        cases = [
            ("repository", "someone/example"),
            ("commit", "not-a-sha"),
            ("protocolVersion", 0),
            ("catalogVersion", True),
        ]
        for key, value in cases:
            descriptor = self.descriptor()
            descriptor["generation"]["bootstrap"][key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaises(project_forge_contract.ProjectForgeContractError):
                    project_forge_contract.resolve_bootstrap_generation(descriptor)

    def test_checked_out_bootstrap_catalog_must_match_public_pin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = root / "catalog"
            catalog.mkdir()
            (catalog / "CATALOG.json").write_text(
                json.dumps(
                    {
                        "repository": "mriekki/project-forge-bootstrap",
                        "catalogVersion": 11,
                        "protocol": {"version": 12},
                    }
                ),
                encoding="utf-8",
            )
            value = project_forge_contract.verify_bootstrap_catalog(
                root,
                repository="mriekki/project-forge-bootstrap",
                protocol_version=12,
                catalog_version=11,
            )
            self.assertEqual(value["catalogVersion"], 11)

            with self.assertRaises(project_forge_contract.ProjectForgeContractError):
                project_forge_contract.verify_bootstrap_catalog(
                    root,
                    repository="mriekki/project-forge-bootstrap",
                    protocol_version=12,
                    catalog_version=12,
                )

    def test_generation_workflow_uses_public_pin_before_private_manifest_validation(self) -> None:
        workflow = (ROOT / ".github/workflows/generate-project.yml").read_text(encoding="utf-8")
        resolve = "python tools/project_forge_contract.py resolve-bootstrap"
        checkout_ref = "ref: ${{ steps.public-contract.outputs.bootstrap_commit || 'main' }}"
        verify = "python tools/project_forge_contract.py verify-bootstrap"
        manifest = "remote_generation.py validate-manifest"
        self.assertIn(resolve, workflow)
        self.assertIn(checkout_ref, workflow)
        self.assertIn(verify, workflow)
        self.assertIn("using Bootstrap main compatibility fallback", workflow)
        self.assertLess(workflow.index(resolve), workflow.index(checkout_ref))
        self.assertLess(workflow.index(verify), workflow.index(manifest))
        self.assertIn('--expected-bootstrap-commit "${{ steps.bootstrap.outputs.sha }}"', workflow)


if __name__ == "__main__":
    unittest.main()
