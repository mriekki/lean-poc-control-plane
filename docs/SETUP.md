# Control Plane Setup

This repository is the public orchestration surface for multi-owner Lean POC generation, developer invitation/authorization, and remote Lean Core synchronization. Reusable product/discovery/generation logic remains private in `mriekki/lean-poc-bootstrap`. Core and Deployment Kit remain canonical private source repositories, while the public `@mriekki/lean` package is the normal reusable-asset delivery boundary for generated POCs.

This repository is the canonical ChatGPT remote-generation execution surface and the cross-account Lean developer authorization surface. Generated consumers may also configure it as their remote `/core-sync` provider so a developer does not need a local Core clone just to receive an accepted Core update.

## Security boundary

Public operational issues contain only safe identities:

```text
[invite-lean] github-owner
[revoke-lean] github-owner
[generate-poc] owner/repository
[sync-core] owner/repository
```

These issue bodies must be empty. Private POC definitions, baseline contents, source code, credentials, or secrets never belong in a Control Plane issue.

Private generation data stays in the target repository's `POC_BOOTSTRAP.json`. Private Core provenance for the separate remote sync path stays in the target repository's `CORE_BASELINE.json`. Workflows read those target-private files only after minting a GitHub App installation token scoped to that exact repository.

Do not store personal access tokens or npm publish tokens in this repository. The credential model is one GitHub App private key stored as an Actions secret. The workflows mint short-lived installation tokens separately for source and target access. Greenfield generation downloads the public npm package anonymously from the registry; npm publication credentials are neither required nor allowed here.

## GitHub App registration

Create one GitHub App owned by `mriekki` and configure it so it can be installed on approved developer accounts.

Recommended display identity:

```text
GitHub App name: Lean POC Generator
```

Keep GitHub's identity terms distinct:

- **App name** is the human-facing registration name, for example `Lean POC Generator`.
- **App slug** is GitHub's URL-safe App identifier. `actions/create-github-app-token` exposes it as `app-slug`.
- **GitHub App bot username** is `<app-slug>[bot]`. This is the account identity that should appear as the author of generated commits when Git is configured correctly.
- **App installation** is the App's authorization on an owner/account and selected repositories. The installation owner or installation UI label is not the bot username.

The generation workflow resolves the actual `app-slug`, looks up `<app-slug>[bot]` to obtain its numeric user ID, and configures Git with the corresponding GitHub noreply address. Do not hard-code a guessed bot name such as `lean-poc-control-plane[bot]`; the registered App slug is authoritative.

Required repository permissions for generation plus the existing remote Core-sync workflow:

- **Contents: Read and write** — read private Bootstrap/Core sources as separately scoped by each workflow and commit/push generated/synchronized target content;
- **Workflows: Read and write** — generated targets may contain `.github/workflows/ci.yml` and Core distributions may update managed workflow files during remote Core sync;
- **Pull requests: Read and write** — remote Core sync creates the consumer PR after publishing the sync branch;
- **Checks: Read-only** — remote Core sync observes consumer PR checks before reporting success;
- **Metadata: Read-only** — GitHub-required repository metadata access.

The control plane does not need target-repository Issues permission. It comments on its own public invitation/generation/sync issues using that workflow run's normal `GITHUB_TOKEN`.

The App does not need webhooks for this design; onboarding, generation, and Core sync are initiated by this repository's issue-triggered Actions workflows.

When Pull requests or Checks permissions are added to an existing App installation, GitHub may require the installation owner to approve the expanded permissions. Confirm the installation is active for each developer before relying on remote Core sync.

## Installations

For a zero-extra-step POC flow, install the App on all repositories in each approved developer account. Each workflow still mints tokens scoped to the exact repositories required by that run:

- invitation/doctor check: the invited developer's App installation;
- generation source token: only `mriekki/lean-poc-bootstrap`;
- Core-sync source token: only `mriekki/lean-agentic-core`;
- target token: only the requested `owner/repository`.

Greenfield generation no longer needs GitHub App read access to `mriekki/lean-poc-deployment-kit` or direct generation-time read access to `mriekki/lean-agentic-core`. The accepted Core + Deployment component snapshots are delivered by the exact public `@mriekki/lean` artifact selected in the approved manifest.

If an account prefers selecting repositories instead of all repositories, every newly created POC repo must be added to the App installation before generation or remote Core sync. The Mark-owned App installation must include private Bootstrap for generation and private Core for the separate remote Core-sync workflow.

## Control-plane Actions configuration

After creating the App:

1. Copy its **Client ID** into this repository as Actions variable `APP_CLIENT_ID`.
2. Generate a GitHub App private key.
3. Store the complete private-key value as Actions repository secret `APP_PRIVATE_KEY`.
4. Do not commit either credential to Git.
5. Optionally set Actions variable `APP_INSTALL_URL` to the actual Lean POC Generator installation URL so invitation comments provide a direct install link. If absent, onboarding falls back to these setup instructions.
6. Keep `config/developers.json`, `config/invitation-policy.json`, and its generated compatibility projection `config/allowed-owners.json` valid under CI.

