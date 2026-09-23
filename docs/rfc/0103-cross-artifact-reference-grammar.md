# RFC-0103: Pointer grammar update — `<kind>:<slug>` for `Parent intent:` and `Brief:`, and `intent:` as a node kind

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-09-22
- **Date closed:** 2026-09-22
- **Decision weight:** standard
- **Related:** [ADR-0033](../adr/0033-intent-level-open-recognized-set-decoupled-from-scale.md), [ADR-0108](../adr/0108-opaque-append-only-loop-contract-identifiers.md), [ADR-0112](../adr/0112-index-tables-are-generated-or-absent.md), [`docs/specs/intent-reference-grammar-migration/`](../specs/intent-reference-grammar-migration/), [`guides/core/reference/product-brief-fields.md`](../../guides/core/reference/product-brief-fields.md)

## What this is about, for a reader arriving cold

Repository artifacts are Markdown files with a metadata preamble of
`- **Field:** value` lines. Four of those fields point from one artifact to
another, and a check called the *traceability graph* walks them.

| Field | Sits on | Points at |
| --- | --- | --- |
| `Parent intent:` | a brief or an intent file | the intent it descends from |
| `Brief:` | a spec | the product brief it was derived from |
| `Contract:` | a spec | the interface contract it implements |
| `Discovery:` | a spec | the upstream research or intent it came from |

Each pointer is written today in one of three shapes — a bare slug
(`payment-retries`), a repository-relative path
(`docs/product/briefs/payment-retries.md`), or a typed id
(`brief:payment-retries`). This record proposes the typed shape as canonical
for the first two fields, and leaves the other two alone.

A few terms recur. A **node** is an artifact the graph recognizes; its **kind**
is the prefix of its id (`spec:`, `brief:`) and its **slug** is the rest,
taken from the file's own `Slug:` field. A **reader** is code that consumes a
pointer value — three do, and they disagree about which shapes they accept. A
**collision slug** is a slug that more than one node id ends in, so a bare
pointer carrying it matches several artifacts. **Dispatch** is the check that
decides whether a queued spec may be worked on; it reads `Brief:` and is the
consumer this record's third decision reaches. A **projection** is a generated
copy of a source file, which must never be edited directly.

## Reviewer brief

- **Decision:** This updates the pointer grammar for two of the four pointer fields; it does not claim to settle one grammar for all of them. A pointer written under the updated grammar is `<kind>:<slug>` — a kind token, a colon, and the target's own slug — and it is adopted now for `Parent intent:` and `Brief:`, the two fields whose target kinds are defined. Separately, a name matching more than one artifact is refused rather than resolved, in every field the resolver sees.
- **Recommended outcome:** accept
- **Change if accepted:**
  - `<kind>:<slug>` becomes the canonical form for `Parent intent:` and `Brief:`. The fallbacks each survive only where their reader already accepts them: the traceability resolver keeps taking a unique bare slug and a path, and the dispatch reader keeps taking a path and keeps refusing a bare slug. No existing artifact breaks. One reader does gain a shape: dispatch begins accepting `brief:<slug>`, which it refuses today — that is the point of D3, and the rest of its refusals, including the bare slug, are unchanged.
  - `intent:` joins the recognized node kinds, covering the 117 files under `docs/product/intents/` that no ladder rung already types. A node's slug comes from its `Slug:` field, never from the filename stem.
  - `brief:<slug>` replaces the repository-relative path as the canonical `Brief:` value, superseding the pin at `guides/core/reference/product-brief-fields.md:100`. The guide says explicitly which reader accepts which fallback: traceability and coverage take a unique bare slug, dispatch does not and never has.
- **Affected surface:** the resolver `resolve_endpoint` in `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py:629` and its two projections; the `Brief:` field row in `guides/core/reference/product-brief-fields.md:100`; the join in `packs/core/.apm/skills/author-delivery-brief/scripts/lint-brief-coverage.py`; the dispatch provenance check in `workspace_status_engine.py`, whose source is `packs/core/.apm/skills/workspace-status/scripts/` with three generated projections, and which refuses the typed form today; and the surfaces that *write* the old `Brief:` form — enumerated by the implementing spec's derivation, not counted here, since every count this RFC has stated was falsified by the next review. Known members include the `new-spec` spec template at `packs/core/.apm/skills/new-spec/assets/spec.md:7`, the instruction stamping it at `packs/core/.apm/skills/new-spec/SKILL.md:213-217`, and the back-link instruction at `packs/core/.apm/skills/author-delivery-brief/SKILL.md:196`.
- **Stakes:** reversible, but one change is load-bearing. Every change lands in version control and nothing is migrated outside it. D3 does reach a validation control on the dispatch path that gates every queued spec, so that edit carries a security review even though the decision itself is reversible by revert.
- **Review focus:** whether refusing an ambiguous name is right where a tiebreak would be cheaper; whether `intent:` should exclude the 33 ladder-typed files rather than cover the directory; whether holding `Contract:` and `Discovery:` back is the right call or an evasion; and whether admitting the typed form at the dispatch provenance check is worth the reach into a second package.
- **Not in scope:** adopting the form for `Contract:` and `Discovery:`, and migrating their 38 and 25 values. Those two fields are deliberately left governed by nothing new here — see D1's scope limit, which is the reason rather than an omission.

