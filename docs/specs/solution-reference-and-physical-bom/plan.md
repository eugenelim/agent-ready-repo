# Plan: solution-reference-and-physical-bom

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (patch bump, eval harness update, portable shipped content, self-host); analogous change: `docs/specs/architect-diagram-drawio-export/` (a new reference and assets plus evals in one architect skill); existing suites `packs/architect/tests/skills/architect-design/test_shaping_reach.py`, `packs/product-engineering/tests/pack/test_architect_optional_offers.py`, `packs/product-engineering/tests/pack/test_intent_skill_structure.py`. Deviation: none.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md`. A genuine artifact error
> follows the controlled-amendment path.

## Approach

This is a prose change to six skills in two packs, plus two templates, one
reference and one asset. The pinned tests are extended first in each task, so
every new rule has a phrase test before the prose grows. The riskiest part is
the narrowed reference-architecture rule. Four surfaces state the old rule
(skill step 2, `DESIGN.md`, `README.md`, the `pack.toml` integration), and all
four move in one task. Guides and release surfaces follow the skill text.

## Constraints

- `packs/AGENTS.md`: patch bump per changed pack; a non-cosmetic pack change updates its eval harness; shipped pack content cites no internal records; run self-host after `.apm/` edits.
- `test_architect_optional_offers.py`: every product-engineering architect offer carries the roster check and the exact silent clause; no "install architect" phrase anywhere under `.apm/`.
- `test_intent_skill_structure.py`: the longer route's numbered names must equal `frame-situation`'s six-step sequence; `(separate skill)` appears five times in the longer route.
- `guides/AGENTS.md`: job-page rules for the new how-to (one opening sentence, verb-phrase H2s, 150–400 words, states needed packs).
- Changelog fragments via `tools/changelog.py new` (run with Python 3.13; system `python3` is 3.9 and lacks `tomllib`).

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none. Agent behaviour is advisory; the eval cases are frozen for a judge, and no run gates this spec.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise — guides + READMEs | T5 | Guide validators pass | Guides match shipped skills |
| Current product truth — skills, assets, reference | T1–T4 | Pinned tests, evals, catalogue lint | AC-0001 to AC-0011 and AC-0013 to AC-0015 checked |
| Decision rationale — architect `DESIGN.md` | T3 | `test_shaping_reach.py` | AC-0003 checked |
| Release history — fragments | T6 | Changelog validator, catalogue verify | AC-0012 checked |

## Design (LLD)

### Design decisions

Owned by: T1, T2, T3, T4

- **Brief owners sentence.** The fixed wording is "Never produce a brief: `lean-canvas` writes the one-page initiative brief and `author-delivery-brief` owns the delivery brief." "Owns" covers the brief `intent decompose` emits for `author-delivery-brief continue`'s gate. Each skill puts it in its anti-pattern list, replacing the old "`place-bet` + `author-delivery-brief create`" clause. For `place-bet`, it replaces the bare "Never produce a brief." Traces to: AC-0009.
- **Longer-route continuation.** It is an unnumbered paragraph under the six numbered steps, so the shaping sequence and its tests keep six steps. Its content: "Then `decompose` (intent mode) takes `capability-map.md` as input." Each Build capability becomes one capability-level child intent (`Level: capability`, `Parent intent:` the de-risked intent, carrying the capability id). Buy, Partner and Adopt capabilities stay as dependencies that children name. Each child runs `intent frame` → `intent de-risk` → `intent decompose`, as on the short route. The parent is the intent the longer route de-risked at step 4. The paragraph contains no numbered item and no `(separate skill)` marker, so the six numbered names and the five-marker count stay unchanged. Traces to: AC-0008.
- **Next-step section.** `map-capabilities`'s conditional "Next step readiness" section becomes an unconditional `## Next step` in the template and examples that names `intent decompose` on the capability map, since `intent` ships in the same pack. `SKILL.md` step 5 drops its "when not detected" clause and says the emitted map always ends with that `## Next step` section. Traces to: AC-0008.
- **`decompose.md` orientation line.** It drops "the longer route ends at `map-capabilities` and does not use it" for "on the longer route it follows `map-capabilities`, taking `capability-map.md` as input". The test's else-branch, which requires "does not use it", gets a `decompose` exception that asserts the new phrase. Traces to: AC-0008.
- **Hard limits home.** `align-value-stream/assets/hard-limits.md` is the single home of the wording. Step 1 shows it as a proposed `## Hard limits` README section. The skill writes it only on confirmation, under the skill's existing path rules. It never overwrites an existing section without acceptance. The skill's "Hard limits — state them honestly" section points to the asset rather than repeating the list. Traces to: AC-0007.
- **Solution reference mode.** This is a separate `## Solution reference mode` section, not one of the three design altitudes. A reference is not a choice between options, so the real-choice check and Stage 0 do not apply. It reuses procedure step 2's grounding rules and step 8's save modes, with the role `current-architecture`. Inputs are the federated catalog (`catalog-info.yaml` Domain → System → Component → API), contract homes, decisions, and links to each component repo's `reference.md`. All inputs are treated as data. The mode asks for any missing component or boundary rather than inventing one. Each template section is proposed for accept / edit / decline, and the mode never overwrites an existing source without per-file acceptance. `Coordination constraints` gives each hard limit's consequence for the architecture (independent deploys mean backward-compatible contracts and expand-then-contract changes). It does not restate the limits as a list. Traces to: AC-0001, AC-0002.
- **Rule narrowing.** Step 2 reads: "Never draft or write a single codebase's reference architecture inside this skill; for a coordinating repo with no app code, use § Solution reference mode." The `core-reference-architecture-handoff` purpose changes "never drafts it" to "never drafts a single codebase's golden path". `DESIGN.md` § Reference architecture and the README's "What if I have no reference architecture?" answer name the new mode. Traces to: AC-0003.
- **Physical architecture and BOM.** It is offered once, at the end of step 7, before the step-9 decision prompt, at every altitude. A direct request on an existing design also enters it. A design with no deployment model gets a "write the design first" answer rather than invented units. The output is a sibling `physical-architecture.md` in the same per-effort folder, saved through step 8's modes. Prices are grounded the way platform contracts already are in step 2: a curated platform skill, then the provider's official pricing page or calculator, then `desk-research`. Currency is USD unless the user names one. A design with no provider still gets a physical topology at the provider-class level, with every line `unpriced`. A physical choice that contradicts the design is raised as a design finding, never silently changed. The architecture-change altitude gets a delta BOM, with a `Change` value (add / remove / resize) and a net monthly change. The sequence is offer, then draft, then one step-8 save. If the design is not saved yet, one confirmation covers both files; if it is already saved, the BOM is saved on its own. Traces to: AC-0004, AC-0005, AC-0013, AC-0014, AC-0015.
- **BOM line identity.** `Kind` is one of `cloud service`, `container image`, `open-source library`, `hardware`, `network connection` or `licence`; the identifier each takes is the one AC-0013 lists. An image's `@sha256:<digest>` appears only when a registry listing, lock file or deployment manifest shows it; an unpublished image gets the visible placeholder `<registry>/<repository>:<tag>` and a note naming who publishes it. An open-source library is written as a purl (for example `pkg:pypi/<name>@<version>`) with its SPDX licence id, read from the lock file or manifest; a free library is `no direct cost` with its SPDX id as the reason, and a paid support subscription for it is its own `licence` line. `Identifier` says what the item is and `Tier / size` how big, split as AC-0013 states. `Price status` is `priced` (cited source, date and region), `unpriced` (a cost exists but is not grounded; counted and left out of the total) or `no direct cost` (an image whose cost the line that runs it carries, named on the line; or a free-to-use item such as an open-source library, with the reason stated). Traces to: AC-0004, AC-0005, AC-0013, AC-0014, AC-0015.
- **Rejected:** a new `architect-reference` skill (Never-do: no new skill); BOM price arithmetic in a script (one obvious rule in prose meets the need; no new script); renumbering the shaping sequence to seven steps (touches about ten surfaces across four packs for no behaviour gain; Ask-first).

