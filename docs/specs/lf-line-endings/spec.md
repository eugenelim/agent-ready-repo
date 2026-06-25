# Spec: lf-line-endings

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The agentbundle CLI writes byte-for-byte LF-terminated text on every platform.
When an adopter runs the CLI on Windows — to project packs into Kiro, Cursor,
Codex, Gemini, Copilot, or any adapter, or to compose `AGENTS.md` and the
self-host tree — every generated file (`*.md`, `*.toml`, `*.json`, `*.yml`,
hooks, state) uses `\n` line endings, identical to the same command run on
macOS or Linux. The user this serves is an adopter on Windows (and the
Windows-clean white-label fork): their generated artifacts no longer drift to
CRLF, so a repo populated on Windows and one populated on macOS produce
identical bytes, and diffs/reviews stop being polluted by line-ending churn.

This is enforced at the source — the writers themselves emit LF — independent
of the consumer's git configuration, complementing (not depending on) the
repo-root `.gitattributes` that normalizes on commit.

## Boundaries

### Always do

- Pass `newline="\n"` to every text-mode file writer the CLI uses to emit a
  generated artifact (`Path.write_text(...)` and text-mode `open(...)` /
  `os.fdopen(...)`).
- Keep existing `Path.write_bytes(...)` calls as-is — they already emit exact
  bytes and are the correct tool for binary/byte-preserving writes.
- Keep the regression guard mechanical and stdlib-only (AST walk), so it runs
  in CI without new dependencies.

### Ask first

- Adding a shared write helper or new module to centralize newline handling —
  decided against for this change (see `plan.md` declined-pattern register);
  revisit only if a future reviewer requires it.
- Forcing `newline="\n"` on any writer that emits content a consumer needs in
  CRLF (none exist today; revisit if a Windows-only artifact is ever shipped).

### Never do

- Add a new dependency, module boundary, or shared abstraction layer to
  deliver this fix — it is `newline="\n"` at each existing call site plus one
  guard test.
- Change `write_bytes(...)` call sites to text mode, or alter the *content*
  any writer emits — only the newline translation behavior changes.
- Suppress the guard test or weaken it to a substring grep that misses
  multi-line calls.

## Testing Strategy

- **Writer-emits-LF behavior: goal-based check, exercised by a unit test.**
  For a representative writer, write content containing `\n` to a temp path
  and assert the file's raw bytes contain no `\r\n`. A unit test is the right
  surface because the contract is a pure property of one call; one
  representative writer proves the kwarg is honored without re-testing stdlib
  on every site.
- **No-regression invariant across the package: goal-based check, exercised by
  an AST guard test.** Walk every non-test `*.py` module in the agentbundle
  package; fail if any text-mode file writer lacks a `newline=` keyword. The
  flagged set is: `.write_text(...)`; `open(...)` / `os.fdopen(...)` /
  `tempfile.NamedTemporaryFile(...)` / `tempfile.TemporaryFile(...)` whose
  mode is text (a `mode=`/positional string containing `w`/`a`/`x`/`+` and not
  `b`). Explicitly *not* flagged: `write_bytes(...)`, binary-mode opens
  (`"wb"`), `os.open(...)` (returns a raw fd, never a text stream),
  `os.write(fd, bytes)`, and default-mode `open(p)` (text *read*). This is the
  invariant that keeps the fix from silently regressing as new writers are
  added.
- **`.gitattributes` is honored: goal-based check.** `git check-attr text eol`
  on a sample tracked file resolves to `text: auto` / `eol: lf`; covered
  inline at the finish checklist rather than a committed test.

## Acceptance Criteria

- [x] A repo-root `.gitattributes` pins `* text=auto eol=lf` with binary
  overrides; `git check-attr text eol` on a tracked `.py`/`.md` file resolves
  to `text: auto` / `eol: lf`.
- [x] `.gitattributes` is listed in `self_host.py`'s `EXCLUDED_PATTERNS` so
  `make build-self` treats it as repo-owned and does not clobber it.
- [x] All 24 text-mode writers pass `newline="\n"`: 21 `Path.write_text(...)`,
  1 `os.fdopen(..., "w")` in `build/adapters/codex.py`, and 2
  `tempfile.NamedTemporaryFile(mode="w")` in
  `build/projections/merge_into_agent_json.py` and
  `build/projections/user_merge_json.py` (the atomic-write paths for
  `.claude/settings.json` and the Kiro/merged settings adopters track in
  dotfiles). Spread across `build/adapters/`, `build/projections/`,
  `build/main.py`, `build/self_host.py`, and `commands/install.py`.
- [x] An AST guard test fails CI if any non-test writer in the agentbundle
  package emits text without an explicit `newline=` keyword, and passes after
  this change.
- [x] A unit test asserts a representative writer produces bytes with no
  `\r\n`.
- [x] The existing agentbundle test suite passes unchanged (no test depended
  on platform newlines — verified at spec time).

## Assumptions

- Technical: Python floor is `>=3.11`; `Path.write_text(newline=...)` exists
  (source: `packages/agentbundle/pyproject.toml` + probe — `inspect.signature`
  shows `newline` parameter present).
- Technical: 24 text-mode writers need the fix (21 `write_text` + 1 `os.fdopen`
  + 2 `NamedTemporaryFile(mode="w")`); `write_bytes`, `mkstemp`+`os.write(fd,
  bytes)`, and `fdopen(..., "wb")` sites are already byte-safe and stay
  (source: grep inventory 2026-06-24, corrected after adversarial review caught
  the two multi-line `NamedTemporaryFile` sites).
- Technical: forcing LF breaks no existing test and ships no CRLF-needing file
  (source: `grep -rn "os\.linesep\|linesep" packages/agentbundle/` → 0 hits;
  `git ls-files | grep -iE "\.(bat|cmd)$"` → 0 hits, 2026-06-24).
- Process: this is a structural / public-interface change (the CLI's
  output-byte contract) → `work-loop` full mode + adversarial plan review. It
  is **not** RFC-gated: the CRLF→LF change on Windows is a correctness
  convergence (Windows output already *should* have matched POSIX/macOS, which
  is what the contract always implied), not a new or modified interface
  adopters relied on — so the bugfix carve-out in `docs/CONVENTIONS.md` § 3
  applies rather than the "modifies a public interface" path (source:
  `docs/CONVENTIONS.md` § 3, `work-loop` risk triggers).
- Process: design is inline `newline="\n"` + AST guard, not a shared helper
  (source: user confirmation 2026-06-24).
- Product: serves adopters running the CLI on Windows (esp. the Kiro adapter)
  and the Windows-clean white-label fork (source: user confirmation
  2026-06-24).
