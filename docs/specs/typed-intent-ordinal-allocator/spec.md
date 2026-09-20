# Spec: Prefix-type-aware intent ordinal allocator

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** docs/product/briefs/intent-identity-and-registration.md
- **Discovery:** docs/product/intents/FEAT-0001-intent-identity-and-registration.md
- **Constrained by:** ADR-0108; ADR-0033

## Objective

Allocate a human-friendly typed ordinal — `VISION-0001`, `STRAT-0001`, `CAP-0001`, `FEAT-0001` — as a filename prefix, using `max + 1` over the directory unioned with `origin`. The existing `next-ordinal.py` cannot be reused: it matches an anchored four-digit-then-separator pattern, so on a directory of typed filenames it returns `0001` with exit 0 and reports `--check` clean because nothing matched. That silent-wrong behaviour is the single most important failure to design against.

The prefix table is closed. `Level` stays open; what is closed is the mapping from altitude to token, so an unmapped altitude is refused an ordinal rather than having one derived for it.

An ordinal is assigned at admission, and ADR-0098 D2 makes `intake-intent` the canonical owner of admitting a repository intent, so this slice also owns the minimal integration: where admission invokes the allocator and what it does with a refusal. Admission *policy* is unchanged — its confinement, provenance and authority-transfer controls are preserved, not re-specified.

## Testing Strategy

- Collision-equivalence against `next-ordinal.py` over the real ADR and RFC corpora plus a synthetic typed corpus.
- Feed unparseable input and typed-but-unmapped altitudes; assert refusal rather than a plausible ordinal.
- Assert an intent refused an ordinal keeps full identity, admission and graph participation.
- Observe one end-to-end admission: a conforming eligible intent admitted through `intake-intent` carries its allocated ordinal in the written filename. Without this the allocator can be correct in isolation while admission never calls it.
- Re-run `packs/core/tests/skills/intake-intent/test_intake_intent.py` unamended, so the integration preserves admission's existing controls rather than re-specifying them.

## Acceptance Criteria

- [ ] An admission-eligible intent whose `Level` the prefix table maps receives an ordinal, sequenced per type so `CAP-0001` and `FEAT-0001` coexist.
- [ ] An intent whose `Level` is absent or unmapped receives no ordinal and no derived prefix, and keeps its full `kind:slug` identity, admission and graph participation.
- [ ] Allocation edits no file other than the intent being created — no counter file, no shared retired list.
- [ ] The allocator returns no ordinal, and reports no clean duplicate check, for input it did not fully parse.
- [ ] The allocator is collision-equivalent to `next-ordinal.py` on untyped corpora, including the `origin` union that catches an unpushed sibling.
- [ ] `intake-intent` invokes the allocator when it admits a repository intent, at a named point in its procedure, and a conforming eligible intent ends up written with its allocated ordinal in the filename.
- [ ] An intent the allocator refuses is still admitted and registered, with no ordinal in its filename and no partial write.
- [ ] `packs/core/tests/skills/intake-intent/test_intake_intent.py` passes unamended, so admission's confinement, provenance and authority-transfer controls are preserved by the integration.
