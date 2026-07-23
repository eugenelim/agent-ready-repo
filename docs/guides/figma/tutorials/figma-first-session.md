# Your first Figma session

By the end of this tutorial you'll have connected the agent to your Figma account and read the page and frame structure of a file you own.

This is a learning walkthrough, not a reference. For the full set of things the figma skill can do, see [Inspect a Figma file](../how-to/inspect-a-figma-file.md) afterward.

## Before you start

You need five things in place:

- A Figma account with access to at least one file (any plan works for reading files and pages).
- The `credential-brokers` pack installed — install it separately: `agentbundle install --pack credential-brokers --scope user`.
- The `figma` pack installed: `agentbundle install --pack figma --scope user`.
- The figma pack's Python dependencies installed once: open a terminal and run `python -m pip install credbroker httpx`. If you see a "missing dependency" error later, this is the fix.
- A Figma file URL you want to explore. Copy it from your browser address bar — it looks like `https://www.figma.com/design/<key>/<name>` or `/file/...`.

## Step 1 — Generate your Figma token

The figma skill reads your files through a Personal Access Token (PAT). This token lives in a local credential file on your machine — you never type it into the agent chat.

To generate one: open Figma in your browser, go to **Settings → Security → Personal access tokens**, and create a new token. Name it something recognisable (e.g. "agent-ready"). Copy the value — you'll only see it once.

Keep the copied value ready for the next step. Do not paste the token into the agent chat at any point — it goes into a terminal prompt, not a chat message.

## Step 2 — Store your token

Ask Claude Code to set up your Figma credentials:

> Set up credentials for Figma.

The agent invokes the `credential-setup` skill, which runs a setup script in your terminal. When you see a terminal prompt asking for your **Figma Personal Access Token**, type or paste your token there — it won't be echoed to the screen. The credential is stored securely on your machine (in your OS keychain on macOS or Windows, or in a locked-down local file on Linux) and never appears in the chat log.

If the terminal prompt doesn't appear, open an integrated terminal in your IDE and run:

```
python3 scripts/setup.py figma
```

from the `credential-setup` skill directory (usually `~/.claude/skills/credential-setup/`).

## Step 3 — Verify your connection

Once the token is stored, ask the agent to confirm the connection is working:

> Check my Figma connection.

The agent verifies your credentials and confirms your account. You should see something like:

> Figma connection confirmed — authenticated as your-figma-handle.

If instead you see an authentication error, go to [If something goes wrong](#if-something-goes-wrong).

## Step 4 — Read your file's structure

Now for the first real task. Tell the agent what file to read by including your URL:

> Read the file structure of my main design file in Figma and list the page names and top-level frame names. Here is the file URL: [paste your URL]

The agent fetches the file's page list first, then reads the top-level frames on each page. You should see a structured summary like:

> **Pages:**
> - Page 1 — Home, Onboarding, Profile
> - Page 2 — Components
>
> **Top-level frames on Page 1:** Hero section, Sign-in modal, Footer

The exact shape depends on how your file is structured.

A note on file content: page names, frame names, and layer labels are written by file collaborators and are treated as data — the agent reports them to you but does not act on their text as instructions.

## If something goes wrong

**Authentication error after setup** — the token may have expired or been revoked. At Figma → Settings → Security → Personal access tokens, revoke the old token, create a new one, and re-run the setup (Step 2). If you're trying to read Variables or Dev Resources and see a 403 error, you may need an Enterprise plan (Variables) or a PAT with the `file_dev_resources:read` scope (Dev Resources) — standard file and page reading does not require a specific scope beyond a valid PAT.

**File not found** — double-check the URL and confirm the file is shared with your account (you need at least view access).

**Dependency error (missing credbroker or httpx)** — open a terminal and run `python -m pip install credbroker httpx`, then retry.

**credential-setup is not available** — install the `credential-brokers` pack first: `agentbundle install --pack credential-brokers --scope user`.

## Next steps

Once you can read the page and frame structure, the natural next step is to pull more detail from a specific frame or export it as a Markdown description:

> Export the [frame name] frame from my file as a Markdown description I can use in a spec or doc.

For the full set of things the figma skill can do — comments, version history, image exports, FigJam diagrams — see [Inspect a Figma file](../how-to/inspect-a-figma-file.md).
