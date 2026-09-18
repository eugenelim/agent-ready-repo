# RFC-0102: An ADR's metadata is checkable, and the freeze binds its prose

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-09-16
- **Date closed:** 2026-09-17
- **Decision weight:** standard
- **Related:** [ADR-0027](../adr/0027-adr-format-is-madr-aligned-but-lean.md), [ADR-0041](../adr/0041-adr-template-optional-summary-revisit-confirmation.md), [ADR-0112](../adr/0112-index-tables-are-generated-or-absent.md), [RFC-0038](0038-align-adr-template-with-madr.md), [RFC-0056](0056-right-size-adr-template-decision-summary-revisit-confirmation.md), [`docs/specs/adr-template-right-sizing/`](../specs/adr-template-right-sizing/)

## Reviewer brief

- **Decision:** An ADR's freeze binds its **prose**, not its metadata. Adopt a metadata block a program can check, and let connection fields in it stay writable after acceptance.
- **Recommended outcome:** accept
- **Change if accepted:**
  - New metadata fields: `Areas` (bounded, multi-valued), `Reversibility`, `Supersedes in part`, `Superseded by`, `Superseded in part`. Reshaped: numbered `D1..Dn` constraints, a bare-token `Status`, and the existing `Supersedes`, which gains a mirror obligation.
  - A prose/metadata freeze split, replacing the Status-only rule the `new-adr` skill, its template and its how-to guide each state today.
  - One portable shape lint over every ADR, warn-only until the corpus is migrated, then enforced.
- **Affected surface** — the same set the Follow-on list enumerates as shipped:
  `new-adr`'s SKILL.md, template and evals, plus `new-rfc`'s errata clause, taking a
  **minor** `governance-extras` bump in both `pack.toml` and `.claude-plugin/plugin.json`
  because the shipped lint script is a new primitive;
  `guides/governance-extras/how-to/new-adr.md`; the lint in both its adopter-shipped and
  `tools/` copies, plus the gate-chain entry that invokes it; and the index generator,
  which must read the new supersession field before any record carries a bare-token
  status.
- **Stakes:** costly. Forward-only, and it changes a rule shipped to adopters in three places.
- **Review focus:** whether the prose/metadata line is the right place to cut the freeze; whether `Areas` earns a field given a curated index already exists.
- **Not in scope, and deliberately carved out:** the `check-adr-immutability` rewrite; dependency edges; file, path, glob or time scope selectors; the spec and RFC freeze rules; the agent-routing consumer.

## The ask

Accept the prose/metadata freeze split, the metadata field set, and a shape lint over
records authored after acceptance.

ADR-0027 deferred exactly this. Its Confirmation section records that "There is **no
mechanical ADR-status lint** today … adding one is a separate, RFC-gated convention and
is deferred". This is that convention.

## Problem & goals

**A body of ADRs accumulates and nothing reads it during work.** `AGENT_RULES.md` — the table built
for "when X, read Y" and read every session — ships empty. Root `AGENTS.md:64` names
`docs/adr/` once, as a row in a documentation index. Two skills in the `iac-terraform`
pack read decision records, both routed through a governance index, both scoped to
infrastructure. Nothing else does.

A decision no future session reads is an archive, not a control. Making one readable
requires that it first be parseable, and the metadata block is not:

- **`Status` is not an enum.** A field that admits a qualifying clause accumulates them.
  Once the lifecycle token can be followed by prose, a record can carry several
  "superseded in part by" clauses, and the token stops being comparable.
- **A reader launders the field to cope.**
  `packs/governance-extras/.apm/skills/new-adr/scripts/index-records.py:64` truncates the
  status at `. `, or at whitespace followed by `—`, `--`, `(` or `<!--`, so the generated
  index shows a clean `Accepted` for a record whose raw status is a paragraph. The
  behaviour is deliberate and pinned by a test; the point is that it exists because the
  field needed it.
- **The constraint has no address.** The decision is prose inside `## Decision`, so a
  partial supersession has nothing to point at and must be narrated.
- **Corrections have no legal home.** `new-adr` defines no correction convention — zero
  mentions in its SKILL.md or template — so authors improvise a section, in whichever
  spelling occurs to them.

