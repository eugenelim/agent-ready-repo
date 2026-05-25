# Trio — windows-hooks-phase3 (Option B1)

Work-loop PLAN artifact for one focused PR. Not a spec — Phase 3 is a
focused port. Updated post-reviewer-iteration-1: behaviour matrices for
the two riskier linters, fixture-flip-scope clarified, the third hook
test runner pinned, Phase-4 Windows-pre-pr ceiling acknowledged.

## The trio (revised)

**Files I'll touch.**
Rewrite as pure-stdlib Python the seven bash scripts that today form the
pre-PR and session-start runtime — `packs/core/.apm/hooks/{session-start,pre-pr}.sh`
and `tools/lint-{agents-md,agent-artifacts,skill-deps,knowledge,build}.sh`;
add pytest smoke tests under `packages/agentbundle/tests/hooks/` for both
hooks; flip the *real-hook* references in the three bundler tests that
name the production hook filename (`test_scope_rails.py` only — verified
via grep; the `baz.sh` / `hook.sh` / synthetic-`pre-pr.sh` literals in
`test_adapter_claude_code.py`, `test_self_host_check.py`, and friends
**stay** as `.sh` because they exercise the `.{sh,py}` *contract*
pattern, not the real hook); flip the `bash …sh` invocations to
`python …py` in seven `tools/test-*.sh` runners (counted: `test-pre-pr.sh`,
`test-session-start.sh`, `test-lint-build.sh`, `test-lint-knowledge.sh`,
`test-lint-skill-deps.sh`, `test-lint-agent-artifacts.sh`, and the
*pack-level* `packages/agentbundle/tests/hooks/test_session_start.sh`);
update `tools/hooks/README.md` example wiring to
`python tools/hooks/session-start.py` and add a one-line Python ≥ 3.11
note under § Runtime there (not in AGENTS.md, which is template
placeholder territory); delete every `.sh` sibling once its `.py`
lands. `tools/hooks/` mirrors `packs/core/.apm/hooks/` (self-host
projection target) so it gets the same delete+add.

**How I'll know it's done.**
Every existing `tools/test-*.sh` runner (six in `tools/` plus the
pack-level `tests/hooks/test_session_start.sh`) is green on macOS *and
on Linux CI* (`.github/workflows/docs.yml`) after pointing at the `.py`
files — the runners contain the substring-assertion oracle that
mechanically diffs bash-vs-Python output. New pytest smoke tests under
`packages/agentbundle/tests/hooks/` invoke the ported hooks as
subprocesses with fixture env and assert exit code + the
`=== knowledge ===` / `=== adapt-to-project: …` / `pre-pr: ✓ …` /
`pre-pr: ✖ … failed` stdout shapes Claude Code expects; the pytest
file MUST mirror all five corruption cases the bash runner exercises
(`agents-md-fail`, `agent-artifact-fail`, `skill-deps-fail`,
`knowledge-fail`, `check-done-fail`) so the parity net survives even
if the bash runner stops being run. The bundler's `pytest -q` is green
with fixture filenames unchanged (the synthetic `.sh` literals test
the contract pattern, not the real hook). `python tools/hooks/pre-pr.py`
on a clean macOS checkout emits five `✓` lines and exits 0.

**What I'm not changing.**
The `--no-symlink` / path-jail / CLI normalisation work (Phase 2);
skill prose, `new-adr`/`new-rfc` sed rewrites, **and the
`conventions-check` symlink relaxation** (Phase 4 — see *Known
Windows-pre-pr ceiling* below); `.gitattributes`, the adopter Windows
guide, README touches (Phase 1, 5); CI matrix additions on
`windows-latest`; the bundler's hook-wiring projection (core remains
`allowed-scopes = ["repo"]` and has no `.apm/hook-wiring/*.toml` —
adopters wire `.claude/settings.json` manually per the README example);
the seven bash test-runners' *bodies* (only the LINTER / HOOK
invocation line inside each gets edited — the bash sandbox setup,
`cp -P`, `git ls-files -z` pipe, and corruption-injection eval stay
bash; rewriting these into pytest is a separate PR); the bundler
fixture *synthetic* `.sh` literals; **`tools/test-all.py`** (the
umbrella that dispatches to bash *runners*, not hooks/linters — the
parity rule "runner bodies stay bash; only the LINTER/HOOK invocation
line changes" doesn't apply because its targets are themselves bash
runners, so the umbrella's body is unchanged by this phase — it was
ported from `.sh` to `.py` separately in PR #111); and the
`docs/specs/windows-hooks-phase3/TRIO.md` scratch file itself (PLAN
artifact for this PR, not a spec).

## Windows-pre-pr — fully unblocked in this PR

Originally Phase 3 deferred `lint-agents-md` check #2 to Phase 4
(`conventions-check` symlink relaxation). User direction reversed that:
check #2 now accepts the Windows-materialised-symlink shape (a regular
file whose entire content is the literal string `AGENTS.md` — the
default `git config core.symlinks false` behaviour on Windows without
Developer Mode). Both shapes pass: real symlink **or** content equal
to `AGENTS.md`. Any other regular-file content still fails as a
drift hazard. Acceptance is therefore "**pre-pr is green on macOS,
Linux, and native Windows** (Developer Mode or not)" — no remaining
ceiling.

