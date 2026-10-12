# Spec: Related intents field

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-10 by eugenelim, spec and plan together, after clean spec-mode shaping (round 4) and adversarial (round 6) reviews with every sustained finding repaired (reports under `.context/reviews/7f4ee554-13ab-4692-8c7e-5cfd7fab5e58/`).
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0105, RFC-0103, ADR-0007, ADR-0074
- **Brief:** brief:intent-navigation-delivery
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A maintainer or agent relates two intents by writing one `Related intents:` line on one of them, and `navigate-intents` shows that relation from both intents in `record` and `tree`, never as a parent, a dependency, or an ordering. The intent corpus lint refuses any value that is not a typed intent reference, names no intent the navigator admits with the stated kind, or names the intent itself, so in a lint-clean corpus every related edge the navigator shows is resolved.

## What Changes

- New optional intent preamble field `Related intents:` — its one-file shape rule and its corpus resolution rule in `packs/core/.apm/skills/work-intake/scripts/intent_shape.py`, run by `intent_corpus_lint.py`, which resolves a target only among the intent files the navigator admits.
- The intent-edge derivation reads the field into related edges — both byte-identical copies of `intent_graph.py` (`navigate-intents/scripts/`, `close-work/scripts/`).
- `record` and `tree` (JSON and text) show related edges from both ends, and `summary` counts refused ones — `navigate-intents/scripts/navigate_intents.py`.
- The closed set of refused-edge states gains `self_reference`, used only by this field.
- The `frame-intent` template lists the field — `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md`.
- Reference and how-to rows for the field and its refusals — `guides/product-engineering/` and `guides/core/how-to/navigate-intents.md`.
- The navigator contract [`intent-navigation`](../intent-navigation/spec.md) is amended in part by this spec, in its criteria 0003, 0007, 0016, 0017, 0071, 0072, and 0076, recorded on that spec's header.
- Delivered through the `feature/intent-navigation` integration branch, inside its single `core` 3.1.0 release; `product-engineering` releases 0.13.25.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Authoring template | Delivery decision 4 lists the field in the template | `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md`; the preamble mirrors in `guides/product-engineering/how-to/frame-the-intent.md` and `guides/product-engineering/how-to/hand-it-to-build.md` (whole-block refresh, so every block marked as a mirror of the template lists the same fields) | `product-engineering` maintainer | AC-0018's test, which reads all three blocks; guide lints | All three blocks list the field with a comment-only value naming its typed form |
| User reference | A new field with a value rule and a corpus rule | `guides/product-engineering/reference/intent-fields-and-modes.md` § Intent fields | `product-engineering` maintainer | AC-0019's test; guide lints | Row states the typed form, the four prefixes, one-sided writing, and both corpus rules |
| User procedure — lint refusals | New refusal messages a writer can meet | `guides/product-engineering/how-to/fix-a-refused-intent.md`, a new section beside the supersession sections | `product-engineering` maintainer | Guide passes `tools/lint-guide-titles.py`, `tools/validate_guides.py`, and `tools/lint-guides-no-repo-only-refs.py` | Section lists each refusal with its message and remedy |
| User procedure — navigation | Related edges appear in query and tree output | `guides/core/how-to/navigate-intents.md` (refused-edge table gains `self_reference`; a related-edges section; the text-line formats) | `core` maintainer | Same guide lints | Guide names both lists, both text lines, and that related edges never place or order anything |
| Skill instructions | The skill's output description changes | `packs/core/.apm/skills/navigate-intents/SKILL.md` § How to run | `core` maintainer | Self-host re-run leaves no diff | `record` and `tree` descriptions name the related lists |
| Architecture | The derivation admits a new field | `packs/core/DESIGN.md` § Intent-edge derivation | `core` maintainer | Section diff | Admitted fields include `Related intents:`, with the rule that no reconciler reads it |
| Historical contract pointer | The navigator contract is amended in part | `docs/specs/intent-navigation/spec.md` header line `Amended in part by:` | `core` maintainer | Header present | Line names this spec and the seven criteria |
| Release history | A `core` and a `product-engineering` behaviour change | `docs/product/changelog.md`: bullets inside `[core][3.1.0]`, including `### Highlights`; a new `[product-engineering][0.13.25]` entry; `packs/product-engineering/pack.toml` and `.claude-plugin/plugin.json` read `0.13.25`; `core` stays `3.1.0` | Pack maintainers | Version test and `/now/` projection test green | Both entries name the field |
| Evaluation harness | `packs/AGENTS.md` asks a non-cosmetic pack change to update its harness | `navigate-intents/evals/eval_queries.json` gains a related-intents positive prompt; `frame-intent/evals/evals.json` gains a case for the template's optional `Related intents:` line, on the pattern of its `Outcome co-owner:` case | `core` and `product-engineering` maintainers | File diffs | Prompt and case present; no activation or eval run is claimed |
| Executable proof | Contract tests | `packs/core/tests/skills/work-intake/`, `packs/core/tests/skills/navigate-intents/`, `packs/core/tests/skills/close-work/`, `tests/roster/test_intent_template_shape_conformance.py`, `tests/roster/test_intent_field_reference_parity.py` | `core` maintainer | Dispatched `build-check`, `test-corpus`, and `test-roster` runs green on the pull request's last commit before its ledger-only record commit, with run ids in that record | Every criterion's named test is green |
| Verification record | CI run ids and the real-corpus lint result | `docs/specs/related-intents-field/notes/verification-ledger.md` (repository-durable) | Implementer | Ledger entries | Ledger present and cited by the closing PR |