Goals: make every metadata field either validated or deliberately unvalidated; give each
constraint a permanent address; give supersession a parseable, two-sided representation;
and give a correction somewhere legal to go.

Non-goals: enforcing that code obeys an ADR (that is a gate, and `reconcile-iac` already
prototypes one); and changing anything about the 115 existing records.

## What this changes, and where that rule lives

The rule this RFC replaces is the **Status-only rule**, and it is stated in three
artifacts, all owned by the `new-adr` skill and all in this RFC's affected surface:

| Where | What it says today |
| --- | --- |
| `packs/governance-extras/.apm/skills/new-adr/assets/adr.md:24` | "Once Accepted, the body is frozen; **only the Status line moves after that**." |
| `packs/governance-extras/.apm/skills/new-adr/SKILL.md:243` | "`Accepted`, the body is frozen (see Lifecycle below)." |
| `guides/governance-extras/how-to/new-adr.md:215` | "The body is frozen at acceptance. **Status-only changes** (`Accepted` → `Deprecated` \| `Superseded by ADR-NNNN`) **are the only edits permitted.** Anything else is a *new* ADR that supersedes." |

The guide also names `Superseded by ADR-NNNN` as a status *value* (`:170`), which § 2
replaces with a bare token plus a dedicated field.

So this RFC does not supersede a third party's rule. It changes a rule the skill it edits
already owns, in the three places that state it, and the RFC's affected surface and
follow-on list both carry all three.

**What replaces it.** The freeze binds an ADR's **prose**. Its metadata block is a
declared set of fields whose values may change after acceptance, per the zones in § 4.

**Why this is not "just adding a line".** The template today ships
`- **Supersedes:** <!-- ADR-NNNN, or "none" -->` — an empty line carrying a comment, no
value. Under this RFC the template pre-declares **every** supersession field with the
`none` sentinel, so a new-format ADR carries them from creation. Recording a supersession
then changes a declared field's *value*; it adds no line and touches no prose. That
distinction is the whole mechanism, and it is why the change is narrow.

**The one genuine widening.** `## Errata` is a prose section, so appending to it is a body
edit however it is framed — no sentinel makes a prose section a declared field. This RFC
licenses that append for meaning-preserving clarifications only: an erratum clarifies what
a decision means and cannot alter what was decided. The residue is real and is carried
explicitly — a reader who greps mid-file still lands on uncorrected prose with no pointer
in view — and the reason to accept it is that an ADR has no living counterpart where the
correction could otherwise live, which is why records already improvised the section.

**Sequencing precondition.** This RFC assumes the Status-only rule is owned by the
`new-adr` skill, its template and its how-to guide. If, when this lands, any other
document also states that rule for ADRs, that statement must be updated in the same change
or this RFC is contradicted on arrival. The affected surface is written on the assumption
that no such document remains.

**A note on supersession grammar.** Say "in part" and say which part; annotate both ends.
Those disciplines are preserved and made mechanical here — § 3's mirrored pairs are the
both-ends rule implemented in fields rather than in review discipline, and
`Superseded in part: ADR-0084 D3` names the part machine-readably. § 3 also restricts the
fields' value domain to decision-record ordinals, so an ADR field can never point at a
spec.

## Proposal

### 1. Parse tiers, stated in the template

Which tier a fact belongs to decides whether a program can check it. T1 facts are single
values or short lists a checker can compare; T2 facts are lines whose *presence and
layout* are fixed; T3 facts are sentences no checker touches.

| Tier | Contents | Lint posture |
| --- | --- | --- |
| **T1** | Metadata: `Status`, `Date`, `Areas`, `Reversibility`, and the supersession fields | value and shape validated |
| **T1-unchecked** | Metadata: `Decision-makers`, `Consulted`, `Informed`, `Related` | **deliberately unvalidated.** Human names and cross-artifact pointers have no checkable domain here; `Related` reaches RFCs, specs and contracts, each needing its own resolver |
| **T2** | `D1..Dn`; `Decision drivers`; `Alternatives considered`; `Confirmation`'s `Mode` / `Signal` / `Owner`; the `Revisit if:` line **in `## Consequences`** | presence and layout checked; wording never |
| **T3** | `Context`, the rest of `## Consequences`, every `Decision summary` bullet — including `Applies to` and the mirrored `Revisit if:` — and the lead sentence of `## Decision` | untouched |

