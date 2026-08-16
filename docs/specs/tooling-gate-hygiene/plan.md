# Plan: tooling-gate-hygiene

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `tools/build-site.py`, `tools/test_build_site_dry_run.py` (new) — AC1/AC2.
- `packages/agentbundle/agentbundle/{system_trust,catalogue}.py` and
  `tests/unit/test_catalogue_trust_fallback.py` — AC3–AC5.
- `tools/repo/build_gate_chain.py`, `tools/test_build_gate_chain.py` — AC6/AC8.
- `docs/specs/digital-experience-contract/spec.md` — AC9.
- `workspace.toml` — AC10.

**What demonstrates done**
- Mutation test for AC1; subprocess tests; `make ci`.

**What I am NOT changing**
- The drift check's logic — promotion is wiring only.
- Any Windows-interop path.

## Declined patterns

- **Tempted:** keep the line-window heuristic for the structural dry-run test.
  **Declined:** three correctly guarded writes sit 9–11 lines below their guard,
  so any fixed window either misses real defects or fails correct code. Scoped to
  the enclosing function instead.
- **Tempted:** let the structural test stand as the dry-run guarantee.
  **Declined:** it would not have caught this defect. Said so in its docstring
  rather than leaving a reader to assume otherwise.
- **Tempted:** chmod the real `docs-site/` tree to test the non-writable case.
  **Declined:** it would break a concurrent build. Asserted the property that
  makes such a run possible — no write at all — with a tmp-dir control proving
  the test can observe a write.
- **Tempted:** wire the drift check into `build-check.yml` directly. **Declined:**
  CI invokes `make build-check`, so a gate-chain step is covered on both sides
  with no parity disposition to maintain.

## Anchor-test sweep

- `test_build_gate_chain.py` pins the step sequence — updated (AC8).
- `test_catalogue_trust_fallback.py`'s plain-linux test asserts on the message —
  extended rather than left to pass vacuously (AC5).

## Verification log

- **AC1/AC2** `--dry-run` leaves no generated tree; mutation-verified — reverting
  the guard fails `test_dry_run_creates_no_generated_directory`, restoring passes.
- **AC3–AC5** 27 tests in `test_catalogue_trust_fallback.py` green, covering both
  branches and the no-interop rail.
- **AC6/AC8** `test_build_gate_chain.py` 16 passed after extending the pinned list.
- **AC7** third clean drift pass recorded 2026-08-16 (exit 0).
- **AC10** slug diff vs `origin/main`: exactly the three intended removed.
- **REVIEW** `adversarial-reviewer` = named skip (session instruction prohibits
  subagent dispatch). Self-reviewed against the spec-less checklist.
