# Catalogue search verb

- **Slug:** `catalogue-search-verb`
- **Status:** Accepted
- **Accepted:** 2026-10-02 by eugenelim, lifecycle owner. Basis: explicit owner direction to de-risk the search verb and apply the needed reviews; the recorded de-risking verdict survived, and intent-mode review of this revision produced no malformed findings. Acceptance frames the product intent only; the pending governing decision record still blocks specification.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **De-risked:** 2026-10-02
- **Shaping-reviewed:** 2026-10-02
- **Decomposed:** no
- **Parent intent:** capability:catalogue-trust-and-adoption
- **Governed by:** pending — a new decision record is required before this intent can produce a specification

## Outcome

- **Input (steerable):** The share of common catalogue-discovery questions that users can answer from the neutral index without opening source manifests or relying on optional descriptive fields.
- **Outcome (lagging):** Catalogue users can find packs, profiles, effects, journeys, and integration relationships through a stable read-only query surface.
- **Guardrail:** Every answer remains inside the neutral index contract, absent optional fields never become hidden prerequisites, and the search surface creates no second discovery schema or source walk.

## Opportunity

Wave 4 provides a deterministic semantic index, but the catalogue does not yet expose a focused query surface that turns those facts into a discovery action.

- **Functional job:** Narrow a catalogue to the packs, profiles, effects, journeys, scopes, or integration relationships relevant to the task at hand.
- **Emotional job:** Trust that a search result reflects the catalogue contract rather than a best-effort scan of uneven prose.
- **Social job:** Point another adopter or reviewer to a reproducible query instead of a hand-curated list.
- **Struggling moment:** The index holds deterministic discovery facts, but users must inspect the whole JSON document or return to source files to answer a focused question.

## Boundary

This intent owns the **find** clause of
[`catalogue-trust-and-adoption`](CAP-0006-catalogue-trust-and-adoption.md): an
outsider can query facts that the generated neutral catalogue index supports.
Every answer must come from that index and remain within its schema. The search
surface must not read `pack.toml`, `JOURNEY.md`, or hand-maintained prose as a
second authority.

The **judge**, **confirm**, **learn**, and **run on** clauses remain with the
other four children named by the parent intent. This intent does not absorb
`adopter-catalogue-test-command` or `catalogue-archive-guide-corpus`, which the
parent records as deliberately unparented.

## Assumptions

- The shipped neutral index remains the authoritative data source for the search surface.
- A conforming index may omit pack descriptions, categories, adapters, content, execution, and documentation, and may omit profile descriptions and pack membership. Useful discovery therefore cannot depend on optional descriptive fields being present.
- The existing index contract is sufficient to expose pack and profile identity, effects, journey states, forward and reverse integrations, and profile membership without adding a second discovery schema.

## Riskiest assumption

**That the existing index can support a useful discovery verb without a schema
change.** The evidence for it is that required pack identity, effects, journey
states, and both integration directions already answer discovery questions no
current command exposes. The evidence against it is that the descriptive fields
a broad text search would usually depend on are optional, as is profile pack
membership.

Test this before specification by running the candidate discovery questions
against conforming indexes with every optional field absent. If the remaining
required facts cannot produce useful answers, return to the decision record and
revise this intent's boundary rather than letting the specification add fields
silently.

## De-risking verdict

- **Reversibility:** two-way door. A prototype can query the shipped index without publishing the eventual CLI or compatibility contract.
- **Prototype approach:** `prototype-led`; the shipped schema and Wave 4 fixture are the smallest honest prototype of the information surface.
- **What would have to be true:** Required index fields alone can answer several useful discovery questions even when every optional descriptive field is absent.
- **Kill condition (predeclared 2026-10-02):** Kill the current boundary if fewer than 4 of these 5 questions are answerable and discriminating from required fields alone: exact pack or profile identity, repository versus user scope, effect kind, journey start or end state, and forward or reverse integration relationship.
- **Probe:** Compare the five questions with the public `catalogue-index.schema.json` required fields and the shipped two-pack Wave 4 fixture and generator tests at revision `2f33168e489345e386977012d553f26b26cdaa8f`, treating every optional field as absent.
- **Result:** Exact identity, scope, effect kind, journey state, and integration relationship are all represented by required fields; the fixture exercises the latter three and the generator sorts identities deterministically. All 5 questions survive without descriptions, categories, adapters, content inventory, execution metadata, documentation links, or profile membership. The kill condition did not fire.
- **Verdict:** **Survived, desk-grounded.** The existing schema can support a bounded discovery prototype without adding fields. Whether users find those five questions useful remains `to-validate` before the decision record fixes the public surface.