`Revisit if:` appears twice by design: the template makes `## Consequences` its canonical
home and the `Decision summary` copy a verbatim mirror. **The T2 check reads the
`## Consequences` line only**; the mirror is T3. Naming which one is checked is the same
discipline the two `Decision` homes need below.

`Mode`, `Signal`, `Owner` and `Revisit if:` are **T2, not T1**: they are `**Key:**`-shaped
lines inside prose sections, the lint checks only that they are present and non-empty, and
`Signal` and `Owner` have no value domain at all. Putting them in T1 would claim a value
check that does not exist. T1-unchecked exists so that § *Problem & goals*' first goal is
met literally — every metadata field the template ships is either validated or explicitly
declared unvalidated, with none left unclassified.

Two things are called "Decision" and the template must not blur them: the
`- **Decision:**` bullet in the optional `Decision summary` is T3 restatement, while
`## Decision` holds a T3 lead sentence followed by T2 numbered constraints.

The template warns against promoting a T3 fact into a T2 line for tidiness. The chain is:
a line with nothing checkable behind it still looks checkable, so the next person extends
the lint to cover it, so the lint starts judging prose, so it produces false positives, so
someone turns it off. Stopping at step one is cheaper than any later step.

### 2. Metadata fields

**`Areas:`** — a comma-separated list, **at most three**, each matching `[a-z0-9_-]+`.
Multi-valued because decisions cross-cut: ADR-0017 binds security, the gate chain and CI
at once, and a single-valued key would make a query for one of those silently miss it.
Bounded at three because the field is a filter, and a record needing four areas is usually
two decisions.

**There is deliberately no fixed vocabulary.** Adopters' architectures differ and a
shipped list would be wrong somewhere. The lint checks arity, uniqueness and token shape —
never which token. Drift is made visible and deliberate rather than policed: `new-adr`'s
existing write gate surfaces the areas already in use and makes coining a new one an
explicit answer.

Areas are conceptual. They do not have to correspond to any folder, and a path is never
an area.

*Relationship to a governance index.* A domain in a governance index is a **kind of area**
— the adopter's curated routing view over part of the same vocabulary. Where such an index
lists a decision under a domain, that domain key should be among that decision's areas.
This is a **convention, not a lint rule**: the lint never checks which token, the index is
adopter-owned and may legitimately lag, and its `adrs:` list is multi-valued per domain so
a record could otherwise be pushed past the arity cap. It is stated as guidance so the two
vocabularies converge by default. The token shape admits `_` so an existing domain key
such as `pipeline_auth` qualifies unchanged.

**`Reversibility:`** — `high` or `low`. `low` means replacing the decision costs a
migration, a data-loss window, or renegotiating a contract with someone outside the team.
Justified on immediate value, as `Areas` is: it tells a human author or reviewer weighing a
change how much of a one-way door they are standing in front of, which today has to be
inferred from `Consequences` prose. Agent consumption is a later payoff and is not claimed
here.

**`## Decision`** gains numbered constraints after its lead sentence:

```
- **D1:** User activity is stored in Postgres, not DynamoDB.
- **D2:** Session data is out of scope and keeps its current store.
```

Dense from D1, never renumbered, never reused: these IDs are permanent addresses other
records point at, so renumbering silently retargets another record's pointer. A carved-out
constraint keeps its bullet as written; the carve-out is recorded in the supersession
fields.

**`Status:`** becomes one bare token from `Proposed | Accepted | Rejected | Deprecated |
Superseded`. The template today offers four bare tokens plus the compound `Superseded by
ADR-NNNN`; this replaces the compound with a bare `Superseded` and moves the pointer to
its own field.

