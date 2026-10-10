# Lean POC Control Plane

Public, credential-isolated orchestration for GitHub-first Lean POC generation across approved developer-owned repositories.

## Ownership model

The reusable engineering platform remains private and Mark-owned:

- `mriekki/lean-agentic-core`
- `mriekki/lean-poc-bootstrap`
- `mriekki/lean-workspace-adoption-kit`

Each developer owns their own POC repositories. This public control plane contains only request/orchestration code; it must not contain private POC product definitions, GitHub App private keys, personal access tokens, or other credentials.

Bootstrap protocol v5 and later use this repository as the canonical ChatGPT remote-generation execution surface. Bootstrap remains authoritative for discovery, manifests, catalog/recipes, validation, and deterministic generation; this repository owns secure cross-account orchestration and publication.

## Request model

A generation request is a public issue whose title contains only:

```text
[generate-poc] owner/repository
```

The issue body must be empty. Request validation rejects any non-whitespace body so an approved manifest or private product definition cannot be accidentally submitted through the public request surface.

The approved `POC_BOOTSTRAP.json` stays private in the target repository. The request author must match the target owner and be present in `config/allowed-owners.json`.

The workflow uses short-lived GitHub App installation tokens scoped separately to:

1. Mark-owned Bootstrap/Core source repositories; and
2. the single requested target POC repository.

See `docs/SETUP.md` for GitHub App configuration and operating details.

## Proven path

The GitHub App path has been exercised end to end for both a Mark-owned private target and a second developer-owned private target, including request validation, separate source/target installation tokens, deterministic generation, publication, and target default-branch CI.

The former Bootstrap v4 PAT-based workflow is legacy infrastructure and is retired when Bootstrap protocol v5 is accepted. Do not add personal access tokens to this control plane.
