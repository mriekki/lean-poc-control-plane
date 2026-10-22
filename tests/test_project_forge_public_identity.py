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
    def test_public_surfaces_use_project_forge_builder_app_name(self) -> None:
        retired_generator_name = "Project Forge " + "P" + "OC Generator"
        for path in PUBLIC_FILES:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(retired_generator_name, text, str(path))
            self.assertIn("Project Forge Builder", text, str(path))

    def test_public_surfaces_use_canonical_control_plane_repository(self) -> None:
        canonical = "mriekki/project-forge-control-plane"
        combined = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_FILES)
        self.assertIn(canonical, combined)

    def test_request_safety_blocks_control_plane_repository(self) -> None:
        request = (ROOT / "tools" / "request.py").read_text(encoding="utf-8")
        self.assertIn('"mriekki/project-forge-control-plane"', request)

    def test_canonical_commands_are_present(self) -> None:
        combined = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_FILES)
        self.assertIn("[invite-project-forge]", combined)
        self.assertIn("/accept-project-forge", combined)
        self.assertIn("[generate-project]", combined)


if __name__ == "__main__":
    unittest.main()
