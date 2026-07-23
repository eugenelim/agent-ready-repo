# Plan: agentbundle-first-value-handoff

<!-- Mode: light -->

- **Spec:** [`spec.md`](spec.md)
- **Status:** Draft

## Constraints

- Touch only `packages/agentbundle/agentbundle/commands/install.py` for the
  production change, and add one new test file. No other files.
- The `installed:` line format must not change.
- No new CLI flags or public API additions.

## Risks

- Existing tests that assert the full stdout of a successful install may fail
  if they match the exact stdout string rather than checking for the `installed:`
  line. Check `test_install_messages.py` and siblings before assuming
  `assertIn` is sufficient.

## Declined patterns

- Tempted to add `--no-handoff` flag: declining — no second caller needs to differ.
- Tempted to add TTY detection: declining — the handoff is additive and
  automation scripts look for the `installed:` line, not the trailing block.
- Tempted to emit the handoff via a new `_HandoffFormatter` class: declining —
  a single helper function is sufficient for one call site.
- Tempted to write the handoff to a separate `_handoff.py` module: declining —
  one call site in `install.py`; keep it local until a second caller appears.

---

## Tasks

### Task 1 — Implement `_emit_first_value_handoff`

**Verification mode:** TDD

**Tests:** `packages/agentbundle/tests/unit/test_install_first_value_handoff.py`

Write these stubs first (red), then implement:

```python
# stub tests — must fail before implementation
def test_level_b_emits_verify_try_expected_next(): ...
def test_level_b_without_next_action_omits_next_line(): ...
def test_level_a_emits_verify_only(): ...
def test_no_first_value_emits_nothing(): ...
```

**Approach:**

Add `_emit_first_value_handoff(first_value: dict) -> None` to `install.py`.
The function reads from `first_value` (the dict at `pack_toml["pack"]["first-value"]`,
or `{}` when the section is absent) and prints to stdout:

```
# if first_value is empty: return immediately

print()  # blank line separator
print(f"Verify:   {first_value['verification']}")
if first_value.get("level-b"):
    print(f"Try:      {first_value['starter-prompt']}")
    print(f"Expected: {first_value['expected-result']}")
    if first_value.get("next-action"):
        print(f"Next:     {first_value['next-action']}")
```

Label padding (two spaces after the colon) keeps values aligned across the
four labels `Verify:`, `Try:`, `Expected:`, and `Next:` — these labels are
at most 8 characters; pad to 10 total (label + colon + two spaces + value).

**Done when:** all four stubs pass; function is a standalone unit with no
side effects beyond printing.

---

### Task 2 — Call `_emit_first_value_handoff` at Step 14

**Verification mode:** goal-based

**Approach:**

In `install.run`, after the Step 13 `for plan in plans:` loop (line ~1407),
and before `return 0`, add:

```python
# ── Step 14: First-value handoff ─────────────────────────────────────────
_emit_first_value_handoff(
    pack_toml.get("pack", {}).get("first-value", {})
)
```

`pack_toml` is already in scope (loaded at line 222). No new I/O.

**Done when:**
- `python -m pytest packages/agentbundle/tests/unit/test_install_first_value_handoff.py` passes.
- `python -m pytest packages/agentbundle/tests/unit/test_install_messages.py` passes without modification.
- `make build-check` exits 0.

---

### Task 3 — Integration test for handoff in full install flow

**Verification mode:** goal-based

**Approach:**

Add test class `InstallFirstValueHandoffIntegrationTests` to the new test
file. Uses the same `_run_install` + `io.StringIO` pattern as
`test_install_messages.py`. Set up a scratch pack directory with a
`pack.toml` that carries a `[pack.first-value]` section (Level B).

Fixtures needed:
- A minimal scratch `pack.toml` with `[pack]`, `[pack.install]`, and
  `[pack.first-value]` sections.
- At least one `.apm/skills/dummy/SKILL.md` so the pack has content to
  project (empty pack renders zero files and short-circuits before Step 13).

Test cases:
- Level B full flow → stdout contains all four handoff labels.
- Level A flow → stdout contains `Verify:` but not `Try:`.
- No `[pack.first-value]` → stdout contains `installed:` but no `Verify:`.
- Dual-scope install (mock or real): `Verify:` appears exactly once in stdout.

**Done when:** all integration test cases pass under `make build-check`.

---

### Task 4 — Manual QA against architect pack

**Verification mode:** visual / manual QA

**Approach:**

1. Create a temp repo directory.
2. Run `agentbundle install architect --catalogue <repo-root> --output <temp-repo>`.
3. Observe stdout: should see `installed: architect @ repo via <adapter>`, a blank
   line, then `Verify:`, `Try:`, `Expected:`, and `Next:` lines using architect's
   actual `[pack.first-value]` data.
4. Record observed output inline in a `notes/` subdirectory.

**Done when:** observed stdout matches the AC1 format; no regression in the
`installed:` line.

---

## Finish-time checklist

- [ ] Gates clean: `make build-check` exits 0.
- [ ] `test_install_messages.py` and all sibling install test files pass without modification.
- [ ] `test_install_first_value_handoff.py` passes (unit + integration).
- [ ] Manual QA transcript recorded in `docs/specs/agentbundle-first-value-handoff/notes/`.
- [ ] `spec.md` Status updated to Shipped; all ACs checked.
- [ ] `workspace.toml` `["ini-002".work].queue` entry moved to `shipped`.
- [ ] `docs/product/changelog.md` `[Unreleased]` entry added.
- [ ] PR description includes a `Deferred:` section listing any deferred items.
