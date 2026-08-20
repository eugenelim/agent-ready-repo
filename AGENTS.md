# AGENTS.md

> **This is the canonical agent context file.** `CLAUDE.md` is a symlink to it.
> Keep universal invariants here; put scoped deltas in the nearest `AGENTS.md`.

## What this repo is

This monorepo publishes a curated catalogue of portable agent-context packs — skills, subagents, commands, hooks, and seed documents — plus the `agentbundle` Python CLI that builds, installs, and verifies them across Claude Code, Codex, Cursor, Copilot, and Gemini CLI; it self-hosts those packs.

Read [the system model](ARCHITECTURE.md) and [the directory map](docs/architecture/overview.md) before exploring unfamiliar areas.

## Keeping changes minimal

- Scope changes precisely to the request; defer unrelated cleanup.
- Surface assumptions before building, and stop for conflicting requirements.
- Push back when warranted; record disagreement rather than complying silently.
- Prefer the simplest obvious solution; add an option, abstraction, or dependency only when it is needed.
- Add types and docstrings to code you change; validate boundaries the change crosses, trusting internal callers and framework guarantees.
- Inline a single-use operation; extract a helper once a second caller appears.
- Do not silently work around a source-of-truth conflict; state the evidence and the trade-off.

## Source of truth

| Question | Home |
| --- | --- |
| Project scope | `docs/CHARTER.md` |
| Decisions and proposals | `docs/adr/` and `docs/rfc/` |
| Durable feature contract, when one exists | `docs/specs/<feature>/` |
| Current architecture | `docs/architecture/` |
| Product direction and history | `docs/product/` |
| Maintainer and adopter guidance | `docs/guides/` and `guides/` |
| Repeating agent workflow | its `SKILL.md` |
| Mechanically knowable fact | code, schema, manifest, test, or linter |

## How we work

Use the `work-loop` skill for repository changes as its instructions require.
It owns mode selection, required artifacts, planning, verification, review,
recovery, and completion. Commit conventions live in
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

## Commands you'll need

```bash
python3 -m pytest packages/<pkg>/tests/ -q
make lint-ruff
make build-self
SKIP_SAST=1 make build-check
make ci
```

## Check before acting

- Get user confirmation before destructive commands or irreversible operations.
- Grep to verify a function exists before importing it.
- Propose a new top-level directory through the repository's decision process.
- Record a new dependency in the owning package instructions or an ADR before adding it.

## Security and privacy

Never commit personal information or credentials. Use generic placeholders in all
repository artifacts. Follow the security workflow for security-boundary changes.
See [Privacy in CONVENTIONS](docs/CONVENTIONS.md#privacy) for the complete policy.

**Blessed security tools/helpers:**

External quality gate: none declared.

- Credential resolution: `credbroker` (`packages/credbroker/`), using env, OS keyring, then dotfile/vault without crossing a process boundary to an LLM.
- Filesystem confinement: `agentbundle.catalogue_tooling.file_safety` — `validate_confined_directory`, `list_confined_regular_files`, `read_confined_regular_file`, and `sha256_confined_regular_file`; violations raise `UnsafeContentError`.
- Outbound HTTP: no blessed helper is declared.

## Scoped instructions

The nearest `AGENTS.md` above the file being edited applies; read it before acting
in that directory. Scoped instructions exist under `packs/`, `profiles/`,
`packages/`, `guides/`, `web/`, `docs-site/`, and `tools/`; deeper package and
pack instructions take precedence. Additional scoped files are in `packs/core/`,
`packs/frontend-engineering/`, `packages/agentbundle/`, and `packages/credbroker/`.

## When this file is wrong

Report stale or conflicting instructions rather than silently working around them.
Update the owning source, not a generated projection.

> Repository maintainers: see [`AGENTS.local.md`](AGENTS.local.md).
