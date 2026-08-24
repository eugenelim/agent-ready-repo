# `review-verdict.v1` — the verdict record

Load when emitting or validating a review verdict record. `SKILL.md` states the
obligation to emit one; this file owns the shape, the state precedence, and what
counts as residual risk.

## Emit

After dispositions and required gates are known, emit exactly one fenced
`json review-verdict.v1` block in the user handoff. In full mode, copy the
byte-identical pre-human-gate block into the PR body's `Review verdict` section.
The pre-gate record uses `human_gate_status: "pending"`; after a human decision,
re-emit it with the observed `approved` or `changes-requested` status.

```json review-verdict.v1
{
  "schema_version": "review-verdict.v1",
  "state": "READY",
  "mode": "full",
  "review_unit": "stable non-empty label",
  "warranted_reviewers": [],
  "named_skips": [],
  "findings": [],
  "required_gates": [],
  "deferrals": [],
  "blind_spots": [],
  "human_gate_status": "pending",
  "non_authoritative_score": null
}
```

## Top level

A closed object with exactly these twelve keys. All unlisted keys, missing
fields, and values of a different primitive type are refused.

| Field | Type | Contract |
|-------|------|----------|
| `schema_version` | string | exactly `review-verdict.v1` |
| `state` | string | `BLOCKED \| CHANGES_REQUIRED \| READY_WITH_RESIDUAL_RISK \| READY` |
| `mode` | string | `full \| light` |
| `review_unit` | string | a stable non-empty string label |
| `warranted_reviewers` | array | present even when empty |
| `named_skips` | array | present even when empty |
| `findings` | array | present even when empty |
| `required_gates` | array | present even when empty |
| `deferrals` | array | present even when empty |
| `blind_spots` | array | present even when empty |
| `human_gate_status` | string | `pending \| approved \| changes-requested` |
| `non_authoritative_score` | null | always JSON `null` |

Collection fields are present and empty rather than null. `non_authoritative_score`
is the only nullable value in the record.

## Nested shapes

Each is closed on the same terms as the top level.

- `warranted_reviewers[]` — `{role, mandatory, outcome, report_ref}`. `role` and
  `report_ref` non-empty strings; `mandatory` boolean; `outcome`
  `clean | findings | named_skip | invalid | missing`.
- `named_skips[]` — `{code, category, reason, residual_eligible}`. First three
  non-empty strings; `residual_eligible` boolean.
- `findings[]` — `{id, source_role, severity, effective_severity, citation,
  text, status}`. `id`, `source_role`, `citation`, and `text` non-empty strings;
  `id` stays unchanged across review, adjudication, disposition, and verdict emission.
  Both severities are `blocker | concern | nit`: `severity` always
  preserves the reviewer value; `effective_severity` always equals `severity`
  under the mandatory gateway model. `status` is
  `unresolved | resolved | rejected | deferred`. Only sustained findings from
  the adjudicator gateway enter this array; refuted findings appear only in
  paired audit artifacts. See [`finding-adjudication.md`](finding-adjudication.md)
  for the full gateway procedure.
- `required_gates[]` — `{name, outcome, evidence}`. `name` and `evidence`
  non-empty strings; `outcome` `passed | failed`.
- `deferrals[]` — `{slug, reason, accepted_by, residual_eligible}`. First three
  non-empty strings; `residual_eligible` boolean.
- `blind_spots[]` — `{surface, reason, evidence_limit, accepted_by,
  residual_eligible}`. First four non-empty strings; `residual_eligible`
  boolean.

## State precedence

Apply in order, without compensation:

1. `BLOCKED` — an unresolved blocker, a failed required gate, a missing
   `finding-adjudicator`, an `ADJUDICATION-INDETERMINATE` stop, an invalid,
   missing, or named-skipped mandatory review, or prohibited silent suppression.
2. `CHANGES_REQUIRED` — a finding still requires action.
3. `READY_WITH_RESIDUAL_RISK` — every mandatory control passed and at least one
   residual-eligible item remains.
4. `READY` — otherwise.

Resolved original blockers stay in the record as evidence without keeping the
state blocked.

## Residual eligibility

Closed. Only a named skip for a warranted non-mandatory reviewer, an explicitly
accepted deferral, or an explicitly accepted analysis blind spot qualifies. A
missing `finding-adjudicator`, a failed gate, an invalid or missing mandatory
review (including a named skip), an unresolved blocker, and silent suppression
never qualify.

An absent graph provider, project-knowledge not requested or unavailable, and
`stateful migration: not triggered` are recorded where they apply but never by
themselves downgrade `READY`.

A downstream numeric score is non-authoritative telemetry outside this record
and cannot override the categorical state.

## Mode semantics are unchanged

Full mode still iterates every warranted reviewer to clean. Light mode still
runs one bounded adversarial pass with the existing Blocker escalation, and a
light non-Blocker disposition reaches `READY_WITH_RESIDUAL_RISK` only when the
record names the accepted residual and all required light-mode gates passed.