## The ask

Accept `<kind>:<slug>` as the canonical pointer form for `Parent intent:` and `Brief:`, accept `intent:` as a node kind keyed on the `Slug:` field, and accept that `brief:<slug>` supersedes the repository-relative-path pin for `Brief:`.

Today a pointer is written in whatever shape its field's guide happened to fix, and a reader resolving one may land on an artifact the author never named. The resolver's bare-slug fallback scans every node id for one ending in `:<slug>`, takes the candidates in sorted order, and returns the first (`lint-traceability.py:643-649`). Its own comment concedes the case — "a slug could in principle suffix-match >1 id" — and resolves it by sort order anyway. Sort order is not a decision anyone made about these two artifacts; it is alphabetical accident standing in for one. The repository has stayed correct so far because no live pointer is ambiguous, not because anything prevents one.

This cohort widens the exposure. Attaching the intent corpus raises the graph from 594 to 711 local nodes and the collision slugs from 1 to 7. No live pointer becomes ambiguous — the registration in D2 is chosen precisely so that none does — but a larger node set means more names a future author can pick that the resolver would silently disambiguate for them.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | What is the canonical pointer form, and which fields adopt it now? | `<kind>:<slug>`, adopted by `Parent intent:` and `Brief:`; an ambiguous name is refused rather than tiebroken | The kind token is what makes a name unique; the two adopting fields are the two whose target kinds are already defined | 2026-09-22 | Accept, or name a tiebreak you would rather have than a refusal |
| D2 | Are intent files graph nodes, and under what id? | Yes — `intent:<Slug: field value>`, covering only the intent files no ladder rung already types | Covering the whole directory makes all 19 live bare pointers ambiguous; a stem-derived id would put an ordinal inside a pointer value | 2026-09-22 | Accept, or choose whole-directory coverage or no `intent:` nodes at all |
| D3 | What is the canonical `Brief:` value? | `brief:<slug>`, superseding the repository-relative path fixed at `guides/core/reference/product-brief-fields.md:100`; the path stays an accepted fallback | One field cannot have two canonical forms, and `Brief:` is the only pointer field whose guide pins a path | 2026-09-22 | Accept, or keep the path canonical and exempt `Brief:` from D1 |

## Problem & goals

**A pointer names a target, and the fields disagree about how.** `Contract:`, `Discovery:`, `Brief:` and `Parent intent:` are the spec-side up-edges the traceability check walks (`lint-traceability.py:185`). They are written by hand, by adopters, in three different shapes: a bare slug, a repository-relative path, and a typed id. The resolver accepts all three, so nothing *breaks* — but no convention says which an author should write, and each field's guide answers differently or not at all.

Three specific failures follow.

**A bare slug can name more than one artifact, and the resolver picks one.** The fallback at `lint-traceability.py:643-649` iterates `sorted(local_ids)` and returns the first id ending in `:<slug>` or `/<slug>`. Two artifacts of different kinds sharing a slug is not exotic — an intent and the capability derived from it naturally share a name. All 19 bare `Parent intent:` slugs resolve today and none is ambiguous. The corpus holds exactly one collision slug — `governance-item-record-routing`, carried by both an `opportunity:` and a `spec:` node — and no pointer uses it. Nothing stops the next author from writing one, and the change recommended here raises the number of such names from 1 to 7.

**The intent corpus is invisible to the graph.** `recognize_ladder` types a file only when it carries `Kind: outcome`, `Kind: opportunity`, or `Level: capability` (`lint-traceability.py:551-558`). That claims 33 of the 150 files under `docs/product/intents/`. The other 117 are not nodes, so nothing points at them, nothing checks whether they are reachable, and an author writing `Parent intent:` at one of them is writing into a name the graph cannot see.