**`Confirmation`'s `Mode`** loses its value enum, because the enum fails structurally
rather than lexically: arity
(`reviewer-checked + lint/CI`), time (`reviewer-checked, escalating to lint/CI when the
route ships`), and scope (``reviewer-checked, with a `none` residual on the retirement
half``). A larger enum fails the same way, because one value cannot hold a compound, a
trajectory, or a per-constraint variation. The lint checks that `Mode`, `Signal` and
`Owner` are present and non-empty, and reserves one token — `none` — as the declared
*deliberately unpoliced* value so that state stays countable. The token leads the value —
`Mode: none — <reason>` — because the template and SKILL.md both require a reason after it,
and a count expecting a bare `none` would find nothing. The five current values
survive as a non-binding example list. An optional `Mode (Dn):` override is available
where enforcement genuinely differs per constraint, is never required, and is T2 like its
parent.

### 3. Supersession: one edge type, two cardinalities, both sides mirrored

Dependency edges are out of scope. Supersession is the only edge that changes whether a
decision **binds**; everything navigational already has `Related:`. An unenforced graph in
Markdown rots, and there is no service here keeping one consistent.

Each cardinality is a *mirrored pair* — the same fact written on both records, so either
can be read alone. In both halves the D-IDs belong to the **superseded** record.

Whole-record supersession, ADR-0050 replaced by ADR-0109, on disk:

```
# ADR-0050 …                            # ADR-0109 …
- **Status:** Superseded                - **Status:** Accepted
- **Superseded by:** ADR-0109           - **Supersedes:** ADR-0050
```

Partial supersession, ADR-0084 carving out ADR-0017's `D3`, on disk:

```
# ADR-0017 …                            # ADR-0084 …
- **Status:** Accepted                  - **Status:** Accepted
- **Superseded in part:** ADR-0084 D3   - **Supersedes in part:** ADR-0017 D3
```

`D3` is ADR-0017's constraint in both files. A record may not name the same target in both
`Supersedes` and `Supersedes in part`. Partial supersession leaves `Status` as `Accepted`,
which is what rule 1 wants — nothing invites a reader to discard a record that is mostly
still correct — and it keeps `Status` a bare token rather than a token plus prose.

**Field grammar.** Every supersession field takes `none` or a `;`-separated list of
entries. An entry is one decision-record ordinal, optionally followed by `,`-separated
D-IDs belonging to the superseded record. The separator split matters: `;` divides
entries, `,` divides D-IDs within an entry, so § 4's append predicate reads
semicolon-separated entries for these fields and comma-separated tokens for `Areas`, whose
values contain neither.

One decision superseding parts of several earlier ones is an ordinary case, not an edge
one, so the grammar admits a list rather than a single target. The value domain is
restricted to decision-record ordinals, which is what preserves the spec-end asymmetry —
no ADR field can name a spec.

`none` is the empty value, not an entry, so replacing it with a target is not a deletion.

### 4. Mutability: the freeze binds prose, not metadata

A claim records what we believed and decided at a moment. A connection records how the
decision sits in a graph that keeps growing. Connections are discovered after the fact by
definition; claims are not.

| Zone | Post-acceptance | Contents |
| --- | --- | --- |
| **Live** | append-only lists; replace-in-place for `Status`, which is a state rather than a list | metadata: `Status`, the supersession fields, `Areas` |
| **Attested** | frozen — these say who decided what, when, and how they judged it *at the time*, so rewriting them falsifies the record rather than correcting it | metadata: `Date`, `Decision-makers`, `Reversibility` |
| **Frozen** | frozen | every prose section, except `## Errata` |
| **Append-only** | items may be added; an existing item may not be removed or rewritten | `## Errata` |

`Reversibility` sits in Attested because it records the judgement made at the time. Open
question 1 records the argument for making it Live instead.

`Consulted` and `Informed` sit in no zone: the template licenses deleting them when empty,
and a field that may be absent cannot be append-only — re-adding it later is the line
addition the sentinel mechanism exists to avoid. They stay outside the mutability rule, as
they are today.

**The append predicate.** For a Live list field, the set of comma-separated entries after
the change must contain every entry present before. For `## Errata`, every entry present
before must still be present byte-identical, where an entry is a top-level `- ` item —
which the template prescribes, so a conforming record has them by construction.

