# Lean POC Control Plane

Public, credential-isolated orchestration for GitHub-first Lean POC generation and remote Lean Core synchronization across approved developer-owned repositories.

## Ownership model

Canonical reusable engineering sources remain separately owned:

- `mriekki/lean-agentic-core` — reusable workflow behavior and Core distribution;
- `mriekki/lean-poc-bootstrap` — discovery, manifest/catalog contracts, and deterministic greenfield generation;
- `mriekki/lean-poc-deployment-kit` — reusable deployment mechanics;
- `mriekki/lean-workspace-adoption-kit` — existing-repository adoption behavior;
- `mriekki/lean-platform` / public `@mriekki/lean` — exact accepted reusable-component assembly and consumer delivery plus the public ChatGPT bootstrap-contract projection.

Each developer owns their own POC repositories. This public control plane contains only request/orchestration and developer-authorization metadata; it must not contain private POC product definitions, GitHub App private keys, personal access tokens, or other credentials.

This repository is the canonical ChatGPT remote-generation execution surface and the cross-account Lean developer invitation/authorization surface. Bootstrap remains authoritative for discovery, manifests, catalog/recipes, validation, and deterministic project/workspace generation. The public `@mriekki/lean` package remains the normal reusable-asset delivery boundary for generated POCs. This repository owns secure cross-account authorization, orchestration, and publication.

Existing Core consumers may also use this repository as a configured remote `/core-sync` provider when no safe local Core checkout is available. That workflow remains a separate existing-consumer compatibility path and does not participate in greenfield package acquisition.

## Developer invitations and authorization

`config/developers.json` is the operational authorization registry. It distinguishes active admins from normal POC authors and records explicit capabilities. `config/allowed-owners.json` remains a generated compatibility projection for the existing generation/sync request validator; CI requires it to exactly mirror active developers with `generate-poc` capability.

An active admin authorizes onboarding by opening one empty-body issue:

```text
[invite-lean] github-owner
```

The issue URL is the onboarding portal. The invited GitHub identity must claim it with `/accept-lean` while the invitation is still valid, and the workflow verifies the Lean POC Generator GitHub App installation before activating authorization. The invited owner may use `/decline-lean`; unclaimed invitations expire under `config/invitation-policy.json`. After activation, `/lean-doctor` verifies registry state, GitHub App installation, and the public Lean ChatGPT bootstrap contract.

Revocation uses one admin-authorized empty-body issue:

```text
[revoke-lean] github-owner
```

Revocation removes future Control Plane authorization only. It never deletes, transfers, disables, or mutates repositories already owned by the developer. The tooling refuses to revoke the last active Lean admin.

See `docs/INVITATIONS.md` for the full lifecycle.

## Request model

A generation request is a public issue whose title contains only:

```text
[generate-poc] owner/repository
```

A remote Core-sync request is a public issue whose title contains only:

```text
[sync-core] owner/repository
```

For both request types, the issue body must be empty. Request validation rejects any non-whitespace body so private product definitions, baseline details, source code, or secrets cannot be accidentally submitted through the public request surface.

The request author must match the target owner and be ACTIVE for the relevant Control Plane capability. Existing request workflows consume `config/allowed-owners.json`, which is mechanically projected from the developer registry. Foundational/platform repositories are not valid remote generation or generic remote Core-sync targets.

The approved `POC_BOOTSTRAP.json` stays private in a generation target. `CORE_BASELINE.json` stays private in a Core-sync target. The workflows read those target-private files only after minting a GitHub App installation token scoped to that exact repository.

The generation workflow uses separate credentials/boundaries for:

1. a short-lived GitHub App source token scoped only to private `mriekki/lean-poc-bootstrap`;
2. public npm acquisition of the exact manifest-approved `@mriekki/lean` version;
3. a short-lived GitHub App target token scoped only to the requested POC repository.

The remote Core-sync workflow separately mints a source token scoped only to `mriekki/lean-agentic-core` plus its exact-target token.

See `docs/SETUP.md` for GitHub App configuration and operating details.

## GitHub-first generation

The `[generate-poc]` workflow keeps the public request surface deliberately empty of private manifest data. After it reads and validates the approved private target manifest, it:

1. validates schema-v2 `generation.lean` and receives exact package, version, `greenfield-poc` profile, and SHA-512 integrity from Bootstrap;
2. downloads that exact public npm tarball with lifecycle scripts disabled;
3. verifies the downloaded tarball against the approved SHA-512 integrity before generation;
4. passes that exact tarball to Bootstrap's canonical `generate_snapshot.py --lean-tarball` path;
5. lets the exact local package CLI perform whole-profile preflight/apply/check for reusable Core + Deployment assets;
6. validates `LEAN_BASELINE.json`, component-native baselines, and the generated no-network managed-baseline checker; and
7. publishes only the validated generated tree to the approved target repository without force-pushing.

Normal greenfield generation does **not** check out private Core or Deployment Kit sources. Their exact accepted repository/commit/distribution provenance is assembled into `@mriekki/lean` upstream by `lean-platform` and recorded in the generated component-native baselines.

A missing package version, integrity mismatch, invalid package/profile identity, reusable managed-path conflict, unavailable required target/source access, or failed generation is a stop condition. The workflow does not substitute another package version, component commit, or generation destination.

## Remote Core sync

The `[sync-core]` workflow is intentionally narrower than arbitrary repository automation. It:

1. validates the owner-authored, authorized, empty-body public request;
2. checks out current accepted `mriekki/lean-agentic-core` using a short-lived source token;
3. checks out only the requested private target using a short-lived target token;
4. requires a valid `CORE_BASELINE.json` owned by `mriekki/lean-agentic-core` and the `greenfield-workspace` distribution;
5. verifies existing Core-managed paths against their recorded hashes before any branch is created;
6. runs Core's canonical sync preview/apply contract, which refuses unsafe consumer drift/conflicts;
7. pushes a new non-force `chore/sync-core-<short-sha>` branch;
8. creates a target-repository PR;
9. observes the target PR checks; and
10. reports the PR only after those checks are green.

If the consumer is already current, no branch or PR is created. Merge remains a human decision in the target repository.

Family Meal Planner is excluded from this generic remote path because it has documented consumer-specific Core override handling; its specialized synchronization contract remains authoritative for that repository.

## Proven path

The GitHub App generation path has been exercised end to end for both a Mark-owned private target and a second developer-owned private target, including request validation, separate source/target installation tokens, deterministic generation, publication, and target default-branch CI.

The current greenfield path now uses exact public `@mriekki/lean` artifact delivery and retains Bootstrap's target/private-manifest safety boundary. Deployment support remains `partial` until the planned unrelated generated-consumer deploy/tear-down proof is completed through this package-based path.

The remote Core-sync path remains subject to its documented end-to-end proof and GitHub App Pull requests/Checks permissions in `docs/SETUP.md`.
