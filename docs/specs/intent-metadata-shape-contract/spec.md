# Spec: Intent metadata shape contract and its two enforcement points

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** docs/product/briefs/intent-identity-and-registration.md
- **Discovery:** docs/product/intents/FEAT-0001-intent-identity-and-registration.md
- **Constrained by:** ADR-0033; ADR-0098

## Objective

Declare what an intent's preamble must carry, and enforce it in the two places that see different failures: the shaping review at ratification, and a corpus lint for drift across intents already on disk. Neither substitutes for the other — a per-artifact gate never sees the corpus, and a corpus lint never sees an artifact at the moment it is ratified.

This slice also ends the practice of inferring shaping progress from `Status: Draft`. Whether an intent has been de-risked or reviewed must be readable from its metadata; a de-risk record in the body is prose and is not that signal.

## Testing Strategy

- Walk conforming and non-conforming fixtures through both enforcement points and assert each accepts and rejects independently.
- Assert the corpus lint names the offending intent and field, and assert its exit code for conforming, non-conforming and unreadable corpora.
- Assert shaping progress is answerable from metadata alone, with the artifact body withheld from the reader.

## Acceptance Criteria

- [ ] The contract separates fields **required to be present** from fields carrying a **closed vocabulary when present**. `Kind` and `Status` carry closed vocabularies; `Level` stays open under ADR-0033 D2.
- [ ] **Decision owed by this spec:** which fields are required to be present, each closed vocabulary's member set, and whether `Kind` presence is ever required — noting the intent model makes `Kind` additive and prompt-only, so requiring it would contradict that model.
- [ ] Whether an intent has been de-risked, and whether it has passed a shaping review, is answerable from its preamble without opening the body.
- [ ] The shaping review accepts a conforming shape and rejects a non-conforming one at ratification.
- [ ] The corpus lint names each non-conforming intent and the field at fault, exits non-zero when any intent is non-conforming, and exits non-zero rather than clean when it could not fully read the corpus.
- [ ] **Decision owed by this spec:** how ratification checks the shape contract without becoming an open-ended schema or quality gate. The parent records this enforcement point as untested and in tension with the reviewer's bounded well-formedness role.
- [ ] **Decision owed by this spec, per field:** how the corpus lint treats intents predating each newly required field — backfill at cutover, a dated legacy exception, or requiring it only from a named point forward.
