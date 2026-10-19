# Project Forge Builder Setup

This page is for a developer who has been invited to **Project Forge**.

You do **not** need to configure the Project Forge Control Plane, GitHub Actions variables/secrets, Bootstrap, or any Project Forge infrastructure. Those are administrator responsibilities.

## Activate your access

Use the Project Forge invitation issue you received.

### 1. Install Project Forge Builder

In the invitation issue, open the **Project Forge Builder** GitHub App link and install/approve it for your GitHub account if needed.

For the simplest experience, allow the App for **all repositories** in your account. You can choose selected repositories instead, but any new Project repository must be added to the App before Project Forge can generate or update it.

If the App is already installed, do not remove or reinstall it just to continue.

### 2. Accept the invitation

Return to the same invitation issue. While signed in as the GitHub account that was invited, add a new comment containing exactly:

```text
/accept-lean
```

Project Forge will automatically verify your GitHub identity, App installation, activation, and public Project Forge contract.

When the issue reports **Project Forge is ready**, GitHub onboarding is complete.

## Next: set up ChatGPT once

Follow the one-time ChatGPT setup guide:

https://github.com/mriekki/project-forge-platform/blob/main/chatgpt/SETUP.md

After that, start a coding Project with:

```text
New Project: <your idea>
```

## If activation says the App is missing

Use the **Project Forge Builder** installation link in your invitation issue, approve the App for the invited GitHub account, then comment `/accept-lean` again.

Do not create GitHub Actions variables, secrets, App credentials, or Control Plane configuration yourself. If the invitation issue does not provide a working App installation link, contact the person who invited you; that is a Project Forge administrator configuration problem.

## More about Project Forge

- Project Forge overview: https://github.com/mriekki/project-forge-platform/blob/main/WELCOME.md
- ChatGPT setup: https://github.com/mriekki/project-forge-platform/blob/main/chatgpt/SETUP.md
- Project Forge Control Plane: https://github.com/mriekki/project-forge-control-plane

Administrators/operators: see [`ADMIN_SETUP.md`](ADMIN_SETUP.md).
