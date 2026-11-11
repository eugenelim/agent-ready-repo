# Slice 1 interface reconciliation

Checked against shipped squash commit `9d39eae8b` (PR #1515) on 2026-10-07.
The prior Slice 2 engine and cohort files are absent. The new code-mode run is
`accb0133-8ca5-414a-a831-41a1bd9f35c4`; no prior gate approval is inferred.
The owner requested no review-round cap.

## Evidence append and replay

`packs/core/.apm/skills/work-loop/scripts/_evidence_store.py` exposes:

```python
EvidenceStore(log_path: Path)
open(audit_sink: Callable[[Any], None] | None = None) -> None
rebuild_indexes() -> None
append_receipt(receipt: dict, *, transaction_id: str,
               issuer: object, grant: object,
               audit_sink: Callable[[Any], None]) -> dict
append_supersession(supersession: dict, *, transaction_id: str,
                   acceptance_fingerprint: str, issuer: object,
                   grant: object, audit_sink: Callable[[Any], None]) -> dict
```

Each append writes one record. Replay validates a record carrying `receipt_id`
as a receipt and every other record as a supersession. There is no public batch
append or review-record replay registration. Receipts have closed fields and
cannot hold a lossless finding assessment.

The approved `semantic-evidence-transaction.v1` schema already permits a
nonempty ordered set of embedded record identities. Slice 1 AC-0008 requires
all of those records to become visible together or none; it does not restrict
record kinds or transaction size to one record. T3 can add a compatible batch
port and a closed code-owned review record registry without changing this
schema or the existing single-record interfaces. T4 must use it to commit the
assessment and every affected criterion receipt together (Slice 2 AC-0014),
and to commit source replacement with all receipt supersessions (AC-0015).
The assessment view must rebuild from those same authoritative frames.

A second journal followed by reconciliation would weaken the accepted atomic
boundary. Encoding an assessment in receipt identity or producer strings would
misuse the predecessor contract. Neither approach is admitted by the plan.

Preserve existing retry and replay behavior:

- An identical record, transaction ID, and acceptance fingerprint returns the
  original transaction without a second frame. Authority and audit availability
  remain required on retry.
- Conflicting identity reuse refuses with `denied-duplicate-transaction-id`,
  `denied-duplicate-receipt-id`, or `denied-duplicate-supersession-id`.
- Replay skips a whole later frame reusing an admitted transaction or record
  identity; the first admitted record remains authoritative.
- An incomplete final frame recovers to the complete prefix. Invalid checksums,
  references, schemas, and parse shapes raise `EvidenceStoreError`.
- Keep `denied-store-not-opened`, `denied-store-poisoned`,
  `denied-lock-timeout`, `denied-log-not-regular`, `denied-log-needs-recovery`,
  `denied-log-corrupt`, `denied-log-size-limit`, and
  `denied-audit-sink-unavailable` unchanged.
- Keep the `denied-invalid-receipt-*`, `denied-invalid-supersession-*`,
  `denied-invalid-transaction-*`, and `denied-append-failed-*` mappings.
  Failed rollback poisons the store until fresh recovery.
- Producer refusals retain `denied-invalid-grant` or
  `denied-producer-authority`; the security event carries the finer scope or
  operation refusal.

## Shared validators and schema identity

There is no `_schema_validation.py`. Validators live with their owning service:

| Module | Callable validators |
| --- | --- |
| `_acceptance.py` | `validate_envelope_dict`, `validate_property_dict`, `validate_verdict_dict` |
| `_subject_projection.py` | `validate_subject_dict` |
| `_policy_import.py` | `validate_approval_dict`, `validate_initial_review_dict` |
| `_evidence_store.py` | `validate_transaction_dict`, `validate_receipt_dict`, `validate_supersession_dict` |

These validators return `(bool, stable_code)`, require closed fields, and admit
only integer schema version `1`, excluding booleans. Evidence identities and
nested identity values are nonempty strings. New review records must use these
approved shared contracts, not an invented universal validator or stronger
identity rule that rejects valid predecessor inputs.

Canonical schemas stay under `contracts/delivery/`. They are test-time
contracts; runtime validation uses sibling code and never loads or copies them.

## Content safety and audit pairing

`_content_safety.py` registers ten Slice 1 record types in
`SLICE_1_WRITER_BOUNDARIES`. Their existing profile assignments stay intact.
The existing `review-report` profile sets a one MiB whole-record bound and a
64 KiB bound per free-text field. The shared checker enforces the whole-record
bound; report validation must also enforce every individual field bound.

T1 resolves and registers the closed review-owned append/replay boundaries
before use and updates the architecture profile matrix and its agreement test.
Unregistered or unknown profiles refuse. Complete reports are validated before
any semantic review record is persisted.

After an allow event, every subsequent refusal must store a denial using the
same generated operation ID. `_emit_post_allow_denial` preserves that pairing
and redacts correlation; a denial-sink failure must not replace the original
refusal. No refused bytes may become audit identifiers or digests.

## Compatibility shadow path

`_compat_facade.py` enables Slice 1 shadow behavior only when
`WORK_LOOP_SHADOW_SERVICES=1`, beneath `<spec-dir>/.shadow-acceptance/`:

```python
shadow_call_on_transition(spec_dir: Path, engine_state: dict,
                          pending_data: dict) -> None
shadow_call_on_plan_locked(spec_dir: Path, engine_state: dict) -> None
```

Both calls run after the legacy commit. Failure records
`shadow-divergence:redacted` and cannot change the legacy result.
T6 preserves this behavior and adds the explicit review compatibility adapter.
Only that adapter can acknowledge paired current and structured review facts
after reconciliation from the source event identity. A Slice 1 shadow call
alone is neither that acknowledgement nor a cutover receipt.

## Reconciliation result

T1, T3, T4, and T6 are regenerated within the accepted Slice 2 envelope.
No protected spec section or Slice 1 schema is amended. The legacy plan lock,
task/cohort writer, procedure authority, and runtime provider remain unchanged.
Pre-EXECUTE adversarial and secure-design review, followed by separate human
spec and plan gates, must approve this new run before implementation starts.
