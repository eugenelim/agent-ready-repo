# Lifecycle hooks

Two agent-lifecycle hooks ship in this directory. Runtime: `python` ≥
3.11 (the hooks parse TOML via stdlib `tomllib`); no other
dependencies. The hooks are stdlib-only and run on native Windows,
macOS, and Linux — invoke via `python` (not `python3`) so the same
command works across platforms (`python3.exe` is rarely on Windows
PATH; `python.exe` and the `py` launcher are). Wiring lives in the
consumer's hook surface (Claude Code's `.claude/settings.json`, Gemini
CLI's config, etc.); this README documents the contracts and shows an
example wiring.

## What's here

### `session-start.py`

Runs at the open of an agent session. Reads
`docs/knowledge/patterns.jsonl` and prints the entries — optionally
filtered to a path or narrower glob — so the agent starts with
accumulated patterns / gotchas / antipatterns already in context.

Output goes to stdout as a `=== knowledge ===` block. Empty knowledge
file produces no output and exits 0 — wire it unconditionally; the
hook is a no-op until you start accumulating entries.

Usage:

```bash
python tools/hooks/session-start.py                                  # every entry
python tools/hooks/session-start.py --scope packages/auth/server.ts  # entries whose stored scope covers this path
```

The `--scope` argument is the caller's path or narrower glob; the
hook returns every entry whose **stored** scope covers it. A caller
of `packages/auth/server.ts` gets entries scoped to
`packages/auth/**` plus the repo-wide `*`. An empty or dash-prefixed
value exits 2 with `--scope requires a path or glob value`.

See [`docs/knowledge/README.md`](../../docs/knowledge/README.md) for
the schema and curation conventions.

### `pre-pr.py`

Runs before a PR opens — the local mirror of CI's artifact-hygiene
checks plus the work-loop's mechanical termination check.

What it runs, in order:

1. `tools/lint-agents-md.py` — root `AGENTS.md` hygiene, drift-watch
2. `tools/lint-agent-artifacts.py` — skill/agent/command frontmatter
3. `tools/lint-skill-deps.py` — manifest dependency resolution
4. `tools/lint-knowledge.py` — `patterns.jsonl` validation
5. `tools/lint-build.py` — build-pipeline hygiene
6. `.claude/skills/work-loop/scripts/loop-cohort.py check <spec-dir>`
   against every `docs/specs/*/` that owns a `state.json`, in both
   `--phase implement` and `--phase review` modes

Exits non-zero on the first failure with a one-line reason. If there
are no active `state.json` files, the loop-cohort step is skipped.

These three layers — `loop-cohort.py` (caps) + the five linters
(artifact hygiene) + `pre-pr.py` (the gate that runs them together) —
make up the project's **enforcement triplet**. Documented in
[`docs/CONVENTIONS.md` § Enforcement](../../docs/CONVENTIONS.md#enforcement-the-triplet).

## Runtime

The hooks and the five sibling linters under `tools/lint-*.py`
require **Python ≥ 3.11** (for stdlib `tomllib`). The repo's
`packages/agentbundle/pyproject.toml` already pins this floor.
Invoke as `python tools/hooks/<name>.py` — works on native Windows
out of the box; on macOS/Linux ensure `python` resolves to a 3.11+
interpreter (or substitute `python3.11` etc.). The dev/CI bash
test-runners under `tools/test-*.sh` invoke `python3` instead — they
target POSIX, where `python3` is the conventional 3.x name; the
adopter-facing wiring example uses bare `python` because it needs to
work on Windows + POSIX with a single string.

**`CLAUDE.md` shape on Windows.** `tools/lint-agents-md.py` check #2
accepts two shapes equivalently: a real symlink to `AGENTS.md` (Unix,
or Windows with Developer Mode) **or** a regular file whose entire
content is the literal string `AGENTS.md` (Windows without Developer
Mode, where `git config core.symlinks false` is the default — git
materialises the symlink as a regular file containing the link
target). Either shape passes the lint; anything else fails as a
drift hazard.

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
          { "type": "command", "command": "python tools/hooks/session-start.py" }
        ]
      }
    ]
  }
}
```

`pre-pr.py` is most useful as a manual or git-hook command rather than
an agent-lifecycle hook — Claude Code doesn't fire on `git push`, so
wire it via `.git/hooks/pre-push` if you want it automatic, or run it
by hand before opening a PR:

```bash
python tools/hooks/pre-pr.py
```

### Other tools

Gemini CLI, Codex, Kiro, and other agent tools each have their own
hook surfaces. The scripts are pure-stdlib Python — wire whatever
event your tool exposes (session-open, pre-commit, etc.) to invoke
them with `python tools/hooks/<name>.py`.

## Testing the hooks

Run them directly against the working tree:

```bash
python tools/hooks/session-start.py
python tools/hooks/pre-pr.py
```

Two pytest smoke suites under `packages/agentbundle/tests/hooks/`
are the canonical parity net:

- `test_session_start_py.py` — exercises `--scope` validation, the
  malformed-line warning, the `KNOWLEDGE_FILE` override, and the
  empty/missing-file silent-exit paths.
- `test_pre_pr_py.py` — corrupts each of the five enforcement layers
  (four linters plus `loop-cohort.py`) in a sandbox copy of the repo
  and asserts `pre-pr.py` fails with the right label.

Two bash self-tests still ship for parity with the pre-Phase-3
contract — they invoke the Python hooks rather than the bash
versions, but their sandbox setup remains bash:

- `tools/test-pre-pr.sh` — the bash-runner equivalent of
  `test_pre_pr_py.py`.
- `tools/test-session-start.sh` — the bash-runner equivalent of
  `test_session_start_py.py`.

The umbrella `tools/test-all.sh` runs every self-test in `tools/`.
Run it by hand whenever a linter, hook, or `loop-cohort.py` changes.

**CI parity.** `pre-pr.py` and CI run the same set of checks in
parallel. CI's `.github/workflows/docs.yml` has a job per
enforcement layer — the five linters, the caps-enforcer self-test,
and a `hooks` job that exercises the aggregator end-to-end (after
seeding a healthy `state.json` so `loop-cohort.py check` actually
runs). Run `tools/test-all.sh` and `python tools/hooks/pre-pr.py`
locally before opening a PR; CI runs the same checks afterward.
