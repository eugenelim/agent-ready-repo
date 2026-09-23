# Verification ledger — intent-reference-grammar-migration

## 2026-09-22 — T1 (RFC authoring): a fourth `Brief:` consumer exists, and it refuses the canonical form

**Status:** blocking. Surfaced to the owner; no spec or plan edit made.

### What the contract says

`plan.md` § Risks states: "**Three consumers read `Brief:` and only two should change.**
`workspace_status_engine.py` never reads the spec header — confirmed, not assumed — so
treating all three alike would break dispatch for nothing."

`spec.md` AC-0009 scopes the three-way agreement to the guide, the `new-spec` template,
and `lint-brief-coverage.py`.

### What the code does

`packages/agentbundle/agentbundle/_data/workspace_status_engine.py` **does** read the
spec header's `Brief:` field, through a generic parser rather than a named one — which
is why a search for the string `Brief` in that module does not find it:

1. `_parse_preamble_fields` (`:1818-1824`) matches `^- \*\*(?P<name>[^*]+):\*\*\s*(?P<value>.*)$`
   over any artifact and keys the result on the **lower-cased** field name. A spec's
   `- **Brief:** …` line therefore lands under the key `brief`.
2. `:2221-2223` reads it into the artifact's provenance parent:
   `parent = _normalized_optional_artifact_value(fields.get("brief") or fields.get("source parent") or fields.get("parent"))`.
3. `_dependency_metadata_safety_finding` (`:2653-2660`) validates that parent for a spec
   with `require_local_brief=kind == "spec"`.
4. `_provenance_path_is_invalid` (`:2629-2640`) returns invalid when the value is not a
   repository-relative path, or is not a canonical local brief path per
   `_is_canonical_local_brief_path` (`:723`), which requires exactly
   `docs/product/briefs/<single-segment>.md`.

### Measured

Loading the module and driving the real functions with a spec preamble:

| `Brief:` value | `_provenance_path_is_invalid(require_local_brief=True)` |
| --- | --- |
| `brief:intent-identity-and-registration` | **True** — emits `invalid_artifact_path` (`dependency parent`) |
| `intent-identity-and-registration` (bare slug) | **True** — same |
| `docs/product/briefs/intent-identity-and-registration.md` | False — accepted |

### Consequence

The guide's parenthetical at `guides/core/reference/product-brief-fields.md:100` — "a bare
slug fails reconciliation and blocks dispatch" — is literally true of the spec header, not
of a different surface. It is the accurate description of this code path.

Adopting `brief:<slug>` without also changing this module would make all 34 swept specs
emit a dispatch finding. The plan's Risks bullet, AC-0009's consumer list, and T6's
`Touches:` are each incomplete against this evidence.

### Provenance

Found by the round-4 adversarial review of RFC-0103 (`.context/reviews/rfc0103-r4-adversarial.md`,
finding 2). Rounds 2 and 3 of that review raised the same surface and were refuted on a
string search for `Brief` in the module — a search that cannot see a generic preamble
parser. The refutation was wrong; this entry supersedes it.

### Owner decision — 2026-09-22

Presented with three routes — withdraw D3 and keep the path form; widen the cohort to
`workspace_status_engine.py`; or pause and re-measure every consumer first — the scope
owner (eugenelim) chose **widen the cohort to the engine**.

Consequences the decision accepts:

- `brief:<slug>` stays the canonical `Brief:` form, so RFC-0103 D3 stands.
- `workspace_status_engine.py` joins the change surface. It sits in
  `packages/agentbundle/`, a different ownership boundary from `packs/core/`.
- The loosened check is `_is_canonical_local_brief_path` (`:723`) or the
  `require_local_brief` gate at `:2657`. Either is a validation control on the
  dispatch path that gates every queued spec, so `security-reviewer` fires on the
  amended contract and again on the diff.
- AC-0009's consumer list becomes four, not three.
- T6's `Touches:` gains the engine plus the two skills that stamp the old form
  (`new-spec/SKILL.md:213-217`, `author-delivery-brief/SKILL.md:196`), the latter pair
  found by round 1 of the same review.

This entry is the owner-authority reference for the controlled contract amendment.

## 2026-09-22 — the contract enumerates closed sets it never derived

**Status:** blocking. Surfaced to the owner. Spec `Draft`, plan `Drafting`, engine at
`SPEC-PLAN-REVIEW`.

Six review rounds have each found new members of a set the contract states as closed.
The individual findings were all repaired; the generator was not.

| Set the contract closes | Stated | Actually | Found in |
| --- | --- | --- | --- |
| Surfaces writing the `Brief:` form | 3 | 5 | rounds 1 and 5 |
| Scripts reading the spec `Brief:` header | 2 | 3 (dispatch) | round 4 |
| Copies of `workspace_status_engine.py` | 1 | 4 (1 source, 3 projections) | round 5 |
| Builder-visible `Parent intent:` values | 19 bare | 23 — 19 bare, 4 markdown-link | round 6 |
| Surfaces writing the `Parent intent:` form | 0 (unscoped) | 15 | round 6 |
| States `resolve_endpoint` returns | "a fourth" | a fifth; four exist today | round 6 |

Two of these were in the spec and plan as **originally approved**, and survived the four
pre-EXECUTE review rounds recorded in `.context/reviews/r1`–`r4`:

- AC-0006 requires every unclaimed intent file to be a node keyed on its `Slug:` field;
  AC-0015 requires an unclaimed intent file with no `Slug:` to contribute no node. For a
  file with no `Slug:` the two criteria demand opposite outcomes.
- `plan.md` § Interfaces calls the ambiguity state "a fourth state beside `local`,
  `satisfied-by-reference`, and `unresolvable`", omitting `dangling`, which
  `resolve_endpoint` also returns. It is the fifth.

The 15 `Parent intent:` writer surfaces are the sharpest consequence. They include
`packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md` and
`packs/core/seeds/docs/product/briefs/_template.md`, both of which stamp the bare-slug
form. T5 sweeps the 19 live values; nothing stops these templates from re-emitting bare
slugs the day after, so the migration does not converge.

**The class.** Every acceptance criterion that names a surface list was written by
enumerating from memory or from a search for a field name. A name search cannot see a
generic parser, a projection, or a template that writes the form without reading it.
Repairing each list as it is found does not end, because the method that produced the
lists is what is wrong.

**What would end it.** A derivation task that produces the surface inventory
mechanically — every writer, reader and copy of each migrated field — with the
acceptance criteria citing that derivation rather than a list. That is a change to how
the contract is specified, not another repair, and it is the owner's call.

## 2026-09-22 — five amendment review rounds did not converge

**Status:** stopped for direction. Spec `Draft`, plan `Drafting`, engine
`SPEC-PLAN-DRAFTING`. No code written, nothing committed.

| Round | Findings | Note |
| --- | ---: | --- |
| amend-r1 | 12 | 9 adversarial + 3 security |
| amend-r2 | 10 | security clean |
| amend-r3 | 6 | |
| amend-r4 | 10 | included the 23→37 cohort discovery |
| amend-r5 | 8 | included a regression introduced in r4 |

