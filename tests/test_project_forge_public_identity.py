from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = [
    ROOT / "README.md",
    ROOT / "docs" / "SETUP.md",
    ROOT / "docs" / "INVITATIONS.md",
    ROOT / ".github" / "workflows" / "invite-developer.yml",
    ROOT / ".github" / "workflows" / "claim-invitation.yml",
]


class ProjectForgePublicIdentityTests(unittest.TestCase):
    def test_public_surfaces_use_project_forge_app_name(self) -> None:
        for path in PUBLIC_FILES:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("Lean POC Generator", text, str(path))
            self.assertIn("Project Forge", text, str(path))

    def test_public_surfaces_use_canonical_control_plane_repository(self) -> None:
        canonical = "mriekki/project-forge-control-plane"
        combined = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_FILES)
        self.assertIn(canonical, combined)
        self.assertNotIn(
            "https://github.com/mriekki/lean-poc-control-plane",
            combined,
            "new public links must use the renamed repository",
        )

    def test_request_safety_blocks_legacy_and_canonical_repo_names(self) -> None:
        request = (ROOT / "tools" / "request.py").read_text(encoding="utf-8")
        self.assertIn('"mriekki/lean-poc-control-plane"', request)
        self.assertIn('"mriekki/project-forge-control-plane"', request)

    def test_compatibility_commands_remain_stable(self) -> None:
        combined = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_FILES)
        self.assertIn("[invite-lean]", combined)
        self.assertIn("/accept-lean", combined)
        self.assertIn("[generate-poc]", combined)


if __name__ == "__main__":
    unittest.main()
