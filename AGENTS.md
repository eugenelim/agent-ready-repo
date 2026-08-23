# AGENTS.md

> **This is the canonical agent context file.** `CLAUDE.md` is a symlink to it.
> Keep repository-wide invariants here; put scoped deltas in the nearest
> `AGENTS.md`.

## Project overview

This monorepo publishes portable agent-context packs—skills, subagents,
commands, hooks, and seed documents—and the `agentbundle` Python CLI that
builds, installs, and verifies them across Claude Code, Codex, Cursor, Copilot,
and Gemini CLI. The repository self-hosts the packs it publishes.

Read [the system model](ARCHITECTURE.md) and
[the ownership map](docs/architecture/overview.md) before exploring an
unfamiliar area.

## Documentation

| Need | Canonical source | Scope |
| --- | --- | --- |
| Project scope | [`docs/CHARTER.md`](docs/CHARTER.md) | Repository |
| Architecture and ownership | [`ARCHITECTURE.md`](ARCHITECTURE.md), [`docs/architecture/`](docs/architecture/) | Repository and subsystem |
| Decisions and proposals | [`docs/adr/`](docs/adr/), [`docs/rfc/`](docs/rfc/) | Repository |
| Durable feature contracts | [`docs/specs/<feature>/`](docs/specs/) | Feature, when present |
| Product direction and history | [`docs/product/`](docs/product/) | Repository |
| Maintainer and adopter guidance | [`docs/guides/`](docs/guides/), [`guides/`](guides/) | Internal and public |
| Repeating agent workflow | its `SKILL.md` | Workflow |
| Mechanically knowable fact | code, schema, manifest, test, or linter | Owning component |

## Development workflow

Use the `work-loop` skill for repository changes. It owns mode selection,
required artifacts, planning, verification, review, recovery, and completion.

- Scope changes precisely to the request and surface assumptions or conflicts
  before building. Record disagreement rather than complying silently.
- Get confirmation before destructive or irreversible operations.
- Propose a new top-level directory through the repository decision process.
- Keep unrelated discoveries out of the current change unless the accepted
  work-loop contract admits them.

## Build and test commands

```bash
make bootstrap-sites   # one-time npm deps for make test and site-link-check
python3 -m pytest packages/<pkg>/tests/ -q
make lint-ruff
make build-self
SKIP_SAST=1 make build-check
make ci
```

## Coding conventions

Commit conventions and the full repository rules live in
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

- Prefer the simplest obvious solution; add an option, abstraction, or
  dependency only when it is needed.
- Add types and docstrings to code you change. Validate crossed boundaries,
  trusting internal callers and framework guarantees.
- Inline a single-use operation; extract a helper when a second caller appears.
- Grep to verify a function exists before importing it.
- Record a new dependency in the owning package instructions or an ADR before
  adding it.
- Do not silently resolve a conflict between documented guidance and code.
  State the evidence and trade-off, then update the owning source—not a
  generated projection.

## Security considerations

Never commit personal information or credentials. Use generic placeholders in
repository artifacts. Follow the security workflow for security-boundary
changes and [the privacy convention](docs/CONVENTIONS.md#privacy).

**Blessed security tools/helpers:**

External quality gate: none declared.

- Credential resolution: `credbroker` (`packages/credbroker/`), using env, OS
  keyring, then dotfile/vault without crossing a process boundary to an LLM.
- Filesystem confinement: `agentbundle.catalogue_tooling.file_safety`—
  `validate_confined_directory`, `list_confined_regular_files`,
  `read_confined_regular_file`, and `sha256_confined_regular_file`; violations
  raise `UnsafeContentError`.
- Outbound HTTP: no blessed helper is declared.

## Scoped instructions

The nearest `AGENTS.md` above a changed file applies. Scoped guidance exists
under `packs/`, `profiles/`, `packages/`, `guides/`, `web/`, `docs-site/`, and
`tools/`, with deeper files under `packs/core/`, `packs/frontend-engineering/`,
`packages/agentbundle/`, and `packages/credbroker/`.

Read the applicable scoped file before acting. Report stale or conflicting
instructions instead of working around them. Repository maintainers should also
read [`AGENTS.local.md`](AGENTS.local.md).
