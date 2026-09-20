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

An ordinal is assigned at admission, so this slice also owns the minimal integration. Admission has **two entry paths**, and the allocator has to be reachable from both. `work-intake` § 6 delegates a classified intent, and `work-intake/SKILL.md:60` routes a request that explicitly names `intake-intent` straight to that owner instead. An allocator wired only into § 6 would be silently skipped on the second path, which is the same class of silent-wrong failure as the one described above.

The two paths get different mechanisms because they have different capabilities, and the capability line is not moved by this slice. `work-intake` declares `Bash` and already "passes the confirmed repository destination, and authority mode to `intake-intent`" (`work-intake/SKILL.md:332`), so it runs the allocator and supplies the result. `intake-intent` declares no shell — its `## Boundaries` section refuses one outright — so it cannot allocate, and this slice does not grant it one: widening the shell boundary of the skill that handles untrusted intent sources is a larger change than the identity it would buy. Instead the owner's Procedure step 3, where it "confirm[s] the proposed repository-relative destination", gains one condition, and it is a refusal rather than a disclosure. For a level the table maps, the owner writes only a destination that already carries an ordinal — one a caller allocated, or one supplied with the request and confirmed. Lacking either, it stops and names the path that allocates. It never derives an ordinal itself, because deriving one by reading the directory would reproduce, prompt-only and without the `origin` union, exactly the plausible-but-wrong answer this slice exists to stop. So a mapped intent is written with an ordinal or it is not written, on both paths.

ADR-0098 D2 is preserved on both paths: `intake-intent` remains the owner of admitting a repository intent, and confinement, provenance and authority transfer are preserved rather than re-specified.

## Testing Strategy

- **Typed sequencing (AC-0001).** Unit tests over a corpus holding every mapped type, asserting each type's ordinal is the max of its own type plus one, so `CAP-0001` and `FEAT-0001` coexist and neither type's records push the other's number up.
- **Collision-equivalence (AC-0005).** Unit tests over the real `docs/adr/` and `docs/rfc/` corpora, asserting the new allocator returns what `next-ordinal.py` returns wherever the corpus is untyped, and that the `origin` union catches an unpushed sibling in a fixture repository.
- **Refusal over plausibility (AC-0002, AC-0004).** Feed unparseable filenames and typed-but-unmapped altitudes; assert the allocator returns no ordinal and reports no clean duplicate check, rather than the `0001` and exit 0 that `next-ordinal.py` returns on the same input.
- **No shared mutable state (AC-0003).** Assert allocation writes nothing: no counter file, no retired list, no cache. A tree snapshot before and after is the check.
- **One end-to-end admission (AC-0006, AC-0007).** An intent taken through `work-intake` into `intake-intent` is written with its allocated ordinal in the filename, and a refused one is written unprefixed with no partial write. Without this the allocator can be correct in isolation while nothing calls it.
- **No path writes a mapped intent unprefixed (AC-0009).** Goal-based check on `intake-intent`'s Procedure step 3, asserting it refuses a destination carrying no ordinal for a mapped level and derives none, plus one recorded direct invocation showing the refusal and its named next step.
- **Admission's own controls are preserved, not restated (AC-0008).** Re-run `packs/core/tests/skills/intake-intent/test_intake_intent.py` unamended; this slice changes none of `intake-intent`'s files.

## Acceptance Criteria

- [ ] **AC-0001.** An admission-eligible intent whose `Level` the prefix table maps receives an ordinal, sequenced per type so `CAP-0001` and `FEAT-0001` coexist.
- [ ] **AC-0002.** An intent whose `Level` is absent or unmapped receives no ordinal and no derived prefix, and keeps its full `kind:slug` identity, admission and graph participation.
- [ ] **AC-0003.** Allocation edits no file other than the intent being created — no counter file, no shared retired list.
- [ ] **AC-0004.** The allocator returns no ordinal, and reports no clean duplicate check, for input it did not fully parse.
- [ ] **AC-0005.** The allocator is collision-equivalent to `next-ordinal.py` on untyped corpora, including the `origin` union that catches an unpushed sibling.
- [ ] **AC-0006.** `work-intake` invokes the allocator at a named point in its procedure and supplies the resulting `<TYPE>-NNNN-<slug>.md` as the confirmed repository destination it already passes to `intake-intent`, so a conforming eligible intent is written with its allocated ordinal in the filename.
- [ ] **AC-0007.** When the allocator refuses, `work-intake` supplies the unprefixed `<slug>.md` destination instead, so the intent is still admitted and registered with no ordinal in its filename and no partial write.
- [ ] **AC-0008.** `packs/core/tests/skills/intake-intent/test_intake_intent.py` passes unamended, so admission's confinement, provenance and authority-transfer controls are preserved rather than re-specified, and `intake-intent` gains no shell, network or new-tool capability.
- [ ] **AC-0009.** On the direct entry path, where a request names `intake-intent` and no caller has allocated, the owner writes no intent for a level the table maps unless the confirmed destination already carries an ordinal. Lacking one it stops with a named refusal that points at the path which allocates, and it never derives an ordinal itself. So no path writes a mapped intent unprefixed.