## Tasks

### T1: Longer-route continuation and one brief-owner sentence

- **Spec:** AC-0008, AC-0009
- **Mode:** TDD
- **Depends on:** none
- **Touches:** `packs/product-engineering/.apm/skills/{intent/SKILL.md,intent/references/decompose.md,intent/references/frame.md,map-capabilities/SKILL.md,map-capabilities/assets/capability-map-template.md,map-capabilities/examples/acme-crm/capability-map.md,map-capabilities/examples/bloom-marketplace/capability-map.md,frame-situation/SKILL.md,identify-opportunities/SKILL.md,diverge-solutions/SKILL.md,place-bet/SKILL.md}`, `packs/product-engineering/tests/pack/test_intent_skill_structure.py`, new `packs/product-engineering/tests/pack/test_brief_owner_sentence.py`, intent and map-capabilities evals
- **Tests:**
  - `test_intent_skill_structure.py`: the existing six-name and five-marker assertions stay unchanged; the longer-route section contains `capability-map.md`, "`decompose` (intent mode)" and "capability-level child intent"; the orientation test's else-branch exempts `decompose` and asserts "follows `map-capabilities`".
  - `test_brief_owner_sentence.py`: the five SKILL.md files each contain the fixed sentence (whitespace-collapsed); a whitespace-collapsed walk over every file under `packs/product-engineering/.apm/` finds neither retired clause AC-0009 names; a mutation that re-adds the old clause to one file is reported.
  - The same new suite asserts the AC-0008 next-step clauses over `map-capabilities/SKILL.md`, the template and every `examples/*/capability-map.md` (globbed, so a new example is covered), reading only `SKILL.md` step 5 and each map's `## Next step` section, so the AC-0009 brief-owner sentence elsewhere in `SKILL.md` does not trip the negative check.
  - `frame.md`'s orientation line keeps the "does not use it" substring the structure test requires for a mode outside the numbered longer route, and adds the child-intent clause, for example: "the longer route opens with `frame-situation` and does not use it until `intent decompose` hands it a child intent".
