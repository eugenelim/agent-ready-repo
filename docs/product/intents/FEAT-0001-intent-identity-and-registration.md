# Intent identity and registration

- **Slug:** `intent-identity-and-registration` <!-- canonical identity; independent of the filename ordinal -->
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:repository-work-graph
- **Status:** Accepted
- **Owner:** eugenelim
- **Accepted:** 2026-09-19 by eugenelim — see [Acceptance record](#acceptance-record)

- **Nonmaterial correction 2026-09-21 by eugenelim, lifecycle owner.** The preamble now carries the field set and order that `guides/product-engineering/reference/intent-fields-and-modes.md` defines — `Slug`, `Level`, `Scale`, `Maturity`, `Parent intent` — with the two lifecycle fields after them. `Accepted:` was 154 words of shaping-review narrative in a field position, which no reader can parse as a value; the narrative moved unchanged to `## Acceptance record` and the field now holds the date and the owner. Two links to this intent's delivery brief carried the brief's former title and now carry its current one. Nothing decided here changed, so the acceptance stands.
- **De-risked:** 2026-09-18
- **Shaping-reviewed:** 2026-09-19
- **Decomposed:** 2026-09-19 brief

## Outcome

- **Steerable input:** Reduce the number of decisions an author or agent has to make by hand when naming and admitting an intent — what to call it, and what identity it carries — and reduce the coordination a new admission needs. Where a repository intent goes is not among them: that directory is a pinned hand-off to core's admission.
- **Lagging outcome:** An author or agent names and registers an intent without deciding its identity by hand, and every **canonical** reference to that intent — from a sibling intent, a brief, a spec or the registry — resolves to exactly one artifact, while an ambiguous or invalid reference fails closed rather than guessing. A placement path that escapes its anchoring root refuses rather than writing outside it. The corpus stays addressable by a human reading a filename and by a machine walking the graph, and keeps being so as intents are added, renumbered and reissued.
- **Guardrail:** A pointer resolves to exactly one artifact or fails; resolution never picks a winner among ambiguous candidates. The existing slug/path identity keeps resolving, existing registered work keeps its meaning, and admission keeps its confinement and provenance checks. No path becomes hierarchical, and no allocation step becomes a file every concurrent author must edit. Adoption is forward-only: the 135 intents that carry no ordinal today are not migrated. The new allocator refuses a corpus it cannot parse rather than returning `0001`, and its `--check` never reports clean on a directory it did not read. A renumber leaves no stale citation, which constraints C3 and C4 below make concrete.

## Opportunity

- **Functional job:** Place a new intent where it belongs and admit it to the repository once, and be able to name it later in a way a person can say out loud.
- **Emotional job:** Admit work without worrying that the placement or the name will have to be redone, or that another author's admission will collide with this one.
- **Social job:** Refer to a piece of work by a name a maintainer, an adopter, or a stakeholder recognizes, rather than by a long slug or a file path.
- **Struggling moment:** A slug is the only identity an intent has today, so there is nothing short and typed to cite. Placement is decided per author: `frame-intent` resolves an output directory from `agentbundle-layout.toml`, and this repository ships no such file, so the path falls to elicitation each time. Admission is also uneven — 23 of the 130 intent files on disk have no registry presence at all.

## Boundary

Inherits the parent's outcome, boundary, and exclusions. Within them, this child owns:

- safe placement paths: a path that escapes its anchoring root through a symlink refuses, one carrying a `..` segment refuses, and one that merely resolves outside the repository is confirmed before use. **Not a precondition for allocation**: a repository intent's directory is a pinned hand-off to core's admission, so the folder `max + 1` scopes to is fixed rather than resolved. Which authority decides repository-versus-personal work, and what a consumer does when configuration is missing, are not this intent's: two accepted records disagree about them and the reconciliation is registered against ADR-0030;
- safe admission of a repository intent, preserving the confinement, provenance, and terse-capture rules admission already applies;
- the **typed ordinal vocabulary** and its filename contract, `<TYPE>-NNNN-<slug>.md`, assigned at admission alongside the existing slug:

  | `Level:` | Prefix | Example filename |
  | --- | --- | --- |
  | `product-vision` | `VISION` | `VISION-0001-<slug>.md` |
  | `product-strategy` | `STRAT` | `STRAT-0001-<slug>.md` |
  | `capability` | `CAP` | `CAP-0001-repository-work-graph.md` |
  | `feature` | `FEAT` | `FEAT-0001-intent-identity-and-registration.md` |

  Ordinals are per type, so `CAP-0001` and `FEAT-0001` coexist. **The table is closed, and an altitude outside it gets no ordinal.** The allocator serves these four and refuses any other `Level:` value rather than deriving a prefix for it; the same applies to an intent carrying no `Level:` at all. A refused intent keeps its full `kind:slug` identity and full graph participation and loses only the human-friendly alias, which is affordable precisely because the ordinal is an alias and not the canonical identity. Adding a token is an explicit reviewed extension of this table, never an inference — so `Level` stays the open field ADR-0033 D2 requires while the prefix vocabulary stays closed and testable;
- the **intent metadata shape contract**: which preamble fields an intent carries, which of them are required, and which carry a closed vocabulary rather than free text — `Kind` and `Status` at minimum — together with the lint that enforces it. `Level` is **not** among them: ADR-0033 D2 keeps it an open field, and what is closed is the **prefix table** that maps an altitude to an ordinal token. Ordinal eligibility is decided by that mapping, so an unmapped `Level` is refused an ordinal without `Level` itself being enum-valued. This is not an addition to this intent's scope; it is the formalisation the ordinal contract above already presumes. Safe admission has the same dependency on `Status`, because the only collection that admits a non-defect entry requires exactly `Draft`;
- **where the shape contract is enforced**, which is two places and not one. The **shaping review** gates it at the moment of ratification: its altitude condition is already the only authority reading an intent's shape, so a `Level` outside the recognized set must fail there rather than be inferred. A **corpus lint** catches drift across intents already on disk, which no per-artifact gate reaches. Neither substitutes for the other;
- the **cross-artifact reference grammar** and the canonical identity beneath it. `kind:slug` is canonical and the ordinal is a human-facing alias, because adoption is forward-only and the intents that will never carry an ordinal must stay addressable. Identity binds to each artifact's `Slug:` field, which the resolver prefers over the filename, so a later altitude change that renumbers a file changes no reference. A pointer value names exactly one artifact without guessing its type, and resolution refuses an ambiguous bare slug rather than choosing among candidates.

- **the decided allocation and naming mechanism.** An ordinal is a typed filename prefix at every altitude — `VISION-0001`, `STRAT-0001`, `CAP-0001`, `FEAT-0001`, one token per altitude — allocated `max + 1` over the directory unioned with `origin`. The same algorithm applies per folder at user scope. Paths never become hierarchical and no shared counter file is created. An ordinal is renumbered to the repository's next free ordinal when an intent is copied from user scope to repository scope; it does not migrate. This is mechanism, recorded here because the de-risk record below settled it — it is deliberately not stated as the outcome;
- **shaping-progress fields in the preamble, so de-risk and review state are declared rather than inferred.** An intent must carry whether it has been de-risked and whether it has passed a shaping review as **preamble metadata**, alongside `Status:` and `Level:`, in the same field block a resolver already parses. A de-risk record in the body is **not** that signal: a body is prose, its headings are unconstrained, and nothing stops an intent from discussing a probe it never ran. This follows the guardrail `CAP-0001` already sets — graph metadata lives in preamble fields and never in artifact bodies — and it is the same rule, applied to shaping progress. Today no such field exists: all 144 intents carry `Status:` and none carries either. The field set and its vocabulary are this child's to define; what the values mean for a transition is [FEAT-0005](FEAT-0005-lifecycle-and-closure.md)'s;

It owns **entry** to the lifecycle and not exit: what each `Status` value means, which transitions are legal and which workflow may make them belong to [Lifecycle and closure](FEAT-0005-lifecycle-and-closure.md). The boundary is that this child decides an intent's **shape**, including that `Status` carries a closed vocabulary, while that one decides what the values in it mean and who may move between them. It does not own the derived graph that reads identity (`intent-graph-navigation`), the mapping from an intent to its brief or spec (`intent-delivery-traceability`), where operational coordination state lives (`workspace-coordination-reorganization`), or any tracker's identifier scheme (`external-tracker-projection`). On mechanism it is deliberately uneven, and the line is drawn here rather than left implicit: the **allocation approach is chosen** — `max + 1` over the directory unioned with `origin`, per type prefix, by owner decision recorded in the de-risk record — because it is what makes the ordinal contract above meaningful. Everything else remains open at this altitude: no file format, no storage shape and no script structure is chosen. There is no derivation rule for an unseeded altitude because the contract above refuses one rather than deferring it.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

- The delivery-slice cut for its Ready brief, which `author-delivery-brief continue` section 4 places behind a second human confirmation. Not yet made.
- Collision-equivalence of the replacement allocator against `next-ordinal.py`, owed by the validation hook and not yet run.
- Whether the existing slug/path identity keeps resolving alongside a filename ordinal.

## Projection

Projects to its delivery brief, [intents get a typed ordinal identity, a declared shape, and canonical references](../briefs/intent-identity-and-registration.md). No outbound tracker projection: that surface is [CAP-0004](CAP-0004-external-tracker-projection.md)'s and is not yet shaped.

## Assumptions

- The existing slug/path identity can remain the resolving identity while an ordinal is added beside it, so nothing that cites a slug today breaks. **Untested.**
- A repository intent's destination needs no configuration: it is a pinned hand-off to core's admission, and authoring a personal intent elsewhere then admitting it is one flow rather than a conflict.
- The shaping review can carry enum enforcement without becoming a schema gate. **Untested**, and it is in tension with the reviewer's own stated posture that it checks well-formedness and not quality — a closed vocabulary is arguably well-formedness, but the boundary needs drawing before the reviewer contract is changed.

Two items left this list once they stopped being assumptions, and the **De-risk record** below owns both: that a typed ordinal can be allocated without a shared counter, which the allocator resolves by deriving `max + 1` and editing no counter file; and that ADR-0108 was precedent rather than constraint, which the record refutes on ADR-0108's own stated ground.


## Acceptance record

Revision `97ffc3a2f484ed5f` returned a clean independent intent-mode shaping review on every substantive run. Two earlier rounds were failed and repaired rather than waived: `MALFORMED(owner)`, because this intent carried no `## Owner` section at all — a gap shared by 8 of the 14 family intents, and one that suppresses the other five conditions — and `MALFORMED(statement)`, because the lagging outcome stated the allocator mechanism instead of an outcome. Both are fixed. A residual `MALFORMED(children)` appears on some runs and is a reviewer defect, not an artifact defect: the rule at `.claude/agents/shaping-reviewer.md` lines 64-74 emits that token for a missing decomposition only when the intent is above the leaf **and** `Accepted`, and this intent is the leaf and lists its delivery brief. Its brief's Spec map is empty because `author-delivery-brief` section 4 defers the slice cut until after Ready, behind a second confirmation. Deliberately unregistered on acceptance: `backlog.open` admits `Status: Draft` alone.

## De-risk record

- **Level kind:** feature, but the dominant assumption is **architectural**, not desirability. Demand for a human-friendly typed ordinal is owner-asserted rather than a market question, and adoption is not in doubt because every citation in the repository already resolves through a slug that keeps working. The risk is whether the ordinal can be allocated at all without recreating the contention the parent's guardrail forbids. That is the assumption tested below; the departure from the level's default kind is recorded here rather than left implicit.
- **Reversibility triage:** one-way door. An ordinal stamped on an artifact and cited from elsewhere cannot be renumbered once the corpus depends on it, and ADR-0108's append-only, never-reused doctrine would forbid reuse even if renumbering were cheap. The triage therefore defaults the approach to `validate-first`.
- **Prototype-approach:** `validate-first`. The repository has been allocating typed ordinals for its decision records for years, so the cheapest probe that can fail is a replay of that real history rather than a new prototype.

### Riskiest assumption

Of the four assumptions above, this one carries the highest risk against the least evidence:

**A typed ordinal can be assigned at admission without a shared counter that every concurrent author must edit.**

The other three are lower risk or already evidenced. The slug-keeps-resolving assumption is additive and testable at any time. The placement assumption was withdrawn: the destination is pinned, so there is nothing to resolve. The ADR-0108 question is decidable by reading a record rather than by experiment. This one is different: if it is wrong, the feature delivers the shared hot counter that the parent intent's own guardrail exists to prevent, which would make the child contradict its parent rather than serve it.

What would have to be true: there must exist at least one allocation rule that needs no shared counter, produces an ordinal a person can say out loud, and survives the repository's real concurrency without collisions or renumbering.

### Kill condition, predeclared

Declared before any measurement was taken, in the test's own currency of collisions and renumberings over real history.

**Kill the assumption if no candidate allocation rule that avoids a shared counter can produce a human-friendly typed ordinal that is both collision-free and never renumbered after assignment, when replayed over the repository's real admission history.**

The bar, concretely: at least one candidate rule must survive a replay over the repository's own typed-ordinal corpus with **zero collisions and zero post-assignment renumberings**. Two ways to fail are declared up front:

- if every candidate rule collides under real concurrency, the assumption is killed;
- if the only collision-free rules abandon human-friendliness — producing something a person cannot say out loud, and therefore indistinguishable in value from the slug the repository already has — the assumption is also killed, because the outcome's whole point is the human-friendly name.

On a kill, Slice 1 is reframed rather than decomposed: either the ordinal is dropped from the outcome, or the repository accepts an explicit serialization point and says so.

### Candidates tested

Measured on 2026-09-18 against the working tree and the real history of the repository's own typed-ordinal corpus: 119 ADRs and 103 RFCs, allocated by `packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py`, which derives `max + 1` from the directory unioned with the default `origin` branch and so edits no counter file. That is a real, years-old instance of the mechanism this assumption needs.

| Candidate rule | Needs a shared counter | Human-friendly | Result |
| --- | --- | --- | --- |
| `max + 1` over directory ∪ `origin` | no | yes | **fails** — 9 post-assignment renumberings |
| assign inside the existing admission lock | no | yes | **fails** — lock is worktree-scoped and cannot see an unmerged peer |
| assign at the merge point | no | yes | **fails** — no single linear writer to main |
| content-derived or random suffix | no | **no** | **fails** the human-friendliness clause |
| per-author or per-branch namespace prefix | no | degraded | **fails** — leaks authorship into identity |
| reserved ordinal blocks per author | yes | yes | **fails** — a shared mutable resource; two demonstrated failures |

The detail behind each row:

- **`max + 1` collides in practice.** Nine records were renumbered after assignment: `0112→0114`, `0109→0111`, `0108→0109`, `0047→0100`, `0074→0101`, `0055→0109`, `0106→0110`, `0101→0102`, `0098→0101`. Each is the same slug moved to a different ordinal, which is the renumbering the bar forbids. Seven of the nine landed inside three days, 2026-09-11 to 2026-09-13, so this is a live failure mode and not early-project noise. The live corpus passes `next-ordinal.py --check` today only because the collisions were resolved by renumbering, which is precisely the cost being measured.
- **The admission lock cannot close it.** `intake_transaction.py` takes `repository_root / ".workspace-repair.lock"`, so the lock is scoped to a worktree root and two worktrees never serialize against each other. Even a repository-wide lock would not help, because a branch that has allocated an ordinal but not merged is invisible to a peer.
- **There is no linear merge point to allocate at.** `main` took 303 merge commits across 2,248 commits in the 90 days to 2026-09-18, the most recent on 2026-09-14. Merge-time assignment therefore has no single writer to rest on.
- **The collision-free schemes are the ones that stop being human-friendly.** A content-derived or random suffix is what four independent prior-art families in [the append-log fragmentation survey](../research/append-log-fragmentation-survey.md) use, and its whole method is to separate uniqueness from anything a person would read. That fails the second predeclared failure mode, because an identifier nobody can say out loud is worth no more than the slug the repository already has.

### The repository had already adjudicated this

The decisive evidence is not the measurement — it is that **ADR-0108 contains this repository's own finding on exactly this question**, and the child's ADR-0108 assumption read it too narrowly. Its Context section records that ADR ordinals 0055 and 0106 each ended up with two files under a convention whose own rule is that numbers are sequential and never reused, that a max-plus-one helper cannot see an unpushed sibling, and that two peer sessions collided on the released pack version twice in one day. It then concludes: *a repository-global identifier counter is a shared mutable resource across concurrent worktrees, and this repository has demonstrated twice that it cannot coordinate one.* Its constraint 3 is that the scheme "needs no counter shared across concurrent worktrees", and that is why ADR-0108 scoped identity to the spec directory and made it opaque.

Two consequences:

- The independent measurement above **reproduces and extends** ADR-0108's evidence. The two ordinals it names, 0055 and 0106, both appear in the nine renumberings measured here, so the same defect has continued after the record was accepted.
- The child's assumption that ADR-0108 is "a precedent and not a constraint, because it scopes itself to acceptance criteria and verification items inside one spec directory" is **refuted**. ADR-0108's *decision* is scoped that way; its *stated ground* is a general finding about this repository. A repository-global `CAP-0001` / `FEAT-0001` counter is the exact object that record names as demonstrated-infeasible here.

### Verdict against the first bar — killed as written

No candidate rule cleared the predeclared bar. Every rule that avoids a shared counter either renumbers under real concurrency or gives up the human-friendly name, and the one rule that keeps both needs the shared counter ADR-0108 shows this repository cannot coordinate.

**The bar was stricter than the parent required, and that is a defect in the bar, not a finding about the mechanism.** It demanded zero renumberings. The parent intent's guardrail demands only that "no allocation step becomes a file every concurrent author must edit". `next-ordinal.py` edits no counter file — it derives `max + 1` from the directory unioned with `origin` — so it satisfied the parent's guardrail all along while still renumbering. Conflating "collision-free" with "no shared counter" is what made the first bar unsatisfiable by anything.

### Owner decision, 2026-09-18

The owner reframed the outcome rather than dropping it, choosing a fourth option not among the three offered:

- **Repo scope reuses the ADR/RFC mechanism exactly** — `next-ordinal.py`, unchanged.
- **User scope applies the same algorithm per folder.**
- **An ordinal does not migrate when an intent is copied from user scope to repo scope**; it is renumbered to the repository's next ordinal.

That waives the zero-renumbering clause deliberately and accepts the renumbering cost the repository already absorbs for its 119 ADRs and 103 RFCs. The nine measured renumberings are therefore a known, accepted cost rather than a refutation. This is recorded as an accepted bet, not as an untested assumption.

### Re-test of the narrowed assumption

**A1′ — The ADR/RFC allocation approach — `max + 1` over the directory unioned with `origin`, forward-only, numbered at admission — serves intents at repo scope and per folder at user scope, without migrating the corpus.**

Tested against `next-ordinal.py` itself, because it is the working instance of that approach. The owner has since chosen a new prefix-type-aware allocator, so the *spelling* below has moved on; every finding in this section is about the approach and the surrounding chain, and all of it still holds for the replacement.

**Kill condition, predeclared before the probe:** kill A1′ if the allocator cannot serve the intent directory without modification, if a digit-prefixed intent path is rejected anywhere in the admission and reconciliation chain, if adoption forces migration of the existing corpus, or if a renumber would have to reach a citation surface that no mechanical substitution can fix.

**Result — survived.** Measured 2026-09-18 by prefixing one real intent, registering it, reconciling, and reverting:

- **The approach serves the intent directory.** `next-ordinal.py docs/product/intents` returns `0001` on the unprefixed corpus and `0002` once one file carries `0001-`, and `--check` reports no duplicate ordinals, exit 0. The directory needs nothing special; the replacement allocator must reproduce this behaviour per type prefix.
- **A digit-prefixed intent path is valid throughout.** `_is_public_slug_segment("0001-repository-work-graph")` is `True` — digits are in the permitted character set and the leading-character exclusion covers only `_` and `-`. Reconciliation accepted the prefixed entry with `findings: []` and produced zero new findings against the baseline.
- **Adoption is free and forward-only.** The allocator matches on `^(\d{4,})[-.]`, so it cannot see the 135 unprefixed legacy intents at all. Nothing must be migrated, which is the same forward-only posture ADR-0108 D6 took for 442 spec directories.
- **User scope is already supported and is the easier half.** The allocator takes a directory argument, so a user-scope folder needs nothing new. With no git remote there, the `origin` union simply does not apply and it degrades to directory-only `max + 1` — which is *more* reliable at user scope, because a single author on one machine has no concurrent branch to collide with.
- **Every renumber citation surface is mechanically reachable.** 161 files cite an intent path. The ADR/RFC renumber trap — a bare ordinal in an index display column — does not carry over, because ADR-0112 made those indexes generated, so a regeneration fixes them.

The consequence the owner's choice makes concrete: **the ordinal lives in the filename**, so an intent becomes `docs/product/intents/<TYPE>-NNNN-<slug>.md`. That is a change to the slug/path identity contract, which is exactly what Slice 1 is chartered to change, and the descriptive slug is retained.

### Owner decisions, 2026-09-18 — a typed prefix in the filename, and a new allocator

Two further owner decisions settle the identity contract:

- The intent prefix appears in the filename for **every** altitude level, not only `feature`.
- A **new prefix-type-aware allocator** is written for it, rather than reusing `next-ordinal.py` unchanged.

So the filename is `<TYPE>-NNNN-<slug>.md` — `CAP-0001-repository-work-graph.md`, `FEAT-0001-intent-identity-and-registration.md`, and the corresponding prefix at the two product altitudes. Ordinals are per type, so `CAP-0001` and `FEAT-0001` coexist. The existing approach is retained: `max + 1` over the directory unioned with `origin`, forward-only adoption, and renumbering at repository admission.

#### Why the new allocator cannot fall back to the old one

Measured 2026-09-18. `next-ordinal.py` matches `^(\d{4,})[-.]`, anchored at the start of the filename, so a leading `CAP-` puts the type where it expects digits:

| Directory contents | `next-ordinal.py` returns | Verdict |
| --- | --- | --- |
| `CAP-0001-alpha.md`, `FEAT-0007-beta.md` | `0001` | **silently wrong** — matches nothing, restarts from 1, so every call collides |
| `0003-gamma.md` + `CAP-0001-alpha.md` + `FEAT-0002-beta.md` | `0004` | **silently wrong** — counts only the digit-first file |

Neither case errors; both exit 0. Worse, `--check` would report the typed corpus clean, because with nothing matched there are no duplicates to find. **This is the most important thing for Slice 1 to get right, because the wrong answer looks like the right one.** The existing script already states the discipline the new one must inherit: reporting "clean" for a directory it never read would make the check worse than useless, so it keeps those two answers distinct. The replacement must refuse a corpus it cannot parse rather than return `0001`.

#### The new risk this spelling carries: altitude becomes identity

Encoding the type in the filename makes the intent's altitude part of its identity, so an altitude change is a renumber. The evidence for whether that happens is the **workflow**, not this repository's corpus — the corpus shows zero `Level` changes across 130 intents, but that measures a repository that authored feature intents directly and never ran the full recursion, so it cannot speak to the workflow's designed behaviour. The contracts can:

- **`decompose-intent`'s retroactive-parent affordance infers the altitude deliberately wrong.** It says to "infer the altitude and name it for the user to correct", and ADR-0033 records the same affordance as producing an altitude that is "named and user-correctable". An operation whose contract is to propose an altitude for correction will change it as a matter of routine.
- **`frame-intent` elicits altitude and expects a one-word override.** For concept-shaped or greenfield input it asks the altitude explicitly, and the user overrides the suggestion in one word.
- **The vocabulary is open, not a closed enum.** ADR-0033 D2 makes `Level` an open string field carrying a recognized set, explicitly "not closed by a lint", and states that an adopter may name an intervening altitude such as an `initiative` or an `epic`. So the prefix namespace is open-ended: a prefix-keyed allocator will meet a type it has never seen, and cannot enumerate its own namespace to prove `--check` complete.

This collides with ADR-0108 D2 and D3, which say an identifier is assigned once, never renumbered on insertion or reorder, and never reused after removal.

**The owner's own copy rule already absorbs most of it.** Ordinals are assigned at repository admission and renumbered rather than migrated from user scope. At user scope the altitude is still being settled; by repo admission it is decided. So the routine altitude churn — retroactive parents, framing overrides — happens upstream of allocation and costs nothing.

**The residual risk is an altitude correction after repository admission**, which changes an ordinal that other artifacts already cite. That case is now decided: reissue at the new prefix behind a tombstone, recorded below. The option of storing the ordinal without the type and rendering it from `Level:` was available and was not taken, because the owner chose the typed filename prefix.

#### The prefix vocabulary — four tokens, and why the table is closed

Owner decision, 2026-09-18. The four seeded tokens and their filename contract are recorded in this intent's Boundary, which is where the delivered contract lives; this section holds only why they were chosen and what the choice still owes.

All four were verified unused at repository scope on 2026-09-18: every `CAP-` and `FEAT-` string in the tree is from this family's own artifacts, and `VISION` and `STRAT` appear nowhere. The tokens follow the established house shape of an uppercase type token plus a zero-padded ordinal, as used by `RFC` (8,282 occurrences), `ADR` (3,555), `AC` (3,147), `INI` (395) and `VI` (70).

`VISION` was chosen over the shorter `VIS` deliberately. `VIS-0001` sits one character from `VI-0001`, which has 70 uses as a verification identifier, and character-level proximity to a heavily-used token is a reading hazard even when the two are formally distinct.

**The table is closed, and that is the decision.** ADR-0033 D2 makes `Level` an open string field that no lint closes, so the prefix namespace could never be enumerated to prove a duplicate check complete, and a naive derivation is measurably hazardous — uppercase-and-truncate yields `INIT` for `initiative`, one character from `INI-001` and its 395 uses. The allocator therefore refuses an altitude it has no token for, and refusal is cheap because the ordinal is an alias: a refused intent keeps `kind:slug` identity and full graph participation. Adding a token is an explicit reviewed extension of the table. `Level` stays open; the prefix vocabulary does not.

#### Post-admission altitude change — reissue behind a tombstone

Owner decision, 2026-09-18. A typed prefix makes altitude part of identity, so an altitude change after repository admission changes the ordinal. The routine churn is already absorbed upstream, because allocation happens at admission and the workflow settles altitude before then. This decision covers only the residual case.

**A post-admission altitude change reissues the intent at the new prefix and leaves a tombstone at the old filename.** The tombstone is a stub that names the new identity and carries no content of its own.

Three properties make this the cheapest correct option rather than a ceremony:

- **It satisfies ADR-0108 D3 without a shared file.** D3 requires that an identifier is never reused after removal and that every removal is recorded. A repository-global retired list would be a shared mutable resource edited by every author, which is exactly the contention this family exists to remove and exactly what ADR-0108's own ground rules out. The tombstone records the removal in place instead.
- **It keeps `max + 1` correct.** Without a tombstone, retiring the only `CAP` intent leaves the prefix with no files, so the allocator's max returns to zero and reissues `CAP-0001` to a different intent — a reuse D3 forbids. The allocator must therefore count tombstones, which is a build-time requirement on the new allocator and is testable.
- **It keeps path-shaped citations resolving.** The old path still exists and points forward, so the C3 registry sweep becomes correctness work rather than the only thing standing between a rename and a broken reference. Pointer values need no sweep at all, because identity binds to `Slug:` and a renumber does not change it.

This is not renumbering in ADR-0108 D2's sense. D2 forbids renumbering "on insertion or reorder"; an altitude change is a semantic reclassification, which is neither. The reissue procedure must still run the C3 lockstep registry edit and update markdown link targets; C4 below records why pointer values need no sweep.

#### The reference grammar — why identity owns it

Added 2026-09-18 after a defect in this family's own artifacts.

Graph node identity is already unambiguous: `lint-traceability.py`'s `_slug_id` builds `<kind>:<slug>`, so `spec:x` and `intent:x` are distinct nodes and no filename appears in the graph. Dispatch is likewise already unambiguous, keying on `kind == "spec"` plus a `docs/specs/<slug>/spec.md` path shape. **Neither needs an ordinal.**

What is ambiguous is the *pointer value*. `resolve_endpoint` takes a bare slug and suffix-matches it against every node id ending in `:<slug>` or `/<slug>`, choosing among multiple hits by sort order — its own comment concedes that "a slug could in principle suffix-match >1 id". So an ambiguous pointer yields a wrong-but-stable edge instead of an error.

Measured 2026-09-18, the corpus already contains **6 cross-type slug collisions**: `intent-identity-and-registration` and `sdlc-guide-uplift-and-learning-paths` as both intent and brief, and `direct-skill-lifecycle`, `distribution-route-registry`, `portable-agent-plugin-projection` and `rendered-page-visual-inspection` as both intent and spec. One of them fired during this family's own shaping: the delivery brief's `Parent intent:` resolved to the brief itself and `lint-traceability` exited 1.

Two facts make this this child's work rather than a lint fix:

- **All 95 pointer values in the repository are untyped.** Measured across specs, briefs and intents: 29 `Brief:`, 36 `Contract:`, 15 `Discovery:`, 15 `Parent intent:`, and not one carries a type token. A grammar change is an identity contract change, which is what this child owns.
- **`intent-graph-navigation` creates the exposure it would suffer.** Four of the six collisions are latent only because feature intents are not graph nodes today. Making them nodes is that child's purpose, so the grammar must land first.

The cheap direction is to type the pointer, not to rename the artifacts. A typed pointer — `intent:<slug>`, `brief:<slug>`, `spec:<slug>` — resolves without guessing. A typed ordinal is a display alias and never a pointer value, because it does not exist for a refused altitude or a forward-only legacy artifact, and ADR-0108 D5 already blesses the `spec:<slug>/` form for cross-spec citation. Renaming spec directories to carry ordinals instead would touch **4,974 `docs/specs/` path occurrences across 1,299 files**, 276 of them in `workspace.toml`, and ADR-0108's own scope note says the existing corpus is not renumbered. Ninety-five pointer values against nearly five thousand references is the whole argument.

### Constraints carried forward

Neither is waivable and both belong to whoever implements Slice 1.

- **C3 — a renumber couples to the hot file.** `workspace.toml` holds 130 intent path references, and a stale `path` raises `missing_artifact`, which `tests/roster/test_workspace_status_projection.py` treats as fail-closed. So every renumber must edit the registry in lockstep with the rename. That puts this child in direct tension with `workspace-coordination-reorganization`, whose whole outcome is to stop coordination depending on that file, and the two must be sequenced with the tension named rather than discovered.
- **C4 — the renumber trap does NOT generalise to the parent pointer, once identity binds to `Slug:`.** This constraint originally read that `Parent intent:` carries the slug twice and that a filename substitution would leave the bare slug wrong. That was true while identity bound to the filename stem. It is false now: the resolver prefers each artifact's `Slug:` field, a renumber changes the ordinal and the filename but not the slug, and this tree's own renumber on 2026-09-18 demonstrated the bare `Parent intent:` value staying correct while only its link target moved. What a renumber must still sweep is **path-shaped citations** — registry `path` entries and markdown link targets — not the pointer values themselves.

- **C5 — shaping progress is not in the metadata, and no body scan substitutes for it.** Nothing in any intent's preamble records whether it was de-risked or reviewed, so the only way to answer the question today is to read the body and pattern-match its headings. That is not a check: it scales as a full-artifact read per node, it cannot be expressed as a lint over metadata, and it is guessing from prose. A body scan run on 2026-09-19 matched 9 of 130 Draft intents — this one, `CAP-0001` and `CAP-0003` among them — which is enough to refute "Draft means un-de-risked", but the number itself is unreliable **because it was inferred the forbidden way**. The remedy is a declared preamble field, not a better scan.
### Validation hook

```
validation_hook:
  assumption: A new prefix-type-aware allocator, reusing the ADR/RFC approach of max+1 over the directory unioned with origin, delivers per-type human-friendly ordinals (CAP-0001, FEAT-0001) as a filename prefix at every altitude, forward-only and numbered at repository admission.
  kill_condition: The replacement allocator is not collision-equivalent to next-ordinal.py — it returns an ordinal for a corpus it did not fully parse, reports --check clean on a directory it did not read, loses the origin union that widens the view past the working tree to records committed on origin's default branch, or cannot handle an altitude prefix outside the recognized set.
  activity: to-validate — two activities are owed and neither has run. First, a collision-equivalence test of the replacement against next-ordinal.py over paired fixtures carrying the same logical ordinals in the typed and untyped filename grammars, plus an unseen altitude prefix and a corpus it cannot parse; the predeclared line is that it never returns an ordinal or a clean check for input it did not read, set before the test is written. Second, one real cross-branch collision handled end to end, renumbering through the C3 registry edit and the markdown link targets, with a predeclared line of zero stale path-shaped citations.
```

**Owner amendment, 2026-09-21 — "renumbered at admission" became "numbered at admission".**
A1′ above and the hook's assumption both carried the older phrase, which in
context said *when* the ordinal is assigned — at admission, rather than from a
counter shared across worktrees, which is the ground this intent's own
`## Guardrail` rests on. But it reads as a requirement that admission rename
files, and adversarial review of `typed-intent-ordinal-allocator` read it that
way twice. It cannot mean that: the `## Guardrail` makes adoption forward-only,
so an admission that renamed would contradict this intent two sections earlier.

The delivery slice then established that no admission surface *can* rename one —
`intake-intent`'s `allowed-tools` carry no move and no delete, `work-intake`'s
`Bash` is declared for local Python validation and the `workspace-status`
backend, and `intake_transaction.py`'s validated target is the only path its
materializer may write. Renaming therefore belongs to
`intent-renumber-and-reissue`, which needs a confined transactional rename for
renumbering regardless. One word closes the reading; the same change is made in
the brief's reuse bullet, which carried the identical phrase.

**Owner amendment, 2026-09-20 — the hook contradicted its own record, twice.** Two clauses were unreachable as written, so a conforming implementation would have satisfied the kill condition.

The kill clause read "loses the origin union that catches an unpushed sibling". The union does no such thing, and this intent says so correctly in *The repository had already adjudicated this* above, quoting ADR-0108's Context: "a max-plus-one helper cannot see an unpushed sibling". `_remote_ordinals` reads `refs/remotes/origin/HEAD`, so it widens the view to records **committed and pushed** but absent from the working tree; a peer's unpushed work is invisible to it by construction, which is the ground on which ADR-0108 rejected a shared counter in the first place. The clause now names what the union actually reaches, and losing that is still a kill.

The activity clause required collision-equivalence "over the real ADR and RFC corpora". A typed allocator finds no typed records there, and a directory with no typed records cannot be distinguished from a valid intent directory holding only legacy names — which must yield the first ordinal. An equivalence assertion over those corpora would therefore contradict first allocation, and equality over a directory neither script can parse is trivially true besides. The activity now calls for paired fixtures carrying the same logical ordinals in both filename grammars, which is the comparison that has content.

Both defects were surfaced by adversarial review of `typed-intent-ordinal-allocator` and are amended here rather than absorbed there, because the hook is this intent's to own. The delivery contract's own criteria already read this way, so the amendment closes the disagreement rather than changing what will be built.

**De-risked 2026-09-18 — assumption reframed twice by the owner, then survived.** The original assumption was killed as written because its bar forbade renumbering. The owner waived that clause, then chose a typed filename prefix at every altitude allocated by a new prefix-type-aware allocator. The underlying approach survived its probe, and what remains open is recorded above as contract decisions rather than untested bets: how a post-admission altitude change is handled, and collision-equivalence of the replacement allocator. One assumption in the list above still carries no kill condition: that the existing slug/path identity keeps resolving alongside the filename ordinal. This intent is ready for `decompose-intent`, carrying constraints C3 and C4 and the allocator's refuse-rather-than-guess requirement into whatever it produces.

## Decomposition

This intent is a `feature`, so it is the leaf: `decompose-intent` produces its delivery unit rather than child intents.

- [Brief: intents get a typed ordinal identity, a declared shape, and canonical references](../briefs/intent-identity-and-registration.md) — the delivery unit this feature projects to. The brief owns its own status and its own Spec map.

Ordinal allocation, repository placement, personal-to-repository promotion, discovery and duplicate validation are candidate delivery slices of this feature. The cut between them belongs to that post-Ready decision.

### Decomposition decisions

- **2026-09-18 — a delivery brief, not a single delivery contract.** ADR-0077 D1 routes one independently shippable change in one repository to a spec and several to a brief with specs beneath it. This intent owns a new allocator, the `<TYPE>-NNNN-<slug>.md` filename contract, a closed prefix table with refusal for any altitude outside it, a renumber and reissue procedure with a tombstone, and safe placement paths. Those are several independently shippable changes that share one outcome and need coordinating, so the brief is the correct projection and a single delivery contract would have bundled unrelated shippable units into one spec.
- **2026-09-18 — the slice cut was deliberately not made here.** Create mode leaves the Spec map empty and creates no placeholder slices, and `author-delivery-brief` §4 places the cut *after* a durable Ready transition behind a second, distinct confirmation — so it is a post-Ready decision, not the Ready decision. Naming slices now would pre-empt a review that has not run and would put a status in a second home.
- **2026-09-18 — placement was kept in the brief rather than split out, and flagged instead.** Configuration-resolved placement is the one in-scope item with no measurement behind it, so it is the weakest candidate for the same brief. It stayed because it shares the admission path with the ordinal work, and the brief records as a Ready gap that a review should decide whether it is separable. Splitting it now would have created a second brief on inferred evidence.
- **2026-09-18 — no tracker projection.** The optional one-way projection step was skipped; `external-tracker-projection` owns that surface and is not yet shaped.
- **2026-09-18 — no ranking step.** Ranking applies to competing children; a leaf with one delivery unit has nothing to rank.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