Each round's findings were real and were repaired. The count did not fall.

**Two things the rounds established that prose review could not have.**

The migration cohort is 37 values, not 23. Recognizing the 117 intent files as
nodes makes 14 of *their own* `Parent intent:` pointers builder-visible, of
which 25 of the 37 resolve and are rewritten and 12 are link-shaped and stay
report-only. The recognizer grows its own cohort; no revision of the contract
modelled that until it was measured.

Four distinct generic readers have now been found, none of which contains the
name of the field it reads: `workspace_status_engine._parse_preamble_fields`
(round 4), and `intent_shape.read_preamble` via `intent_corpus_lint` (round 5),
plus the projection sets for two different scripts. Every one was missed by an
enumeration, and each was found only by consuming the field through the code
that reads it.

**A regression the loop introduced and caught.** Round 4 replaced AC-0017's
finite malformed-value list with a positive predicate, which was correct, but
the predicate admitted exactly two forms and so would have refused a blank,
`none`, comment-only or omitted `Brief:` header. `_normalized_optional_artifact_value`
(`workspace_status_engine.py:2186-2192`) maps those to absence, and the field is
optional, so the criterion as written would have blocked dispatch for every spec
that legitimately has no brief — a wider blast radius than the migration. AC-0024
now scopes both criteria to non-placeholder values.

**Assessment.** The remaining findings are predominantly of one kind: the
contract's prose still states or implies surface sets that T0's derivation is
what exists to establish. Reviewing enumerations that T0 will replace does not
converge, because the reviewer is comparing prose against a repository the prose
cannot yet describe. The contract is now structurally sound in the places that
matter — inventory-derived `Touches:`, a predicate-equivalence refusal test, a
cohort derived after recognition, a single confinement boundary — and the
cheapest next evidence is T0's output, not a sixth review round.

### Owner approval — 2026-09-22

The scope owner (eugenelim) approved the amended contract and directed that T0
execute. The approval is recorded here because it is given with review findings
open, which the normal pre-EXECUTE gate would not allow.

Waived to execution, with the reasoning that each is a statement the derivation
is what settles:

- amend-r5 #1 (consumer inventory not closed) and #5 (conflicting fixed surface
  lists across the three artifacts). Both say the prose still names sets T0
  derives. AC-0019 now covers all four pointer fields, and `Touches:` is
  inventory-derived, so T0's output is what closes them.

Repaired before approval, not waived: amend-r5 #2 (the optional-`Brief:`
regression, now AC-0024), #3 (briefs-directory confinement in T6's mechanism),
#4 (D3 denying its own amendment), #6 (the 37-value cohort breakdown), #7 (the
invalid `Proposed` status gate), and the security lane's single blocker, which
was the same confinement gap as #3.

One plan correction was made under `Drafting` authority immediately before
approval: T0's `Depends on:` changed from `T1` to `none`. T0 reads the
repository and writes only under this spec's `notes/`; it cannot contradict the
convention T1 supersedes, and gating it on the governance round would withhold
the measurement every later task cites.

## 2026-09-22 — T0 executed: the surface inventory is derived

**Result:** `notes/derive-surfaces.py` and `notes/surface-inventory.md` exist;
659 entries across the four pointer fields; re-run produces a zero diff;
`make lint-ruff lint-mypy` passes (~4s).

### Mutation evidence — the self-check can fail

The script refuses to write the inventory unless five differential probes are
present. Each was proved to fail by mutating the mechanism it tests, with the
mutation script asserting its own match so it cannot silently no-op:

| Mutation | Result |
| --- | --- |
| generic-parser detection disabled | FAILS — Parent intent / Discovery readers, and the dynamic-import reader |
| generated-copy detection disabled | FAILS — Brief / generated-copy |
| templates reclassified as corpus | FAILS — Parent intent / writes |
| baseline restored | green |

**Two defects in the control itself, caught by mutation, not by review.**

The first probe asserted `workspace_status_engine.py` under `Brief / reads`.
That file contains the literal `Brief` six times (`BriefQueue`,
`_is_canonical_local_brief_path`), so the probe was satisfied by the *name*
path and survived disabling generic parsing entirely — a check that could not
fail for the reason it named. It contains `Parent intent` and `Discovery` zero
times and parses both generically, so those are the probes only the generic
path can satisfy. The probes are now differential by construction.

The first two mutation runs were silent no-ops: the mutation used `.replace()`
without asserting the target matched, and the indentation did not. Their green
was read as evidence before the miss was noticed. Every mutation now asserts.

### What the derivation found that enumeration had not

- **Five distinct generic preamble parsers**, not one: `workspace_status_engine`,
  `intent_shape`, `lint-spec-status`, `lint-contract-item-alignment`,
  `lint-adr-shape`. Each reads all four fields and none names any of them.
- **`intent_corpus_lint.py`**, which reaches `Parent intent:` only through
  `_load_sibling("intent_shape", …)` — invisible to both a name search and a
  static import scan.
- **11 `Parent intent:` writers** (7 sources + 4 projections), including the
  `frame-intent` intent template and the brief seed template. These are what
  AC-0020 must repoint or the sweep does not converge.
- **19 `Brief:` writers and 59 stating surfaces**, against the three, then five,
  that successive revisions of the contract asserted.

### Calibration applied during the task

Four predicates were tightened after their first output was measured rather
than assumed correct: name-based reads matched the bare word (`Contract`
appeared in unrelated prose, 118 readers → 47); one-hop propagation matched any
reader stem (1362 entries) then any import of one (414 Discovery readers) before
being scoped to the generic parsers alone; and the generic detector matched bold
markdown generally, flagging 35 files including shape linters and tests, before
being anchored on the `^- \*\*…:\*\*` shape both real parsers compile.

### Against T0's `Done when`

- inventory exists — yes, `notes/surface-inventory.md`
- script re-runs with a zero diff — yes, verified twice
- each named member appears under its correct label — yes, 12/12 probes, which
  includes the three classes the task names plus the readers rounds 4 and 5
  found by hand

### T0 addendum — `reads` split from `parses`, and a receipt correction

The first inventory labelled every generic parser a `reads` of all four fields.
That conflates "parses a preamble containing this field" with "consumes this
field's value": `lint-spec-status`, `lint-contract-item-alignment` and
`lint-adr-shape` each parse the preamble and mention `brief` zero times.
AC-0009 discharges against this label, so as written it would have obliged
`lint-adr-shape` to accept `brief:<slug>` — an obligation with no meaning.

`reads` now requires the file to name the field, as the header form
`Contract:` or as the lower-cased key a generic parser returns
(`fields.get("brief")`). A generic parser that names it nowhere is `parses`.
Counts moved accordingly: `Parent intent` readers 71 → 15, `Discovery` 72 → 10.
Mutation-checked: forcing `acts = True` collapses the split and fails the
`parses` probes.

