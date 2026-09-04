# AGENTS.md

> **This is the canonical agent context file.** `CLAUDE.md` is a symlink to it.
> Keep repository-wide invariants here; put scoped deltas in the nearest
> `AGENTS.md`.

## Project overview

This monorepo publishes portable agent-context packs—skills, subagents,
commands, hooks, and seed documents—and the `agentbundle` Python CLI that
builds, installs, and verifies them across Claude Code, Codex, Cursor, Copilot,
and Gemini CLI. The repository self-hosts the packs it publishes.

## Rule lookups

Before your first user-facing response or unrelated tool call, silently read [`AGENT_RULES.md`](AGENT_RULES.md), then every `always` rule and every conditional rule there that matches the work. For work under `docs/`, also read the scoped [`docs/AGENTS.md`](docs/AGENTS.md). Read both lookup files with one bounded, repository-confined operation that rejects links, reparse points, non-regular files, multiple links, oversized files, and identity changes while opening. If the host loaded a file before agent control, do not claim this check covered the host load.

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
git push -u origin HEAD && B="$(git branch --show-current)"  # dispatch precondition
gh workflow run build-check.yml --ref "$B"  # chain + bandit/pip-audit/semgrep/npm
gh workflow run test-corpus.yml --ref "$B"  # make test
gh workflow run test-roster.yml --ref "$B"  # roster suite, parallel
gh workflow run pages.yml       --ref "$B"  # site and browser build
# ^ DISPATCH these: verdict-only, so remote. Partial evidence, never a required check.
make build-self && make bootstrap-sites  # LOCAL: these WRITE files you then read
```

## Coding conventions

Commit conventions and the full repository rules live in
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

- Cut before adding. After reading the code a change touches, take the first
  sufficient option and stop:
  1. Skip an addition that is not genuinely needed and say so once.
  2. Make one bounded search for an adequate repository solution; reuse a hit
     or move on after a decisive empty result.
  3. Use the standard library when it satisfies the outcome.
  4. Use a native platform capability when it satisfies the outcome.
  5. Use an already-installed dependency when it satisfies the outcome. An
     import missing from the owning manifest is a new dependency.
  6. Use one obvious line when it is a complete, maintainable solution.
  7. Otherwise make the minimum correct change in the fewest statements and
     files that preserve ownership and tests.
- Prefer obvious code over merely short code. The bounded discovery check does
  not replace contradictory-evidence handling, freshness checks, required
  gates, or correctness review.
- Never cut trust-boundary validation, data-loss-preventing error handling,
  security or privacy controls, accessibility, accepted requirements, required
  tests/migrations/documentation/human approval, or non-waivable policy and
  platform restrictions.
- Remove claims that do not affect the accepted outcome. Ground a necessary
  assertion about a named repository target with one bounded read or search;
  otherwise label it as an assumption or a discovery condition.
- Lead with the outcome, omit routine tool narration, and end completion
  receipts with changed state, verification, and remaining work. Continue any
  interactive updates required by the host.
- Add types and docstrings to code you change. Validate crossed boundaries,
  trusting internal callers and framework guarantees.
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
