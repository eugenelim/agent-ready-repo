# Owner decisions on this delivery

Every scope-owner decision this delivery rests on, with its date and what it
changed. Recorded here because a criterion or an engine transition that cites an
owner decision needs a durable artifact to resolve to, not a session transcript.

Owner: eugenelim (scope owner and Approver for RFC-0096).

## 2026-09-03 — Build the read-free link *and* admit a new finding code

`workspace-routing-invariants` § *Ask first* reserves adding a finding code to
the owner. Granted for `cooled_child_scope_unknown`, over two alternatives:
reusing `unsatisfied_dependency` alone (declined — the refusal would name the
brief, not the entry a maintainer must edit), and re-registering the follow-on
unbuilt (declined for the mechanism half). Measured basis and the full option set
are in `ask-first-review.md`.

## 2026-09-03 — `cooled_child_scope_unknown` is the code's name

Chosen over `unresolved_parent_link` and `cooled_entry_scope_undeclared`. No
repository source decides a code name, so this is a naming call and is recorded
as one.

## 2026-09-03 — Reverse AC59's undeclared half through an ADR

Closing `cooling-brief-child-scope` makes false a ticked criterion in a frozen
spec. `docs/CONVENTIONS.md:111` and `:143-185` § *Superseding a frozen document*
license exactly one edit to a frozen spec — a `Status`-token parenthetical, whose
form is at `:154-155` — and rule 2 at `:162-163` requires it to point at an ADR
rather than a spec or an RFC erratum. No route was available to an
implementing agent without an Approver signature. Granted, and discharged by
ADR-0110 plus the `Status` pointer AC14 pins.

## 2026-09-03 — Include the engine slug retag as a bundled fix

Withdrawn 2026-09-04 by the *Drop AC22 and T4* decision below, which records
the evidence that withdrew it.

## 2026-09-04 — Apply a bounded fix and proceed to the approval gates

Withdrawn 2026-09-04 by *Converge until clean* below. It was acted on as though
it also licensed skipping `finding-adjudicator` on round 3, which it did not;
`review-record.md` holds that correction.

## 2026-09-04 — Converge until clean

Directed that convergence continue and that round 3 be adjudicated. This is the
authority for the `contract-amendment` transition that clears the approval and
schedule baseline sealed at run sequence 9-11, since that seal does not represent
a converged contract.

## 2026-09-04 — Derive the acceptance criteria from the probes

Round 4 measured AC9 and AC10 false: neither pinned the brief's body status, and
the fixture helper's default puts a `brief_queue.executing` brief out of lifecycle
vocabulary, adding a second `impossible_transition` that both criteria's counts
ignore. Round 3 had found the same defect shape on the child's status axis.

Decision: rewrite the criterion block so each criterion states the fixture its
probe actually ran, with every input pinned and the printed output as the
asserted observable — rather than patch the two instances found. A probe cannot
under-specify an input it had to supply in order to run, so deriving criteria
from probes removes the defect class instead of its instances. One confirming
review round follows, to confirm rather than to hunt.

## 2026-09-04 — Drop the engine slug retag and its task

The engine slug retag is withdrawn. Three facts decided it, none available when
it was authorized on 2026-09-03:

1. No document authorizes it. RFC-0096's 2026-09-01 and 2026-09-03 Errata never
   mention the deferral slug; the 2026-09-03 entry gives Wave 7b "only its
   mechanism half … the read-free parent link". The only live assignment is
   `workspace.toml:378`'s own summary, which is an inference by elimination
   rather than erratum text, and which the withdrawn criterion itself disclaimed as authority.
2. Completing it would leave three surfaces contradicting shipped code, two of
   them frozen: `docs/specs/dependency-scoped-completion-receipts/spec.md:160`
   still lists `engine-cross-repo-deferral-slug-stale` as open, and that spec's
   `notes/follow-ons.md:66` records "This delivery deliberately does **not**
   rename it" — the decision it reverses. This spec's own Boundaries forbid
   editing that directory.
3. The stale comment is the state Wave 7a-ii chose deliberately and recorded its
   reasoning for. Reversing it needs that spec's owner, not this delivery's.

