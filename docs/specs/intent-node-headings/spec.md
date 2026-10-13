# Spec: Intent node headings

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-12 by eugenelim, spec and plan together, after clean spec-mode shaping (round 2) and adversarial (round 2) reviews.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0105, RFC-0108, ADR-0007, ADR-0074
- **Amends:** [intent-navigation](../intent-navigation/spec.md) — the heading its `search` `text` selector matches, which now follows this spec's preamble-bounded rule. It also adds a `heading` field to brief and spec nodes and to `outstanding` items, which no criterion there defined.
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

Every brief and spec in the intent graph carries a human-readable `heading`, taken from its title line by the same rule intents use, so a person or agent can scan open work by name rather than by slug. The bounded query's `outstanding` items and the offline export carry that heading without any extra file read. A spec whose only title is a YAML front-matter `title:` key, 13 of 558 on 2026-10-12, keeps an empty heading.

## What Changes

- `intent_graph.py`'s derivation sets `heading` on brief and spec nodes, as it already does on intent nodes. For all three types, the title is read only from the preamble region the preamble reader already uses: above its `## ` boundary, with HTML comment regions hidden.
- `close-work`'s byte-identical copy of `intent_graph.py` changes in the same commit.
- `navigate_intents.py` adds `heading` to each `outstanding` item, copied from its node.
- The export needs no change of its own: its `nodes` already mirror the derivation.
- Core moves from 3.1.0 to 3.1.1, and `navigate-intents`' evaluations gain a case that names open work by title.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | The query's node and `outstanding` item shapes gain one field, and the `search` heading rule is bounded | `packs/core/.apm/skills/navigate-intents/SKILL.md`: the `outstanding` result paragraph and the `search` `text` comment | `navigate-intents` owner | Both passages name the heading as this spec defines it | Both passages match the derivation |
| Release history | A pack content change | `docs/product/changelog.md`, a free-standing `## [core][3.1.1]` entry with a `### Highlights` decision | Pack release workflow (`packs/AGENTS.local.md`) | Changelog entry naming the field | Entry present at the bumped version |
| Current product truth | The shipped navigator contract's `search` heading rule changes | `docs/specs/intent-navigation/spec.md` header's `Amended in part by:` line, naming this spec for its `search` heading criterion | This spec's implementer | Header line present | Line present when this spec ships |

## Agent Rules

### Always do

- Change both copies of `intent_graph.py` in one commit, and keep them byte-identical.
- Derive the heading from bytes the derivation already reads; add no file read, no new read path, and no new limit.
- Keep the heading raw: whitespace-trimmed text of the title line, with any leading "Spec:", "Brief:" or "Intent:" label kept.

### Ask first

- Changing the `search` operation's scope, or its match rule beyond the heading boundary this spec sets.
- Adding a heading to any query output other than nodes and `outstanding` items.

### Never do

- Strip, rewrite, truncate or normalise heading text in the derivation; display shaping belongs to the view.
- Add a dependency, module, or new script file; the change stays inside the existing scripts.
- Find a heading outside the preamble region the preamble reader uses, or by a second boundary rule of its own.

## Testing Strategy

- **TDD (AC-0001, AC-0002, AC-0003, AC-0004):** The heading rule and the `outstanding` field are pure functions of fixture files, so derivation-level tests decide them; the existing byte-identity assertion in `test_intent_delivery_relations_copies.py` decides the copy.
- **Goal-based check (AC-0005):** A one-line JSON check finds the eval case.

## Acceptance Criteria

- [ ] **AC-0001.** Every brief, spec and intent node carries `heading`. The preamble region is every line before the first line that, with HTML comment regions hidden, starts with `## `, which is the boundary the preamble reader stops at. Within that region, with comment regions hidden, the first line whose whitespace-trimmed form starts with `# ` supplies the heading: the whitespace-trimmed text after `# `, with any leading type label kept.
- [ ] **AC-0002.** A node whose preamble region holds no such line has `heading` equal to the empty string. That includes a file whose only `# ` line is inside an HTML comment or below the boundary.
- [ ] **AC-0003.** Every item in the `outstanding` operation's `placed` and `no_parent` lists carries `heading` equal to its node's `heading`. Over the `mixed` fixture, the outstanding items `brief:bravo-delivery` and `spec:bravo-spec` carry the non-empty headings `Brief: Bravo delivery` and `Spec: Bravo spec`.
- [ ] **AC-0004.** `packs/core/.apm/skills/navigate-intents/scripts/intent_graph.py` and `packs/core/.apm/skills/close-work/scripts/intent_graph.py` are byte-identical.
- [ ] **AC-0005.** `navigate-intents`' `evals/eval_queries.json` holds a `should_trigger: true` case asking for open specs or briefs by title.

## Assumptions

none