**`Brief:` is pinned to a path by a guide that a typed grammar contradicts.** `guides/core/reference/product-brief-fields.md:100` states the field is "named by its repository-relative path (a bare slug fails reconciliation and blocks dispatch)". That pin is the accepted convention, and two skills instruct authors to follow it. Adopting D1 without superseding it would leave the repository's own guide and skills telling adopters the opposite of what its template stamps — which is why this decision needs an RFC rather than a pull request.

**Goals.** An author writing a pointer names exactly one artifact. A reader resolving one reaches that artifact or is told the name is ambiguous. One field has one canonical form, stated the same way in its guide, the skills that stamp it, its template, and the scripts that join on it.

**Non-goals, deliberately excluded.** Bringing `Contract:` and `Discovery:` under the grammar, for the reason D1 gives. Closing the recognized-kind set: ADR-0033 D2 keeps `Level` an open string field, and this RFC does not narrow it. Replacing the bare-slug and path fallbacks with a hard refusal: the canonical form is what authors and tools should write, not the only thing a reader accepts.

## Proposal

### D1 — `<kind>:<slug>` is the canonical pointer form, for two fields now

A pointer value is a kind token, a colon, and the target artifact's slug: `intent:agent-ready-repo`, `brief:intent-identity-and-registration`, `spec:intent-reference-grammar-migration`. The kind token comes from the recognized node kinds the traceability graph builds; the slug is the target's own identity.

This form is not new to the repository. ADR-0108 D5 already fixes cross-spec citation as the `spec:<slug>/` marker. D1 generalizes an accepted pattern rather than inventing one.

**The form is adopted by `Parent intent:` and `Brief:`, and by no other field yet.** A pointer field can adopt `<kind>:<slug>` only once every artifact it can name has a kind and a slug rule. That holds for the two adopting fields: `Parent intent:` targets are intent files, typed by D2 or already by `recognize_ladder`, and `Brief:` targets are briefs, typed by the existing `recognize_briefs`.

It does not hold for the other two, and pretending otherwise would be the same defect this RFC exists to remove:

- **`Contract:`** targets are mostly contract files, which `recognize_contracts` already types as `contract:<name>@<version>` (`lint-traceability.py:513-531`). That id embeds a version, so `<kind>:<slug>` is not yet the right shape for them and the versioned form needs its own decision.
- **`Discovery:`** targets are not one class. Some are intent files, which D2 covers; others point into `docs/product/research/`, which has no registered node kind at all. Declaring a canonical form for a field whose targets have no kind would make the form unwritable for those values.

Both fields keep their current behaviour, unchanged and ungoverned by this RFC. Their adoption is a later decision that must first answer what kind their targets carry — and that question is cheapest to answer alongside the migration that has to sweep them, not here, where nothing would test the answer.

**Two fallbacks stay accepted, each by the readers that accept it today.** In the traceability resolver, a bare slug matching exactly one node resolves to it, and a repository-relative path resolves as it does now. The dispatch reader is narrower and stays narrower: it accepts the path form and the new typed form, and it keeps refusing a bare slug, which it has never accepted. Neither fallback is canonical and neither is removed — the point of accepting one is that no existing artifact breaks on the day this lands — but "accepted" is a statement about a reader, not about the repository. D3 widens exactly one reader by exactly one shape: dispatch gains `brief:<slug>`. Its path fallback and every other refusal stay as they are.

**An ambiguous name is refused.** When a bare slug matches more than one node id, the resolver reports the value together with every candidate and makes the check exit non-zero. It does not choose by sort order, kind priority, recency, or shortest candidate. A tiebreak is a decision about which of two artifacts the author meant, and no rule available to the resolver has any information about that. Refusing costs the author one edit — adding the kind token, which is the canonical form anyway. Choosing wrong costs a wrong edge that nothing detects.

Refusal applies to every bare slug the resolver sees, including one in a field that has not adopted the canonical form. The refusal is a property of the resolver, not of the field: a name that matches two artifacts is unanswerable wherever it appears.

The resolver's implementation is the concern of `docs/specs/intent-reference-grammar-migration/spec.md`; what this RFC fixes is that a tiebreak is not an option available to it.

### D2 — `intent:` is a node kind, keyed on the `Slug:` field

`intent:` covers every file under `docs/product/intents/` that `recognize_ladder` does not already claim: 117 of the 150 files present.