Scope now matches the erratum exactly: the read-free parent link, nothing else.
The `engine-deferral-register-summary-stale` follow-on is withdrawn with it,
since nothing in this delivery makes that summary stale any more.

## 2026-09-04 — Change one acceptance criterion of a live sibling delivery

`docs/specs/cooling-scope-closure/spec.md` is `Status: Implementing`, so
`docs/CONVENTIONS.md:119-129` pins it in substance. Its AC23 is an **unticked**
criterion pinning six file digests, one of which is
`docs/specs/status-projection-and-context-exclusion/spec.md` — the exact file
this delivery's `Status`-line edit changes. The prior Boundaries named five
*frozen* directories and the prior `Ask first` grant reached only a *ticked*
criterion in a *frozen* spec, so nothing authorized the edit: AC23 is neither.

Granted, scoped to that one digest row, with a criterion covering both sites
that hold it and a Boundary forbidding any other change to that spec. The
concurrent Wave 7c delivery is moving four other rows of the same table under
its own owner's approval, so the shape has a live precedent.

## 2026-09-04 — Return adopter documentation to scope

The delivery adds a closeout-time obligation — declare `source.parent` when
cooling an artifact — that otherwise reaches a maintainer only after a
repository-wide refusal has fired. 99 of 115 spec entries declare no
`source.parent`, so the first maintainer to cool one meets the refusal with no
documented warning.

`guides/core/how-to/close-and-disposition-work.md`'s `cool-30-days` row and
`guides/core/reference/workspace-toml-schema.md`'s `parent` row each gain a
criterion, and the Durable Outputs row moves from *Not applicable* to
*Applicable*. Documentation is not waived.

## 2026-09-08 — Spec and plan approved

Both artifacts approved by the scope owner at revision `spec.md` sha256
`4284acb2…`, `plan.md` sha256 `1535d0d2…`, base `79b23d294`. This is the
authority for the `spec-approved` and `plan-approved` transitions and for
`approve-plan` sealing that baseline.

Round 3 of spec review returned one blocker and nine lesser findings, all
dispositioned before the gates fired; `review-record.md` carries the counts.

## 2026-09-08 — Do not widen the grant to the sibling's prose

The `Status`-line edit falsifies two statements in `cooling-scope-closure`
beyond the digest row this delivery's grant covers. Measured, they fail
differently:

- Its Durable Outputs row, "two frozen spec directories are depended on and
  neither may change", is falsified **outright** — and by the concurrent Wave 7c
  delivery on its own, which changes both files of
  `thirty-day-cooling-and-retirement`.
- Its AC23 **title**, "Every pinned file is byte-unchanged", is falsified, but
  its **body** is not: the body reads "The SHA-256 of each file below equals the
  value beside it", a digest-agreement test that this delivery's criterion
  satisfies by moving both sites. So that is a title/body mismatch in that spec,
  not a broken criterion — whoever repairs it should retitle rather than
  re-scope, or they will rewrite a criterion that still holds.

Decision: do not widen the grant. Editing a live sibling delivery's criterion
text is a larger boundary move than the digest row the grant licenses, and
neither delivery could make it complete alone. Wave 7c lands first and carries
the record in its own spec's follow-ons, naming both deliveries as causes and
`cooling-scope-closure`'s owner as the party who restates its prose. This
delivery therefore records no duplicate follow-on.

## 2026-09-08 — The approval covers post-approval repair, at a new revision

The approval above was recorded at `spec.md` `4284acb2…` and `plan.md`
`1535d0d2…`, base `79b23d294`. It was given as "spec and plan approved; make the
updates as appropriate … then review", so it authorizes repair at a later
revision rather than only that one. Two review rounds and Wave 7c's merge have
since moved both artifacts.

Revision now under the same approval: `spec.md` `8386750cf2fb…`, `plan.md`
`d53ffc623aca…`, base `9ab376dcc`.

Two changes are material enough to name, because they alter what the contract
promises rather than how it reads:

