# figma

A credentialed Figma REST API primitive for reading and acting on Figma files
from your agent.

## What's inside

- Read files, nodes, metadata, versions, comments, variables, and dev
  resources.
- Render frame images and post comments.
- Convert FigJam connector graphs to Mermaid.

## Install

`figma` is **user-scope by default** — your Figma token is yours.

```
agentbundle install --pack figma <catalogue>
```

## Set up credentials

The `figma` CLI needs a Figma personal access token. Install the
`credential-brokers` pack, then tell your agent **"set up credentials"** — the
interactive `credential-setup` skill prompts you for the token and stores it in
your OS keychain (or a `0600` dotfile on Linux). Secrets never go on the command
line and never enter the repo. See the
[`credential-brokers` README](../credential-brokers/README.md).

## Usage

Once credentials are set up, ask your agent, for example:

- "List the variables defined in this Figma file: <file-url>."
- "Render frame 3 of this Figma file as a PNG."
- "Convert the FigJam connector graph in <file-url> to a Mermaid diagram."
