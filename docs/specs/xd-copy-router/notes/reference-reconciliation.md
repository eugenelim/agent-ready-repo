# Reference reconciliation — xd-copy-router

Six references shared a name across the folded skills and disagreed. This note
records, per file, how the divergence was classified, which variant won or how
both survived, every substantive difference, and why. A silent pick is a rule
change wearing a merge's clothes, so the classification is recorded **before**
the rewrite rather than inferred from the result.

Measured 2026-09-26. Line counts are `wc -l`; changed-line counts are
`diff <a> <b> | grep -c '^[<>]'`, which counts both sides.

## Classification

| Reference | `copy-direction` | `tone-of-voice` | Changed | Verdict | Task |
| --- | ---: | ---: | ---: | --- | --- |
| `copy-arbitration.md` | 33 | 42 | 37 | **Pervasive, scope-borne** — rewrite with one named scope parameter | T3 |
| `interrogation-sequence.md` | 49 | 53 | 40 | **Pervasive, scope-borne** — rewrite with one named scope parameter | T3 |
| `editorial-quality-gates.md` | 76 | 77 | 7 | **Localized, three-way** — one canonical body, one substantive verdict | T3 |
| `copy-grounding.md` | 52 | 56 | 42 | Localized | T4 |
| `plain-language-floor.md` | 27 | 33 | 20 | Localized | T4 |
| `audience-jtbd.md` ↔ `copy-jtbd.md` | 42 | 40 | 22 | Two names, one role — merge into `copy-jtbd.md` | T4 |

**What makes a divergence scope-borne.** Both variants restate the same rule,
paragraph by paragraph, differing only in whose scope they name: `copy-direction`
says "this surface", `tone-of-voice` says "this brand's register". Letting one
win deletes the other surviving mode's scope, which the preservation criterion
forbids — so the "one variant wins outright" branch is not available. Per-mode
clausing every paragraph would be the forbidden concatenation under a different
name. The remaining move is to name the scope once, as a parameter, and write
the body against it.

## `copy-arbitration.md` — pervasive, scope-borne

**Outcome:** one body at `content-design/references/copy-arbitration.md`, opening
with a **scope parameter** table that binds "the scope" to *one surface* for the
per-surface acquisition copy goals mode and to *the brand across surfaces* for
the brand-level register mode. Neither variant was deleted; neither won.

| Difference | Classification | Disposition |
| --- | --- | --- |
| Title: "Copy arbitration for per-surface direction" vs "Copy arbitration" | Scope-borne | Scope-neutral title `# Copy arbitration`; the scope now lives in the parameter table, not the title |
| Opening: `copy-direction` omits the worked "Earned authority"/"Warm directness" example | Richer on one side | `tone-of-voice`'s example kept — it is a rule illustration, not a scope claim |
| "whoever is arguing loudest wins, and the copy direction drifts" | Rule present only in `tone-of-voice` | Kept. It is the reason ranking is required |
| "Everything else records the consequences" | Rule present only in `tone-of-voice` | Kept |
| Urgency vs. warmth: surface examples vs brand-posture examples | Scope-borne | Both kept, each labelled by mode. This is a named per-mode clause inside one file, which the criterion permits for a localized difference inside a parameterised body |
| Brevity vs. completeness: same split | Scope-borne | Both kept, each labelled by mode |
| "Brevity and completeness are both legitimate; which wins is a choice, not a quality judgment" | Rule only in `tone-of-voice` | Kept |
| Authority vs. approachability: `tone-of-voice` explains *why* mixed seniority conflicts | Richer on one side | Kept — it is the operative detail |
| Specificity vs. universality: `tone-of-voice` adds "too vague to land" | Richer on one side | Kept |
| Rank step 1: "do its job on this surface" vs "serve this brand's register" | Scope-borne | Parameterised: "do its job for the scope" |
| Rank step 2: "that decision *is* the ranking" | Rule only in `tone-of-voice` | Kept |
| Rank step 3: "surface the gap — one of them is wrong" | Rule only in `tone-of-voice` | Kept |
| Record step: "so the build does not reopen it", "stated as the dominant goal applied", "so a future reader sees the reasoning" | Rules only in `tone-of-voice` | All kept |
| Closing: "not on the direction to re-prove itself" | Rule only in `tone-of-voice` | Kept |
| Whole section: "Adding a new conflict type" (3 steps + rationale) | Present only in `tone-of-voice` | Kept in full. Its one scope-bound phrase, "record it in the doc", became "record it in the document this mode writes" |

**Nothing dropped.** Every heading and every distinctive rule from both variants
is present in the merged body; the only heading not carried is
`copy-direction`'s scope-bound title, which the parameter replaces.

## `interrogation-sequence.md` — pervasive, scope-borne

**Outcome:** one body at `content-design/references/interrogation-sequence.md`
with the same scope-parameter treatment. `creative-direction`'s third variant of
this basename is **not** touched; the spec refuses that edit outright and the
Follow-on records it.

