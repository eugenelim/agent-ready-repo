# Spec: agentbundle-first-value-handoff

<!-- Mode: light (no risk trigger fired) -->

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 Amendment #4 — cross-pack first-value adoption overlay; spec/portfolio-pack-first-value-contract (the `[pack.first-value]` schema this spec consumes)
- **Brief:** none
- **Discovery:** none
- **Shape:** behavioral — additive stdout output in `packages/agentbundle/agentbundle/commands/install.py`

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A successful `agentbundle install` ends with `installed: {pack} @ {scope} via
{adapter}` on stdout, then exits. For a first-time adopter of a Level B pack
(non-technical or mixed audience), that output tells them the install worked
but nothing about what to do next: no verification step, no copy-ready prompt,
no expected result. They either explore by guessing or consult docs.

This spec consumes the `[pack.first-value]` contract (shipped in
spec/portfolio-pack-first-value-contract) to add a **first-value handoff
block** after the `installed:` line:

- **Level B packs** (`level-b = true`): verification step, expected result,
  copy-ready starter prompt, and optional next action.
- **Level A packs** (all others with `[pack.first-value]`): verification step only.
- **Packs without `[pack.first-value]`**: output unchanged.

The `installed:` line and all existing stdout/stderr parsing contracts are
unchanged. Dry-run, upgrade, and profile-install paths are unaffected.
Graphical onboarding (Claude's graphical client) remains the Level B default
for graphical-install users; this spec is for the terminal-install path only.

## Boundaries

### Always do

- Read from `pack_toml["pack"]["first-value"]` — already loaded in `install.run`;
  no additional I/O.
- Emit the handoff block to stdout (the same stream as the `installed:` line).
- Emit a blank line between the last `installed:` line and the handoff block.
- For dual-scope installs (two `installed:` lines), emit the handoff once after
  both lines.
- Show the `next-action` field when present (it is optional in the schema).
- Skip the handoff when `pack_toml` has no `[pack.first-value]` section.
- Scope the change to `install.py` only. The `upgrade`, `profile`, and
  `dry-run` paths are not affected (upgrade returns before Step 14; profile
  wraps each `run()` call in `redirect_stdout(io.StringIO())` so per-pack
  stdout, including any handoff, is suppressed; dry-run exits before Step 13).

### Ask first

- Whether to suppress the handoff when stdout is not a TTY (piped to a script).
  Current decision: no TTY detection — the handoff is additive and does not
  change the `installed:` line that scripts parse. Revisit if a concrete
  automation breakage is reported.

### Never do

- Modify the `installed: {pack} @ {scope} via {adapter}` line format.
- Emit the handoff block to stderr.
- Add a `--no-handoff` CLI flag — no second caller needs to differ.
- Read `pack.toml` a second time — `pack_toml` is already in scope.
- Emit a handoff for profile installs: `_run_profile` wraps each individual
  `run()` call with `redirect_stdout(io.StringIO())` (lines 4218, 4235), so
  per-pack stdout — including the handoff — is suppressed. Profile emits its
  own summary via `_emit_profile_summary` instead.
- Emit a handoff on `--dry-run` (the dry-run path exits before Step 13).
- Emit a handoff on the upgrade-offer path (Step 4a `return _offer_upgrade(…)`
  at line 532 exits before Step 14).

## Output format

### Level B pack

```
installed: architect @ repo via claude-code

Verify:   Ask your agent to review a module — you should see structured architecture guidance.
Try:      Describe the system architecture of this repository, starting with the main entry point.
Expected: A structured breakdown of your system's components, patterns, and improvement areas.
Next:     Use architect-review to evaluate an existing architecture against well-known principles.
```

Labels and padding are fixed so every value starts at column 10 (e.g.
`"Verify:   "`, `"Try:      "`, `"Expected: "`, `"Next:     "`). `Next:` is
omitted when `next-action` is absent in the pack's schema.
The `Try:` value is the verbatim `starter-prompt` field — no truncation, no
angle-bracket substitution (the validator guarantees no `<placeholder>` tokens).

### Level A pack

```
installed: core @ repo via claude-code

Verify:   Run /workspace-status in your agent — you should see your active initiative and work queue.
```

One line, same label style.

## Testing Strategy

**Unit (TDD):** `packages/agentbundle/tests/unit/test_install_first_value_handoff.py`

A new test module drives `install.run` in-process (same pattern as
`test_install_messages.py`) with a scratch pack whose `pack.toml` carries a
`[pack.first-value]` section. Captures stdout via `io.StringIO` and asserts on
the output. Uses the real converters pack (Level B) and core pack (Level A) as
fixtures; a scratch pack with no `[pack.first-value]` provides the AC3 baseline.

Positive fixtures:
- Level B pack (converters): stdout contains `Verify:`, `Try:`, `Expected:` lines.
- Level A pack (core, no `level-b`): stdout contains `Verify:` but not `Try:`.
- Level B pack without `next-action` (unit-only): stdout contains `Verify:`,
  `Try:`, `Expected:` but no `Next:` line.
- Dual-scope install (converters at user scope, then repo+force): handoff appears
  exactly once after both `installed:` lines (`stdout.count("Verify:") == 1`).

Negative fixtures (handoff must NOT appear):
- Scratch pack has no `[pack.first-value]` section → stdout unchanged.
- `--dry-run` flag → stdout is the plan summary, no handoff.
- Upgrade-offer path (pack already installed at same scope; non-TTY auto-refuses)
  → `return 1` before Step 14, no handoff in stdout.

**Goal-based gates:**
- `make build-check` green after the change.
- Existing unit tests in `test_install_messages.py` and siblings still pass
  (the `installed:` line is unchanged; only additive output is added).

**Manual QA (visual):**
- Run `agentbundle install architect` against a temp repo; observe the handoff
  block in stdout with architect's actual `[pack.first-value]` data.

## Acceptance Criteria

### AC1 — Level B handoff block

- [x] After all `installed:` line(s), if `pack_toml["pack"]["first-value"]["level-b"]`
  is truthy, stdout contains (in order): a blank line, then `Verify:`, `Try:`,
  `Expected:` lines using the pack's `verification`, `starter-prompt`, and
  `expected-result` fields.
- [x] When `next-action` is present in `[pack.first-value]`, a `Next:` line
  appears after `Expected:`.
- [x] When `next-action` is absent, no `Next:` line appears.
- [x] The `Try:` value is the verbatim `starter-prompt` string — no truncation,
  no added angle-bracket tokens.

### AC2 — Level A handoff block

- [x] After all `installed:` line(s), if `[pack.first-value]` exists but
  `level-b` is absent or false, stdout contains a blank line then a single
  `Verify:` line using the `verification` field.
- [x] No `Try:`, `Expected:`, or `Next:` lines appear for Level A packs.

### AC3 — No first-value section: output unchanged

- [x] If `pack_toml` has no `[pack.first-value]` section, the install stdout
  is byte-identical to the pre-spec output (existing test assertions still pass).

### AC4 — Dry-run: no handoff

- [x] `--dry-run` output is unchanged (the dry-run path exits before Step 13,
  so no code change is required; the test verifies this as-is).

### AC5 — Backward-compat: installed: line unchanged

- [x] The `installed: {pack} @ {scope} via {adapter}` line format is unchanged.
- [x] Existing install tests that assert on the `installed:` line content pass
  without modification.

### AC6 — Dual-scope install: handoff appears once

- [x] A dual-scope install (two `installed:` lines) emits one handoff block,
  after both lines, not one per scope.

### AC7 — Upgrade-offer and profile paths: no handoff

- [x] The Step 4a upgrade-offer path (`_offer_upgrade` branch) does not emit
  a handoff.
- [x] The `_run_profile` path does not emit a handoff.

## Assumptions

1. `pack_toml` is already read via `load_pack_toml` before Step 13; the
   `[pack.first-value]` data is available in memory at Step 14 with no
   additional file I/O.
2. All 17 packs have `[pack.first-value]` populated as of the shipped
   spec/portfolio-pack-first-value-contract PR (AC4 of that spec).
3. The `starter-prompt` field in every Level B pack contains no
   `<placeholder>` tokens (the `lint-first-value-contract.py` validator
   enforces this at build time).
4. `--dry-run` exits at line 929 (before the `installed:` lines at line 1356),
   so the handoff is naturally suppressed without a conditional.
5. `make build-check` is the correct local preflight gate (confirmed in
   AGENTS.local.md § Commands).
6. The converters pack is Level B (`level-b = true`) with a complete
   `[pack.first-value]` section — it ships as the Level B integration fixture.
   The "no handoff" negative fixture uses a scratch `pack.toml` without
   `[pack.first-value]`, since all 17 real packs now have the section.
7. The `next-action` field is required by `lint-first-value-contract.py` for
   any `level-b = true` pack at build time, so the optional branch and its
   unit test cover a state the build gate forbids. The defensive `.get()`
   guard is kept as belt-and-suspenders; the spec's factual claim is that
   `next-action` is schema-required for Level B.

## Changelog

<!-- Add an entry under [Unreleased] in docs/product/changelog.md when this
     spec is implemented. Format: feature bullet, one line. -->