## Agent Rules

### Always do

- Read `Related intents:` only from an intent's preamble, through the derivation's existing confined read.
- Keep the two copies of `intent_graph.py` byte-identical; make every derivation change in both.
- Show every related edge, resolved or refused, with its basis and trust class.
- Fold this slice's `core` changelog bullets into `[core][3.1.0]`, and leave `core` at 3.1.0.
- Merge to `feature/intent-navigation`, not to the default branch.

### Ask first

- Any change to how `Parent intent:`, `Brief:`, or `Discovery:` edges resolve, or to the refused-edge states they can take.
- Any reader other than the derivation, the navigator, and the corpus lint consuming the field.
- Adding the field to any artifact type other than an intent, or to any writer other than the `frame-intent` template.

### Never do

- Never let a related edge become a parent, a child, an ancestor, a cycle member, a placement, or an ordering or blocking input.
- Never read `Related intents:` in `close-work`'s closure code, the delivery resolver, `lint-traceability.py`, `loop-cohort.py`, or `workspace-status`.
- Never accept a bare slug, a repository path, or a markdown link as a related target.
- Never add a runtime dependency outside the Python standard library, a new module, or a new query operation.

## Testing Strategy

- **TDD (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0007, AC-0008, AC-0009, AC-0010, AC-0021, AC-0022, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0017):** Contract tests over temporary fixture corpora drive the corpus lint and the navigator's query entry point, one fixture per accepted form and per refusal, because each is an invariant over constructed inputs.
- **TDD across two components (AC-0006):** One fixture set runs through both the lint and the navigator, because the guarantee is an agreement between them that neither suite alone can observe.
- **Goal-based check (AC-0016, AC-0018, AC-0019, AC-0020):** A source scan, a template line read, the existing guide-parity test, and the existing byte-identity test. Each is a property of files, so a fixture would add nothing.

## Acceptance Criteria

### Field shape and corpus rules