- **Done when:** the Tests bullets pass under `pytest packs/product-engineering/tests -q`.

### T2: Hard-limits asset and the solution-reference offer in align-value-stream

- **Spec:** AC-0006, AC-0007
- **Mode:** TDD
- **Depends on:** none
- **Touches:** `align-value-stream/SKILL.md`, new `align-value-stream/assets/hard-limits.md`, `align-value-stream/evals/evals.json`, `packs/product-engineering/pack.toml`, `test_architect_optional_offers.py`, new `packs/product-engineering/tests/pack/test_align_value_stream_hard_limits.py`
- **Tests:**
  - `OFFER_FILES` gains `"align-value-stream"`, so the existing silent-clause test covers the new offer paragraph.
  - The manifest test asserts an architect integration whose `consumers` include `skill:align-value-stream`.
  - `test_align_value_stream_hard_limits.py`: the asset names the three limits; step 1 names `assets/hard-limits.md`, "README" and confirmation before writing.
- **Done when:** the Tests bullets pass under `pytest packs/product-engineering/tests -q`.

### T3: Solution reference mode and the narrowed rule

- **Spec:** AC-0001, AC-0002, AC-0003
- **Mode:** TDD
- **Depends on:** none
- **Touches:** `architect-design/SKILL.md` (step 2 and the new section), new `architect-design/assets/solution-reference.md`, `packs/architect/{DESIGN.md,README.md,pack.toml}`, `test_shaping_reach.py`
- **Tests:**
  - `test_shaping_reach.py`: step-2 test adds "single codebase"; a new test pins the `## Solution reference mode` phrases; a new test parses the template's H2 order and its two `mermaid` blocks; the manifest test asserts "single codebase" in `purpose`; the DESIGN.md test asserts "Solution reference mode" or "solution reference mode".