**The exclusion is load-bearing, and the measurement is the reason.** Registering a blanket `intent:` kind over the directory would give each of the 33 ladder-typed files a second id — `capability:foo` *and* `intent:foo` for the same artifact. Both ids are real nodes, so nothing overwrites; what breaks is bare-slug resolution, because the slug now suffix-matches two nodes that are the same file. Projected against the corpus, with the current graph as the baseline:

| | Today | Exclusion (recommended) | Blanket registration |
| --- | ---: | ---: | ---: |
| Local nodes | 594 | 711 | 744 |
| Collision slugs | 1 | 7 | 39 |
| Of those, new and self-inflicted | — | 0 | 32 |
| Live bare `Parent intent:` pointers made ambiguous | 0 of 19 | 0 of 19 | 19 of 19 |

The recommended registration adds six collision slugs and leaves every live pointer resolving. Blanket registration makes **every** live bare pointer ambiguous against its own target, which is precisely the failure D1 exists to prevent. Each of the 33 ladder-typed files carries a distinct `Slug:`, so each contributes its own self-collision rather than clustering.

**The slug is the `Slug:` field value, never the filename stem.** Five of the 117 filenames carry an ordinal prefix, so a stem-derived id would place an ordinal inside a pointer value. That is refused on its own grounds, not by borrowing another record's authority: an ordinal identifies a record's place in a series, and a series position is not a name. Two records can swap places in a listing without either changing what it is about, so a pointer keyed on one is a pointer that can be silently wrong. ADR-0108 D2 and D3 hold the neighbouring line — an identifier, once assigned, is never renumbered and never reused — which is why this repository's ordinals are stable enough to *cite*; stability is not the same property as being an address, and D2 and D3 do not claim it. All 117 files carry a `Slug:` field and no two share a value, so the field-derived id is available for every one of them.

A file carrying no `Slug:` field is reported and contributes no node. It does not fall back to the stem, because the stem is the form the previous paragraph rules out. No file in the corpus is in this state today; the rule exists so that the first one to arrive is reported rather than quietly given an ordinal-bearing id.

### D3 — `brief:<slug>` is the canonical `Brief:` value

The `Brief:` field row at `guides/core/reference/product-brief-fields.md:100` is amended: the canonical value becomes `brief:<slug>`, and the row states the fallbacks **per reader** rather than as a blanket allowance. The repository-relative path is accepted by all three readers. A bare slug is accepted by the traceability resolver and the coverage join, and is refused by dispatch — which has always refused it, and which this decision does not change. A row saying only "the bare slug remains accepted" would be false of the reader whose refusal blocks the queue.

Several surfaces state or write the old form, and they move together, because a guide that disagrees with the skill stamping the field changes nothing an author sees. **The authoritative set is the one the implementing spec derives mechanically, not the list below.** Three successive revisions of this RFC each stated a total — three, then five — that the next review falsified, which is why the count is now delegated rather than asserted. Known members include:

- `guides/core/reference/product-brief-fields.md:100` — the field row, and the pin this decision supersedes.
- `guides/core/how-to/write-the-contract.md:88` — the template excerpt reproduced for authors, carrying the same path comment.
- `packs/core/.apm/skills/new-spec/assets/spec.md:7` — the template comment offering `docs/product/briefs/<slug>.md`.
- `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md:133-137` — the contract reference, which states the path form *and* that "a bare slug fails that check and blocks dispatch". That sentence is the accurate description of the dispatch reader below, written down before this delivery went looking for it.
- `packs/core/.apm/skills/author-delivery-brief/SKILL.md:196` — "set the canonical repository-path `Brief:` back-link", which names the old form *as* canonical and so contradicts this decision directly.

and at least `packs/core/.apm/skills/new-spec/SKILL.md`, which stamps the path, and `packs/core/seeds/docs/product/briefs/_template.md`, whose own `Slug:` comment instructs derived specs to back-link by path. Each of these was missed by an enumeration that preceded it, which is the evidence for delegating the set rather than listing it.

Some surfaces **act on** the value and others merely see it, and the authoritative split is the implementing spec's derivation rather than any count fixed here. The three that act on it at the time of writing are below, and the third is the one that nearly got missed.

- `lint-brief-coverage.py` joins a spec to its brief on this value and must accept `brief:<slug>` alongside the two fallbacks.
- `lint-traceability.py` reads the same field but resolves it through `resolve_endpoint`, so it needs no change of its own for D3. The three words this RFC uses for the path form's fate are not synonyms: the resolver *accepts* the value (it is well-formed and does not error), classifies its endpoint state as `unresolvable` (it names no local node), and therefore attaches it to an *external stub* rather than to the brief. The typed form resolves `local` instead, which is the edge D3 is buying.
- `workspace_status_engine.py` reads it on the **dispatch** path, and refuses the typed form today. Its source is `packs/core/.apm/skills/workspace-status/scripts/`; the copy under `packages/agentbundle/agentbundle/_data/` is one of three byte-identical projections, and editing a projection is the error this delivery corrects elsewhere.

