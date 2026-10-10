# Lean POC Control Plane

Public, credential-isolated orchestration for GitHub-first Lean POC generation across approved developer-owned repositories.

## Ownership model

The reusable engineering platform remains private and Mark-owned:

- `mriekki/lean-agentic-core`
- `mriekki/lean-poc-bootstrap`
- `mriekki/lean-workspace-adoption-kit`

Each developer owns their own POC repositories. This public control plane contains only request/orchestration code; it must not contain private POC product definitions, GitHub App private keys, personal access tokens, or other credentials.

## Request model

A generation request is a public issue whose title contains only:

```text
[generate-poc] owner/repository
```

The approved `POC_BOOTSTRAP.json` stays private in the target repository. The request author must match the target owner and be present in `config/allowed-owners.json`.

The workflow uses short-lived GitHub App installation tokens scoped separately to:

1. Mark-owned Bootstrap/Core source repositories; and
2. the single requested target POC repository.

See `docs/SETUP.md` for GitHub App configuration and migration details.

## Current status

This repository is not canonical generation infrastructure until all of the following are true:

1. the initial control-plane PR is merged with green CI;
2. the GitHub App is created and installed on approved developer accounts;
3. an end-to-end generation test succeeds;
4. `mriekki/lean-poc-bootstrap` explicitly advances its protocol/catalog to the multi-owner control plane.

Until then, Bootstrap protocol v4 remains authoritative.