**Receipt correction.** T0's dispatch receipt was first recorded as
`no-implementer-installed`. That was false — the `implementer` subagent is
available in this session. It has been re-recorded as `human-directed`, which
is accurate in that the owner directed T0's execution, though the precise fact
is that the controller implemented it rather than dispatching. The closed
reason vocabulary has no value for that case. Later tasks dispatch the
`implementer` subagent per the cohort's dispatch instruction.

## 2026-09-22 — the orphan risk is null, and AC-0012 is unsatisfiable

Measured while reviewing RFC-0103, after a fresh-reader pass named the unmeasured
orphan impact as the one thing blocking approval. It is measurable before
acceptance, so it was measured rather than deferred to T4.

### The orphan risk does not exist

`classify_standalone` (`lint-traceability.py:792-826`) classifies only nodes whose
kind is in `CHAIN` (`:112-115`):

    ("outcome", "opportunity", "capability", "screen", "action",
     "service", "contract", "spec", "component")

`intent` is not in it, and neither is `brief`. **Registering a kind does not make
its files chain-checkable; only joining `CHAIN` does, and D2 does not do that.**

Projected by building the graph, adding the 117 `intent:` nodes exactly as D2
specifies, and wiring the 14 parent edges they carry:

| | Baseline | With `intent:` nodes |
| --- | ---: | ---: |
| Nodes | 640 | 757 |
| Edges | 109 | 115 |
| Structural orphans | 488 | **487** |
| New orphans introduced | — | **0** |
| `intent`-kind nodes classified as orphans | — | **0** |

The count falls by one, because a newly wired parent edge gives an existing node
a producer it lacked.