A further set merely **parses** it. Two modules in this repository compile a *generic* preamble pattern — `workspace_status_engine`'s `field_re` and `intent_shape`'s `_FIELD_LINE`, each matching a line-anchored `- **`, a captured name, then `:**`. Both therefore see every preamble field including `Brief:`; only the first acts on it. `intent_shape` names no pointer field at all, so it is unaffected by D3 and carries no obligation under it. The distinction matters because a criterion discharged against "readers" would otherwise oblige a parser that does nothing with the value to accept `brief:<slug>`.

The consumer that makes the point best is `intent_corpus_lint`, which reaches `Parent intent:` only through a dynamic `_load_sibling("intent_shape", …)`, iterates the returned pairs, and names no field. It is invisible to a name search and to a static import scan alike. Together with the dispatch reader above — which parses `Brief:` through a pattern that never contains the word — these are the evidence for this RFC's premise: a pointer field's consumer set cannot be established by searching for the field's name.

An earlier revision of this paragraph claimed five such parsers, adding `lint-spec-status`, `lint-contract-item-alignment` and `lint-adr-shape`. That was wrong, and wrong in this RFC's own characteristic way: the derivation behind it tested for the pattern's opening and closing fragments *independently*, so a file with `^- \*\*Acceptance Criteria:\*\*` in one regex and `\*\*Status:\*\*` in another satisfied both. Those three parse named fields, not arbitrary ones. The count is two.

**The dispatch reader is real, and the guide was right about it.** The parenthetical this supersedes — "a bare slug fails reconciliation and blocks dispatch" — is an accurate description of live behaviour, not a stale claim about another surface. The chain is four steps, and none of them names the field, which is why a search for the string `Brief` in that module does not find it:

1. `_parse_preamble_fields` (`:1818-1824`) matches `- **<Name>:** <value>` over any artifact and keys the result on the lower-cased name, so a spec's `Brief:` line lands under `brief`.
2. `:2221-2223` reads that key into the artifact's provenance parent.
3. `_dependency_metadata_safety_finding` (`:2653-2660`) validates it for a spec with `require_local_brief=True`.
4. `_provenance_path_is_invalid` (`:2629-2640`) rejects any value that is not a repository-relative path, and then any that is not a canonical local brief path per `_is_canonical_local_brief_path` (`:723`).

Driving those functions directly: `brief:<slug>` is **refused**, a bare slug is **refused**, and `docs/product/briefs/<slug>.md` is accepted. Adopting D3 without changing this module would make every swept spec emit an `invalid_artifact_path` finding on the path that gates the work queue.

So this module joins the change surface. The change admits the typed form at the provenance check and nothing else: `_is_canonical_local_brief_path` itself is not relaxed, because the same helper validates `workspace.toml` entry and dependency paths — `entry.path` at `:2862`, `dep.path` at `:2413`, and validated values at `:808`, `:841`, `:881`, `:1379` and `:2638` — where a slug has no meaning and must keep failing. A value that is neither the typed form nor a canonical local brief path still produces a finding; that refusal is what keeps this from being a blanket loosening of a control on the dispatch path.

**One naming hazard is real and is accepted knowingly.** `workspace.toml` already uses a `brief:` prefix in its `needs` tokens, pinned to `^brief:docs/product/briefs/<slug>\.md$` at `workspace_status_engine.py:5270` — the same prefix, but carrying a **path** rather than a slug. After this decision the token `brief:` means a path in `workspace.toml` and a slug in a spec header. The two never meet: no code reads one grammar in the other's position, and the workspace pattern is anchored so a slug-valued token fails it loudly rather than silently. The cost is that an author moving between the two files must keep them apart, and the alternative — renaming one of the two prefixes — is a migration of a surface this RFC is not otherwise touching.

## Options considered

Options are enumerated along an axis that is *mutually exclusive, collectively exhaustive* (MECE): every candidate falls under exactly one option.

**D1 splits into two independent questions, and they are decided separately** — conflating them is what makes a single option list incoherent, because a canonical form and an ambiguity policy can each be chosen without the other.