**Scope.** This rule binds every ADR. There is no grandfathered set and no format
threshold: the corpus is migrated to the new format (§ 7), so one rule governs one
corpus. Keys the corpus carries that the template does not define — `Deciders`,
`Renumbered`, `Refined by`, `Extended by`, `Carried forward by` — are migration findings,
resolved by renaming or removing them, not a classification the zone table has to absorb.

Attribution is the one thing migration does not rewrite. `Decision-makers` is Attested, so
a record carrying the legacy `Deciders` key has the key renamed and the value preserved
exactly.

### 5. Errata

`new-adr` gains an `## Errata` section using the format
`packs/governance-extras/.apm/skills/new-rfc/SKILL.md:277-286` already defines:
append-only dated entries, a later entry superseding an earlier one by being later,
entries never deleted, and authoritative current state preferred over a dated audit trail
once more than one entry exists **or any entry supersedes another**.

**An erratum clarifies what a decision means. It cannot alter what was decided.** A
changed decision is a new ADR; a partially changed one is the mirrored pair in § 3.
Supersession is for replacement only.

Two narrowings from the RFC convention. ADRs take only the `## Errata` half — a `Proposed`
ADR is not frozen and can simply be edited, so there is no in-flight `## Amendments`
state. And for ADRs the heading is **fixed**, because a check keying on it cannot accept
three spellings. Three of the eight records carrying a correction section use
`## Amendments` or `## Erratum (<date>)`; the migration renames them to `## Errata`,
which is a heading change and leaves every entry intact.

`new-rfc`'s "sole home of this convention" claim narrows to RFCs. Root `AGENTS.md` cuts
both ways — it asks that a lasting rule live "in one place that is easy to find", and that
each skill "stand whole on its own". The tiebreak is **reader attention, not path
resolution**: both skills ship in `governance-extras` and install together, so the file is
on disk either way, but an author invoking `new-adr` has no reason to open `new-rfc`'s
SKILL.md, and a convention they never read is one they will reinvent, in whichever
spelling occurs to them. The duplication is one short section and is stated as deliberate.

### 6. Enforcement: one lint, warned then enforced

A **portable shape lint** — file-level, local, fast, checking T1 and T2, shipped to
adopters and ported to `tools/`. It reads every ADR. There is no scope key, no threshold
and no exclusion list, because there is no legacy set to separate: § 7 migrates the corpus
instead.

**It warns first, then blocks.** On acceptance it runs advisory over the whole corpus,
which is the migration worklist. Once the corpus is clean it flips to blocking, via its
entry in the gate chain (`tools/repo/build_gate_chain.py`) alongside the existing
`check-adr-ordinals` and `check-adr-index` steps.

The warn-only phase is the pattern this RFC criticises elsewhere — a check that always
exits 0 is documentation, not a control. It is only defensible because the flip has a
named precondition and a tracked owner: the migration in § 7, and the follow-on item that
carries the flip. If the migration stalls, the lint stays advisory and this RFC has bought
a worklist rather than a control; that is the honest failure mode, recorded in Risks.

**One surface this RFC does not ship.** The `check-adr-immutability` rewrite is follow-on
work, and it owns two problems this RFC does not solve: the job runs `tail -n +12` on
`git diff` output rather than on the file and always exits 0
(`.github/workflows/docs.yml:341-360`); and it requires a `- ` bullet on the status line
(`:352`), so it silently skips any record that writes `**Status:** Accepted` unbulleted —
a shape the index generator accepts by design, which is how the two readers diverged. It also cannot block a merge where it sits — `docs.yml` is not a required
context, a finding this repository already recorded for `pages.yml`
(`.github/workflows/build-check.yml:375`) — so rehoming it belongs to that work.

### 7. Migration

A repository adopting this format migrates its existing records to it. Most of that is
metadata, which § 4 makes writable after acceptance, so it needs no exemption: assign
`Areas` and `Reversibility`, rename a legacy attribution key without touching its value,
and pre-declare the supersession fields with their sentinel. The rest is prose structure —
numbered constraints, a `Revisit if:` line, an alternatives shape — which is a body edit,
so it is licensed here as a one-time conversion rather than left to accrue as drift.

