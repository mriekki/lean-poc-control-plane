# Project Forge Developer Invitations

The invitation system is the onboarding/authorization layer for Builders who use Project Forge.

Canonical Control Plane repository:

```text
mriekki/project-forge-control-plane
```

The public GitHub App display name is **Project Forge Builder**. Canonical technical identifiers include `[invite-project-forge]`, `/accept-project-forge`, `poc-author`, `[generate-project]`, and `POC_BOOTSTRAP.json`.

The onboarding model separates three questions:

```text
Invitation / developer registry
Who may use Project Forge?

Public ChatGPT contract
How should ChatGPT guide the Builder now?

Generated Project repository
What is true about this Project?
```

## Admin quick actions

From **Issues → New issue** choose:

- **Invite a Project Forge Builder** — real authorization invitation for another GitHub owner;
- **Test Project Forge onboarding** — non-authorizing self-test using the active admin's own GitHub account.

The self-test is zero-input: submit the prefilled empty-body issue. The workflow infers the active admin from the issue opener.

## Developer registry

`config/developers.json` is the operational developer registry.

Current technical roles remain:

- `admin` — normal Project Builder capabilities plus invitation/revocation administration;
- `poc-author` — role identifier for a normal Project Builder with generation and supported update/sync authorization.

`config/allowed-owners.json` remains a generated authorization projection for existing validators and must mirror ACTIVE developers with `generate-project`. CI validates that invariant.

No credential, private Project definition, private repository content, or secret belongs in either file.

## Product-facing invitation flow

An active admin creates one public issue with an empty body:

```text
[invite-project-forge] github-owner
```

Creating that issue is the meaningful administrative authorization gate.

The issue URL is the invitation/onboarding portal. The notification and issue instructions make the complete Builder action explicit:

```text
1. Open the Project Forge invitation issue.
2. Install/approve the Project Forge Builder GitHub App if needed.
3. In that same issue, add a new comment containing exactly:
   /accept-project-forge
```

The invited Builder does not need to understand or configure the Control Plane, GitHub Actions, Bootstrap, package plumbing, App credentials, or contract internals before accepting. Builder-facing guidance lives in `docs/SETUP.md`; operator setup lives separately in `docs/ADMIN_SETUP.md`.

For the smoothest flow, install Project Forge Builder for all repositories in the invited account. Exact workflow tokens remain scoped to the repository being operated on. Selecting individual repositories is supported, but each newly created Project repository must then be added before generation/update operations can use it.

The invitation workflow derives the GitHub App installation URL automatically from the actual App slug returned by `actions/create-github-app-token`. There is no separate `APP_INSTALL_URL` configuration variable and no fallback from a Builder invitation into administrator setup documentation.

The claim workflow verifies:

- the invitation was opened by a currently authorized admin;
- the commenter exactly matches the invited owner;
- the invitation is still inside the configured claim window;
- the Project Forge Builder GitHub App installation can be minted/verified for that owner.

Only then does it activate the developer registry and authorization projection.

Knowing or forwarding an invitation URL does not grant authorization.

The invited developer may instead comment `/decline-project-forge`; decline closes the invitation and makes no registry change.

## Automatic readiness after activation

Successful `/accept-project-forge` performs the normal readiness check automatically:

```text
PENDING
→ identity verified
→ Project Forge Builder GitHub App verified
→ ACTIVE
→ public Project Forge contract verified
→ READY FOR PROJECT FORGE
```

The Builder should not need a separate doctor command on the happy path.

If activation succeeds but the public contract cannot be verified, authorization remains ACTIVE and the invitation remains the recovery surface. After the underlying problem is fixed, the Builder or admin may comment `/project-forge-doctor`.

An already-ACTIVE Builder without an invitation issue can instead open:

```text
[project-forge-doctor] github-owner
```

The readiness check verifies ACTIVE registry state, Project Forge Builder App availability, and the SHA-256-pinned public Project Forge contract.

After readiness, the Builder configures a ChatGPT coding Project once using the public setup guide, then starts normal work with:

```text
New Project: <idea>
```


## Admin onboarding test mode

An active admin can rehearse onboarding before inviting a real Builder by submitting the empty-body **Test Project Forge onboarding** issue template:

```text
[test-invite-forge]
```

The opener identity is the test identity. The `/accept-project-forge` commenter must be that same active admin. A self-test cannot target another Builder.

The test portal reproduces:

```text
short invitation preview
→ direct Project Forge Builder GitHub App install page
→ /accept-project-forge
→ GitHub identity verification
→ App installation verification
→ public Project Forge contract verification
→ TEST READY FOR PROJECT FORGE
```

The test is deliberately non-authorizing:

- test claim repository contents permission is read-only;
- no activation operation runs;
- developer registry and authorization projection are never written;
- no role/capability change occurs;
- no Project repository is created/generated;
- no deployment or tear-down path is available.

A successful test demonstrates onboarding UX and readiness without changing future authorization.

## Invitation lifecycle

The invitation claim lifetime comes from `config/invitation-policy.json`.

Terminal states include:

```text
DECLINED
EXPIRED
```

Expiration and decline never mutate developer authorization. A failed App check leaves the invitation pending.

## Revoke flow

An active admin creates an empty-body issue:

```text
[revoke-project-forge] github-owner
```

Revocation removes future Control Plane authorization only. It never deletes, transfers, disables, rewrites, or otherwise mutates repositories already owned by the Builder. The tooling refuses to revoke the last active admin.

## GitHub App administration

`APP_CLIENT_ID` and `APP_PRIVATE_KEY` remain the Control Plane workflow credentials. The invitation workflow uses them to resolve the real App slug and derive GitHub's standard installation URL automatically.

Builders do not configure these values. Administrator setup is documented in `docs/ADMIN_SETUP.md`.

## Public onboarding pages

Project Forge overview:

```text
https://github.com/mriekki/project-forge-platform/blob/main/WELCOME.md
```

Builder GitHub onboarding:

```text
https://github.com/mriekki/project-forge-control-plane/blob/main/docs/SETUP.md
```

ChatGPT one-time setup:

```text
https://github.com/mriekki/project-forge-platform/blob/main/chatgpt/SETUP.md
```

Low-level public bootstrap entrypoint:

```text
https://github.com/mriekki/project-forge-platform/blob/main/chatgpt/START_HERE.md
```

New Builders should use the invitation + Project Forge public onboarding path. They do not need legacy handoff files or direct access to private Bootstrap/Core repositories.
