# user-guide-diataxis

A Diátaxis-shaped user-guide skeleton on top of `core`, so a project's
end-user docs start with the right four-quadrant structure.

## What's inside

- `guides/` with `tutorials/`, `how-to/`, `reference/`, and `explanation/`
  seed READMEs.
- `new-guide` skill that writes into the matching quadrant.

## Install

`user-guide-diataxis` is **repo-scope** — it scaffolds *this* project's user
guides. It **requires `core`** (`^0.1`); install `core` first or alongside.

```
agentbundle install --pack user-guide-diataxis <catalogue>
```

## Usage

Ask your agent, for example:

- "Write a how-to guide for resetting a password."
- "Draft a tutorial that walks a new user through their first import."
- "Add a reference page documenting the CLI flags."