- [x] **AC-0001.** `intent_corpus_lint.py` reports a violation naming the field `Related intents` for a live intent whose value, after one trailing HTML comment and one pair of backticks around the whole value are stripped, is not empty and is neither of these: a value that AC-0007 reads as no relation; or a comma-separated list whose every item, trimmed of spaces, is `<kind>:<slug>` with `<kind>` one of `intent`, `capability`, `outcome`, or `opportunity` and `<slug>` matching `^[a-z0-9]+(?:-[a-z0-9]+)*$`, with no empty item and no item repeated. Fixtures for a bare slug, a repository path, a markdown link, a `brief:` item, a `spec:` item, an unknown prefix, an uppercase slug, a trailing comma, a repeated item, and items each wrapped in their own backticks each make the lint exit 1; a list using all four prefixes, and a value that is only an HTML comment, each exit 0.
- [x] **AC-0002.** The lint reports a violation naming `Related intents` and the item for an item whose slug names no single live intent the navigator admits: a non-tombstone file directly in the linted directory whose name matches `^[A-Za-z0-9][A-Za-z0-9._-]*\.md$`. Fixtures for a slug no file carries, a slug only a tombstone carries, a slug only a file in a subdirectory carries, and a slug two admitted live intents carry each make the lint exit 1.
- [x] **AC-0003.** The lint reports a violation naming `Related intents` and the item for an item whose prefix differs from the target's kind, where the target's kind is decided from its preamble by the node-id rule in [`intent-navigation`](../intent-navigation/spec.md) criterion 0004.
- [x] **AC-0004.** The lint reports a violation naming `Related intents` and the item for an item whose slug is the intent's own `Slug:`, whichever of the four kinds prefixes it.
- [x] **AC-0005.** A target's `Status:` never decides resolution: fixtures whose target is `Superseded`, `Withdrawn`, `Cancelled`, and `Fulfilled` each make the lint exit 0.
- [x] **AC-0006.** The lint and the navigator agree on this field. Over a fixture corpus that the lint passes and that carries all four prefixes, with targets whose `Level:` values are written in mixed letter case and followed by ` (` or ` →`, and whose `Kind:` values sit beside a comment or inside backticks, and with one source whose whole value is wrapped in backticks and followed by a comment and another whose value is `None — later`, the navigator returns every `Related intents` edge resolved and none from the second source. For each refusal state AC-0008 or AC-0021 lets the navigator return for this field, a fixture producing that state makes the lint exit 1.

### Derivation

- [x] **AC-0007.** An intent's `Related intents:` value is read after the stripping AC-0001 states, and produces one edge from that intent for each distinct non-empty item, split on `,` and trimmed. An empty value, or one whose first whitespace-separated word is `none` in any letter case, is no relation and produces no edge. This amends `intent-navigation` criterion 0003, which otherwise holds.
- [x] **AC-0021.** When the field appears more than once in an intent's preamble and two or more distinct values remain after the values AC-0007 reads as no relation are dropped, the intent has exactly one related edge: a `multiple_values` refusal whose `basis.values` lists those remaining values. When one distinct value remains, it is read under AC-0007.
- [x] **AC-0022.** No brief, spec, or tombstone produces a related edge, whatever its preamble carries.
- [x] **AC-0008.** An intent-kind reference is an item `<kind>:<slug>` whose kind is one of the four intent kinds and whose slug matches `^[a-z0-9]+(?:-[a-z0-9]+)*$`. Such an item resolves when its slug names a live intent whose node id equals the item. Otherwise each item's edge is refused with exactly one state, checked in this order:
      - `self_reference` — an intent-kind reference whose slug is the intent's own slug;
      - `kind_mismatch` — an intent-kind reference whose slug names a live intent with a different node id;
      - `retired_target` — an intent-kind reference whose slug names only a tombstone, with its `Reissued as:` value shown and never followed;
      - `dangling` — an intent-kind reference whose slug names nothing;
      - `out_of_type` — a `brief:` item whose remainder matches the slug pattern, or a `spec:` item whose remainder is a valid spec directory name;
      - `unparseable` — any other item, including a known prefix with a malformed remainder such as `intent:Foo` or `brief:Bad_Slug`, a bare slug, a path, a markdown link, and an unknown prefix.
      `self_reference` joins the closed set in `intent-navigation` criterion 0007 and applies to no other field. Each edge's `basis.form` follows that spec's criterion 0071.
