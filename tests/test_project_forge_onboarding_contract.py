from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProjectForgeOnboardingContractTests(unittest.TestCase):
    def test_invitation_is_two_step_product_facing_flow(self):
        text = (ROOT / ".github" / "workflows" / "invite-developer.yml").read_text(encoding="utf-8")
        self.assertIn("Welcome to Project Forge", text)
        self.assertIn("Project Builder", text)
        self.assertIn("Step 1 of 2", text)
        self.assertIn("Step 2 of 2", text)
        self.assertIn("/accept-lean", text)
        self.assertNotIn("After activation, comment \\`/lean-doctor\\`", text)

    def test_claim_runs_readiness_automatically(self):
        text = (ROOT / ".github" / "workflows" / "claim-invitation.yml").read_text(encoding="utf-8")
        self.assertIn("Automatically verify public Project Forge contract", text)
        self.assertIn("Project Forge is ready", text)
        self.assertIn("New Project: <your idea>", text)
        self.assertIn("/lean-doctor", text)

    def test_doctor_is_retry_path_with_new_project_language(self):
        text = (ROOT / ".github" / "workflows" / "onboarding-doctor.yml").read_text(encoding="utf-8")
        self.assertIn("Project Forge readiness check", text)
        self.assertIn("READY FOR PROJECT FORGE", text)
        self.assertIn("New Project: <idea>", text)

    def test_invitation_docs_preserve_technical_compatibility_identifiers(self):
        text = (ROOT / "docs" / "INVITATIONS.md").read_text(encoding="utf-8")
        self.assertIn("Project Forge Developer Invitations", text)
        self.assertIn("poc-author", text)
        self.assertIn("[invite-lean]", text)
        self.assertIn("New POC:", text)
        self.assertIn("compatibility alias", text)

    def test_test_mode_has_clear_preview_and_non_authorizing_result(self):
        invite = (ROOT / ".github" / "workflows" / "invite-developer.yml").read_text(encoding="utf-8")
        claim = (ROOT / ".github" / "workflows" / "claim-invitation.yml").read_text(encoding="utf-8")

        self.assertIn("[test-invite-forge]", invite)
        self.assertIn("Invitation message preview", invite)
        self.assertIn("TEST MODE — no access or authorization will be granted or changed", invite)
        self.assertIn("[test-invite-forge]", claim)
        self.assertIn("TEST READY FOR PROJECT FORGE", claim)
        self.assertIn("Developer registry mutation: NOT PERFORMED", claim)
        self.assertIn("Compatibility allowlist mutation: NOT PERFORMED", claim)
        self.assertIn("Project generation: NOT PERFORMED", claim)

    def test_test_claim_job_is_repository_read_only_and_has_no_activation_steps(self):
        claim = (ROOT / ".github" / "workflows" / "claim-invitation.yml").read_text(encoding="utf-8")
        marker = "  test-claim:\n"
        self.assertIn(marker, claim)
        test_job = claim.split(marker, 1)[1]
        self.assertIn("contents: read", test_job)
        self.assertIn("issues: write", test_job)
        self.assertNotIn("tools/invitation.py activate", test_job)
        self.assertNotIn("git push", test_job)
        self.assertNotIn("config/allowed-owners.json", test_job)
        self.assertNotIn("Commit operational registry update", test_job)


if __name__ == "__main__":
    unittest.main()