*First: is there a canonical form at all?* Either one form is named as canonical, or none is and every accepted shape stays equal. Naming none is today's state: three shapes, no guidance, and a `Brief:` guide contradicted by the template that stamps it. Rejected because the disagreement between guide, skill and template has no resolution procedure without a canonical answer.

*Second: what happens when a bare slug matches several nodes?* Either the resolver refuses, or it selects by some rule — the sorted-first behaviour it has today is one such rule, and kind priority, recency and shortest-candidate are the others. Selection keeps the check green and interrupts nobody. Rejected because the interruption is the product: a resolver that selects is making an authorship decision with no authorship information, and the resulting edge is indistinguishable from a correct one, so the error survives every downstream check.

**D2 — exclude, cover everything, or register nothing.** The axis is which files the new kind claims: none, some, or all.

- *Register no `intent:` nodes.* Costs nothing and changes nothing, which is the problem: the 117 files stay invisible, `Parent intent:` keeps pointing at names the graph cannot see, and the field cannot adopt D1 because its targets are not nodes. Rejected because it leaves the second of the three stated problems entirely unaddressed.
- *Cover the whole directory.* Simpler to state and to implement. Rejected on measurement: it makes all 19 live bare pointers ambiguous and raises collision slugs from 1 to 39.
- *Cover only the unclaimed files* (recommended). Keeps every live pointer resolving at the cost of a recognizer that must ask what `recognize_ladder` already claimed.

**D3 had no contested alternative.** Once a canonical form exists, a field cannot keep a different one without exempting itself, and no property of `Brief:` argues for the exemption. The decision is recorded because it supersedes an accepted guide and that supersession must be citable.

## Risks & what would make this wrong

**Registering 117 files as nodes does not make them orphan-checkable — measured, after an earlier draft claimed it would.** A draft of this section called that the largest unmeasured quantity in the work: 117 files becoming orphan- and reachability-checkable at once, with `--strict` treating a structural orphan as exit 1. It was inferred from "these files become nodes", and it is wrong.

`classify_standalone` (`lint-traceability.py:792-826`) classifies only nodes whose kind is in `CHAIN` (`:112-115`) — `outcome`, `opportunity`, `capability`, `screen`, `action`, `service`, `contract`, `spec`, `component`. `intent` is not in that tuple and neither is `brief`. Registering a kind does not enrol its files in the chain check; only joining `CHAIN` does, and D2 does not do that.

Projected by building the graph, adding the 117 `intent:` nodes exactly as D2 specifies, and wiring the 14 parent pointers they carry:

| | Today | With `intent:` nodes |
| --- | ---: | ---: |
| Nodes | 640 | 757 |
| Edges | 109 | 115 |
| Structural orphans | 488 | **487** |
| New orphans introduced | — | **0** |

The count falls by one, because a newly wired parent edge gives an existing node a producer it lacked. No `intent`-kind node is classified as an orphan, because none can be.

**What this leaves.** `--strict` already exits 1 today on 488 pre-existing orphans, almost all specs with no producer up-edge; the default invocation exits 0. Neither figure is this delivery's doing and neither changes because of it. The honest risk is therefore not orphan breakage but the opposite: this delivery adds 117 nodes to a graph whose strict mode is already failing, and does not improve it. Enrolling `intent` in `CHAIN` would be a separate decision with a real orphan question attached, and this RFC does not propose it.

**Holding two fields back leaves the repository mid-migration.** `Contract:` and `Discovery:` keep their current shapes after this lands, so for a while two fields have a canonical form and two do not. That is what an incremental grammar update costs, and it is why this record is scoped as an update rather than as the final word. The alternative on offer was a canonical form some values cannot express — `contract:<name>@<version>` does not fit `<kind>:<slug>`, and some `Discovery:` targets have no registered kind at all. If the review would rather settle all four now, the remedy is to answer the kind-coverage question, not to widen the claim without answering it.

**Refusal could be noisier than predicted.** The claim that no live pointer is ambiguous rests on the corpus as of 2026-09-22. A pointer added between acceptance and execution could be ambiguous, and its author would meet a refusal they did not expect. The corpus holds one collision slug today and would hold seven after the recommended registration, so the case is reachable rather than theoretical. The mitigation is that the refusal names every candidate, so the fix is mechanical — but the cost is real and lands on whoever is nearest.

**D3 reaches into a validation control on the dispatch path.** Admitting a new accepted value at the provenance check touches the code that decides whether a queued spec is dispatchable. Done narrowly it admits one shape; done carelessly it weakens a check that also guards `workspace.toml` paths. The mitigation is that the helper itself is untouched and the "neither form" case keeps its refusal, asserted as its own criterion — but the honest statement is that this decision costs a security review it would not have needed if `Brief:` had stayed a path.

