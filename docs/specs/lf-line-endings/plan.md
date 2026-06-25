# Plan: lf-line-endings

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn.

## Approach

Two independent layers, one PR. The **commit-boundary** layer is a repo-root
`.gitattributes` (`* text=auto eol=lf` + binary overrides) plus listing it in
`self_host.py`'s `EXCLUDED_PATTERNS` so projection treats it as repo-owned.
The **source** layer adds `newline="\n"` to the 24 text-mode writers the CLI
uses to emit generated artifacts, so the bytes are LF before git ever sees
them. The regression guard is the riskiest-to-get-right part: a substring grep
both false-positives on the several multi-line `write_text(...)` calls and
misses the multi-line `NamedTemporaryFile(mode="w")` writers, so the guard is
an AST walk that inspects each call's keywords. Order: land the guard test
first (red, enumerating all 24 violations), then green it by fixing the sites,
then add one representative byte-level unit test.

## Constraints

None. Not RFC-gated — a bugfix to the CLI's output-byte contract, not a
charter/convention/structure change (spec § Assumptions).

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** `git check-attr text eol` on a tracked `.py`/`.md`
file resolves to `text: auto` / `eol: lf` (finish-checklist, AC1).

## Design (LLD)

### Design decisions
- Inline `newline="\n"` at each call site, **not** a shared `write_text_lf()`
  helper. The only shared element is a one-token kwarg, not logic; a wrapper
  imported across 6 modules is abstraction for no reuse. The AST guard, not a
  helper, is the regression defense. *Declined: shared write helper / new io
  module — would add a structural boundary the fix doesn't need.* Traces to:
  AC3, AC4.
- Guard is an **AST walk**, not a regex/grep — multi-line `write_text(...)`
  calls (several exist) defeat line-based matching. Stdlib `ast` only, no new
  dependency. Traces to: AC4.
- `write_bytes(...)` sites are left untouched — they emit exact bytes already
  and are correct for binary writes (install-marker, user_config). The guard
  ignores them. Traces to: AC3.

### Failure, edge cases & resilience
- Guard must not flag `write_bytes`, binary-mode `open(..., "wb")`, or test
  files. It keys on text-mode writers in non-test modules only.

## Tasks

### T1: .gitattributes pins LF and is repo-owned

**Depends on:** none

**Tests:**
- Goal-based (AC1): `git check-attr text eol -- <a .py file>` →
  `text: auto`, `eol: lf`.
- Goal-based (AC2): `.gitattributes` appears in `EXCLUDED_PATTERNS` in
  `build/self_host.py`.

**Approach:**
- Repo-root `.gitattributes`: `* text=auto eol=lf` + binary overrides
  (`*.png`, `*.jpg`, … ). *(Already in working tree.)*
- Add `".gitattributes"` to `EXCLUDED_PATTERNS` in
  `packages/agentbundle/agentbundle/build/self_host.py`, next to `.gitignore`.
  *(Already in working tree.)*

**Done when:** both goal-based checks above pass. (`git add --renormalize .`
reporting no changes on the maintainer/CI checkout is a confirming
observation, not a gate — whether it rewrites anything depends on that
checkout's committed bytes, not on this diff.)

### T2: AST guard test fails on text writers missing `newline=`

**Depends on:** none

**Tests:**
- The test itself is the artifact. On the pre-fix tree it must FAIL, naming
  the 24 offending `file:line` sites (AC4, red state).

**Approach:**
- Add `packages/agentbundle/agentbundle/build/tests/test_writers_emit_lf.py`.
- Walk every non-test `*.py` under `packages/agentbundle/agentbundle/` with
  `ast`. Flag a `Call` lacking a `newline` keyword when it is:
  - a `.write_text(...)` attribute call; or
  - `open(...)` / `os.fdopen(...)` / `tempfile.NamedTemporaryFile(...)` /
    `tempfile.TemporaryFile(...)` opened in **text mode**.
- **Mode-detection rules** (so the walk doesn't hand-roll a brittle substring
  check):
  - For `open`/`os.fdopen`: the mode is the second positional arg or `mode=`
    kwarg, a string literal. Text mode = contains `w`/`a`/`x`/`+` and **not**
    `b`. A *missing* mode arg means text-read → not flagged.
  - For the `tempfile.*` factories: mode is the `mode=` kwarg (literal);
    same text-vs-binary test; default (`"w+b"`) is binary → not flagged.
  - **Never flag** `os.open(...)` (returns a raw int fd, not a stream),
    `os.write(...)`, or `*.write_bytes(...)`.
- Collect violations into a list; assert it is empty, printing `file:line`
  for each on failure.

**Done when:** running the test on the current tree fails and lists exactly
the 24 known sites (sanity that the walk catches them all, including the two
multi-line `NamedTemporaryFile` calls).

### T3: all 24 text writers pass `newline="\n"` (guard goes green)

**Depends on:** T2

**Tests:**
- The T2 guard test passes (AC3, AC4 green).
- Existing agentbundle suite still passes (AC6).

**Approach:** add `newline="\n"` to all 24 sites, touching only the kwarg — no
content or formatting changes:
- 21 `Path.write_text(...)` across
  `build/adapters/{cursor,gemini,kiro,kiro_ide}.py`,
  `build/projections/{codex_agent_toml,gemini_command_toml,copilot_agent_md,copilot_hooks_json,kiro_ide_hook,merge_json}.py`,
  `build/main.py`, `build/self_host.py`, `commands/install.py`.
- 1 `os.fdopen(fd, "w", ...)` in `build/adapters/codex.py` (this file's only
  text writer — it has no `write_text`).
- 2 `tempfile.NamedTemporaryFile(mode="w", ...)` in
  `build/projections/merge_into_agent_json.py` and
  `build/projections/user_merge_json.py`.

**Done when:** T2 guard test passes; full `pytest` for the package is green.

### T4: representative writer proves LF bytes

**Depends on:** T3

**Tests:**
- Unit (AC5): invoke one representative writer path (or the smallest unit that
  calls `write_text`) with content containing `\n`, read the file back in
  binary, assert `b"\r\n" not in data` and `b"\n" in data`.

**Approach:**
- Add the byte-level assertion to `test_writers_emit_lf.py` (or a sibling),
  using a `tmp_path` target.

**Done when:** the byte-level test passes on every platform's interpreter
(behavior is platform-independent because the kwarg is explicit).

## Rollout

Pure source + config change. Delivery: big bang, fully reversible (revert the
PR). No infra, no external systems, no sequencing. The `.gitattributes` takes
effect for downstream forks when the tree-copy transform next runs; no action
required of existing adopters beyond a one-time `git add --renormalize .` if
their repo already has committed CRLF.

## Risks

- A writer that legitimately needed platform-native or CRLF output would be
  forced to LF. Verified none exists (no `.bat`/`.cmd`, no `os.linesep` test
  dependence) — spec § Assumptions.
- The AST guard could under-match a future writer idiom (e.g. a writer aliased
  through a variable). Accepted: it catches the direct `write_text`/`open`
  forms that account for all current and idiomatic future sites; a creative
  alias is out of scope and would be caught in review.

## Changelog

- 2026-06-24: initial plan.