| Difference | Classification | Disposition |
| --- | --- | --- |
| Summary: "a felt copy vibe for a specific surface" vs "a felt copy vibe" | Scope-borne | Parameterised |
| Stage 1's three prompts, each worded per scope | Scope-borne | One prompt each, with both scope forms given inline |
| Stage 2 preamble: "pin down *this* meaning for *this* surface" vs "pin down *this* meaning" | Scope-borne | Parameterised to "for the scope in hand" |
| Register distinction: "Two readings of the same word point at two different directions" | Rule only in `tone-of-voice` | Kept |
| Register distinction: "get wrong on this surface" | Scope-borne | Kept as a per-mode aside |
| Association: "anything where the tone is right" | Richer on one side | Kept |
| Failure mode: "often easier to name than the goal itself" | Rule only in `tone-of-voice` | Kept |
| Stage 3: the "friendly *like a colleague*" worked example | Richer on one side | Kept |
| Stage 3: "Fewer, sharper goals beat more, fuzzier ones" | Rule only in `tone-of-voice` | Kept. "several brands" generalised to "several directions", the one word that was scope-bound |
| Stage 4 bullets: `tone-of-voice` adds "or by expertise shown rather than earned" and the "(too direct)/(too warm)" gloss | Richer on one side | Kept |
| Stage 4 close: "too soft to steer by" | Rule only in `tone-of-voice` | Kept; "on this surface" parameterised to "within the scope" |
| "Handling make it sound like X" heading gains "(example-only users)" | Richer on one side | Kept |
| That section: "copying X whole gives you X's direction, not yours" | Rule only in `tone-of-voice` | Kept |
| Step 2: "The rejected qualities are as load-bearing as the chosen ones" | Rule only in `tone-of-voice` | Kept; the per-surface "wrong for this surface" kept as a per-mode aside |
| Step 3: "with X demoted to one reference among several, not the spec" | Rule only in `tone-of-voice` | Kept |
| "If a user offers several examples, the overlap between them is the signal" | Rule only in `tone-of-voice` | Kept |
| Exit: "Goals that survived their opposite are real" | Rule only in `tone-of-voice` | Kept |

## `editorial-quality-gates.md` — localized, and genuinely three-way

This file existed in three skills, not two. The genre fold relocated
`conversion-design`'s copy to `information-architecture` and pinned it there, so
reconciling only the copy-layer pair would have left a third variant standing.

**The substantive verdict.** The three differed on the gating condition:

- `copy-direction`: "Apply these gates **when the upstream content brief declares
  `communication_mode: product-copy`**."
- `tone-of-voice` and the relocated `information-architecture` copy: "Apply these
  gates **to product-copy mode output**."

**`copy-direction`'s form wins.** It names the actual trigger — a declared field
on the upstream content brief — which `tests/roster/test_content_design_communication_mode_contract.py`
already asserts as a real contract value. "Product-copy mode output" names no
trigger and, after this fold, is actively ambiguous: "mode" now denotes one of
`content-design`'s three modes, so a reader would reasonably apply the gates to
the wrong one. Byte-pinning the surviving pair to the relocated bytes, as the
mechanical path invited, would have silently dropped the upstream condition —
which is the precise rule loss this delivery forbids.

**The other two differences were not substantive.** Both are in the duplication
note, which is removed entirely (below): one copy said the reference is
duplicated *into* `conversion-design`, which the genre fold made false by
deleting that skill; another added "See the pack README."

**The recorded autonomy note is removed from both surviving copies.** All three
carried *"Skill autonomy beats DRY at this scale — each skill stands alone."*
This fold reverses that decision: the two copies are now held byte-identical by
`test_every_editorial_quality_gates_copy_is_byte_identical`, following the
`containment.md` precedent. The note is deleted rather than left to contradict
the test, and `DESIGN.md` records the supersession under T8 — the reference-side
deletion alone would leave the reversal unstated.

Both surviving copies are byte-identical at
`1308734c18d8ec49592408dff5e15e74751645ba8efae2ef0f5900bbcb506f77`.

## Brand-naming convention

**`[example service]` wins; real company names do not survive.**

Measured: `copy-direction` uses the `[example service]` placeholder in 4 places
(`copy-grounding.md` ×2, `interrogation-sequence.md` ×1, `SKILL.md` ×1), while
`tone-of-voice` names real companies in 5 (`copy-grounding.md` ×2,
`interrogation-sequence.md` ×2, `SKILL.md` ×1). `tools/lint-experience-agnostic.py`
checks neither, so nothing else catches a regression here.

The placeholder wins for three reasons. The root `AGENTS.md` security rule
directs generic placeholders in repository artifacts rather than real
identifiers. A named company's register is a moving target: a reader who knows
the brand may take its current copy as normative, and the example silently rots
when that brand changes. And naming vendors cuts against the framework
agnosticism ADR-0024 and RFC-0033 establish for shipped pack content.

No meaning is lost: in every instance the sentence already names the *attribute*
being borrowed, which is the referent the rule is about — the company name was
never load-bearing.