**Audited Windows-hostile surfaces** (only one is hostile; the rest are
portable):

- `Path.rglob` exclusions, `re.search` patterns, `git check-ignore`,
  `git ls-tree -d`, `git merge-base`, `Path.stat().st_mtime`,
  `subprocess.run` list-form, `tomllib.loads`, `json.loads`,
  `argparse` — all work on native Windows without remediation.
- `Path("CLAUDE.md").is_symlink()` returns `False` on a Windows
  default checkout (no Developer Mode) — **this is the single
  hostile surface**, hard-failing `lint-agents-md` check #2 as
  documented above.

## Declined-pattern register (revised)

- **`tools/hooks/_shared.py` helper for `REPO_ROOT` + stderr helpers** — declining; two-or-three callers don't justify a module, and `tools/lint-*.py` live in a different directory than `tools/hooks/`, so the helper would need a third location. Three-times rule: extract once a third caller in `tools/hooks/` actually appears. *(Note: each port duplicates a ~5-line `_repo_root()` and ~5-line `_err/_ok/_warn` helper. Accepting the duplication.)*
- **OS-detection in the hook body to pick `python` vs `python3`** — declining; the invoker (`.claude/settings.json` `command` string, or `pre-pr.py`'s own subprocess spawn) names the interpreter. The hook body uses `sys.executable` to spawn its own children (see matrix row for `pre-pr.py` linter dispatch). No `platform.system()` in any hook body.
- **`--dry-run` flag on `pre-pr.py`** — declining; no second caller exists. Bash version doesn't have it; parity is the bar.
- **`tools/hooks/_compat.py` exit-code constants** — declining; three literal integers are clearer than a constants module.
- **Porting `tools/test-*.sh` runner *bodies* to pytest** — declining; out of scope, dev/CI infrastructure rather than adopter runtime, big diff. Only the invocation lines (`bash …sh` → `python …py`) inside the runners change.
- **Consolidating five linters into one `tools/lint.py` with subcommands** — declining; would orphan seven `tools/test-lint-*.sh` runners' label-string assertions, break the `pre-pr.sh` aggregator's per-step labelling, and contradict `tools/hooks/README.md`'s per-linter doc. That's a refactor needing an RFC, not a port.
- **`pyproject.toml` at repo root** — declining; one already lives at `packages/agentbundle/pyproject.toml`; a second top-level surface would trip `lint-build`'s new-top-level-directory audit without buying anything.
- **`tomli-w` / `click` / `rich`** — declining; stdlib-only is a hard constraint of the prompt and matches `lint-build`'s stdlib-import audit.
- **Pre-emptive removal of `lint-agents-md` check #2 (CLAUDE.md symlink)** — declining; that's Phase-4 (`conventions-check` symlink relaxation) scope. See *Known Windows-pre-pr ceiling*.
- **Pre-emptive `os.path.normpath` / `Path(..).resolve()` calls inside ports to "be safe" on Windows paths** — declining; the bash sources don't normalise, parity-pinning is the bar, and `Path` already handles separators. Add normalisation only if a test actually fails for the right reason.

## Verification mode per task (split per reviewer concern 13)

- **#2 session-start.py, #3 pre-pr.py, #7 lint-agents-md.py, #8 lint-build.py — TDD-adjacent / parity-pinned.** The bash here is load-bearing (find walks, stat fallbacks, git plumbing, control flow). Construction tests = new pytest scaffolds *plus* the existing `tools/test-*.sh` runners as a second oracle.
- **#4 lint-knowledge.py, #5 lint-skill-deps.py, #6 lint-agent-artifacts.py — goal-based check.** The bash is a thin wrapper around an existing python heredoc; the port is *lifting the heredoc body out* of the wrapper. The python *body* is unchanged. Acceptance: existing `tools/test-lint-*.sh` runner stays green after the invocation flip. No new pytest required (would assert what the existing runner already asserts).
- **#9 pytest smoke tests for hooks — TDD.**
- **#10 — DROPPED.** Originally proposed a "settings.json shape regression test" with a path I'd invented. Reframed: the prompt's intent ("emitted JSON has the right shape per platform") doesn't apply because the bundler doesn't emit settings.json for the core pack. The platform-agnostic-wiring claim is instead asserted by **a one-line grep test inside `test_pre_pr_py.py`** that reads `tools/hooks/README.md` and confirms the example wiring uses `python` (not `python3`, not `bash`, no `os.name` branching). No separate file.
- **#11 fixture-flip + .sh delete — goal-based.** `pytest -q packages/agentbundle/` green; `git grep -nE '\.apm/hooks/(session-start|pre-pr)\.sh|tools/hooks/(session-start|pre-pr)\.sh|tools/lint-[a-z-]+\.sh' -- ':!docs/specs/windows-hooks-phase3/'` returns no production references.
- **#12 README + AGENTS.md docs — goal-based.** `python tools/lint-agents-md.py` green; `tools/hooks/README.md` grep matches `python tools/hooks/session-start.py` and `Python ≥ 3.11`.
- **#13 GATES + REVIEW — goal-based for gates; adversarial + security for review (see below).**

## Post-EXECUTE reviewer set (per reviewer concern 14)

- **adversarial-reviewer** — always.
- **security-reviewer** — yes, the diff crosses two boundaries: (a) deserialization of user-controlled JSON/TOML from env-var-named paths (`KNOWLEDGE_FILE`, `ADAPT_REPO_MARKER`, `ADAPT_USER_MARKER`); (b) `subprocess.run` dispatch with file paths in argv. The bash version had the same trust model, but stripping the bash layer is the right moment to confirm the Python port preserves it deliberately. The brief: "trust model unchanged from bash; confirm list-form subprocess everywhere, no shell=True, no string-interpolation into argv; env-var path-traversal is intentional (dev-only)."
- **quality-engineer** — optional per the work-loop's "diff-warranted" rule. The diff is mostly transliteration; observability/reliability/maintainability concerns are low. Will skip unless adversarial or security surface a quality smell.

## Construction-test sketch — expanded for both hooks

The session-start sketch in iteration 0 had 5 cases. The pre-pr sketch
had 2 — expanded to 5 below mirroring `tools/test-pre-pr.sh`. Both
sketches use `sys.executable` (not literal `python`) to ensure the
parent's Python interpreter is what runs the child hook, matching the
matrix row for `pre-pr.py`'s linter dispatch.

```python
# tests/hooks/test_session_start_py.py — TDD scaffold (#2).
import os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]  # repo root
HOOK = REPO_ROOT / "packs" / "core" / ".apm" / "hooks" / "session-start.py"

def _run(env_overrides, *args):
    env = {**os.environ, **env_overrides}
    return subprocess.run(
        [sys.executable, str(HOOK), *args],
        env=env, capture_output=True, text=True,
    )

def test_session_start_emits_knowledge_block(tmp_path):
    kb = tmp_path / "knowledge.jsonl"
    kb.write_text(
        '{"id":"K-0001","kind":"pattern","scope":"*","title":"T","body":"B","source":"S"}\n'
    )
    result = _run({"KNOWLEDGE_FILE": str(kb),
                   "ADAPT_REPO_MARKER": "/dev/null",
                   "ADAPT_USER_MARKER": "/dev/null"})
    assert result.returncode == 0
    assert "=== knowledge ===" in result.stdout
    assert "[K-0001]" in result.stdout
    assert result.stderr == ""

def test_session_start_malformed_warns_to_stderr(tmp_path):
    kb = tmp_path / "knowledge.jsonl"; kb.write_text("{not json\n")
    result = _run({"KNOWLEDGE_FILE": str(kb),
                   "ADAPT_REPO_MARKER": "/dev/null",
                   "ADAPT_USER_MARKER": "/dev/null"})
    assert result.returncode == 0
    assert "skipped 1 malformed" in result.stderr

def test_session_start_adapt_nudge_when_marker_has_packs(tmp_path):
    marker = tmp_path / "marker.toml"
    marker.write_text('[[packs-installed]]\nname = "core"\n')
    kb = tmp_path / "kb.jsonl"; kb.touch()
    result = _run({"KNOWLEDGE_FILE": str(kb),
                   "ADAPT_REPO_MARKER": str(marker),
                   "ADAPT_USER_MARKER": "/dev/null"})
    assert result.returncode == 0
    assert "=== adapt-to-project:" in result.stdout
    assert "core" in result.stdout

def test_session_start_scope_arg_requires_value():
    result = _run({"KNOWLEDGE_FILE": "/dev/null",
                   "ADAPT_REPO_MARKER": "/dev/null",
                   "ADAPT_USER_MARKER": "/dev/null"}, "--scope")
    assert result.returncode == 2
    assert "--scope requires a path or glob value" in result.stderr

def test_session_start_help_describes_scope_arg():
    result = _run({"KNOWLEDGE_FILE": "/dev/null",
                   "ADAPT_REPO_MARKER": "/dev/null",
                   "ADAPT_USER_MARKER": "/dev/null"}, "--help")
    assert result.returncode == 0
    assert "--scope" in result.stdout

def test_session_start_scope_coverage_glob(tmp_path):
    kb = tmp_path / "kb.jsonl"
    kb.write_text(
        '{"id":"K-0001","kind":"pattern","scope":"packages/auth/**","title":"T1","body":"B1","source":"S1"}\n'
        '{"id":"K-0002","kind":"gotcha","scope":"src/other/x.ts","title":"T2","body":"B2","source":"S2"}\n'
    )
    result = _run({"KNOWLEDGE_FILE": str(kb),
                   "ADAPT_REPO_MARKER": "/dev/null",
                   "ADAPT_USER_MARKER": "/dev/null"},
                  "--scope", "packages/auth/server.ts")
    assert "K-0001" in result.stdout
    assert "K-0002" not in result.stdout

# tests/hooks/test_pre_pr_py.py — TDD scaffold (#3). Mirrors the 5
# corruption cases the existing tools/test-pre-pr.sh exercises so the
# pytest layer is self-sufficient.
def test_pre_pr_readme_wiring_uses_python_not_bash():
    """Cross-platform invocation guarantee (replaces dropped task #10).
    Asserts both hook names, both directions — addresses iteration-2 N7.
    """
    text = (REPO_ROOT / "tools" / "hooks" / "README.md").read_text()
    for name in ("session-start", "pre-pr"):
        assert f"python tools/hooks/{name}.py" in text
        assert f"bash tools/hooks/{name}.sh" not in text

def test_pre_pr_clean_repo_passes():
    result = subprocess.run([sys.executable,
        str(REPO_ROOT / "tools" / "hooks" / "pre-pr.py")],
        cwd=REPO_ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    for label in ["agents-md hygiene", "agent-artifact lint",
                  "skill-deps lint", "knowledge lint", "build lint"]:
        assert f"pre-pr: ✓ {label}" in result.stdout
    assert "pre-pr: all checks passed" in result.stdout

# _seed_sandbox helper used by the corruption-case tests below.
# NUL-delimited list of git-tracked files (matches the bash runner's
# `git ls-files -z` safety net — filenames with spaces/newlines are
# preserved). `git init` inside `dst` so check-ignore has a real .git
# to read against. Returns the sandbox path.
import shutil
def _seed_sandbox(dst: Path) -> Path:
    raw = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO_ROOT,
        capture_output=True, check=True,
    ).stdout
    files = [p.decode() for p in raw.split(b"\0") if p]
    for rel in files:
        src = REPO_ROOT / rel
        if not src.exists():  # symlink to a removed target
            continue
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        # copy2 with follow_symlinks=False preserves the CLAUDE.md→AGENTS.md
        # symlink so lint-agents-md check #2 stays satisfied in the sandbox.
        shutil.copy2(src, out, follow_symlinks=False)
    subprocess.run(["git", "init", "-q"], cwd=dst, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "add", "-A"], cwd=dst, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-q", "-m", "baseline"], cwd=dst, check=True)
    return dst

# Plus four more corruption-case tests mirroring test-pre-pr.sh's
# agents-md-fail / agent-artifact-fail / skill-deps-fail / knowledge-fail /
# check-done-fail — each seeded via _seed_sandbox(tmp_path / "repo"),
# then a one-shot mutation (rm AGENTS.md / sed-strip a model: line /
# break a SKILL dep path / plant {not json / plant a pending-plan
# state.json), then subprocess.run pre-pr.py with cwd=sandbox and
# assert the matching `pre-pr: ✖ <label> failed` substring.
```

## Per-hook behaviour matrix — `session-start.sh` → `session-start.py`

| `session-start.sh` branch (line) | `session-start.py` |
|---|---|
| `set -uo pipefail` (22) | `# defaults: argparse handles unknown args; explicit exit codes` |
| `git rev-parse --show-toplevel \|\| pwd` (24) | `_repo_root()` — `subprocess.run(["git","rev-parse","--show-toplevel"], capture_output=True, text=True); fallback Path.cwd()` |
| `KNOWLEDGE_FILE` env (25) | `os.environ.get("KNOWLEDGE_FILE", str(REPO_ROOT / "docs/knowledge/patterns.jsonl"))` |
| `--scope` parse (28-37) | `argparse` with `--scope` required-value flag; on empty/dash-prefix → `sys.exit(2)` with `"--scope requires a path or glob value"` to stderr |
| `--help`/`-h` → `sed -n '2,22p' "$0"` (38-41) | Hard-coded usage string ported from the bash header comment (lines 2-21). NOT `__doc__` — that's the module docstring, easy to drift. |
| Unknown arg → exit 2 (42-45) | `argparse` raises; printed shape: `session-start: unknown argument <arg>` to stderr |
| `[[ -f $KF && -s $KF ]]` (50) | `path.exists() and path.stat().st_size` |
| Inline Python heredoc, knowledge block (52-106) | Lifted verbatim as `_emit_knowledge(path, scope_filter)` function. Stdout block headers (`=== knowledge ===`) and entry shape (`[K-NNNN] (kind, scope) title\n    body\n    — source`) unchanged. |
| Malformed JSONL stderr (84-89) | `print(f"session-start: skipped {n} malformed line(s) — run tools/lint-knowledge.sh", file=sys.stderr)` — exact wording |
| `ADAPT_REPO_MARKER`, `ADAPT_USER_MARKER` env (121-122) | `os.environ.get(..., default)` |
| Inline Python heredoc, adapt nudge (124-162) | Lifted as `_emit_adapt_nudge(repo_marker, user_marker)`. Stdout shape `=== adapt-to-project: N pack(s) pending adaptation across S scope(s): names — run /adapt-to-project ===` unchanged. |
| TOML parse failure → silent skip (135-138) | `try: tomllib.loads(...) except Exception: return []` |
| Entry-point guard | Body lives behind `if __name__ == "__main__":` |
| stdin / argv | Reads `sys.argv` only via argparse; no stdin reads (Claude Code session-start hooks have no transcript on stdin per the project's prior wiring) |

## Per-hook behaviour matrix — `pre-pr.sh` → `pre-pr.py`

| `pre-pr.sh` branch (line) | `pre-pr.py` |
|---|---|
| `REPO_ROOT="$(git rev-parse ...)"` + `cd "$REPO_ROOT"` (22-23) | `_repo_root()` helper; `os.chdir(repo_root)` **inside `if __name__ == "__main__":`** — module-level chdir would leak when imported by future tests. |
| `run "label" cmd…` helper (25-33) | `def _run(label, argv) -> None: result = subprocess.run(argv, check=False); if rc != 0: print(f"pre-pr: ✖ {label} failed", file=sys.stderr); sys.exit(1); print(f"pre-pr: ✓ {label}")` |
| `run "agents-md hygiene" bash tools/lint-agents-md.sh` (35) | `_run("agents-md hygiene", [sys.executable, "tools/lint-agents-md.py"])` — **`sys.executable` not literal `"python"`** so child interpreter = parent |
| (×5 linter shell-outs) (35-39) | (×5 list-form subprocess.run with `sys.executable`) |
| `shopt -s nullglob; state_files=(...)` (41-43) | `state_files = sorted(Path("docs/specs").glob("*/state.json"))` — `sorted` matches bash glob expansion order |
| Empty-state branch (45-46) | `if not state_files: print("pre-pr: (no active state.json — skipping check-done)")` — exact wording |
| `for state in ... for phase in implement review` (48-55) | `for state in state_files: for phase in ("implement", "review"):` |
| `python3 .claude/skills/work-loop/scripts/check-done.py "$state" --phase "$phase"` (50) | `subprocess.run([sys.executable, str(check_done_path), str(state), "--phase", phase], check=False)` |
| `echo "pre-pr: all checks passed"` (59) | `print("pre-pr: all checks passed")` |
| Exit code | First `_run` failure → `sys.exit(1)`; otherwise `sys.exit(0)` |

## Per-linter behaviour matrix — `lint-agents-md.sh` → `lint-agents-md.py`

Added per reviewer Blocker 5.

| `lint-agents-md.sh` (line) | `lint-agents-md.py` |
|---|---|
| `set -euo pipefail` (16) | Default Python error behaviour; explicit `sys.exit(1)` on `fail` count |
| Constants `MAX_ROOT_LINES=250 MAX_SUB_LINES=150 STALE_DAYS=180` (18-20) | Module-level constants, same values |
| `REPO_ROOT` + `cd` (22-23) | `_repo_root()` + `os.chdir(repo_root)` inside `__main__` guard |
| `note() warn() ok()` helpers (26-28) | `def _note(msg)`, `_warn(msg)`, `_ok(msg)` — `_note` increments a closure-or-global `fail` counter |
| Check #1: `[[ -f AGENTS.md ]]` (31-35) | `Path("AGENTS.md").is_file()` |
| Check #2: `[[ -L CLAUDE.md ]]` + `readlink CLAUDE.md` (37-49) | `Path("CLAUDE.md").is_symlink()` + comparison: `os.readlink(claude_md) == "AGENTS.md"`. **Relaxed in this PR** to also accept a regular file whose content is exactly `"AGENTS.md"` (the Windows-materialised-symlink shape). |
| Check #3: `wc -l < AGENTS.md` (52-58) | `len(Path("AGENTS.md").read_text().splitlines())` (or `.read_bytes().count(b"\n")` — both match `wc -l` parity for files ending in newline) |
| Check #4: `find . -name AGENTS.md ...` (62-74) | `Path(".").rglob("AGENTS.md")` filtered to exclude `.git/`, `node_modules/`, plus the special-case bump for `./packs/core/seeds/AGENTS.md` → `MAX_ROOT_LINES` |
| Check #5: link regex `grep -oE '\]\([^)]+\)'` + `sed -E ...` + `grep -vE '^https?:'` (78-93) | `re.findall(r"\]\(([^)]+)\)", text)`; filter scheme-prefixed and anchor-only; resolve `dir / target` and check `Path.exists()` |
| Check #6: `docs/CHARTER.md` exists (95-100) | `Path("docs/CHARTER.md").is_file()` |
| Check #7: no `docs/constitution/` (103-107) | `not Path("docs/constitution").is_dir()` |
| Check #8: Diátaxis dirs (110-119) | Loop `("tutorials","how-to","reference","explanation")` over `Path(f"docs/guides/{d}").is_dir()` |
| Check #9: stale-doc warn — `stat -c %Y \|\| stat -f %m \|\| now_epoch` (130-138) | `Path(f).stat().st_mtime` (cross-platform; supersedes both stat invocations) — int-cast to seconds-since-epoch, age = `(now - mtime) // 86400` |
| Check #10: `drift_check` helper (141-204) | `def _drift_check(pattern, canonical, forbidden_files)` — `re.search(pattern, text)` on canonical (if non-empty); same on each forbidden, with the inverted assertion. **Three explicit `_drift_check` invocations enumerated below** + the vendor-token grep loop (lines 188-193) + the gitignore-probe loop (lines 197-204; uses `git check-ignore --quiet` via subprocess). |
| Check #10a: drift_check #1 (162-165) | pattern=`r'"max_iterations":\s*[0-9]+'`; canonical=`".claude/skills/work-loop/assets/state.json"`; forbidden=`[".claude/skills/work-loop/SKILL.md", "AGENTS.md", "docs/CONVENTIONS.md"]` |
| Check #10b: drift_check #2 (173-176) | pattern=`r'(hard )?cap of (five\|5) (in-session )?iterations?'`; canonical=`""` (empty = no canonical-home check); forbidden same as #10a |
| Check #10c: drift_check #3 (181-184) | pattern=`r'\*\*Goal-based check\*\*'`; canonical=`".claude/skills/work-loop/SKILL.md"`; forbidden=`["AGENTS.md", "docs/CONVENTIONS.md"]` |
| Check #10d: vendor-token loop (188-193) | For each f in `["AGENTS.md","docs/CONVENTIONS.md","docs/CHARTER.md","docs/APPROACH.md"]`: `re.search(r'\bultrathink\b\|Plan Mode \(Shift\+Tab', text)` → note |
| Check #10e: gitignore probes (197-204) | For each probe in `["docs/specs/example/state.json","docs/specs/example/notes/implementer-T1-0.md",".worktrees/T1/README.md"]`: `subprocess.run(["git","check-ignore","--quiet",probe],check=False).returncode == 0` (rc≠0 → note) |
| `git check-ignore --quiet <probe>` (201) | `subprocess.run(["git","check-ignore","--quiet",probe], check=False).returncode == 0` |
| Exit `"Docs lint: failed."` / `"Docs lint: passed."` (206-213) | Same exact strings, same exit codes |

## Per-linter behaviour matrix — `lint-build.sh` → `lint-build.py`

Added per reviewer Blocker 5 + Concern 7 (exit-code interleaving) + Concern 9 (`git ls-tree -d`).

| `lint-build.sh` (line) | `lint-build.py` |
|---|---|
| `set -uo pipefail` (26) | Default Python; explicit exit codes at end |
| `REPO_ROOT` + `cd` (28-29) | `_repo_root()` + chdir under `__main__` guard |
| `LINT_BUILD_DIR` env (34-35) | `os.environ.get("LINT_BUILD_DIR", "packages/agentbundle/agentbundle/build")` |
| `find $BUILD_DIR -name "*.py" ! -path "$FIXTURES_SUBDIR/*"` (39-41) | `Path(build_dir).rglob("*.py")` filtered to exclude paths under `fixtures_subdir` |
| Stdlib-import audit Python heredoc (47-79) | Lifted verbatim as `_audit_imports(py_files) -> int` returning violation count |
| **`_audit_imports([])` returns `0`** (empty `py_files` fast-path; matches bash line 45 `(( ${#py_files[@]} > 0 ))` short-circuit) | `if not py_files: return 0` at function entry — keeps `import_violations` at 0 so part-2 still runs on a clean tree |
| **Part-1 exit assignment** `import_violations=$?` (80) | `import_violations = _audit_imports(...)` |
| `echo "lint-build: stdlib-import audit passed"` only if `==0` (83-85) | Same conditional emission |
| Part-2 `git merge-base HEAD main \|\| { echo ...; exit "$import_violations"; }` (89-92) | `subprocess.run(["git","merge-base","HEAD","main"])`; on rc≠0 → `print("lint-build: warning: ...skipping top-level audit", file=sys.stderr); sys.exit(import_violations)` |
| `RFC_AUTHORISED_DIRS=( "packs" ... )` (98-100) | Module-level list, same single entry |
| `git ls-tree -d --name-only HEAD` (103) and `... $merge_base` (104) | Two `subprocess.run(["git","ls-tree","-d","--name-only", ref], capture_output=True, text=True)` calls; split lines, build sorted sets |
| `comm -23 <(... HEAD \| sort) <(... merge_base \| sort)` (102-104) | `sorted(head_dirs - base_dirs)` — set-difference; empty-element filter |
| Authorised-dir filter loop (108-120) | `[d for d in new_dirs if d and d not in RFC_AUTHORISED_DIRS]` |
| `echo "lint-build: new top-level directories introduced (RFC required):"` + indented list + `exit 1` (122-128) | Same exact wording, same exit |
| `echo "lint-build: no-new-top-level-directory audit passed"` (131) | Same exact wording |
| **Final `exit "$import_violations"`** (133) | `sys.exit(import_violations)` — preserves part-1 status when part-2 passes (the critical interleaving) |