```yaml
validation_hook:
  assumption: Catalogue users value bounded factual filtering over required index fields even when descriptive text search is unavailable.
  kill_condition: Fewer than 4 of 5 target users complete at least 4 of the 5 discovery tasks unaided on a prototype backed only by required index fields.
  activity: Give catalogue maintainers, platform engineers, and adopters a realistic neutral index with all optional fields removed and observe task completion, wrong answers, and requests for unavailable descriptive search.
```

## What the decision requires

The new decision record must:

- define the public CLI surface, query model, matching semantics, result ordering, output contract, and error behavior;
- state how searches over optional fields behave when those fields are absent, without making optional descriptions, categories, adapters, or profile membership prerequisites for a useful result;
- decide whether a query reads a committed `catalogue-index.json` or regenerates the index in memory, accounting for stale committed data and the cost of a full catalogue walk;
- bound the answerable discovery actions to facts already present in the index, including pack and profile identity, effect kinds, journey start and end states, forward and reverse integrations, and profile membership;
- place the read-only verb coherently beside `catalogue index` and `catalogue contracts`, including the catalogue-root and human/JSON output conventions, without assuming the current commands use one uniform argument shape; and
- define compatibility and test evidence for the public command before a specification fixes implementation details.

## Non-goals

- Adding fields to `catalogue-index.json` or introducing another public discovery format.
- Searching source manifests, journey files, or author-maintained prose directly.
- Defining flag names, query syntax, exact versus substring or fuzzy matching, ranking, or an output shape in this intent.
- Taking ownership of catalogue evaluation, release integrity, authoring documentation, migration closeout, adopter test execution, or the archive-guide corpus.
- Producing an implementation specification before the governing decision record is accepted.

## Current state — checked 2026-11-05

`agentbundle catalogue --help` lists ten verbs (lint, verify, build, self-host, package, sync-defaults, init, sync, index, contracts) and no search verb. `agentbundle catalogue index .` on this repository yields 23 packs and 3 profiles. The five questions are answerable from required fields, but not equally on the real data: scope splits 14 user to 9 repo, journeys are present for 15 packs, integrations for 5, and `effects` is empty for all 23. Effect kind therefore discriminates only where authors declare effects, so the verb reports an empty result as "none declared", not as "no match". Four of five questions still discriminate, so the kill condition does not fire.

## Resolved questions — recommended answers, pending the decision record

- **Governing record:** a short ADR written first, then one feature spec.
- **Source of truth:** regenerate the index in memory for each query. A committed `catalogue-index.json` can be stale, and the intent forbids a second schema. Accept an explicit `--index <file>` for a pre-built file.
- **Searchable facts and combination:** exact match on identity, scope, effect kind, journey start or end state, and integration direction. Several filters combine with AND, and results sort by identity.
- **Output and errors:** a human table and `--json`, with distinct exit codes for no match, invalid query, unreadable index, and index-generation failure.

## Projection

After the new decision record is accepted, this intent projects to one focused
feature specification for the read-only catalogue search surface. It does not
project to implementation while `Governed by:` remains pending.

## Decomposition

None yet. After the governing decision is accepted, this feature intent projects to one focused search specification.

## Readiness

- **Route:** an ADR first, then new-spec. The `packages/agentbundle/**` change needs an `Engine-Change-RFC:` trailer; cite the new ADR in it. The gate (`tools/lint-catalogue-curation-guard.py`) checks only that the trailer is present, and recent commits cite an accepted record or write `n/a` with the reason, so no new RFC is needed.
- **First slice, one session:** write the ADR from the answers above.
- **Second slice, one session:** the read-only verb over the in-memory index.
- **Agent-only proof:** tests run each of the five questions against indexes with every optional field removed and against a fixture that carries effects, journeys and integrations; each exit code has a case; a run against this repository's catalogue passes.
- **Manual follow-up, not blocking:** the five-task user test named in the validation hook, run after release.
- **Size:** M.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 2f33168e489345e386977012d553f26b26cdaa8f