1. *The shipped command emits the finding* is no longer manual QA. Its evidence
   home was a hand-written note, so it could not fail once the pull request
   closed, and three shipped roster suites already drive `workspace_status.py`
   as a subprocess. Group 3's mode changes with it and `notes/manual-qa.md` is
   no longer an evidence home. This also removes a violation of this spec's own
   *Never do* rail against claiming what a shipped function emits without
   constructing it.
2. The shared parent-scope fixtures are named — **Declared**, **Empty**,
   **Absent** — instead of being reached through a sibling criterion's ordinal.
   Ten criteria resolved their inputs through up to three ordinal hops, which is
   the reference form this delivery already measured as breaking five times.

Neither narrows scope, adds an obligation, or touches a boundary. If either
reads as a scope change to the owner, the `contract-amendment` edge is the route
back.

## 2026-09-08 — Fix the three discovered defects in this delivery

This delivery surfaced three defects it did not cause, recorded them in
`notes/follow-ons.md`, and descoped them. The owner directed that all three be
fixed here instead. That admits work the accepted contract does not cover, so it
is recorded as an owner decision rather than treated as in-scope.

1. **`.gitignore` covers an interrupted suite's residue.** Three patterns are
   ignored — `/test_state_guard_*.py`, `/state_guard_fs_*` and
   `/state_guard_unused*` — each verified against a real file rather than by
   reading the pattern.

   **The premise this was requested on was wrong, and the correction is
   recorded rather than quietly applied.** The dedup guard does not leak: it
   unlinks every file it creates in a `finally` block, and a complete run —
   measured, `27 passed in 168.93s` — leaves the repository root clean. The
   residue this delivery found came from running that suite in a foreground
   shell with a 120-second limit, so it was killed before `finally` executed.

   The rule is kept because interruption is real and recurring, and a killed
   run does strand files named `test_*.py` where a bare `pytest` collects them.
   It stops the residue reaching a commit; it cannot stop collection.
   `notes/follow-ons.md` carries the corrected entry, including an explicit
   instruction not to rewrite the working cleanup block.
2. **All internal-governance citations are removed from the two shipped
   `workspace-status` scripts.** Each site now states its rule directly, which
   is what `packs/AGENTS.md` asks for; no comment lost its meaning.

   **The first pass claimed zero against the wrong denominator.** It matched
   `AC<n>` and `RFC-<n>` only, cleared seven sites, and recorded zero — while
   five citations remained that the pattern never looked for: `Wave 7`,
   `Wave-6` twice, `Wave 5`, and the repository-only spec slug
   `wave6-dependency-scoped-completion-receipts`. A review measured them. The
   denominator is now records (`ADR-nnnn`, `RFC-nnnn`), criteria (`AC<n>`), wave
   vocabulary, and spec slugs, and under that set both files measure zero.

   The lesson is the claim, not the citations: a count is only as good as the
   pattern that produced it, so the pattern belongs beside the number.
3. **The ADR index is complete.** ADR-0105's row was added as directed. An
   audit of all 107 ADR files against the index then found one further gap,
   ADR-0060, whose Status is Accepted and whose neighbours 0059 and 0061 are
   both listed — an omission rather than a convention. Its row was added too, so
   the count of ADR files without a README row is now zero. That second row was
   not requested and is one line; it is called out here because it is the only
   part of this decision the owner did not name.

No acceptance criterion changes. The delivery's own criteria are unaffected:
none of them reads a comment, the `.gitignore`, or the ADR index.

## 2026-09-08 — Two corrections to T4's registration, after the plan froze

`plan.md` is hash-frozen from approval, so these are recorded here rather than
edited into it. Both were found by the full local roster run, not by inspection.

### The `[work]` collection is `active`, not `shipped`

T4's approach says to register the spec entry "**into `shipped`**", reasoning
that "this PR ends with the spec at `Shipped`". That reasoning is wrong about
*when* the gate reads the value. Measured in
`packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`:

| Collection | Status the engine requires |
| --- | --- |
| `work.active` | `Implementing` |
| `work.shipped` | `Shipped` |
| `work.queue` | anything except `Implementing` or `Shipped` |