**Accepting two fallbacks means the canonical form is a convention, not a constraint.** Nothing rejects a path-valued `Brief:` after this lands. An adopter can write the old form indefinitely, and the corpus can drift back. That is the deliberate price of not breaking existing artifacts; if drift becomes the problem, the answer is a later lint, not a different grammar.

**A kind token is only as unique as the kind set.** ADR-0033 D2 keeps `Level` an open string field, so the recognized-kind table is closed by decision rather than derived. Adding a future kind whose slugs overlap an existing kind's would reintroduce collisions the grammar cannot see coming. The uniqueness check therefore runs over the derived corpus rather than against a fixed kind list.

## Evidence & prior art

### How every number here was produced

Every count comes from the working tree on 2026-09-22, derived one of four ways.

- **Graph counts** load `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py` as a Python module, call `build_standalone` with the repository root, and read the resulting graph. A node count means **local** nodes — those whose kind is not `external`. The graph also holds `external` stubs, created when a pointer resolves outside the local node set; counting those too gives 640 rather than 594, and both are true of the same corpus. Stating which is meant is what keeps a reader from concluding the figures are wrong.
- **Corpus counts** walk `docs/product/intents/*.md`, skip leading-underscore files, and apply the module's own `_SLUG_RE`, `_KIND_RE` and `_LEVEL_RE` to each.
- **Pointer-field counts** re-run the module's own recognizers to get the artifact set each field is read from — `recognize_briefs` and `recognize_ladder` for `Parent intent:`, `recognize_specs` for `Brief:` — then apply `field_re("<field>")` to each file and drop placeholder values with `_is_placeholder`. This is the builder-visible set, which is narrower than every occurrence of the string in the repository: projections and test fixtures carry the same headers and are not read by the builder.
- **Projected counts** — the collision and ambiguity figures for a change not yet made — take the built local node set, add the ids the change would create, and re-run the collision test over that union. Nothing is written to disk. The implementing spec commits this projection as a re-runnable probe (its task T4), which is what makes these numbers auditable rather than transcribed.

A **collision slug** is a slug that more than one node id ends in, so a bare pointer carrying it would suffix-match several nodes. A **live ambiguous pointer** is a bare value actually present in a builder-visible field that suffix-matches more than one node.

| Figure | Value today |
| --- | --- |
| Local nodes | 594 |
| External stubs | 46 |
| Files under `docs/product/intents/` | 150 |
| Of those, typed by `recognize_ladder` | 33 |
| Of those, unclaimed — what `intent:` would cover | 117 |
| Unclaimed files carrying a distinct `Slug:` | 117 of 117 |
| Builder-visible `Parent intent:` values | 23, of which 19 are bare slugs |
| Bare `Parent intent:` slugs resolving to a local node | 19 of 19 |
| Specs carrying a `Brief:` value | 34, all resolving `unresolvable` today |
| Collision slugs | 1 (`governance-item-record-routing`) |

### Cited code and records

- `lint-traceability.py:643-649` — the bare-slug fallback iterates `sorted(local_ids)` and returns the first suffix match; the adjacent comment states a slug could match more than one id.
- `lint-traceability.py:185` — `_SPEC_UP_FIELDS` fixes the four pointer fields as `("Contract", "Discovery", "Brief", "Parent intent")`.
- `lint-traceability.py:551-558` — the three conditions by which `recognize_ladder` types a file, which is what leaves 117 of the 150 intent files unrecognized.
- `lint-traceability.py:513-531` — `recognize_contracts` builds `contract:<name>@<version>` ids, the versioned shape behind D1's scope limit.
- `guides/core/reference/product-brief-fields.md:100` — the pin D3 supersedes.
- `packs/core/.apm/skills/new-spec/SKILL.md:213-217` and `packs/core/.apm/skills/author-delivery-brief/SKILL.md:196` — the two instructions that stamp the old form, the second calling it canonical.
- ADR-0108 D5 — cross-spec citation already uses a `spec:<slug>/` marker, establishing the typed-prefix form before this RFC generalizes it.
- ADR-0033 D2 — `Level` is an open string field not closed by a lint, the constraint behind checking id uniqueness over the derived corpus.
- ADR-0112 — an index over a corpus is generated or absent, which is why no hand-maintained table of cohort membership is created.

## Follow-on artifacts