Two ordering constraints hold wherever this is done. The index generator must read
`Superseded by:` **before** any record carries a bare-token status, or the generated index
loses its supersession pointers. And the guidance surfaces named in *What this changes*
should land with or before the conversion, so a migrated record does not contradict the
instructions a reader is following.

Sizing the conversion is a local matter for whoever adopts the format, and the lint in § 6
produces the worklist.

## Options considered

**Where the freeze cuts** — axis: what the freeze binds.

| Option | Verdict |
| --- | --- |
| **Prose frozen, metadata live** | **Chosen.** A pre-declared metadata field changing its value is not a prose edit, and the Status-only rule already licensed exactly one such field — this widens that set rather than inventing the category. |
| Keep the Status-only rule as stated | Rejected. It cannot express a supersession that carries a machine-readable target and a constraint list, and it leaves a correction with nowhere legal to go — records improvised one anyway. |
| Whole record mutable, git as the audit trail | Rejected by the Attested zone. Rewriting who decided what and when is falsification, not correction. |

**Should `Areas` be a field at all, or an external index?** — axis: where the
classification lives.

| Option | Verdict |
| --- | --- |
| **A record-owned field, alongside the existing index** | **Chosen.** Self-registering: written when the record is written, presence enforced by the lint. |
| Extend the governance index only; add no field | Rejected on three grounds, only one of which is contingent. Contingent: the claim that a skill "adds any missing domain rows" is unimplemented, so nothing in the repository writes one — registered as a defect whose fix is an owner call, and if it is implemented this ground lapses. Standing regardless: the index is adopter-owned and declares itself "not a generated scaffold", so a pack cannot author it; and it holds a framing question and standards paths an ADR field cannot carry. The rejection survives on the two standing grounds alone. |
| Generate one from the other | Rejected in both directions: nothing writes an index row to generate a field from, and generating the index would contradict its stated adopter-authored design. |

**Cardinality and vocabulary of `Areas`** — axis: openness and arity.

| Option | Verdict |
| --- | --- |
| **Bounded multi-valued, open vocabulary** | **Chosen.** Decisions cross-cut, so single-valued produces silent misses; unbounded stops filtering. |
| Single-valued | Rejected. A query for one area would miss a record filed under another that binds it equally. |
| Closed vocabulary | Rejected. Adopters' architectures differ. The conventional names are `tags` where free-text and `domain` where enumerated; `domain` is taken here by the index and `tags` would signal unbounded, so neither name is available. |

**Where the supersession pointer lives** — axis: dedicated field vs annotation on the
status token.

| Option | Verdict |
| --- | --- |
| **Dedicated fields** | **Chosen.** Partial supersession needs a machine-readable target and constraint list, which a status annotation cannot carry. |
| Keep the annotation on the status token | Rejected. It is the thing the index generator already truncates. |

**Confirmation `Mode` vocabulary** — axis: openness of the value set. Chosen:
presence-checked with one reserved token. Rejected: keeping or widening the enum, because
most failures are structural (see Evidence) and no enum size fixes them.

## Risks & what would make this wrong

- **`Areas` ships unconsumed by tooling.** No agent-routing consumer lands here, and the
  row shape for one is constrained: the seeds lint requires a routing row's read target to
  be a backticked `.agents/rules/*.md` path
  (`packages/agentbundle/agentbundle/catalogue_tooling/lint.py:559-579,641-654`), so a row
  cannot name `docs/adr/` or express a query. The legal route is a rules seed naming the
  binding decisions, which is separate work. `Areas` is justified on immediate value — a
  classification an author can search before re-deriving a decision — not on routing that
  has not shipped.
- **An open vocabulary fragments.** Synonyms are the documented failure of open tagging and
  no mechanism is proven to eliminate them. Bounded arity and confirm-before-coining are
  mitigations, not guarantees.