So the claim in `plan.md` § Risks and in RFC-0103 § Risks — "117 files become
orphan- and reachability-checkable at once", "the largest unmeasured quantity in
the work", "`--strict` fails on a structural orphan" — is **false as stated**. It
was inferred from "these files become nodes" without checking what makes a node
chain-checkable. T4 still has work (edge counts, field-origin for T7's oracle)
but its stated headline risk is null.

### AC-0012 cannot pass, and could not before this delivery began

    $ lint-traceability.py --root . --strict   -> exit 1  (488 structural orphans)
    $ lint-traceability.py --root .            -> exit 0

AC-0012 requires the `--strict` invocation to exit 0 over the repository. It
exits 1 today, on a clean tree, from 488 pre-existing orphans that have nothing
to do with this change — overwhelmingly specs with no producer up-edge.

The criterion is unsatisfiable as written and always was. It survived the four
pre-EXECUTE review rounds recorded in `.context/reviews/r1`-`r4` and all five
amendment rounds, because every round reasoned about the criterion's wording and
none of them ran the command.

The repairable form asserts what the delivery can control: the default
invocation continues to exit 0, and the `--strict` orphan count does not
increase. Both are measured above.

### The spec's open Assumption is answered: the sweep changes no orphan verdict

`spec.md` § Assumptions asks "whether attaching the 34 newly local `Brief:`
edges changes `lint-traceability`'s orphan, reachability, or cycle verdict".

Projected over the full post-sweep state — 117 `intent:` nodes, their 14 parent
edges, and all 34 `Brief:` values typed:

| | Orphans |
| --- | ---: |
| Today | 488 |
| Full post-sweep projection | **487** |
| New orphans introduced | **0** |

Net −1, and the −1 comes from a parent edge, not from the brief sweep. The
brief sweep moves no spec in or out of orphan status, because the path form
*already* produces an in-edge: it resolves `unresolvable` and attaches the spec
to an external stub, which satisfies the has-producer test just as a local edge
would. Typing the value repoints that edge from the stub to the real brief
node. That is a correctness gain in the graph, not a change in the orphan
verdict.

So the Assumption resolves to "no", and T4's orphan measurement — the reason
T4 was placed between the resolver work and the sweeps — has been answered
before either sweep runs, by projection rather than by execution.

### Consequences for the pinned contract

Four statements in the sealed artifacts are now false or unsatisfiable:

1. `spec.md` AC-0012 — requires `--strict` to exit 0. It exits 1 today on 488
   pre-existing orphans and always did. Unsatisfiable as written.
2. `spec.md` § Assumptions — states the orphan question as open. It is answered.
3. `plan.md` § Approach — "the riskiest part is not the sweep but the node-set
   growth … `--strict` treats a structural orphan as exit 1".
4. `plan.md` § Risks and T4 § Approach — the same claim, and T4's instruction to
   Surface on an orphan finding, which now has nothing to fire on.

All four sit under `approved_spec_hash` / `approved_plan_hash`, so correcting
them is a controlled amendment, not an in-place edit. Recorded here and raised
with the owner rather than actioned unilaterally.

### Owner decision — 2026-09-22 (second amendment)

The scope owner directed that the spec and plan be corrected, on the grounds
that the falsified orphan claim and the unsatisfiable AC-0012 affect the work
rather than only the prose. Authority for the controlled amendment below.

Scope of the amendment:

- AC-0012 replaced with a form the delivery can satisfy and that still detects
  the regression it was reaching for.
- The `Assumptions` entry closed: it asked the orphan question, which is now
  measured and answered "no change".
- `plan.md` § Approach and § Risks corrected — the node-set growth is not the
  riskiest part, because it carries no orphan consequence.
- T4 retained but re-shaped: its orphan measurement becomes a standing
  non-increase assertion rather than an open question with a Surface clause,
  and its remaining reason to exist is the field-origin oracle T7 needs,
  because `Graph.add_edge` stores only `(producer, consumer)`.

### The "reachability" half of the refuted claim fails for a second reason

The claim under repair was that 117 files become "orphan- **and
reachability**-checkable". The orphan half is refuted by `CHAIN` membership
above. The reachability half fails independently and more simply: the
reachability pass runs only in sidecar mode.

`check()` guards it with `if using_sidecar:` (`lint-traceability.py:~1197`), and
`discover_sidecar` returns `None` in this repository — there is no
`_state/traceability.json` anywhere in the tree. `reachability_sidecar` is
therefore never called on any invocation this delivery affects, for any node
kind, before or after the change.

Caught because a reviewer began reading the reachability code and the
verification above had only covered `classify_standalone`. Half a refutation
read as a whole one is the same defect as the claim it was refuting: a
conclusion drawn about a mechanism that was never executed.

### Owner decision — 2026-09-22 (accept and proceed)

The owner accepted RFC-0103, accepted the amended contract as it stands, and
directed that implementation continue, with verification to come from code and
tests and the contract to adapt as that evidence arrives. Recorded as the
authority for approving without a further review round: the round-2 findings
were applied, and the alignment lint reports nothing against this spec.

T1 is discharged: RFC-0103 is `Accepted` (closed 2026-09-22), its `Amendments`
section renamed to `Errata` per the `new-rfc` convention, and `spec.md`'s
`Constrained by:` already cites the ordinal.

## 2026-09-22 — T2 complete; a scoped rule the contract never wired in

### T2 result

`resolve_endpoint` gained a fifth state, `ambiguous`, routed at all three call
sites including `resolve_sidecar_endpoints`, and the docstring's "three endpoint
states" undercount was corrected to five. AC-0005's ordinal refusal reuses
`dangling` rather than adding a sixth state, on the reading that `dangling`
already means a missing or malformed target.

- `make lint-ruff lint-mypy`: pass
- `test_lint_traceability.py`: 54 passed in 16.6s (48 pre-existing + 6 new)
- Red proved by reverting the production file to HEAD and re-running: the stub
  and three others failed; the two tests pinning pre-existing behaviour passed
  on unmodified code, which is what they are for
- `lint-traceability.py --root .`: exit 0, 640 nodes, 109 edges, 488 structural
  orphans — the recorded baseline, confirming the refusal is inert as T2's
  Approach predicted

### The gap the implementer surfaced

`packs/AGENTS.md:43-47` requires every non-cosmetic change under `.apm/**` or
`seeds/**` to bump matching versions in `pack.toml` and
`.claude-plugin/plugin.json` — patch for changed content, minor for new
primitives, major for removals, and never borrowing another change's unreleased
version.

This delivery changes `packs/core/.apm/**` in T2, T2a, T3 and T6, and
`packs/core/seeds/**` in T6. **No task owns the bump.** T8's `Touches:` covers
`.agents/**`, `.claude/**`, the `_data/` engine projection, the brief erratum
and `CHANGELOG.md` — not `packs/core/pack.toml` or
`packs/core/.claude-plugin/plugin.json`, which currently both read `2.26.29`.

This is the same class as the surface-inventory findings: an obligation that
lives in a scoped `AGENTS.md`, applies to files the delivery certainly touches,
and was never enumerated because nobody walked the rule down to a task. The
difference is that this one was caught by an implementer reading its own scope
rather than by a review round.

It needs a contract amendment to place: T8 is the natural owner, alongside the
changelog entry it already carries. Raised with the owner rather than actioned,
because `Touches:` is pinned.

## 2026-09-22 — T6 complete; waves 1 and 2 closed

### T6 result

`brief:<slug>` is canonical across every writing and stating surface the T0
inventory names for the field; the coverage join accepts it (AC-0010); and the
dispatch provenance check admits it by normalizing to
`docs/product/briefs/<slug>.md` before the existing lexical checks, leaving
`_is_canonical_local_brief_path` untouched. Confinement is the one check not
reused: two small pure functions were added because the plan's Approach
explicitly forbids relaxing the repo-root helper for the stricter briefs-root
case.

Verified by the controller, not taken from the report:

- no projection under `.agents/`, `.claude/` or `packages/agentbundle/_data/`
  was modified
- `make lint-ruff lint-mypy`: pass
- `lint-traceability.py --root .`: exit 0
- work-loop + author-delivery-brief + workspace-status: **253 passed, 1 skipped** in 29.8s
- new-spec + pack (the five prose-pinned template suites): **545 passed, 79 subtests** in 114s

### AC-0017's predicate-equivalence test earned its place immediately

It failed on two length-boundary mismatches — a 200-character slug was wrongly
refused — and those are exactly the cases the ten-example list the criterion
forbids would have missed. The criterion was written to reject a finite negative
list; the first run of the test that replaced it found a real boundary defect.

### Parallel dispatch, and a scheduler prediction that was wrong

T2 and T6 ran as two concurrent `implementer` subagents. The cohort reported
`predicted-disjoint: yes` for this wave, and that prediction was **wrong**: it
reads the literal `Touches:` text, and T6's is prose — "every surface the
inventory labels…" — so it could not see that the inventory lists
`lint-traceability.py` under `Brief: reads`, which is T2's file.

The controller partitioned the write surface instead: T2 owned that file, and
T6's brief carried the exclusion with its reason from RFC-0103 D3 plus an
instruction to surface rather than edit if it disagreed. T6 read
`resolve_endpoint`, confirmed an exact `brief:<slug>` id already matches
`local_ids` directly, and left it alone.

**A task whose `Touches:` is derived rather than enumerated cannot be checked by
the disjointness predictor.** That is a property of the scheduler worth knowing
before trusting `predicted-disjoint` on any future inventory-scoped task.

### Both implementers independently flagged the version-bump gap

Neither was told about the other's finding. `packs/core/pack.toml` and
`.claude-plugin/plugin.json` remain at `2.26.29` while `.apm/**` and `seeds/**`
have changed, and no task owns the bump. Two independent reads of the same
scoped rule reaching the same conclusion is stronger evidence than one.

### Wave bookkeeping

`dispatch_receipts` is keyed by plan hash, so the second amendment's re-schedule
discarded the wave-0 receipts recorded before it. They were re-recorded against
the new hash. Waves 0 and 1 are now closed: T1 and T0 as `human-directed`
declines (controller-implemented), T2 and T6 as receipts (implementer subagents).
Current wave is 2 — T2a and T3.

### Owner decision — 2026-09-22 (third amendment: the version bump)

The owner directed that the pack version bump be placed. It goes to T8, which
already owns the changelog entry and the reprojection, so the release surface
moves as one unit. Authority for the controlled amendment below.

`packs/AGENTS.md:43-47` requires a non-cosmetic change under `.apm/**` or
`seeds/**` to bump matching versions in `pack.toml` and
`.claude-plugin/plugin.json` — patch for changed content, minor for a new
primitive, major for a removal, never borrowing another change's unreleased
version. This delivery changes `.apm/**` in T2, T2a, T3 and T6 and `seeds/**`
in T6, all content changes rather than new primitives, so the bump is a patch
from `2.26.29`.

Surfaced independently by both wave-2 implementers.

## 2026-09-22 — T2a complete; the brief was narrower than the criterion

`_wire_up` is now two passes: candidates are classified first, with `dangling`
and `ambiguous` still reported immediately in every position, then the winner is
picked from the resolved candidates, preferring `local`. `_SPEC_UP_FIELDS` and
its field priority are untouched, as the Approach requires.

- `make lint-ruff lint-mypy`: pass
- `test_lint_traceability.py`: 57 passed in 17.0s
- `lint-traceability.py --root .`: exit 0, **640 nodes, 109 edges** — both
  unchanged, which is `Done when`'s actual test: no `Brief:` value is typed yet,
  so a correct preference change moves nothing in the live corpus

### The controller's brief was narrower than AC-0013

The dispatch brief said "make a candidate resolving `local` win over an earlier
one resolving only `unresolvable`". The implementer implemented `local` beating
*either* non-local resolving state, and flagged the difference rather than
absorbing it.

The implementer is right. AC-0013 says "an earlier producer pointer that
resolves only to an **external reference**". `satisfied-by-reference` is an
external reference resolved through the rollup; `unresolvable` is a well-formed
cross-repo reference with no resolution. Both are external, so the criterion
covers both and the brief narrowed it.

Measured, to confirm the wider rule is not a widening past the owner's granted
bound: across all 120 up-field candidates the states are 101 `unresolvable` and
19 `local`. **`satisfied-by-reference` occurs zero times, and the rollup holds
zero entries.** The two readings are therefore identical on this corpus, which
is independently confirmed by the unchanged edge count.

### The "bundled fix" is better classified as in-scope repair

The implementer recorded a corrected docstring in `test_up_field_fallthrough_reference`
as a bundled fix, noting the brief had not authorized the carve-out. It is not a
ride-along: the docstring said "the first that resolves wins", which *this
change* falsified. Repairing a statement the change itself made false is part of
the change, not an unrelated improvement carried alongside it. No unauthorized
carve-out occurred.

## 2026-09-22 — T3 complete, and it falsified an accepted claim

`recognize_intents` registers the 117 unclaimed intent files as `intent:<slug>`
nodes, keyed on `Slug:`, skipping what `recognize_ladder` already claimed and
skipping — with a report and no node — any file lacking `Slug:`. Its path map
joins the existing `Parent intent:` wiring pass, so a new node's own producer
pointer wires like a brief's or a ladder rung's.

- `make lint-ruff lint-mypy`: pass
- `test_lint_traceability.py`: **63 passed** in 15.2s (57 + 6 new)
- Red proved by reverting the production file to the T2a state
- Nodes **640 → 757**, exactly the projected 594 local + 117 + 46 stubs
- Edges **109 → 115**
- `--strict`: 487 orphans, matching the projection of 488 → 487 with none
  introduced, because `intent` is not in `CHAIN`

### The finding: default mode now exits 1

Wiring the 14 newly visible `Parent intent:` values resolves 6 and leaves 8
`dangling`, which is a hard violation in every mode. The 8 are markdown links:

    - **Parent intent:** [Digital experience doctrine](digital-experience-doctrine.md)

`field_re` truncates at the first space, so the value becomes `[Digital`, which
contains no `/` and therefore fails `_CROSSREPO_RE`; it lands `dangling` rather
than `unresolvable`. The implementer did not suppress them, correctly: the Agent
Rules forbid sweeping a value the corpus cannot resolve and require reporting it.

**This is expected and temporary, but it was not predicted.** T3's `Done when`
does not require exit 0, so T3 is complete against its contract. The controller's
dispatch brief said "Expect exit 0", which was wrong — extrapolated from T2 and
T2a rather than derived. RFC-0103's Risks section asserted the same thing, and
now carries an erratum.

The end state is unaffected: both link targets resolve to existing capability
nodes — `capability:digital-experience-doctrine` and
`capability:nontechnical-pack-first-value-rollout` — so T5's sweep rewrites all
8 to the canonical form and default exit returns to 0, which is where AC-0012
is read. **T5 must cover these 8; they are inside AC-0008's "every resolvable
value" predicate precisely because their targets resolve.**

### The same half-verification, a third time

The projection that produced "488 → 487, zero new orphans" measured nodes, edges
and orphans. It never read the exit code, and never inspected `g.dangling`. The
earlier reachability gap and the `Brief:`-probe gap were the same shape: a
mechanism checked on one axis and reported as checked. The implementer's real
run found in one command what three projections had missed.

## 2026-09-22 — T4 complete

`notes/corpus-probe.py` re-derives the graph through the production
recognizers, unchanged, then spies on `_wire_up` during that one real build to
capture the exact `local_ids`/`rollup` each call used, and replays its
winner-selection logic per consumer with `resolve_endpoint` — both pure
functions taken from the production module, never re-derived — to record which
candidate field supplied the winning producer. Report:
`notes/corpus-probe.md`.

- `make lint-ruff lint-mypy`: pass
- Two consecutive runs of `corpus-probe.py --root .` on the unchanged tree
  produce byte-identical `corpus-probe.md`
- **Nodes 757, edges 115** — unchanged from T3's own measurement, confirming no
  drift between the two independent readings
- **Structural orphans: 487**, against the pre-delivery baseline of 488
  recorded in this plan's Design section — **AC-0025 PASSES** (non-increase,
  none introduced)

