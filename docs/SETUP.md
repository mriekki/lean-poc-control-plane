# Control Plane Setup

This repository is the public orchestration surface for multi-owner Lean POC generation and remote Lean Core synchronization. Reusable product/discovery/generation logic remains private in `mriekki/lean-poc-bootstrap`; Core remains private in `mriekki/lean-agentic-core`; reusable deployment mechanics remain private in `mriekki/lean-poc-deployment-kit`.

This repository is the canonical ChatGPT remote-generation execution surface. Generated consumers may also configure it as their remote `/core-sync` provider so a developer does not need a local Core clone just to receive an accepted Core update.

## Security boundary

Public issue requests contain only a target repository name:

```text
[generate-poc] owner/repository
[sync-core] owner/repository
```

The issue body must be empty. The request validator rejects any non-whitespace body.

Private generation data stays in the target repository's `POC_BOOTSTRAP.json`. Private Core provenance stays in the target repository's `CORE_BASELINE.json`. Workflows read those target-private files only after minting a GitHub App installation token scoped to that exact repository.

Do not store personal access tokens in this repository. The credential model is one GitHub App private key stored as an Actions secret. The workflows mint short-lived installation tokens separately for source and target access.

## GitHub App registration

Create one GitHub App owned by `mriekki` and configure it so it can be installed on approved developer accounts.

Recommended identity:

```text
GitHub App name: Lean POC Generator
```

Required repository permissions for generation plus remote Core sync:

- **Contents: Read and write** — source checkout plus generated/synchronized target branch commit/push;
- **Workflows: Read and write** — generated targets may contain `.github/workflows/ci.yml` and Core distributions must not be blocked from updating managed workflow files;
- **Pull requests: Read and write** — remote Core sync creates the consumer PR after publishing the sync branch;
- **Checks: Read-only** — remote Core sync observes consumer PR checks before reporting success;
- **Metadata: Read-only** — GitHub-required repository metadata access.

The control plane does not need target-repository Issues permission. It comments on its own public request issue using that workflow run's normal `GITHUB_TOKEN`.

The App does not need webhooks for this design; generation and Core sync are initiated by this repository's issue-triggered Actions workflows.

When Pull requests or Checks permissions are added to an existing App installation, GitHub may require the installation owner to approve the expanded permissions. Confirm the installation is active for each allowlisted developer before relying on remote Core sync.

## Installations

For a zero-extra-step POC flow, install the App on all repositories in each approved developer account. Each workflow still mints tokens scoped to the exact repositories required by that run:

- generation source token: `mriekki/lean-poc-bootstrap`, `mriekki/lean-agentic-core`, and `mriekki/lean-poc-deployment-kit`;
- Core-sync source token: only `mriekki/lean-agentic-core`;
- target token: only the requested `owner/repository`.

The generation workflow does not check out Deployment Kit when `generation.deploymentKit.enabled=false`; including the repository in the short-lived source token scope only makes the exact pinned checkout available when the approved manifest enables it.

If an account prefers selecting repositories instead of all repositories, every newly created POC repo must be added to the App installation before generation or remote Core sync. The Mark-owned App installation must also include the private Bootstrap, Core, and Deployment Kit source repositories.

## Control-plane Actions configuration

After creating the App:

1. Copy its **Client ID** into this repository as Actions variable `APP_CLIENT_ID`.
2. Generate a GitHub App private key.
3. Store the complete private-key value as Actions repository secret `APP_PRIVATE_KEY`.
4. Do not commit either credential to Git.
5. Add each approved developer's GitHub login to `config/allowed-owners.json` through the normal PR/CI path.

The private key should exist only in GitHub's App configuration and this repository's Actions secret store. Rotate it if exposure is suspected.

## Per-POC generation request contract

After discovery and manifest approval:

1. If ChatGPT cannot create repositories, the developer creates a **private, empty, uninitialized** target repository under their own GitHub account. Do not add a README, `.gitignore`, license, or application files.
2. ChatGPT verifies the authenticated GitHub identity exactly matches the approved target owner and verifies the target is safe for first publication.
3. ChatGPT writes only the approved `POC_BOOTSTRAP.json` seed to that target repository.
4. ChatGPT opens a public issue here with title `[generate-poc] owner/repository` and an empty body.
5. The request author must equal the target owner and must appear in `config/allowed-owners.json`.
6. The workflow obtains repository-scoped GitHub App installation tokens.
7. Bootstrap validates the private manifest against the current accepted Bootstrap `main` commit, target identity, recipe/catalog contract, exact Core commit, and optional exact Deployment Kit repository/commit/distribution.
8. The workflow checks out the exact manifest-pinned Core source and, only when enabled, the exact manifest-pinned Deployment Kit source.
9. The deterministic generator receives those exact source paths and replaces only the approved seed state with the generated workspace baseline.
10. Before publication, the workflow validates Core provenance and, when enabled, `DEPLOYMENT_BASELINE.json` repository/commit/distribution/managed-path provenance plus the generated Deployment Kit hash checker. The disabled case rejects unexpected Deployment Kit provenance.
11. ChatGPT verifies target default-branch CI on the exact published commit before local clone/fetch and setup acceptance.

A missing/inaccessible target or required source repository, a source commit mismatch, or a failed/unavailable control-plane run is a stop condition. It is **not** permission for ChatGPT to silently switch to local generation, use another Deployment Kit commit/distribution, or create a ZIP/downloadable generated workspace. Local generation is used only when the human explicitly chooses that path.

## Remote Core-sync request contract

A generated/self-contained consumer may configure the generic Core `/core-sync` skill with this provider. When no safe local Core checkout is available, the developer authorizes one public request:

```text
[sync-core] owner/repository
```

with an empty body.

The remote workflow then:

1. verifies the request author equals the target owner and the owner is allowlisted;
2. refuses foundational/platform repositories, including Family Meal Planner's specialized consumer path;
3. mints a read-only source token scoped only to `mriekki/lean-agentic-core`;
4. mints a target token scoped only to the requested consumer;
5. checks out current accepted Core `main` and the consumer default branch;
6. validates the consumer's `CORE_BASELINE.json` is schema version 1, belongs to `mriekki/lean-agentic-core`, uses `greenfield-workspace`, and has managed-path provenance;
7. runs Core's canonical baseline-integrity check before making target changes;
8. exits cleanly without a branch if the consumer already matches current Core;
9. otherwise runs the canonical Core sync preview and refuses unsafe drift/conflicts during apply;
10. creates a new `chore/sync-core-<short-sha>` branch without force-updating any existing branch;
11. applies the managed overlay and refreshes exact `CORE_BASELINE.json` provenance;
12. re-runs baseline integrity and strict current-Core checks;
13. commits and pushes only the new sync branch;
14. creates a consumer PR;
15. waits for the consumer PR checks; and
16. reports success on the public request only when those checks are green.

The remote request never authorizes merging the consumer PR. The normal human merge/finalize gate remains.

If the consumer has Core-managed local drift, missing managed files, conflicts, an unsupported distribution, or an existing sync branch for that Core commit, the workflow stops rather than overwriting or force-updating state.
