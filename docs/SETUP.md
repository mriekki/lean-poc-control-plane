# Project Forge Control Plane Setup

This repository is the public orchestration surface for Project Forge generation, Builder invitation/authorization, and supported remote update workflows. Reusable discovery/generation logic remains in `mriekki/lean-poc-bootstrap`; the public `@mriekki/lean` package remains the normal reusable-asset delivery boundary for generated Projects.

Canonical repository identity after the coordinated rename:

```text
mriekki/project-forge-control-plane
```

Technical compatibility commands and schema identifiers remain unchanged.

## Security boundary

Public operational issues contain only safe identities:

```text
[invite-lean] github-owner
[test-invite-forge]
[lean-doctor] github-owner
[revoke-lean] github-owner
[generate-poc] owner/repository
[sync-core] owner/repository
```

Issue bodies must remain empty. Private Project definitions, baseline contents, source code, credentials, and secrets never belong in a Control Plane issue.

Private generation data stays in the target repository's `POC_BOOTSTRAP.json`. Workflows read target-private files only after minting a GitHub App installation token scoped to that exact repository.

Do not store PATs or npm publish tokens in this repository. The credential model is one GitHub App private key stored as an Actions secret; workflows mint short-lived installation tokens for the exact source/target repositories needed by each operation.

## GitHub App registration

Create one GitHub App owned by `mriekki` and configure it so it can be installed on approved Builder accounts.

Public display identity:

```text
GitHub App name: Project Forge
```

Keep GitHub's identity terms distinct:

- **App name** is the human-facing registration name: `Project Forge`.
- **App slug** is GitHub's URL-safe App identifier and may retain historical wording after a display-name change.
- **GitHub App bot username** is `<app-slug>[bot]`.
- **App installation** is the App's authorization on an owner/account and selected repositories.

Workflows must resolve the actual App slug/bot identity rather than guessing it. A display-name rename must not be coupled to a bot-identity or credential migration unless GitHub itself changes those values.

Required repository permissions for generation plus the existing remote Core-sync workflow:

- **Contents: Read and write**;
- **Workflows: Read and write**;
- **Pull requests: Read and write**;
- **Checks: Read-only**;
- **Metadata: Read-only**.

The Control Plane does not need target-repository Issues permission. It comments on its own public issues using the workflow run's normal `GITHUB_TOKEN`.

The App does not need webhooks for this design; onboarding, generation, and Core sync are initiated by this repository's issue-triggered Actions workflows.

When permissions are expanded on an existing App installation, GitHub may require the installation owner to approve the change. Confirm the installation remains active before relying on the new permission.

## Installations

For the smoothest Project Forge flow, install **Project Forge** on all repositories in each approved Builder account. Each workflow still mints tokens scoped to the exact repositories required by that run:

- invitation/doctor check: the invited or already-active Builder's installation;
- generation source token: only `mriekki/lean-poc-bootstrap`;
- Core-sync source token: only `mriekki/lean-agentic-core`;
- target token: only the requested `owner/repository`.

If an account selects repositories instead of all repositories, every newly created Project repository must be added before generation/update operations can use it.

## Control Plane Actions configuration

After creating/configuring the App:

1. Store its **Client ID** as Actions variable `APP_CLIENT_ID`.
2. Store the complete App private key as Actions secret `APP_PRIVATE_KEY`.
3. Do not commit either credential.
4. Set Actions variable `APP_INSTALL_URL` to the actual **Project Forge** installation URL so onboarding gets a direct install link. If absent, onboarding falls back to this setup guide.
5. Keep `config/developers.json`, `config/invitation-policy.json`, and `config/allowed-owners.json` valid under CI.

Renaming the App display name does not require rotating `APP_CLIENT_ID` or `APP_PRIVATE_KEY`.

## Developer invitation contract

Normal onboarding uses the invitation workflow; do not manually add a normal Builder to `config/allowed-owners.json`.

An ACTIVE admin creates one empty-body issue:

```text
[invite-lean] github-owner
```

The issue is the onboarding portal. The invited Builder:

1. opens the issue;
2. installs/approves **Project Forge** if needed; and
3. while signed in as the exact invited GitHub owner, adds a new issue comment containing exactly:

```text
/accept-lean
```

The claim workflow verifies identity, invitation lifetime, and Project Forge App installation before updating the developer registry and compatibility allowlist.

The invited owner can decline with `/decline-lean`. Unclaimed invitations expire after the configured claim window.

Successful activation automatically verifies the public Project Forge ChatGPT contract. `/lean-doctor` remains the retry/diagnostic path if readiness later needs attention.

An already-ACTIVE Builder without an invitation issue can open:

```text
[lean-doctor] github-owner
```

The doctor verifies ACTIVE registry state, Project Forge App installation, and the SHA-256-pinned public contract at `mriekki/lean-platform/chatgpt/current.json`.

## Admin onboarding self-test

Choose **Issues → New issue → Test Project Forge onboarding** and submit the prefilled empty-body issue:

```text
[test-invite-forge]
```

The workflow infers the target from the active admin who opened the issue. It cannot target another user and never mutates authorization state. Continue by adding `/accept-lean` to that same test issue when instructed.

## Per-Project generation request contract

After discovery and Project Definition approval:

1. the Builder owns a private, safe target repository;
2. ChatGPT verifies exact GitHub owner/target safety;
3. only the approved schema-v2 `POC_BOOTSTRAP.json` seed is written before generation;
4. the manifest pins exact Bootstrap provenance and an exact `@mriekki/lean` package/version/profile;
5. ChatGPT opens an empty-body public issue here titled `[generate-poc] owner/repository`;
6. the author must equal the target owner and be ACTIVE with generation authorization;
7. the workflow obtains a Bootstrap-only source token and exact-target token;
8. Bootstrap validates the private manifest and resolves machine provenance such as registry integrity;
9. the workflow downloads/verifies exactly the approved package;
10. deterministic generation runs through Bootstrap's canonical package path;
11. generated tools/baselines are verified before publication;
12. the validated generated tree is published without force-pushing; and
13. target default-branch CI is verified before local setup acceptance.

Missing access, unavailable exact packages, integrity mismatch, invalid provenance, managed-path conflict, or failed generation are stop conditions. They never authorize silent fallback to a different package, local ZIP, destination, or component commit.

## Remote Core-sync compatibility path

A supported consumer may request:

```text
[sync-core] owner/repository
```

with an empty body. The workflow validates authorization and baseline integrity, uses exact source/target tokens, creates a new non-force branch when needed, opens a consumer PR, and reports success only when its checks are green. Merge remains a human decision.

## Repository rename boundary

The canonical repository is `mriekki/project-forge-control-plane`. Historical `mriekki/lean-poc-control-plane` links may redirect at GitHub, but new documentation, contracts, and tooling must emit the canonical Project Forge repository identity. Compatibility command/schema identifiers are intentionally unchanged.
