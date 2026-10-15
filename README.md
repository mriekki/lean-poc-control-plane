# Lean POC Control Plane

Public, credential-isolated orchestration for GitHub-first Lean POC generation and remote Lean Core synchronization across approved developer-owned repositories.

## Ownership model

The reusable engineering platform remains private and Mark-owned:

- `mriekki/lean-agentic-core`
- `mriekki/lean-poc-bootstrap`
- `mriekki/lean-workspace-adoption-kit`
- `mriekki/lean-poc-deployment-kit`

Each developer owns their own POC repositories. This public control plane contains only request/orchestration code; it must not contain private POC product definitions, GitHub App private keys, personal access tokens, or other credentials.

Bootstrap protocol v5 and later use this repository as the canonical ChatGPT remote-generation execution surface. Core consumers may also use it as a configured remote `/core-sync` provider when no safe local Core checkout is available. Bootstrap remains authoritative for discovery, manifests, catalog/recipes, validation, and deterministic generation; Lean Agentic Core remains authoritative for reusable synchronization behavior; Deployment Kit remains authoritative for reusable deployment mechanics; this repository owns secure cross-account orchestration and publication.

## Request model

A generation request is a public issue whose title contains only:

```text
[generate-poc] owner/repository
```

A remote Core-sync request is a public issue whose title contains only:

```text
[sync-core] owner/repository
```

For both request types, the issue body must be empty. Request validation rejects any non-whitespace body so private product definitions, Core baseline details, source code, or secrets cannot be accidentally submitted through the public request surface.

The request author must match the target owner and be present in `config/allowed-owners.json`. Foundational/platform repositories are not valid remote generation or generic remote Core-sync targets.

The approved `POC_BOOTSTRAP.json` stays private in a generation target. `CORE_BASELINE.json` stays private in a Core-sync target. The workflow reads target-private metadata only after minting a GitHub App installation token scoped to that exact target repository.

The workflows use short-lived GitHub App installation tokens scoped separately to:

1. Mark-owned Bootstrap/Core/Deployment Kit source repositories as needed; and
2. the single requested target POC repository.

See `docs/SETUP.md` for GitHub App configuration and operating details.

## GitHub-first generation

The `[generate-poc]` workflow keeps the public request surface deliberately empty of private manifest data. After it reads and validates the approved private target manifest, it:

1. checks out the exact manifest-pinned Lean Core commit;
2. when `generation.deploymentKit.enabled=true`, conditionally checks out the exact manifest-pinned `mriekki/lean-poc-deployment-kit` commit using the same read-only source installation token;
3. passes that checkout to Bootstrap's canonical `generate_snapshot.py --deployment-kit-path` integration;
4. validates generated Core provenance and, when enabled, `DEPLOYMENT_BASELINE.json` plus the generated Deployment Kit hash checker before publication; and
5. performs no Deployment Kit checkout and rejects unexpected Deployment Kit provenance when integration is disabled.

Repository/commit mismatches or inaccessible required source repositories fail generation. There is no PAT fallback and no fallback to another Deployment Kit commit or distribution.

## Remote Core sync

The `[sync-core]` workflow is intentionally narrower than arbitrary repository automation. It:

1. validates the owner-authored, allowlisted, empty-body public request;
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

Family Meal Planner is intentionally excluded from this generic remote path because it has documented consumer-specific Core override handling. Its specialized synchronization contract remains authoritative until that exception is retired canonically.

## Proven path

The GitHub App generation path has been exercised end to end for both a Mark-owned private target and a second developer-owned private target, including request validation, separate source/target installation tokens, deterministic generation, publication, and target default-branch CI.

Exact Deployment Kit source checkout/provenance is integrated into that path but still requires the planned unrelated greenfield consumer proof before deployment support is promoted beyond `partial`.

The remote Core-sync path must be proven end to end after its workflow is merged and the GitHub App has the additional Pull requests and Checks permissions documented in `docs/SETUP.md`.

The former Bootstrap v4 PAT-based workflow is legacy infrastructure and is retired when Bootstrap protocol v5 is accepted. Do not add personal access tokens to this control plane.