- **Done when:** the Tests bullets pass under `pytest packs/architect/tests -q`.

### T4: Physical architecture and BOM offer

- **Spec:** AC-0004, AC-0005, AC-0013, AC-0014, AC-0015
- **Mode:** TDD
- **Depends on:** T3
- **Touches:** `architect-design/SKILL.md` (step 7), new `references/physical-bom.md`, new `assets/physical-architecture-bom.md`, new `packs/architect/tests/skills/architect-design/test_physical_bom.py`
- **Tests:**
  - `test_physical_bom.py`: step 7 names `references/physical-bom.md`; the reference carries the rule phrases AC-0004, AC-0013, AC-0014 and AC-0015 list, one test per criterion; the asset's BOM header row equals the AC-0005 column list, and the asset has a topology table, a `mermaid` block and the totals phrases; a mutation that drops `unpriced` is reported.
- **Done when:** the Tests bullets pass under `pytest packs/architect/tests -q`.

### T5: Evals and guides

- **Spec:** AC-0010, AC-0011
- **Mode:** TDD (eval inventory), goal-based check (guides, lint)
- **Depends on:** T1, T2, T3, T4
- **Touches:** `architect-design/evals/{evals.json,eval_queries.json}`, `align-value-stream/evals/evals.json`, new `packs/architect/tests/skills/architect-design/test_new_mode_evals.py`, `packs/product-engineering/tests/pack/test_align_value_stream_hard_limits.py` (eval-id assertions), `guides/architect/how-to/establish-reference-architecture.md`, new `guides/architect/how-to/get-a-physical-architecture-and-bom.md`, `guides/architect/README.md`, `guides/product-engineering/how-to/{map-capabilities.md,run-a-capability-across-a-value-stream.md}`, `guides/product-engineering/explanation/the-intent-tree.md`, `guides/_shared/reference/detailed-operating-model.md`, `docs/architecture/lifecycle-flow.md`, `guides/core/explanation/role-journeys.md`, both pack READMEs
- **Tests:**
  - `test_new_mode_evals.py` and the align-value-stream suite load each evals file and assert the AC-0010 ids, at least three assertions per case, and the "Does not mention" assertion, following the pattern of `test_architect_optional_offers.py::test_eval_ids_and_silent_assertions`; the architect suite also asserts the AC-0011 trigger queries.
  - Goal-based: `agentbundle catalogue lint --root . --deep` exits 0; the guide validators pass; `git grep -n "ends at \`map-capabilities\`"` over `guides/`, `docs/architecture/` and `packs/` returns nothing, and every longer-route listing in the touched guides names the `intent decompose` continuation.
- **Done when:** the Tests checks pass.

### T6: Release surfaces

- **Spec:** AC-0012
- **Mode:** goal-based check
- **Depends on:** T5
- **Touches:** both packs' `pack.toml` and `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, two `docs/product/changelog.d/` fragments, self-host projections
- **Tests:** no stub (goal-based).
  - `agentbundle catalogue self-host --root . --write`, then `agentbundle catalogue verify --root .`; the changelog validator accepts both fragments.
  - Base comparison: for `architect` and `product-engineering`, read `version` from `git show $(git merge-base HEAD origin/main):packs/<pack>/pack.toml` and assert the branch's `pack.toml`, `plugin.json` and marketplace entry all equal that version with the patch part plus one.
- **Done when:** the Tests checks exit 0 and `git status` shows only intended files.

## Changelog

- 2026-10-20: spec approved by eugenelim
- 2026-10-20: plan approved by eugenelim
- 2026-10-20: amended spec approved by eugenelim
- 2026-10-20: amended plan approved by eugenelim
