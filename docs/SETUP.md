# Control Plane Setup

This repository is the public orchestration surface for multi-owner Lean POC generation. Reusable product/discovery/generation logic remains private in `mriekki/lean-poc-bootstrap`; Core remains private in `mriekki/lean-agentic-core`.

Bootstrap protocol v5 and later use this repository as the canonical ChatGPT remote-generation execution surface.

## Security boundary

The public issue request contains only a target repository name:

```text
[generate-poc] owner/repository
```

The issue body must be empty. The request validator rejects any non-whitespace body.

The approved `POC_BOOTSTRAP.json` remains inside that developer's private target repository. The workflow reads it only after minting a GitHub App installation token scoped to that target repository.

Do not store personal access tokens in this repository. The intended credential is one GitHub App private key stored as an Actions secret. The workflow mints short-lived installation tokens separately for source and target access.

## GitHub App registration

Create one GitHub App owned by `mriekki` and configure it so it can be installed on approved developer accounts.

Recommended identity:

```text
GitHub App name: Lean POC Generator
```

Required repository permissions:

- **Contents: Read and write** — source checkout plus generated target commit/push;
- **Workflows: Read and write** — generated targets contain `.github/workflows/ci.yml`;
- **Metadata: Read-only** — GitHub-required repository metadata access.

The control plane does not need target-repository Issues permission. It comments on its own public request issue using that workflow run's normal `GITHUB_TOKEN`.

The App does not need webhooks for this design; generation is initiated by this repository's issue-triggered Actions workflow.

Allow installation on **Any account** so each approved developer can install the same App on their personal GitHub account.

## Installations

For a zero-extra-step future POC flow, install the App on all repositories in each approved developer account. The workflow still mints tokens scoped to the exact repositories required by that generation run:

- source token: only `mriekki/lean-poc-bootstrap` and `mriekki/lean-agentic-core`;
- target token: only the requested `owner/repository`.

If an account prefers selecting repositories instead of all repositories, every newly created POC repo must be added to the App installation before generation.

## Control-plane Actions configuration

After creating the App:

1. Copy its **Client ID** into this repository as Actions variable `APP_CLIENT_ID`.
2. Generate a GitHub App private key.
3. Store the complete private-key value as Actions repository secret `APP_PRIVATE_KEY`.
4. Do not commit either credential to Git.
5. Add each approved developer's GitHub login to `config/allowed-owners.json` through the normal PR/CI path.

The private key should exist only in GitHub's App configuration and this repository's Actions secret store. Rotate it if exposure is suspected.

## Per-POC request contract

After discovery and manifest approval:

1. If ChatGPT cannot create repositories, the developer creates a **private, empty, uninitialized** target repository under their own GitHub account. Do not add a README, `.gitignore`, license, or application files.
2. ChatGPT verifies the authenticated GitHub identity exactly matches the approved target owner and verifies the target is safe for first publication.
3. ChatGPT writes only the approved `POC_BOOTSTRAP.json` seed to that target repository.
4. ChatGPT opens a public issue here with title `[generate-poc] owner/repository` and an empty body.
5. The request author must equal the target owner and must appear in `config/allowed-owners.json`.
6. The workflow obtains repository-scoped GitHub App installation tokens.
7. Bootstrap validates the private manifest against the current accepted Bootstrap `main` commit, target identity, recipe/catalog contract, and exact Core commit.
8. The deterministic generator replaces only the approved seed state with the generated workspace baseline.
9. ChatGPT verifies target default-branch CI on the exact published commit before local clone/fetch and setup acceptance.

A missing/inaccessible target repository or a failed/unavailable control-plane run is a stop condition. It is **not** permission for ChatGPT to silently switch to local generation or create a ZIP/downloadable generated workspace. Local generation is used only when the human explicitly chooses that path.

## Bootstrap v4 retirement

Bootstrap protocol v5 retires the old Bootstrap-hosted PAT workflow. After the Bootstrap v5 PR is merged and its post-merge `main` CI is green, the platform owner should manually remove the obsolete `LEAN_POC_AUTOMATION_TOKEN` Actions secret and revoke/delete the corresponding personal access token.

Do not expose, paste, or inspect the old token during retirement.
