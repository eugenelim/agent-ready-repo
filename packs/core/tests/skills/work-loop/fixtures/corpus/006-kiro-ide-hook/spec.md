# Spec: kiro-ide-hook primitive

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0005](../../rfc/0005-user-scope-hook-support.md)
  — sole driving RFC for this primitive (§ *Kiro IDE event hooks —
  new `kiro-ide-hook` primitive*, § *Validate-time rule lift* →
  *Sibling vocabularies for IDE event hooks*, and § *Follow-on
  artifacts*).

> **Stub.** The canonical design lives in RFC-0005. AC for this
> work are pinned in that RFC's § *Kiro IDE event hooks* subsections
> on `kiro-ide-hook` and the corresponding entries in § *Follow-on
> artifacts*. See [`plan.md`](plan.md) for the task breakdown.

This loop anchor exists so `loop-cohort.py` has a directory to point
its state file at; the spec amendments delivered by this work live
in two existing specs ([`distribution-adapters`](../distribution-adapters/spec.md)
and [`agent-spec-cli`](../agent-spec-cli/spec.md)) rather than in
this stub. No separate spec is being drafted — the RFC drives the
work directly per the prompt brief.

## Changelog

- 2026-05-31 — Status reconciled to Shipped (retroactive). The in-session implementation landed via PR #99 (`kiro-ide-hook-impl`): the `kiro_ide_hook.py` projector (`packages/agentbundle/agentbundle/build/projections/`), the validate-time rail in `commands/validate.py` (T-C2), the `adapter.schema.json` extension, and the test suite (`tests/unit/test_kiro_ide_hook_{rail,schema,projection}.py` + `tests/integration/test_kiro_ide_hook_e2e.py`). This spec is a loop-anchor stub with no acceptance-criteria checkboxes of its own; the contract amendments live in `distribution-adapters` and `agent-spec-cli`. Probe-gated refinements (Q6 `.kiro/hooks/<subdir>/` recursion, Q11 real IDE-authored vocabulary capture), the post-implementation ADR, and the first consumer pack remain tracked in `docs/backlog.md` § kiro-ide-hook.