- `docs/specs/intent-reference-grammar-migration/spec.md` — authored, and reopened to `Draft` by a controlled amendment when execution found the dispatch reader. It implements D1, D2 and D3 and sweeps the 19 `Parent intent:` and 34 `Brief:` values; its `Constrained by:` already cites RFC-0103. Its AC-0009 now discharges against the derived inventory rather than a count, and AC-0016 to AC-0018 carry the dispatch reader's acceptance, its refusals, and the untouched behaviour of the shared helper's other call sites.
- `guides/core/reference/product-brief-fields.md` — the `Brief:` field row is amended by that spec's task T6, which is where the supersession in D3 lands.
- A later decision and spec for `Contract:` and `Discovery:`, answering what kind their targets carry — the versioned `contract:<name>@<version>` shape for the first, and a kind for the `docs/product/research/` targets of the second — and sweeping their 38 and 25 values once it can.

## Errata

- 2026-09-22: corrected D3 while in flight. The draft asserted that
  `workspace_status_engine.py` does not read the spec's `Brief:` header and that
  dispatch was therefore unaffected. Driving the module's own functions showed
  the opposite: it reads the field through the generic `_parse_preamble_fields`,
  lands it in the provenance parent, and refuses both `brief:<slug>` and a bare
  slug. D3 now names that reader, the module joins the affected surface, and the
  Risks section records the security review the change costs. The original claim
  rested on a search for the string `Brief` in a module whose parser never names
  the field.
- 2026-09-22: updated D3 from the implementing spec's derivation (task T0),
  which ran after this RFC was drafted. Two corrections: the reader count is
  delegated rather than stated, as the writer count already was; and "reads" is
  split from "parses", because five generic preamble parsers see `Brief:` while
  only three act on it. Obliging the other two to accept a new form would have
  been meaningless. The derivation is the evidence for D1's premise, not just
  an input to D3.
- 2026-09-22: corrected the writer inventory from three surfaces to five,
  adding `guides/core/how-to/write-the-contract.md:88` and
  `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md:133-137`.
  The second of those already stated that a bare slug blocks dispatch, which
  corroborated the correction above from a source the draft had not read.
- 2026-09-22: reframed from "one pointer grammar" to a pointer grammar
  *update*, at the owner's direction. The earlier title and decision line read
  as though this record settled the grammar for all four pointer fields, while
  the body adopts it for two and explicitly leaves `Contract:` and `Discovery:`
  alone. Both reviews flagged the gap independently. The scope did not change;
  the claim was brought down to it.
- 2026-09-22: replaced the orphan risk with a measurement that falsifies it.
  The section had called 117 files becoming orphan-checkable the largest
  unmeasured quantity in the work. `classify_standalone` only classifies kinds
  in `CHAIN`, which contains neither `intent` nor `brief`, so the projected
  change is 488 structural orphans to 487 and no new orphan at all. A
  fresh-reader review had named this the one thing blocking approval, which is
  what prompted measuring it rather than deferring it to the implementing
  spec's T4.
- 2026-09-22: added an opening orientation section, and distinguished
  "accepted", "unresolvable" and "external stub", after a fresh-reader review
  found the Reviewer brief unusable without repository context — "ladder rung"
  used 29 lines before anything defines it, "collision slug" 150 lines before.
- 2026-09-22: corrected "five generic preamble parsers" to two. The figure came
  from a derivation that tested the pattern's opening and closing fragments
  independently, so files parsing *named* fields were counted as parsing
  arbitrary ones. `workspace_status_engine` and `intent_shape` are the two. The
  claim was this record's headline evidence for its own premise, which is why
  the correction is recorded rather than quietly applied.
- 2026-09-22: **the default invocation does not stay at exit 0 through the
  migration.** The Risks section states that `--strict` already exits 1 on
  pre-existing orphans while "the default invocation exits 0 … neither changes
  because of it". Implementation falsified the second half. Recognizing the
  intent files makes 14 of their own `Parent intent:` values builder-visible;
  6 resolve, and 8 are markdown links whose field regex truncates at the first
  space, yielding a token like `[Digital` that matches no cross-repo shape and
  so classifies `dangling` — a hard violation in every mode. Default exit is 1
  between the recognizer landing and the sweep that rewrites those values. The
  targets resolve (`capability:digital-experience-doctrine` and
  `capability:nontechnical-pack-first-value-rollout`), so the sweep clears them
  and the end state is exit 0; the interim is not. The projection behind the
  original claim measured node, edge and orphan counts and never read the exit
  code, which is the same half-verification this record has had to correct
  twice before.