- **Homonyms, from sharing a namespace with a governance index.** One token can carry two
  meanings — an adopter using `state` for a state machine while the index's `state` means
  remote Terraform state. Reserving the index's domain keys is the available answer and is
  not proposed here; the case is recorded rather than solved.
- **A single label may not carry retrieval alone.** Bounded multi-valued with an open
  vocabulary is asking a label to do work that path or glob scope would do more precisely.
  If routing precision disappoints, the correct response is to add path scope —
  deliberately out of scope — and **not** to add more area vocabulary.
- **Two status grammars.** ADRs stop sharing the supersession carrier that frozen specs
  use. The spec linter walks `docs/specs/*/spec.md` only
  (`packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py:18`) and has never read an
  ADR, so no checker breaks; the cost is a reader learning two conventions.
- **D-ID discipline is human.** The lint catches gaps and duplicates but not a renumber
  that stays dense. A mirrored pointer breaks on renumber, covering the cases that matter.
- **The lint never leaves warn-only.** This is the likeliest way the RFC fails. Clearing
  an existing corpus is real work, and an advisory check that nobody clears is the
  inert-gate pattern this RFC exists to remove. The mitigation is that the flip is a
  tracked follow-on with the conversion as its stated precondition — not that anyone has
  promised to do it.
- **This would be wrong if** the classification never narrows anything in practice — if
  authors file everything under two or three broad areas, the field costs upkeep and
  returns nothing.

## Evidence & prior art

**Grounded in mechanism, not in one corpus.** Each failure above is checkable against the
code rather than against a record count, which is what makes it portable:

- A qualifying clause in `Status` forces a downstream reader to truncate. The generated
  index does exactly that today —
  `packs/governance-extras/.apm/skills/new-adr/scripts/index-records.py:64` cuts the value
  at `. `, or at whitespace followed by `—`, `--`, `(` or `<!--`. The behaviour is
  deliberate and pinned by a test. It exists because the field needed it.
- `Mode`'s enum fails on arity, time and scope, shown by the three value shapes quoted in
  § 2. None of them is a typo; each is a real conformance story one value cannot hold.
- `Applies to` carries exclusions and conditions a token list cannot express — "not the
  CLI, the adapter contract, or other packs"; "this repo's own web surface only — **not** a
  primitive, template, or framework prescribed to adopters"; "forward-only, no existing ADR
  is converted". `Areas` narrows the candidate set and `Applies to` decides applicability;
  neither is derivable from the other.
- A `## Decision` written as prose gives a partial supersession nothing to point at, which
  is why the pointer ends up narrated in `Status` rather than recorded in a field.

**Prior art in repo.** `tests/roster/test_decision_record_ordinal_uniqueness.py` is the
precedent for a control that walks the real corpus and asserts a non-empty floor first.
Its `RENAMES` table is not exhaustive — `docs/adr/0114-…:6` records a fifth repair
(`0112`→`0114`) the table omits — which is why § 6's claim about completed repairs is
stated over the corpus rather than over the table. `reconcile-iac` is the precedent for
gating a diff against resolved decision records.