- [x] **AC-0009.** Every related edge, resolved or refused, carries `field` and `basis.field` `Related intents` and trust class `pointer_checked`. This amends `intent-navigation` criterion 0071 for this field only.
- [x] **AC-0010.** Related edges change no parent edge, child list, ancestor chain, cycle refusal, forest root, outstanding set, or placement. A fixture corpus with a mutual pair and a three-intent loop of related edges, and the same corpus with every `Related intents:` line removed, give byte-identical results once `provenance.generated_at` is removed for `outstanding`, for `ancestors` and `record` on every intent, for `search` with no selector, and for whole-forest `tree` JSON, with the two related lists removed from `record` and `tree`. No related edge in the loop is refused as `cycle`.

### Query surface

- [x] **AC-0011.** `record --id <identity>` returns `related_written_here`, every related edge from that intent, resolved or refused, in the order its items appear in the value; and `related_written_elsewhere`, every resolved related edge whose target is that intent, ordered by source node id in code-point order. A refused edge from another intent appears in neither list of the intent it fails to name. This amends `intent-navigation` criterion 0072.
- [x] **AC-0012.** Each intent in a `tree` JSON result carries the two lists of AC-0011. `search` and `ancestors` results carry neither. This amends `intent-navigation` criterion 0076.
- [x] **AC-0013.** Each entry in either list counts as one edge toward `intent-navigation` criterion 0016 limit of 400 edges, so an edge that appears under both of its intents counts twice. A `tree` JSON fixture with at most 200 intents and at most 400 parent, delivery, and refused parent edges, whose related entries take the count above 400, returns `result_too_large` naming the edge limit and the observed count including related entries. This amends `intent-navigation` criterion 0016.
- [x] **AC-0014.** In `tree --format text`, after an intent's line and any refused-parent line, and before its first child intent's line, each `related_written_here` edge prints one depth level deeper as `~ related <target node id>` when resolved, or `! refused related <state>` when refused; then each `related_written_elsewhere` edge prints at the same depth as the `related_written_here` lines, one level deeper than the intent's line, as `~ related from <source node id>`. Every field is escaped as `intent-navigation` criterion 0017 states. This amends that criterion.
- [x] **AC-0015.** `summary`'s refused-edge counts by state include refused related edges, with `self_reference` counted under its own key.

### No reconciler reads the field

- [x] **AC-0016.** Across every `.py` file under `packs/core/.apm/`, the literal `Related intents` appears only in `navigate-intents/scripts/intent_graph.py`, `close-work/scripts/intent_graph.py`, `navigate-intents/scripts/navigate_intents.py`, and `work-intake/scripts/intent_shape.py`. A scan that plants the literal in another file under a temporary copy reports it.
- [x] **AC-0017.** A `close-work` closure decision over a `children` closure whose descendants are all terminal returns `ClosureEligible`, reached through the descendant walk rather than a precondition refusal, both for a fixture corpus whose intents carry related edges and for the same corpus with every `Related intents:` line removed. The related edges include a resolved edge to a non-terminal intent outside the closure, a `self_reference`, and a `dangling` edge.

### Template, reference, and copies

- [x] **AC-0018.** The `frame-intent` template's preamble, and every guide preamble block marked as a mirror of that template, lists `- **Related intents:**` directly after `- **Outcome co-owner:**`, with a value that is only an HTML comment, and the resolved template still passes the live-intent and corpus-scoped rules.
- [x] **AC-0019.** `guides/product-engineering/reference/intent-fields-and-modes.md` lists `Related intents` with the tier `constrained when present`, checked by the guide-to-validator parity test.
- [x] **AC-0020.** `close-work/scripts/intent_graph.py` stays byte-identical to `navigate-intents/scripts/intent_graph.py`, checked by the test that pins the skills' copies.

## Follow-ons

none

## Assumptions

none