### The stale cross-reference in T4's own `Tests:`

T4's `Tests:` cites AC-0012 for the orphan non-increase. AC-0012 was later
split by the second amendment into "the default invocation exits 0" and
AC-0025 "`--strict` reports no more structural orphans than before". The
non-increase is recorded against **AC-0025** above; AC-0012 does not hold yet
and is not expected to until T5's sweep clears the 8 dangling values below —
the probe does not assert it.

### Collision set: 7 slugs, matching the plan's own projection

The probe groups local node ids (external reference stubs excluded) by their
post-kind slug — the exact suffix `resolve_endpoint`'s bare-slug scan matches
against. It finds **7 colliding slugs** over the live 757-node graph, which
matches the Design section's own projection for this exclusion design at
"711 nodes, 7 collision slugs" (the 46 difference is external reference
stubs, absent from the Design section's local-node count). The
**ambiguous-pointer set is 0** — no live pointer today actually suffix-matches
more than one id — matching the Design section's "0 of 19 live bare `Parent
intent:` pointers ambiguous" exactly.

### Reachability: measured as not run, not assumed

`check()` (`lint-traceability.py:1292`) guards `reachability_sidecar` with
`if using_sidecar:`, and the probe calls `discover_sidecar` directly and
observes it return `None` on this tree — there is no
`_state/traceability.json` sidecar. The standalone path runs instead, so the
reachability pass never executes and there is no reachability figure for this
corpus. Recorded as an honest absence, not a number.

### The 8 pre-sweep dangling `Parent intent:` values, named for T5

T3 wired 14 newly-visible `Parent intent:` pointers; 6 resolve and 8 are
`dangling` because `field_re` truncates a markdown-link value at the first
space. All 8 are intent files, and both truncated tokens' link targets resolve
to existing `capability:` nodes:

- `intent:claude-apps-first-value-entry` → `[Nontechnical-pack` → resolves to
  `capability:nontechnical-pack-first-value-rollout`
- `intent:cross-pack-experience-eval` → `[Digital` → resolves to
  `capability:digital-experience-doctrine`
- `intent:digital-product-guides-update` → `[Digital` → same target
- `intent:product-engineering-shaping-doctrine` → `[Digital` → same target
- `intent:product-strategy-adoption-doctrine` → `[Digital` → same target
- `intent:xd-design-system-foundations` → `[Digital` → same target
- `intent:xd-ia-archetypes-objects` → `[Digital` → same target
- `intent:xd-state-reviewer-doctrine` → `[Digital` → same target

This is the pre-sweep baseline T5 must clear; the after-sweep comparison
against these 8 named ids is what proves the sweep worked, and AC-0012 (exit 0
by default) is read there, not here.

### Field-origin recording: T7's only oracle

For every consumer wired through `_wire_up` — 503 specs and 37
brief/ladder-rung/intent `Parent intent:` consumers, 540 total — the probe
records which field won. Today, before the `Brief:` sweep (T5, T7): of the
specs with a resolving producer, **26 win on `Brief:`** (matching the "26 to
34" figure T2a's Approach projected for the post-sweep move), 38 on
`Contract:`, 22 on `Discovery:`, and 417 have no resolving candidate (an
orphan). Of the 37 `Parent intent:` candidates, 29 resolve and 8 are the
dangling set named above (29 + 8 = 37, cross-checking T3's own count). Because
`Graph.add_edge` (`:357`) stores only `(producer, consumer)`, this recording —
not the built edge set — is the only oracle T7 has for "no in-edge is won by a
field other than `Brief:`".

### T4 controller verification, and one figure corrected before T7 uses it

Probe re-run on an unchanged tree produced an identical md5
(`1f1f62fe5e4f263f6709d215058ed9ca`), so the zero-diff property holds.
`make lint-ruff lint-mypy` passes. Every figure matched the projection: 757
nodes, 115 edges, 487 orphans (AC-0025 passes against the 488 baseline), 7
collision slugs, 0 ambiguous pointers, reachability recorded as not run.

**Corrected before T7 consumes it.** T4's handoff says T7's sweep is "expected to
move those 60 non-Brief winners to `Brief`". That reads as 60 and is wrong as a
headline, though its own trailing caveat — "wherever a `Brief:` value is typed" —
is what saves it.

Only **34** specs carry a `Brief:` value at all, and 26 already win their in-edge
on `Brief:`. A spec with no `Brief:` value cannot win on `Brief:`, so the ceiling
is 34 and the movement is **26 → 34: eight specs flip**. The 38 `Contract:` and
22 `Discovery:` winners without a `Brief:` value stay where they are.

That is exactly the bound the owner measured when granting T2a under `Ask first`:
brief in-edges 26 to 34, and no spec's in-edge moving to a field other than
`Brief:`. T7 asserts against 34, not 86.

### Owner decision — 2026-09-22 (fourth amendment: T5's edge expectation)

T5's `Done when` requires "the repository run's edge count is unchanged from
T4's recorded figure", i.e. 115. Measurement shows that is impossible for a
correct sweep.

None of the 8 dangling consumers holds an in-edge today — verified by checking
each against the built edge set — because `_wire_up` routes a dangling candidate
to `g.dangling` without calling `add_edge`. Sweeping each one to its resolving
target therefore *adds* an edge: **115 → 123**.

The clause was written when the plan believed the `Parent intent:` cohort was 19
bare slugs that already resolved, where a sweep genuinely moves no edge. T3 made
14 further values visible, 8 of them dangling, and the clause did not follow.

The sweep is required rather than optional: AC-0012 needs default-mode exit 0,
which cannot happen while those 8 dangle. The Agent Rule against sweeping an
unresolvable target does not bar it — the corpus resolves both link targets to
existing `capability:` nodes; it is the markdown-link *value* that fails to
tokenize, not the target that fails to exist.

Amended under the owner's standing direction to work through the tasks and adapt
the contract as code and tests require.

## 2026-09-22 — a measured fact for the Contract/Discovery follow-on

Measured while preparing the follow-on handover:

| Figure | Value |
| --- | ---: |
| `Contract:` values on specs | 38, all resolving `unresolvable` |
| `Discovery:` values on specs | 25, all resolving `unresolvable` |
| `contract` nodes in the graph | 34 |
| **Of those, ids carrying `@version`** | **0** |

RFC-0103 D1 excludes `Contract:` from the grammar on the ground that
`recognize_contracts` types targets as `contract:<name>@<version>`, and "that id
embeds a version, so `<kind>:<slug>` is not yet the right shape for them".

**No contract node in this repository carries a version.** `recognize_contracts`
(`lint-traceability.py:513-531`) parses `name.vN` / `name@N` from the filename
and degrades to `contract:<stem>` when no version is encoded; all 34 take the
degraded path. The versioned shape is reachable by the code, not present in the
corpus.

So the exclusion's stated ground is true of the recognizer and false of the
data. `contract:<slug>` would express all 34 targets today. That does not by
itself reverse D1 — a future versioned contract would still not fit, and
`Discovery:`'s unregistered `docs/product/research/` targets are an independent
and unaffected reason to hold that field back — but it means the follow-on is
likely smaller than D1 implies, and should re-measure rather than inherit the
rationale.

RFC-0103 is Accepted and frozen; this belongs in its Errata, which is the
controller's to add and is not done here because a sweep task is mid-flight.

## 2026-09-22 — T5 complete; the sweep landed on the amended numbers

33 `Parent intent:` values rewritten to `<kind>:<slug>` across
`docs/product/intents/`; 4 in `docs/product/briefs/` left and reported, because
they classify `unresolvable` (cross-repo shaped) and already carry an edge to an
external stub — retyping those would repoint an existing edge, which `Done when`
forbids. Six writer surfaces repointed, derived from T0's inventory.

| | Before | After |
| --- | ---: | ---: |
| Nodes | 757 | 757 |
| Edges | 115 | **123** |
| Dangling | 8 | **0** |
| Structural orphans | 487 | 487 |
| Default-mode exit | 1 | **0** |

Exactly the fourth amendment's expectation: +1 edge for each formerly dangling
value, and default exit restored, so AC-0012 can pass. `make lint-ruff
lint-mypy` passes; no projection was touched.

### Owner decision — the dropped decoration stands

The sweep replaced the entire field value, dropping a human-readable decoration
that 25 of the 33 values carried:

    - **Parent intent:** graph-powered-sdlc — [Graph-powered SDLC](STRAT-0001-graph-powered-sdlc.md)
    + **Parent intent:** opportunity:graph-powered-sdlc

Preserving it was possible at zero cost: `field_re` truncates at the first
space, so `intent:foo — [Title](foo.md)` tokenizes to `intent:foo` and resolves
identically — verified, not assumed. The contract does not settle the question:
AC-0008 says the value "is `<kind>:<slug>`", which supports dropping it, while
the Outcome is satisfied either way.

Surfaced to the owner rather than decided by the loop. **Owner chose: keep as
swept.** The decisive point is that the dropped links were keyed on
ordinal-prefixed filenames (`STRAT-0001-…`), the addressing this delivery exists
to retire; preserving them would have carried the anti-pattern forward into 25
files and left a second migration behind.

## 2026-09-22 — T7 complete; every `Brief:` value is typed

Before-state recorded first (`sweep-brief.py` did not exist yet and this
recording is what the "rollup verdict is unchanged" test compares against):
`lint-brief-coverage.py --root .` output, byte-captured pre-sweep, and
`corpus-probe.md`'s pre-sweep snapshot (both untouched by the sweep — the
repository was clean except for the new script before either ran).

34 specs carry a `Brief:` value, all repository-relative-path shaped
(`docs/product/briefs/<slug>.md`); `sweep-brief.py` rewrote all 34 to
`brief:<slug>`, left 0, reported an empty remainder. Re-running the script
against the swept tree rewrites 0 and reports the same empty remainder — the
zero-diff proof.

| | Before | After |
| --- | ---: | ---: |
| Edges | 123 | 123 |
| Structural orphans (`--strict`) | 487 | 487 |
| Default-mode exit | 0 | 0 |
| `--strict` exit | 1 | 1 |
| Specs winning their in-edge on `Brief:` | 26 | **34** |
| Specs winning on a field other than `Brief:` (of the 34-spec cohort) | 8 (4 `Contract:`, 4 `Discovery:`) | **0** |
| `lint-brief-coverage.py` exit | 0 | 0 |
| `lint-brief-coverage.py` rollup verdict | — | **byte-identical to the before-recording** |

Exactly the fourth amendment's / T2a's owner-granted expectation: brief
in-edges 26 to 34, no spec's in-edge moving to a field other than `Brief:`.
The 8 flips are `agent-skill-engineering-foundation`,
`distribution-route-contract`, `distribution-route-registry`,
`portable-agent-plugin-projection` (all previously won on `Contract:`) and
`intent-metadata-shape-contract`, `intent-reference-grammar-migration`,
`intent-renumber-and-reissue`, `typed-intent-ordinal-allocator` (all
previously won on `Discovery:`) — verified per-consumer against
`corpus-probe.py`'s winning-field oracle, not inferred.

### Node count moved (757 → 747), not held — measured and explained

The task brief's own expectation stated nodes would stay at 757. They did not;
747 is correct and the mechanism is fully accounted for, not a defect.
`_wire_up` registers an external-reference stub node
(`g.nodes.setdefault(resolved, "external")`) **only for the winning
candidate**, keyed by its raw target string. Before the sweep, 10 distinct raw
strings each won at least one consumer's in-edge while resolving
`unresolvable` (7 `docs/product/briefs/<slug>.md` path strings across the 26
already-Brief-winning specs, 1 shared `docs/product/intents/FEAT-0001-…` string
across the 4 `Discovery:` flips, 1 shared `contracts/distribution-routes.toml`
string across 3 of the `Contract:` flips, and 1
`.../okf-pack-profile-v1.schema.json` string for the fourth) — ten external
stub nodes. After the sweep every one of those specs' winning candidate
resolves `local` to an *already-recognized* `brief:<slug>` node (`recognize_briefs`
registers all 17 briefs regardless of whether any spec references them, so no
new local node is added), so none of the ten raw strings is registered as a
stub any more. 757 − 10 = 747, confirmed directly against the graph's node
kinds (`kind == "external"`), not inferred from the count alone. Edges hold at
123 for the same reason the plan anticipated for the field-form change: a
typed `Brief:` repoints an existing edge from the stub to the real node rather
than adding one; it also, as a side effect the plan did not name, deletes the
stub node that edge no longer needs.

### T7 controller verification

All 34 `Brief:` values typed; no untyped value remains. `lint-brief-coverage.py`
exits 0 and its rollup output is byte-identical to the pre-sweep capture.
`lint-traceability.py --root .` exits 0. 127 tests pass across the two suites.
`make lint-ruff lint-mypy` passes.

Winning field, within the 34-spec cohort: **26 → 34**, exactly the bound the
owner measured when granting T2a under `Ask first`. The 8 flips are named
individually in T7's report — 4 from `Contract:`, 4 from `Discovery:`.

**The node count moved and the explanation checks out.** The controller's brief
predicted 757 would hold; it fell to 747. Verified: local nodes are unchanged at
**711** and external stubs fell **46 → 36**. `_wire_up` registers an external
stub only for a *winning* candidate, keyed on its raw target string. Ten such
strings won before the sweep and resolve `local` after it, to brief nodes
`recognize_briefs` already registers regardless of reference — so those ten
stubs are no longer created. Edges hold at 123 because an edge repoints from
stub to real node rather than being added.

The implementer measured this against the graph rather than inferring it, and
was right where the brief's prediction was wrong.

## 2026-09-22 — T8 complete: projections, release surface, follow-on record

Recorded command output, as `Done when` requires.

    $ make lint-ruff lint-mypy
    All checks passed!
    Success: no issues found in 148 source files

    $ lint-traceability.py --root .                      # AC-0012
    posture=single-repo, 747 node(s), 123 edge(s)
    487 structural orphan(s) (informational)
    exit 0

    $ lint-traceability.py --root . --strict             # AC-0025
    487 structural orphan(s) — FAIL (--strict)
    exit 1

    $ lint-spec-status.py --root .
    spec metadata clean (36 of 503 spec(s) changed against origin/main)
    exit 0

AC-0012 passes: the default invocation exits 0. AC-0025 passes: 487 orphans
against the 488 pre-delivery baseline, a decrease. `--strict` exits 1 on
pre-existing orphans this delivery did not cause and does not claim to fix.

### Projections — AC-0011 and the fourth copy

`make build-self` reprojected after the tree was clean. Byte-identical, verified
by md5:

| Set | Copies | Distinct hashes |
| --- | ---: | ---: |
| `lint-traceability.py` | 3 | 1 |
| `new-spec` spec template | 3 | 1 |
| `workspace_status_engine.py` | **4** | 1 |

The engine's fourth copy under `packages/agentbundle/agentbundle/_data/` is why
AC-0011's three-copy comparison does not cover it, and why T8's tests name it
separately.

### Release surface

`packs/core/pack.toml` and `.claude-plugin/plugin.json` both bumped
**2.26.29 → 2.26.30**, one patch, matching. Changelog entry added directly
beneath `[Unreleased]` as a free-standing release heading; it names the retained
path and bare-slug fallbacks and says which reader accepts which, not only the
new canonical form.

### Brief erratum

`docs/product/briefs/intent-identity-and-registration.md` now carries an
`## Errata` section recording that its collision count depends on reading
`Slug:` rather than the filename stem, and that the two differ for 5 of the 117
unclaimed intent files. Measured by `Slug:`: 1 collision slug before, 7 after,
39 had the kind been registered over the whole directory.

### Follow-on record

`workspace.toml` `["ini-010".shaping_queue].backlog` now holds
`contract-discovery-reference-grammar`. It is a **shaping** item, not a build
item: RFC-0103 left both fields ungoverned and the governing decision does not
exist yet. The entry's comment carries the measured facts a later session needs,
including that RFC-0103 D1's stated ground for excluding `Contract:` — that
contract ids carry a version — is false of all 34 contract nodes in this corpus.
The spec's Follow-ons section cites the slug.

## 2026-09-22 — review findings 3, 4, 9 and 10 repaired

All four were adjudicated SUSTAINED against current evidence before repair.

### Finding 4 — AC-0007 was a control that could not fail

The duplicate fixture spied on `Graph.add`, asserted the pre-insertion sequence
carried the duplicate, then asserted the built set held one node. Both pass
against an implementation that silently overwrites, which is what the shipped
code did: AC-0007 ("no two nodes share an id") was observed, never enforced.

Repaired at the generator rather than the instance. `Graph.add` now records a
collision at insertion into `g.duplicate_ids`, and `check()` reports it as a
hard violation in every mode. `recognize_briefs` was writing `g.nodes[bid]`
directly, bypassing the guard entirely, and now goes through `add`. External
stubs keep their `setdefault` and are deliberately outside the guard: a stub is
keyed on a raw target string and legitimately repeats when consumers share a
target.

Measured before enforcing, because a legitimate double-registration would have
broken the repository: **694 `add()` calls, 694 distinct ids, 0 duplicates.**
Red proved by reverting the production file — `AttributeError` on
`g.duplicate_ids` — then 63 tests green.

### Finding 3 — the four markdown links are now typed

The sweep attempted link resolution only for `dangling` values. `dangling` and
`unresolvable` both mean the *value* did not resolve, not that the target does
not exist: a markdown link tokenizes to a fragment, and whether that fragment
contains a `/` decides which of the two states it lands in. The split is an
artefact of tokenization, so link resolution now runs for both.

| | Before | After |
| --- | ---: | ---: |
| Untyped resolvable `Parent intent:` | 4 | **0** |
| Nodes | 747 | 744 |
| External stubs | 36 | **33** |
| Edges | 123 | **123** |

Edges hold, which is what T5's "preserve every edge rather than repointing one"
clause exists to protect. Its literal wording — each rewritten value resolving
to the same id as before — is not met, because the id moves from an external
stub to the real node. The clause's purpose is served and its letter is not;
recorded rather than amended, since the same reasoning already covered the 8
dangling values in the fourth amendment.

### Finding 10 — governance citations removed from shipped sources

`packs/AGENTS.md:51-52`: "Under `packs/`, write portable guidance only. Do not
cite this catalogue's internal records, acceptance criteria, or repository-only
paths; state the rule directly." The delivery added 12 such citations across 4
shipped files, none present at the merge base.

Removed from the three this session owns — `lint-traceability.py`,
`lint-brief-coverage.py`, `new-spec/references/spec-and-plan-contract.md` — by
restating each rationale in standalone terms rather than deleting it. The
ordinal rule, for instance, now says why a series position is not a name
instead of citing the record that decided it.

**Four citations remain in `workspace_status_engine.py` (`:741`, `:1842`,
`:2679`, `:2686`).** That file is being edited concurrently by another session
fixing review findings 1 and 2, so it is theirs to clear; flagged to them rather
than edited underneath them.

### Finding 9 — the second version-bump rule

`packages/AGENTS.md:7` requires a non-cosmetic package change to update both
`version.py` and `pyproject.toml`. The bundled engine changed (+52/−3) and both
still read `0.47.3`. Bumped to `0.47.4` with a changelog entry.

That is **two** scoped version-bump rules this contract missed, in two different
`AGENTS.md` files, both found by review rather than by the plan. The packs rule
cost a contract amendment; this one was caught before the release surface
closed.

## 2026-09-22 — findings 5, 6, 7 and 8 closed

### #7 found a real defect in the code it tests

AC-0017's predicate-equivalence test generated mutations from nine hand-picked
characters. `@` was not among them, so an identifier rule that additionally
accepted `@` passed every candidate — the reviewer's mutant, and the reason a
sampled domain cannot establish a complement.

Widened to the whole printable ASCII range, the control bytes, and five
non-ASCII categories (accented Latin, CJK, astral plane, zero-width joiner, a
Cyrillic homoglyph of `a`). The first run failed on a value nobody had
considered: **`brief:valid-slug_123\n` was admitted while a trailing tab, space
or carriage return was refused.**

`_BRIEF_POINTER_RE` was `^brief:(?P<slug>.*)$`, and in Python `$` also matches
just before a trailing newline. So exactly one character of the excluded set
leaked: the newline was silently dropped and the value normalised through to a
canonical path. Fixed to `\Z` with `re.S`.

The first repair attempt was wrong and is worth recording. The mismatch was read
as the *predicate* failing to model a `.strip()` the engine performs elsewhere,
and the predicate was amended to strip. Measuring each whitespace character
separately refuted that: the implementation refused tab, space and carriage
return and admitted only the newline, which no strip explains but an anchor
does. The predicate was restored and the implementation fixed instead.

Verified: the reviewer's `@` mutant now fails the test, where it previously
passed. 73 passed, 1 skipped.

### #8 — AC-0021 now has a durable assertion

`tools/test_brief_slug_matches_filename.py`. It lives under `tools/` because it
reads the real corpus and a pack test cannot read above its own pack.
Mutation-checked: changing one brief's `Slug:` to disagree with its filename
fails it. A second case asserts the corpus is non-empty, because an empty glob
would make the first vacuous.

### #6 and #5 — roles, then regenerate

198 of 455 inventory entries were fixtures, eval cases and review transcripts
labelled as authoring surfaces. Non-surfaces are now excluded; `examples/` is
deliberately kept, because a shipped example is author-facing and the brief
sweep repointed one. `generated-copy` was keyed on matching basenames and is now
keyed on the byte-identical duplicate group, so the evidence for the
relationship is the relationship.

Test files stay under `reads` and `parses` on purpose: a test that drives the
resolver is a genuine consumer, and hiding it would hide a surface a later form
change must update.

Inventory regenerated at 355 entries, all ten known surfaces present under the
expected role, zero-diff re-run holds. The regeneration had to follow
`make build-self`, because the tightened derivation refuses to report a
projection whose copies have drifted — it now fails while the tree is
mid-reprojection rather than recording a relationship that does not hold.

## 2026-09-22 — the anchor defect was a class, and I repaired only the instance

A peer session found a second member of the defect class I had just fixed, in
code I had not swept. `workspace_status_engine.py:4124`:

    _CROSS_INI_RE = re.compile(r'^(ini-[^:]+):work:(.+)$')

Consumed with `.match()`, and group 2 compared straight against a workspace
entry's path. Verified independently rather than taken on trust:

| token | `$` (before) | `\Z` (after) |
| --- | --- | --- |
| `ini-002:work:spec/foo` | `spec/foo` | `spec/foo` |
| `…spec/foo` + newline | **`spec/foo`** | refused |
| `…spec/foo` + tab | `spec/foo\t` | `spec/foo\t` |

So a need token carrying a trailing newline yielded the *clean* path and its
dependency reported satisfied — a gate opening on a malformed token. The tab
case was already fail-closed; only the newline leaked, and only because of the
anchor. Fixed to `\Z`, with a generated test over the whole excluded domain that
fails against the old anchor.

**The lesson is mine.** I fixed the `_BRIEF_POINTER_RE` instance and did not
sweep for the class, in a session whose own repair doctrine says repair the
generator, not the instance. A peer had to find the second one.

### The sweep I should have run first

Patterns ending in `$`, bound to a name, consumed by `.match`/`.search` and
never by `fullmatch`, across `packs/core/.apm/`, `tools/` and
`packages/agentbundle/`: **67**.

Most are not defects. The anchor only leaks where the input can carry a trailing
newline, and the large majority of those 67 parse lines from `splitlines()`,
which cannot. The defect class is the subset that validates a whole *value* —
a token or an identifier — sourced from TOML, JSON or a field capture.

Two such cases existed in this delivery's own surface and both are now fixed.
The remainder of the 67 sit in packages and tools this delivery does not touch,
and around fifteen of them are value validators of the same shape
(`_SAFE_SLUG_RE`, `_SHA_RE`, `KEBAB`, `_OWNER_RE`, `_REPO_RE`, `_REF_RE`,
`ID_PATTERN`, `_RE_FINGERPRINT` and others). **They are recorded here and not
fixed**: changing sixty validators across three packages is not this change's
scope, and doing it unilaterally is the widening this delivery has refused
elsewhere. It is a follow-on the owner should place.