**Prior art, external.** [MADR 4.0](https://adr.github.io/madr/) presents status as
optional metadata with illustrative values and specifies no immutability rule, no closed
status vocabulary, no machine-readable schema and no validation tooling. There is no
standard to diverge from on any point here.

**Evidence against this proposal, recorded because it is the strongest counter.** A survey
of ADR tooling found that the most widely used tools — adr-tools, MADR, the Backstage ADR
plugin, Structurizr — expose **no** classification field at all, and that MADR evaluated a
per-record category explicitly and rejected it, choosing filesystem subfolders.

Two reasons this does not decide the question. MADR's stated objections were losing
filesystem filtering and falling outside CommonMark; we filter with a lint, and this
template is already not CommonMark-pure. More decisively, MADR's chosen alternative is
**foreclosed here**: its own decision notes that subfolders make ordinals local to a
category rather than unique across the repository, and this repository gates global ordinal
uniqueness in the build chain. Of the options MADR weighed, the one it picked is the one we
cannot have. Adoption counts are also a weak guide to correctness, and enterprise
practitioner guidance runs the other way, arguing for multi-axis tagging at scale.

No study was found showing that classifying decision records improves retrieval, in either
direction. The absence is recorded as a gap in the evidence, not as support for either
position.

## Experiment / validation

A prototype lint was built and run against the drafted template before this RFC was
written. **The prototype is not retained in the repository**, so the figures below are
unverifiable by a reviewer and are offered as authoring evidence, not as a checkable
artifact. Acceptance re-derives them: the ported lint and its fixtures land under `tools/`
with the first new-format ADR, and that is the copy a reviewer can run. It implements **15 check classes** across T1 and T2, including both halves of each
supersession pair. Fixtures are **synthetic records modelled on real ones**; no existing
record was converted, consistent with the forward-only migration.

| Run | Result |
| --- | --- |
| Clean fixtures, including one carrying three areas with a `snake_case` domain key | 0 findings, exit 0 |
| One fixture broken on purpose | 14 findings across 13 codes |
| Void test — 4 mutations to clean records | all 4 caught |
| Void test — 4 mutations to each half of a mirrored pair | all 4 caught, reported from both sides |
| Void test — over-cap, duplicate, bad token, absent `Areas` | all 4 caught |

A fixture modelled on ADR-0017's four narrative clauses was re-expressed as mirrored pairs
and validated in both directions, including that each cited D-ID exists in the record that
defines it.

**The void test refuted two earlier designs, which is why neither survives.** Scoping the
lint on the presence of the classification field is fail-open — deleting the field silently
removed a record from the scan. Replacing that with a format threshold then let the lint
report success having checked nothing, a control that cannot fail. Reading every record
removes both by construction: there is no scope key to subvert and nothing to exclude, so
an empty scan cannot pass.

Validation plan on acceptance: port the prototype to `tools/`, walk it against the real
corpus for the floor, and land it in the same change as the first new-format ADR, which is
its first fixture.

## Open questions

None outstanding. Two were carried in earlier drafts and are now decided:

- **`Reversibility` is Attested.** It records a judgement at a point in time, and making it
  editable would let someone downgrade `low` to `high` to make a change look cheaper. Where
  the assessment later changes, that is a `Revisit if:` trigger, not an edit. The migration
  assigns it once, dated, as a later assessment by the same decision-maker.
- **There is no format threshold.** An earlier draft keyed the lint's scope on an ordinal,
  which needed a value nobody could know before merge and an exclusion for renumbered
  records. Migrating the corpus removes the question.

## Follow-on artifacts

Every item below is either in the affected surface above or explicitly carved out of it.

**Shipped on this RFC's acceptance:**

- `packs/governance-extras`: template, `new-adr` SKILL.md with the confirm-before-coining
  step, evals, a version bump, and one narrowing edit to `new-rfc`'s errata section.
- `guides/governance-extras/how-to/new-adr.md`: it states that the body is frozen and that
  status-only changes are the only permitted edits, both superseded by § 4.
- The shape lint, ported to `tools/`.
- An ADR recording this format decision, authored in the new format, shipping with the lint
  as its first fixture.

**Carved out, each needing its own artifact:**

- **The record conversion** described in § 7, which is the stated precondition for the
  item below. Sizing and sequencing it is local work, not part of this decision.
- **The enforcement flip** — moving the lint from advisory to blocking in the gate chain
  once the migration is clean. Tracked separately so that an advisory check cannot quietly
  become permanent.
- The `check-adr-immutability` rewrite and its move to a required context.
- An `## Errata` entry on ADR-0027, noting that the lint it deferred has shipped — the
  first exercise of the new convention, and a test of whether it is usable. It rides with
  the migration, since that is when ADR-0027 is edited anyway.
- A replacement spec for index-table generation, superseding the historical
  `docs/specs/index-table-generation/`: read the new supersession field so the generated
  index keeps rendering a pointer, and decide open question 2.
- A rules seed under `.agents/rules/` plus the `AGENT_RULES.md` row that points at it — the
  agent-routing consumer.
- Aligning `reconcile-iac`'s expectation that an ADR carries a `Constraints` section with
  where constraints actually live; no ADR has such a section.
