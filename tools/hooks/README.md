# Lifecycle hooks

Two agent-lifecycle hooks ship in this directory. Runtime: bash plus
`python3` (already required by the artifact linters and
`loop-cohort.py`); neither depends on any one agent tool's runtime.
Wiring lives in the consumer's hook surface (Claude Code's
`.claude/settings.json`, Gemini CLI's config, etc.); this README
documents the contracts and shows an example wiring.

## What's here

### `session-start.sh`

Runs at the open of an agent session. Reads
`docs/knowledge/patterns.jsonl` and prints the entries — optionally
filtered to a path or narrower glob — so the agent starts with
accumulated patterns / gotchas / antipatterns already in context.

Output goes to stdout as a `=== knowledge ===` block. Empty knowledge
file produces no output and exits 0 — wire it unconditionally; the
hook is a no-op until you start accumulating entries.

Usage:

```bash
bash tools/hooks/session-start.sh                                  # every entry
bash tools/hooks/session-start.sh --scope packages/auth/server.ts  # entries whose stored scope covers this path
```

The `--scope` argument is the caller's path or narrower glob; the
hook returns every entry whose **stored** scope covers it. A caller
of `packages/auth/server.ts` gets entries scoped to
`packages/auth/**` plus the repo-wide `*`. An empty or dash-prefixed
value exits 2 with `--scope requires a path or glob value`.

See [`docs/knowledge/README.md`](../../docs/knowledge/README.md) for
the schema and curation conventions.

### `pre-pr.sh`

Runs before a PR opens — the local mirror of CI's artifact-hygiene
checks plus the work-loop's mechanical termination check.

What it runs, in order:

1. `tools/lint-agents-md.sh` — root `AGENTS.md` hygiene, drift-watch
2. `tools/lint-agent-artifacts.sh` — skill/agent/command frontmatter
3. `tools/lint-skill-deps.sh` — manifest dependency resolution
4. `tools/lint-knowledge.sh` — `patterns.jsonl` validation
5. `.claude/skills/work-loop/scripts/loop-cohort.py check` against every
   `docs/specs/*/state.json`, in both `--phase implement` and
   `--phase review` modes

Exits non-zero on the first failure with a one-line reason. If there
are no active `state.json` files, the loop-cohort step is skipped.

These three layers — `loop-cohort.py` (caps) + the four linters
(artifact hygiene) + `pre-pr.sh` (the gate that runs them together) —
make up the project's **enforcement triplet**. Documented in
[`docs/CONVENTIONS.md` § Enforcement](../../docs/CONVENTIONS.md#enforcement-the-triplet).

## Wiring

The hooks are configured at the consumer side. The template does not
ship a committed `.claude/settings.json` (or equivalent for other
tools) — consumers may want to customize differently, and config
files are not portable across agent tools.

### Claude Code

Add to your project-local `.claude/settings.json` (gitignored):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "bash tools/hooks/session-start.sh" }
        ]
      }
    ]
  }
}
```

`pre-pr.sh` is most useful as a manual or git-hook command rather than
an agent-lifecycle hook — Claude Code doesn't fire on `git push`, so
wire it via `.git/hooks/pre-push` if you want it automatic, or run it
by hand before opening a PR:

```bash
bash tools/hooks/pre-pr.sh
```

### Other tools

Gemini CLI, Codex, Kiro, and other agent tools each have their own
hook surfaces. The scripts are bash plus `python3` — wire whatever
event your tool exposes (session-open, pre-commit, etc.) to invoke
them.

## Testing the hooks

Run them directly against the working tree:

```bash
bash tools/hooks/session-start.sh
bash tools/hooks/pre-pr.sh
```

Two dedicated self-tests cover the hook scripts themselves:

- `tools/test-pre-pr.sh` — corrupts each of the five enforcement
  layers in turn (the four linters plus `loop-cohort.py`, in a sandbox
  copy of the repo) and asserts `pre-pr.sh` fails with the right
  label.
- `tools/test-session-start.sh` — exercises `--scope` validation, the
  malformed-line warning, the `KNOWLEDGE_FILE` override, and the
  empty/missing-file silent-exit paths.

The umbrella `tools/test-all.sh` runs every self-test in `tools/`
(both of the above plus `test-loop-cohort.sh`, `test-lint-knowledge.sh`,
`test-lint-agent-artifacts.sh`, `test-bootstrap-targets.sh`). Run it
by hand whenever a linter, hook, or `loop-cohort.py` changes.

**CI parity.** `pre-pr.sh` and CI run the same set of checks in
parallel. CI's `.github/workflows/docs.yml` has a job per
enforcement layer — the four linters, the caps-enforcer self-test,
and a `hooks` job that exercises the aggregator end-to-end (after
seeding a healthy `state.json` so `loop-cohort.py check` actually runs).
Run `tools/test-all.sh` and `tools/hooks/pre-pr.sh` locally before
opening a PR; CI runs the same checks afterward.
