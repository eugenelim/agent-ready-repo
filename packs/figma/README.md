# figma

Let your agent work with your Figma files from a normal share URL: **read a
design's structure, render a frame to an image, pull comments or variables, and
turn a FigJam connector diagram into Mermaid**. You give it a Figma URL and a
frame name — no file keys, node IDs, or subcommands to learn.

## What it changes — and what it doesn't

Figma's REST API is **read + comments only**, and this pack stays inside that:

- **It does not edit your design.** No creating, moving, or changing nodes —
  that needs Figma's Plugin API, not REST.
- **It can post comments**, and comments are **visible to every collaborator**
  on the file. A comment write always asks for your confirmation first.
- **Every render ends with a receipt** naming the source frame, the local file
  it wrote, the format, any skipped or lower-fidelity nodes, and
  **`No Figma changes made`** — so you always know nothing on Figma's side moved.

## Before you install

You'll need:

1. A **Figma account** with at least **view** access to the file you want to read.
2. A **Figma personal access token** (PAT), created at Figma → Settings →
   Security → Personal access tokens.
3. **Python** on your machine — the pack shells out to a small Python client.

**About token scopes and 403s.** Reading files, frames, and comments works on
any plan. **Variables** (design tokens) typically require an **Enterprise** org,
and **Dev Resources** require **Dev Mode** / the `file_dev_resources:read`
scope — without them, those two calls return **403**. Generate your PAT with the
scopes you need *before* you start, not after the first failure.

## Setup, in order

Do these once, top to bottom:

1. **Install the figma pack** — user scope by default, so your token stays yours:
   ```
   # <catalogue> is your catalogue URI: a local clone path or a git+https://… URL.
   agentbundle install --pack figma <catalogue>
   ```
2. **Install the Python dependencies** — `python -m pip install credbroker httpx`
   (`httpx` is the HTTP client; `credbroker` resolves your token — step 3's pack
   also ships `credbroker` as a fallback, so this pip install just guarantees
   it's importable).
3. **Install the credentials capability** — the
   [`credential-brokers`](../credential-brokers/README.md) pack. It ships the
   `credbroker` resolver and the interactive `credential-setup` skill.
4. **Create your Figma PAT** (see *Before you install* above).
5. **Complete credential setup interactively** — tell your agent
   **"set up credentials"**. The `credential-setup` skill prompts *you* for the
   token and stores it in your OS keychain (or a `0600` dotfile). **This step is
   yours, not the agent's:** the agent never types your token for you, and
   secrets never go on the command line or into the repo.
6. **Check the connection** — ask your agent to **"check my Figma connection"**.
   It runs a reachability probe (the agent does this) and confirms your account
   is visible with no auth error.

## Usage

Give your agent a normal Figma share URL and a frame name. For example:

- "Read the structure of this Figma file and list its pages and top-level
  frames: `<file-url>`."
- "Render the 'Login' frame of `<file-url>` as a PNG."
- "Convert the FigJam connector graph in `<file-url>` to a Mermaid diagram."

The result is a plain answer in chat (structure, comments) or a local image file
(renders) — with the render receipt above so you can find it and confirm nothing
changed on Figma.

---

→ **Go deeper:** the [`figma` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/figma/).