The private key should exist only in GitHub's App configuration and this repository's Actions secret store. Rotate it if exposure is suspected.

No npm token is configured for generation. The workflow uses public registry reads only.

## Developer invitation contract

Do not manually add a normal developer to `config/allowed-owners.json` as the onboarding mechanism. The invitation workflow owns normal cross-account activation.

An ACTIVE admin creates one empty-body public issue:

```text
[invite-lean] github-owner
```

That issue creation is the meaningful administrative authorization gate. The issue becomes the one onboarding URL.

The invited developer installs/approves the Lean POC Generator App and comments exactly:

```text
/accept-lean
```

The claim workflow verifies the exact GitHub identity, invitation lifetime from `config/invitation-policy.json`, and GitHub App installation before updating `config/developers.json` and the compatibility `config/allowed-owners.json` projection.

The invited owner can decline with:

```text
/decline-lean
```

Unclaimed invitations expire automatically after the configured claim window. Decline/expiration make no authorization change.

After activation, the developer or an admin can comment:

```text
/lean-doctor
```

The doctor verifies ACTIVE registry state, GitHub App installation, and the SHA-256-pinned public ChatGPT bootstrap contract at `mriekki/lean-platform/chatgpt/current.json`.

See `docs/INVITATIONS.md` for full lifecycle and revocation rules.

## Per-POC generation request contract

After discovery and manifest approval:

1. If ChatGPT cannot create repositories, the developer creates a **private, empty, uninitialized** target repository under their own GitHub account. Do not add a README, `.gitignore`, license, or application files.
2. ChatGPT verifies the authenticated GitHub identity exactly matches the approved target owner and verifies the target is safe for first publication.
3. ChatGPT writes only the approved schema-v2 `POC_BOOTSTRAP.json` seed to that target repository.
4. The manifest pins exact Bootstrap provenance and one exact reusable distribution choice under `generation.lean`: package `@mriekki/lean`, exact version, profile `greenfield-poc`, and normally `integrity: "registry"`. An exact SHA-512 SRI remains valid when already supplied by trusted automation. Humans are not expected to discover or paste npm integrity metadata.
5. ChatGPT opens a public issue here with title `[generate-poc] owner/repository` and an empty body.
6. The request author must equal the target owner and must be ACTIVE with generation authorization. The current workflow consumes the compatibility projection in `config/allowed-owners.json`, which is validated against `config/developers.json` by CI.
7. The workflow obtains a Bootstrap-only source token and an exact-target token.
8. Bootstrap validates the private manifest against the current accepted Bootstrap `main` commit, target identity, current protocol/catalog, exact Lean package contract, and resolves `registry` to the exact npm SHA-512 value for orchestration.
9. The workflow downloads exactly `@mriekki/lean@<approved-version>` with npm lifecycle scripts disabled and verifies the downloaded tarball against Bootstrap's exact resolved SHA-512 output.
10. The deterministic generator receives that exact tarball through `generate_snapshot.py --lean-tarball`; Bootstrap/package logic resolves/verifies provenance before mutation, performs whole-profile preflight/apply/check, writes generated `POC_BOOTSTRAP.json` with the exact SRI, and writes `LEAN_BASELINE.json`, `CORE_BASELINE.json`, and `DEPLOYMENT_BASELINE.json`.
11. Before publication, the workflow compiles generated tools, runs the generated no-network managed-baseline checker, confirms the generated manifest carries the exact package/version/profile/resolved integrity, and confirms the umbrella baseline identifies the expected `core` + `deployment` components.
12. The workflow replaces only the approved seed state, verifies the staged diff, commits as the actual `<app-slug>[bot]` GitHub App identity, pushes without force, and records the generated baseline commit.
13. ChatGPT verifies target default-branch CI on the exact published commit before local clone/fetch and setup acceptance.

A missing/inaccessible target or Bootstrap repository, unavailable exact npm package, package integrity mismatch, invalid package/profile identity, managed-path conflict/drift, failed generator/package check, or failed/unavailable control-plane run is a stop condition. It is **not** permission for ChatGPT to silently switch to local generation, choose another package version/component commit, or create a ZIP/downloadable generated workspace. Local generation is used only when the human explicitly chooses that path.

## Remote Core-sync request contract

A generated/self-contained consumer may configure the generic Core `/core-sync` skill with this provider. When no safe local Core checkout is available, the developer authorizes one public request:

```text
[sync-core] owner/repository
```

with an empty body.

This existing-consumer workflow is separate from greenfield package acquisition. It remains available for consumers that still use the Core-specific sync contract.

The remote workflow then:

1. verifies the request author equals the target owner and the owner is currently authorized by the compatibility projection derived from the developer registry;
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
