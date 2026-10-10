# Control Plane Setup

This repository is the public orchestration surface for multi-owner Lean POC generation. Reusable product/discovery/generation logic remains private in `mriekki/lean-poc-bootstrap`; Core remains private in `mriekki/lean-agentic-core`.

## Security boundary

The public issue request contains only a target repository name:

```text
[generate-poc] owner/repository
```

The approved `POC_BOOTSTRAP.json` remains inside that developer's private target repository. The workflow reads it only after minting a GitHub App installation token scoped to that target repository.

Do not store personal access tokens in this repository. The intended credential is one GitHub App private key stored as an Actions secret. The workflow mints short-lived installation tokens separately for source and target access.

## GitHub App registration

Create one GitHub App owned by `mriekki` and configure it so it can be installed on both Mark's and Kyle's personal accounts.

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

1. The developer creates the private target repository under their own GitHub account.
2. ChatGPT writes only the approved `POC_BOOTSTRAP.json` seed to that target repository (an optional default GitHub README stub may coexist).
3. ChatGPT opens a public issue here with title `[generate-poc] owner/repository`; the issue body contains no private product definition and no secret.
4. The request author must equal the target owner and must appear in `config/allowed-owners.json`.
5. The workflow obtains repository-scoped GitHub App installation tokens.
6. Bootstrap validates the private manifest against the current accepted Bootstrap `main` commit, target identity, recipe/catalog contract, and exact Core commit.
7. The deterministic generator replaces only the approved seed state with the generated workspace baseline.
8. ChatGPT verifies target default-branch CI before local clone/fetch and setup acceptance.

## Migration from Bootstrap v4

Until Bootstrap protocol v5 is explicitly merged after this control plane passes an end-to-end test, the existing v4 PAT-based generation workflow in `mriekki/lean-poc-bootstrap` remains the canonical Mark-only service.

Do not delete `LEAN_POC_AUTOMATION_TOKEN` or the v4 workflow merely because this repository exists. Retirement is a separate migration step after the GitHub App path is proven.