The spec reads `Status: Implementing` for the whole of EXECUTE and only becomes
`Shipped` at closeout, which is after every gate in this delivery runs. Placed
in `shipped`, the entry drew `impossible_transition` ("shipped spec status") and
failed `test_no_fail_closed_lifecycle_findings`, which is zero-tolerance over
the real `workspace.toml`.

The entry is registered in `ini-002`'s `work.active`. Closeout moves it to
`shipped` together with the Status, which is the ordinary lifecycle rather than
a deviation.

The plan review that produced T4's collection clause was right that the
collection is not a free choice and must be tied to the end-state Status. It was
wrong only about which end state the gate observes — and so was this delivery,
which implemented it as written.

### The `[backlog].open` summary exceeded the 500-character bound

The entry's `summary` was 501 characters against a bound of 500 enforced at
`_is_bounded_text(summary, 500)`, which returns `invalid_entry`. One character
over. The concurrent Wave 7c entry sits at 494.

This was named as a shared-surface hazard before either delivery started, and
still shipped, because nothing measures the length at authoring time — the
failure surfaces only in a roster run that takes about fifteen minutes. The
summary is now 391 characters and names all four follow-ons rather than the two
the longer version listed.

## 2026-09-08 — T4 omitted the web reprojection its own `Highlights` step requires

Recorded here because `plan.md` is frozen. Found by CI, not by inspection or by
any local gate.

T4 makes the `Highlights` disposition an explicit step and answers it yes,
drafting the bullets under `### Highlights` in the changelog. It does not name
what that answer obliges downstream: `web/src/lib/now-highlights.generated.json`
is a tracked projection of those bullets and the `/now/` page renders from it.

`FORCE=1 make build-self` does not emit web projections, so the file stayed at
`[core][2.25.6]` while the changelog said `[core][2.25.7]`. Neither
`SKIP_SAST=1 make build-check` nor the roster suites read it. Only `make test`
does, which is why the remote `test-corpus` workflow was the only gate that
failed and the only one that could have.

The regenerator is `python3 tools/build-site.py --journeys-only`. Run at base
`02742751a` it reported `118 released highlight(s) in 84 release group(s)` and
changed exactly one file. Segmentation is partial, and the record says so
because the earlier version of this paragraph claimed otherwise: body text is
split into `text` and `code` segments, but a bold lead is emitted as one
`strong` segment whose value is the raw source, and the renderer prints a
`strong` segment without nested parsing. So the second bullet's `` `none` ``
reaches the page with its backticks visible. Six earlier releases already carry
that shape, which makes it the projection's existing behaviour rather than
something this delivery introduced.

**The lesson for the task shape, not just this instance.** T4's Touches list was
extended twice during review to name projections its own commands rewrite, and
it still missed this one — because this projection is written by a *different*
command than the one T4 names. A step that produces published content owes both
the artifact and its regenerator, and the two are not always the same tool.

## 2026-09-08 — Amend the contract to state which memberships resolve a declared parent

A confirming review found the repaired predicate pinned by four tests and by no
acceptance criterion. The Read-free parent scope section names no criterion for
kind-based, collection-agnostic resolution: nothing in the spec covers a brief in
`[backlog].open`, a brief retained as a legacy bare string, or a mis-collected
`kind = "spec"` entry sitting in a brief queue.

So the durable contract still permitted the defect that produced three of this
delivery's five review blockers. A later change could revert to collection-keying
and satisfy every criterion in the spec — the suite would fail, which makes the
guard real, but not contractual.

Decision: amend. Fire `contract-amendment`, add one criterion, re-approve, and
re-seal. The owner accepted the cost: the amendment clears the sealed approval
baseline, so the spec and plan need re-approval and the schedule needs
recomputing before EXECUTE resumes.

The alternative — ship and record the gap as a follow-on — was declined. The
reasoning: a criterion is what makes the behaviour survive a later maintainer
who reads the spec rather than the suite, and this is precisely the predicate
three independent reviewers each got wrong from a different direction.

**Fixtures are already built.** All four arms exist as cases from the review
repairs, so the criterion is transcribed from tests that run rather than written
from intent — the same discipline the parent-scope criteria were derived under.

T0 through T4 are complete and their evidence is carried into the amendment
rather than discarded.
