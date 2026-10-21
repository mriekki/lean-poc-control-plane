# Project Forge Control Plane

Public, credential-isolated orchestration for **Project Forge** onboarding, GitHub-first Project generation, developer authorization, and supported remote update workflows.

Canonical repository identity after the coordinated rename:

```text
mriekki/project-forge-control-plane
```

Canonical technical commands and schema identifiers include `[invite-project-forge]`, `/accept-project-forge`, `[generate-project]`, and `PROJECT_BOOTSTRAP.json`.

## Admin quick start

From **Issues → New issue**, choose:

- **Invite a Project Forge Builder** — real invitation/authorization for another GitHub owner;
- **Test Project Forge onboarding** — non-authorizing self-test using your own active admin account.

The self-test is zero-input: submit the prefilled issue. The workflow infers the active admin from the issue opener, renders the prospective invitation message, and can report `TEST READY FOR PROJECT FORGE`. It never changes authorization, Projects, or deployments.

For a real invitation, use:

```text
[invite-project-forge] github-owner
```

The invitation issue is the onboarding portal. The invited GitHub identity:

1. opens the invitation;
2. installs/approves the **Project Forge Builder** GitHub App if needed; and
3. replies in that same issue with exactly `/accept-project-forge`.

The workflow verifies the exact identity and GitHub App installation before activation. The invited owner may use `/decline-project-forge`; unclaimed invitations expire under `config/invitation-policy.json`.

Builder-facing setup is intentionally concise in `docs/SETUP.md`. Administrator/operator configuration is separate in `docs/ADMIN_SETUP.md`. See `docs/INVITATIONS.md` for the complete real/test invitation lifecycle.

## Ownership model

Canonical reusable engineering sources remain separately owned:

- `mriekki/project-forge-core` — reusable workflow behavior and Core distribution;
- `mriekki/project-forge-bootstrap` — Project Discovery, manifest/catalog contracts, and deterministic greenfield generation;
- `mriekki/project-forge-deployment-kit` — reusable deployment mechanics;
- `mriekki/project-forge-adoption-kit` — existing-repository adoption behavior;
- `mriekki/project-forge-platform` / public `@mriekki/project-forge` — exact accepted reusable-component assembly, consumer delivery, and public ChatGPT bootstrap contract;
- `mriekki/project-forge-control-plane` — secure cross-account authorization and GitHub orchestration.

Each Builder owns their own Project repositories. This public Control Plane contains only safe request/orchestration and developer-authorization metadata; it must not contain private Project definitions, GitHub App private keys, PATs, or other credentials.

## Developer authorization

`config/developers.json` is the operational authorization registry. `config/allowed-owners.json` remains a generated authorization projection for existing generation/sync validators; CI requires it to mirror active developers with `generate-project` capability.

An already-active Builder can use the doctor issue:

```text
[project-forge-doctor] github-owner
```

The doctor verifies registry state, Project Forge Builder GitHub App installation, and the public Project Forge ChatGPT contract. It is onboarding/readiness evidence, not a per-Project discovery requirement.

Revocation uses:

```text
[revoke-project-forge] github-owner
```

Revocation removes future Control Plane authorization only. It never deletes, transfers, disables, or mutates repositories already owned by the Builder. The tooling refuses to revoke the last active admin.

## Public request model

Generation request:

```text
[generate-project] owner/repository
```

Remote Core-sync request:

```text
[sync-core] owner/repository
```

For both request types, the issue body must be empty. Private product definitions, baseline details, source code, and secrets stay in the target repository.

The request author must match the target owner and be ACTIVE for the relevant capability. Foundational/platform repositories are never valid generation or generic Core-sync targets.

The approved `PROJECT_BOOTSTRAP.json` stays private in a generation target. `CORE_BASELINE.json` stays private in a Core-sync target. Workflows read those files only after minting a short-lived GitHub App installation token scoped to the exact repository.

## GitHub-first generation

The `[generate-project]` workflow:

1. validates the authorized, owner-authored, empty-body request;
2. reads and validates the private target `PROJECT_BOOTSTRAP.json`;
3. obtains a Bootstrap-only source token and an exact-target token;
4. resolves/verifies the exact public `@mriekki/project-forge` package selected by the approved manifest;
5. runs Bootstrap's canonical deterministic generation path;
6. validates generated baselines and managed-file integrity; and
7. publishes only the validated generated tree without force-pushing.

Normal approved discovery may use `generation.project-forge.integrity: "registry"`. Humans approve the exact package/version/profile, not npm hash plumbing. Bootstrap resolves registry metadata to the **resolved exact SHA-512 integrity** at the generation boundary, verifies it before reusable mutation, and records that exact value in generated provenance.

A missing package/version, integrity mismatch, invalid profile, managed-path conflict, unavailable required access, or failed generation is a stop condition. The workflow never silently substitutes another package, source commit, or destination.

## Remote Core sync

The `[sync-core]` workflow remains the narrower Core-specific path for generated consumers that still use Core-specific sync. It validates current baseline integrity, creates a new non-force branch when needed, opens a consumer PR, and reports success only after target PR checks are green. Merge remains a human decision in the consumer repository.

## GitHub App and setup

The public GitHub App display name is **Project Forge Builder**. GitHub's generated App slug/bot username remains an implementation identity and is resolved dynamically rather than guessed.

- Builder onboarding: `docs/SETUP.md`
- Control Plane administrator setup: `docs/ADMIN_SETUP.md`
