# Project Forge Developer Invitations

The invitation system is the onboarding/authorization layer for developers who use Project Forge through the existing public Lean Control Plane infrastructure.

Project Forge is the human-facing product name. Technical compatibility identifiers such as `lean-poc-control-plane`, `[invite-lean]`, `/accept-lean`, `poc-author`, and `[generate-poc]` remain stable until a separate migration is justified.

The onboarding model intentionally separates three questions:

```text
Invitation / developer registry
Who may use Project Forge?

Public ChatGPT contract
How should ChatGPT guide the Builder now?

Generated project repository
What is true about this project?
```

## Developer registry

`config/developers.json` is the operational developer registry.

Current technical roles:

- `admin` — normal Project Builder capabilities plus invitation/revocation administration;
- `poc-author` — the compatibility identifier for a normal Project Builder with generation and supported update/sync authorization.

`config/allowed-owners.json` remains a generated compatibility projection for the existing generation/sync request validator. It must exactly mirror ACTIVE developers that carry `generate-poc`. CI validates that invariant.

No credential, private project definition, private repository content, or secret belongs in either file.

## Product-facing invitation flow

An active admin creates one public issue with an empty body:

```text
[invite-lean] github-owner
```

Creating that issue is the meaningful administrative authorization gate.

The issue URL is the single invitation/onboarding portal. The workflow explains what Project Forge is, makes clear that the invited Builder owns their own repositories, links to the public Project Forge welcome page, and presents only two normal activation actions:

```text
1. Install/approve Project Forge's GitHub App
   (currently registered as Lean POC Generator)
2. While signed in as the exact invited GitHub owner,
   comment /accept-lean
```

The invitation should not require the developer to understand Control Plane, Bootstrap, package, or contract internals before accepting.

For the smoothest zero-extra-step generation experience, install the GitHub App for all repositories in the invited account. Exact workflow tokens remain scoped to the repository being operated on. Selecting individual repositories is supported, but every newly created Project Forge repository must then be added to the App installation before generation/update operations can use it.

The claim workflow verifies:

- the invitation was opened by a currently authorized admin;
- the commenter exactly matches the invited owner;
- the invitation is still inside the configured claim window;
- the required GitHub App installation can be minted/verified for that owner.

Only then does it activate the developer registry and compatibility allowlist.

Knowing or forwarding an invitation URL does not grant authorization.

The invited developer may instead comment:

```text
/decline-lean
```

Decline closes the invitation and makes no registry/authorization change.

## Automatic readiness after activation

A successful `/accept-lean` now performs the normal onboarding readiness check automatically after activation.

The happy path is therefore:

```text
PENDING
→ identity verified
→ GitHub App verified
→ ACTIVE
→ public Project Forge contract verified automatically
→ READY FOR PROJECT FORGE
```

The developer should not need to run a separate doctor command on the normal path.

If activation succeeds but the public Project Forge contract cannot be verified, authorization remains ACTIVE and the invitation stays available as the recovery surface. After the underlying problem is corrected, the developer or an admin may comment:

```text
/lean-doctor
```

That command is a retry/diagnostic mechanism, not a ceremonial onboarding step.

For an already-ACTIVE developer who has no invitation issue, the developer can open one empty-body public issue under their own GitHub identity:

```text
[lean-doctor] github-owner
```

An active admin may open the same issue for that developer. Opening the standalone doctor issue runs the check immediately.

The readiness check verifies:

- the developer is `ACTIVE`;
- the GitHub App installation remains available;
- the public `lean-platform/chatgpt/current.json` descriptor is reachable;
- every referenced public contract document matches its SHA-256 digest.

The successful result is:

```text
READY FOR PROJECT FORGE
```

After readiness, the developer configures a ChatGPT coding Project once using the public Project Forge setup guide and a small personal Developer Profile. Normal work then begins with:

```text
New Project: <idea>
```

`New POC:` remains a compatibility alias for the same internal discovery/generation protocol.

## Invitation lifecycle

The configured invitation claim lifetime is read from `config/invitation-policy.json` (currently 30 days).

Terminal states remain:

```text
DECLINED
EXPIRED
```

Expired invitations are closed automatically by the scheduled expiry workflow. Expiration and decline never mutate the developer registry. A failed App check leaves the invitation pending and does not activate authorization.

## Revoke flow

An active admin creates an empty-body issue:

```text
[revoke-lean] github-owner
```

Revocation removes the developer from future Control Plane authorization.

It must never delete, transfer, disable, rewrite, or otherwise mutate repositories that developer already owns.

The tooling refuses to revoke the last active admin.

## GitHub App setup

For the smoothest invitation experience, configure repository variable:

```text
APP_INSTALL_URL
```

to the actual GitHub App installation URL. The registered App name may remain `Lean POC Generator` during the compatibility period even though the public product is Project Forge.

If `APP_INSTALL_URL` is absent, the invitation points to the Control Plane setup documentation instead.

The existing `APP_CLIENT_ID` variable and `APP_PRIVATE_KEY` secret remain the only App credentials used by workflows. Invitation records never contain them.

## Public onboarding pages

Project Forge overview:

```text
https://github.com/mriekki/lean-platform/blob/main/WELCOME.md
```

ChatGPT one-time setup:

```text
https://github.com/mriekki/lean-platform/blob/main/chatgpt/SETUP.md
```

The low-level public bootstrap entrypoint remains:

```text
https://github.com/mriekki/lean-platform/blob/main/chatgpt/START_HERE.md
```

New developers should use the invitation + Project Forge public onboarding path. They should not need copies of legacy Mark/Kyle handoff files or direct access to private Bootstrap/Core repositories.
