# Lean Developer Invitations

The invitation system is the onboarding/authorization layer for developers who use the public Lean Control Plane.

It intentionally separates three questions:

```text
Invitation / developer registry
Who may use Lean?

Public ChatGPT bootstrap contract
How should ChatGPT behave now?

Generated POC repository
What is true about this project?
```

## Developer registry

`config/developers.json` is the operational developer registry.

Current roles:

- `admin` — normal POC-author capabilities plus invitation/revocation administration;
- `poc-author` — normal POC generation and remote Core-sync authorization.

`config/allowed-owners.json` remains a generated compatibility projection for the existing generation/sync request validator. It must exactly mirror ACTIVE developers that carry `generate-poc`.

No credential, private POC definition, private repository content, or secret belongs in either file.

## Invite flow

An active admin creates one public issue with an empty body:

```text
[invite-lean] github-owner
```

Creating that issue is the meaningful administrative authorization gate.

The issue URL is the invitation/onboarding portal. The workflow posts the current instructions and marks the invitation logically `PENDING`.

The invited developer:

1. installs/approves the Lean POC Generator GitHub App for their account;
2. signs in as the exact invited GitHub owner;
3. comments exactly:

```text
/accept-lean
```

The claim workflow verifies:

- the invitation was opened by a currently authorized admin;
- the commenter exactly matches the invited owner;
- the required GitHub App installation can be minted/verified for that owner.

Only then does it activate the developer registry and compatibility allowlist.

Knowing or forwarding an invitation URL does not grant authorization.

## Invitation lifecycle

```text
PENDING
→ claim identity verified
→ GitHub App installation verified
→ ACTIVE
```

Other terminal states:

```text
REVOKED
```

A failed App check leaves the invitation pending and does not mutate authorization.

## Onboarding doctor

After activation, the developer or an admin can comment:

```text
/lean-doctor
```

The doctor verifies:

- the developer is `ACTIVE`;
- the GitHub App installation remains available;
- the public `lean-platform/chatgpt/current.json` descriptor is reachable;
- every referenced public contract document matches its SHA-256 digest.

The successful result is:

```text
READY FOR LEAN
```

The developer then configures a ChatGPT coding Project once using the public bootstrap entrypoint and a small personal profile.

## Revoke flow

An active admin creates an empty-body issue:

```text
[revoke-lean] github-owner
```

Revocation removes the developer from future Control Plane authorization.

It must never delete, transfer, disable, rewrite, or otherwise mutate repositories that developer already owns.

The tooling refuses to revoke the last active Lean admin.

## GitHub App setup

For the smoothest invitation message, configure repository variable:

```text
APP_INSTALL_URL
```

to the actual Lean POC Generator installation URL.

If it is absent, the invitation points to the Control Plane setup documentation instead.

The existing `APP_CLIENT_ID` variable and `APP_PRIVATE_KEY` secret remain the only App credentials used by workflows. Invitation records never contain them.

## ChatGPT handoff migration

The public ChatGPT bootstrap entrypoint is:

```text
https://github.com/mriekki/lean-platform/blob/main/chatgpt/START_HERE.md
```

Existing Mark/Kyle long-form handoffs may remain temporarily as fallback compatibility context while the new path is proven.

New developers should start directly with invitation + public bootstrap contract. They should not need copies of the legacy shared handoff files.
