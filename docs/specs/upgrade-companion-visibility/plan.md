# Plan: upgrade companion-drop visibility

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn.

## Approach

Two complementary changes in one PR:

1. **Code (bug-fix shape).** In `upgrade.py`'s projection walk, the Tier-2 branch
   (`upgrade.py:365-374`) writes the `.upstream.<ext>` companion silently. Collect
   each companion relpath into a per-run list as it is written, then after the
   walk emit a single stderr summary naming the count and the companion paths.
   This follows `install.py:891-904`'s seed-companion notice (same "kept as
   `*.upstream.<ext>` companions" vocabulary, same stderr-not-stdout rationale) and
   **extends** it by naming the path(s) — `upgrade` has no install-state marker to
   record them in, unlike `install`'s projection-walk rail (`install.py:809-817`).
   The Tier-2 write itself and the state update are unchanged; this is purely
   additive observability. The per-primitive upgrade path (`upgrade.py:335-353`)
   walks the same Tier-2 branch, so it is covered by the same change.

2. **Governance (erratum).** Add an Approver-signed entry to RFC-0001 § Errata
   reconciling the frozen body's Tier-2 in-CLI three-option prompt with the shipped
   companion-drop + surfacing + `adapt-to-project`-owned-interactivity design,
   matching the existing 2026-05-30 erratum's format. The frozen body is unchanged;
   the erratum is the correction of record. Resolve the `docs/backlog.md` item.

**Riskiest part:** none in the code (additive stderr). The judgement risk is the
erratum wording — it must reconcile, not silently rewrite, a frozen Accepted RFC.
That is why the pre-EXECUTE adversarial review runs on the spec + plan + erratum
draft before any code.

### The trio

- **Files touched:** `packages/agentbundle/agentbundle/commands/upgrade.py`
  (companion collection + stderr summary); `packages/agentbundle/tests/integration/test_upgrade_cmd.py`
  (regression test); `docs/rfc/0001-bundle-distribution-by-adapter-spec.md`
  (§ Errata entry); `docs/backlog.md` (resolve item); this spec dir.
- **Tests that show "done":** a new integration test that edits a projected file
  post-install to force Tier-2, runs `upgrade`, and asserts the companion exists
  with upstream content, the adopter edit is preserved, and stderr names the
  companion path; the existing `test_tier_invariants.py` harness stays green.
- **Not changing:** the Tier-2 file-safety contract (still companion-drop, never
  clobber); `install.py`; the stdout `upgraded:` recap; non-TTY behavior (identical
  but for the added stderr line). No `--dry-run`/plan (separate spec).

### Declined patterns

- Tempted to implement RFC-0001's three-option in-CLI prompt (keep / overwrite-with-`.pre-update.bak` / adapt) — **declining**; it clobbers Tier-2, contradicting two Shipped specs + the conformance harness. Reconciled via erratum instead.
- Tempted to add a `--dry-run` / projection-plan flag now — **declining**; it is a real feature deferred to its own spec, gated on user go/no-go.
- Tempted to extract `install`'s companion-summary into a shared helper for `upgrade` to reuse — **declining**; two call sites with different surrounding context (install records paths in the install-marker; upgrade in a stderr recap). Inline until a third caller appears (CONVENTIONS: inline a single-use operation).
- Tempted to surface a full per-file projection manifest (Tier-1 writes too) on every upgrade — **declining**; scope is the silent-companion gap, not a general install log. That is `--dry-run` territory.

## Constraints

- RFC-0001 is **Accepted/frozen**: bodies are immutable; corrections land in
  § Errata, Approver-signed (CONVENTIONS § 4; the existing 2026-05-30 erratum is
  the pattern).
- `agent-spec-cli` and `distribution-adapters` specs are **Shipped/frozen** — no
  body edits; their Boundaries ("never clobber Tier-2; always emit a companion")
  are the contract this change must not violate.
- `test_tier_invariants.py` pins the Tier-2 invariant across `upgrade`; it must
  stay green unmodified.

## Construction tests

**Integration tests:** see T1 `Tests:`.
**Manual verification:** none (no TTY-only path; the notice fires in non-TTY too).

## Tasks

### T1: `upgrade` surfaces Tier-2 companion-drops (parity with `install`)

**Depends on:** none

**Touches:** packages/agentbundle/agentbundle/commands/upgrade.py, packages/agentbundle/tests/integration/test_upgrade_cmd.py

**Tests:** (write first, red → green)
- Install v1 into `tmp_path`; overwrite one projected file with adopter bytes
  (forces Tier-2 on next upgrade); upgrade to v2 and assert:
  - the adopter bytes are still on disk at the original path (never clobbered);
  - the `.upstream.<ext>` companion exists with the v2 content;
  - **stderr names the companion path** and a count (the new visibility). [AC2]
- Negative: a clean install→upgrade (no edit) emits **no** companion notice on
  stderr. [AC3]
- Regression: `test_tier_invariants.py` (already covers `upgrade`) stays green
  unmodified. [AC1, AC4]

**Approach:**
- Initialise an empty `companions: list[str]` before the projection walk.
- In the Tier-2 branch, after `safety.write_companion(...)`, append
  `safety.companion_path(Path(relpath)).as_posix()` to `companions`. Leave the
  existing `pack_state.files[relpath] = {...}` update untouched.
- After the walk, if `companions`, print a single stderr summary: the count, that
  the files were modified since install and kept as `*.upstream.<ext>` companions
  (edits preserved), and the companion path(s). Vocabulary follows
  `install.py:895-903`, extended to list the path(s).

**Done when:** the new integration tests pass, `test_tier_invariants.py` stays
green, and `agentbundle upgrade` over a Tier-2 collision prints the companion path
to stderr while leaving the adopter file untouched.

### T2: RFC-0001 § Errata reconciliation + backlog resolution

**Depends on:** none

**Touches:** docs/rfc/0001-bundle-distribution-by-adapter-spec.md, docs/backlog.md

**Tests:** goal-based —
- RFC-0001 § Errata gains a dated, Approver-signed (@eugenelim) entry stating the
  Tier-2 in-CLI prompt is superseded by deterministic companion-drop + surfacing
  + `adapt-to-project`-owned interactivity; frozen body unchanged. [AC5]
- `docs/backlog.md`'s `agent-spec-cli` "Tier-2 upgrade prompt" item is removed/
  resolved (no dangling inbound `#anchor` — it is a plain bullet). [AC5]
- `python .claude/skills/work-loop/scripts/lint-spec-status.py` passes.

**Approach:**
- Append an Errata entry below the 2026-05-30 one, same shape (short version,
  numbered correction, Approver-signed sign-off, pointer to this spec).
- Delete the resolved backlog bullet (grep first to confirm nothing links it).

**Done when:** the erratum reads as a reconciliation (not a body rewrite), the
backlog item is gone, and `lint-spec-status.py` is clean.

## Risks

- Erratum wording could read as rewriting the frozen decision rather than
  recording the as-built divergence. Mitigation: pre-EXECUTE adversarial review;
  use "superseded by the shipped design" framing, not silent edits to the body.

## Changelog

- 2026-06-11: initial plan.
