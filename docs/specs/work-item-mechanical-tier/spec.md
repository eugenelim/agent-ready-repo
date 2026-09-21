# Spec: The capture mechanical tier — which two checks, over which field

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Plan:** none — no plan is authored until the field decision lands; every
  criterion here is blocked, so a plan would schedule work nothing can start
- **Contract:** `contracts/jsonschema/knowledge-captured-observation.schema.json`,
  read-only here. This spec adds no field to it; if the field decision
  chooses a new one, that is an amendment to
  `docs/specs/work-item-capture/spec.md` § D2, not a change made here
- **Brief:** none
- **Discovery:** docs/product/intents/FEAT-0006-work-item-capture-contract.md
- **Constrained by:** docs/specs/work-item-capture/spec.md — the record this tier validates is written under the contract that spec settles. That spec ships without this tier; `docs/specs/work-item-capture/spec.md` § D10's merge-path disclosure and `docs/specs/work-item-capture/spec.md` § D6's stored-path set are the two surfaces this one must not contradict.

> **Contract tier.** `## Decisions this spec makes, and what it still owes`
> is **contract**, on the same footing as Acceptance Criteria: the two-check
> scope and the anchor exclusion change only by amendment, and so does every
> point in the owed list. `## Objective` and `## Boundaries` are **working
> material** — they restate fences other artifacts own. This mirrors
> `docs/specs/work-item-capture/spec.md`'s tiering, which the carried body
> was written under.

## Objective

Settle the deterministic half of capture validation: two checks over a cited
repair target, and the questions that choosing that target opens. The owed
list below is the assertion; no count appears here, because that list grew at
every review round and a literal falsifies as soon as it does again.

This was § D12 of `docs/specs/work-item-capture/spec.md` — a section that
no longer exists there, its numbering having ended at § D11 — and is split
out
because it did not converge. Across nine review rounds its owed list grew at
every round without exception, while that spec's other decisions were stable
throughout, and two attempts to supply the missing field from inside it each
produced a round's worth of findings. The capture spec now ships its
unblocked criteria; this spec carries the five that were blocked.

## Boundaries

- **The record contract.** `docs/specs/work-item-capture/spec.md` owns what a
  record must be, including `docs/specs/work-item-capture/spec.md` § D6's stored-path set and `docs/specs/work-item-capture/spec.md` § D10's merge-path
  disclosure. This spec adds a field to that contract only through an
  amendment there, never by restating it here.
- **The reasoning tier.** That spec's `docs/specs/work-item-capture/spec.md` § D3 owns it. This tier is the floor
  beneath it, and `AC-0003` and `AC-0004` are the fail-closed controls
  that make the floor hold.
- **Anchor-versus-bytes comparison.** Excluded, and it stays the registered
  freshness item's — `workspace.toml` `[backlog].open`, slug
  `knowledge-freshness-pins-bytes-and-the-pins-do-not-hold`. That exclusion is settled and is the one part of the
  original § D1 that never came into question.

## Decisions this spec makes, and what it still owes

**Made here**, carried from the original section and not reopened by the
split: the tier is **exactly two checks**, and anchor-versus-bytes comparison
is **excluded** and stays the registered freshness item's — `workspace.toml`
`[backlog].open`, slug
`knowledge-freshness-pins-bytes-and-the-pins-do-not-hold`. Approving this
spec approves that scope.

**Owed**, and settled nowhere: the field the two checks read, and every point
listed under it. The body below is the original section carried verbatim,
including its two rejected candidates and the grounds for rejecting each — so
neither is retried.

### D1 — the mechanical tier is exactly two checks

FEAT-0006 names the tier three times over: § Validation at capture enumerates a frozen
target, a recorded anchor still matching the file, and a cited artifact that
exists and carries a readable status — while the same intent's § Non-goals
registers *whether a stored digest reflects a file's current state* as a
separate open item with its own owner, which
`docs/specs/work-item-capture/spec.md` § Inherited constraints
accepts verbatim. The middle check sits in both lists.

The tier is therefore the two checks that are not the registered item's:

1. **The cited target is not frozen.** Read the cited artifact's `Status:`; a
   frozen target cannot take the repair the item proposes, which is the first
   of the three error classes FEAT-0006 § Validation at capture names.
2. **The cited artifact exists and carries a readable status.**

> **Open at the gate: which field names the repair target.** Both checks
> read "the cited artifact" — the file the item proposes to change — and the
> record contract has no field with that meaning. This spec does not settle
> it, and the two candidates were each tried and rejected:
>
> - **A new `work_item` field.** Costs permanent v2 surface and re-opens three
>   settled sets: the privacy-scan derivation, `docs/specs/work-item-capture/spec.md` § D6's stored-path set, and a
>   fail-open rule for its absence. Each needed its own criterion.
> - **`freshness_anchor.path`.** Semantically wrong. `docs/specs/work-item-capture/spec.md` § D5 contracts the anchor
>   as the *provenance pin* — what a cold session holds — not the repair
>   target, and a submitter chooses both independently. A record proposing a
>   repair to a frozen document, anchored at any readable non-frozen file,
>   clears check 1 unrefused: the tier would refuse a frozen *anchor* and
>   never a frozen *target*. Check 2 also drags the anchor onto the existence
>   axis, which is the registered freshness item's.
>
> Until the owner settles this, **both § D1 checks are unimplementable** and
> **all five criteria that quantify over them are blocked**: `AC-0001`,
> `AC-0002`, `AC-0003`, `AC-0004` and `AC-0005`. **`AC-0003` and `AC-0004`** are
> the fail-closed controls — named by id, never by position, because a
> positional citation is what broke most references when this list was
> renumbered — so an implementer who drives them against a stubbed or
> invented tier turns the suite green on a tier that never ran.
>
> The decision owes these, besides the field. The list is the assertion;
> no count appears, because this list has grown at every review round and a
> literal falsifies as soon as it does:
>
> 1. **[catalog-code]** **The `docs/specs/work-item-capture/spec.md` § D4 catalog code a § D1 refusal returns.** None of the fifteen
>    baseline codes fits and this spec adds none, so `docs/specs/work-item-capture/spec.md` `AC-0037` has nothing
>    to draw for this path. `docs/specs/work-item-capture/spec.md` `AC-0037` is **not** blocked — it ticks green
>    over the other refusal paths — but settling this **amends `docs/specs/work-item-capture/spec.md` § D4**:
>    its table and its pinned count of eleven both move, and `docs/specs/work-item-capture/spec.md` § D4 is the
>    single home for that count, so `docs/specs/work-item-capture/plan.md`
>    T5's enumeration moves with it.
> 2. **[absence-behaviour]** **What the tier does when the field is absent.** Fail-closed, or
>    justified otherwise. This question survived both rejected candidates: it
>    was invisible only under the anchor, which the schema requires. If
>    absence admits, the whole mechanical tier is bypassed by omitting one
>    field and `AC-0003`/`AC-0004` are void.
> 3. **[write-side-membership]** **Whether the chosen field joins `docs/specs/work-item-capture/spec.md` § D6's stored-path set** and so
>    `docs/specs/work-item-capture/spec.md` § D6's stored-path rules at write time (which confine that set to the repository and do not classify sensitivity). `_expect_repo_path` is applied
>    field-by-field at each call site, so a new path-bearing field is
>    unvalidated until someone wires it, and
>    `docs/specs/work-item-promotion-handoff/spec.md`'s obligation 1
>    is post-resolution confinement over the *command*, not this field.
>    § D1 settles the read; this settles the write.
> 4. **[privacy-scan]** **Which privacy scan the chosen field reaches**, or the ground for
>    excluding it. `docs/specs/work-item-capture/spec.md` `AC-0031` derives its set from `work_item` properties
>    only, and this decision rejected the `work_item` candidate — so a
>    field chosen outside that object reaches neither
>    `assert_persistable_text` nor `assert_persistable_paths`, and
>    `docs/specs/work-item-capture/spec.md` `AC-0031`'s totality partition never sees it, so nothing fails
>    loudly. State also whether `docs/specs/work-item-capture/spec.md` `AC-0031`, `docs/specs/work-item-capture/spec.md` `AC-0035` and `docs/specs/work-item-capture/plan.md` T5's pinned six
>    move.
> 5. **[requiredness]** **Whether the chosen field is required, and for which shapes.** This
>    is not the same as the **absence-behaviour** point, which settles
>    what happens when it is
>    absent; this settles whether absence is reachable at all. Making
>    it shape-required amends `docs/specs/work-item-capture/spec.md` § D2, which is contract, and moves
>    `AC-0003`'s per-shape missing-field set and `AC-0004`'s
>    complete-record set. The answer need not be uniform: a `question`
>    plausibly cites no repair target, and a conditionally required
>    field makes check 1 conditional — which is the shape the
>    **absence-behaviour** point's fail-closed rule must be written against.
> 6. **[read-path]** **Whether the tier runs on the read path or only at the write path.**
>    `docs/specs/work-item-capture/spec.md` § D11 makes the version-selected validator the read path's rule and
>    `docs/specs/work-item-capture/spec.md` `AC-0015` replays every record in the store, so if the checks live
>    inside the v2 validator a replaying reader performs filesystem
>    access on an attacker-supplied path in **their** tree, once per
>    record. Nothing in `docs/specs/work-item-capture/spec.md` § D10, `docs/specs/work-item-capture/spec.md` § D11 or § D1 says the tier is
>    write-path-only. If it can run on read, say which principal's tree
>    bounds it, and note that the **indistinguishability** point's answer
>    governs that site too.
> 7. **[refusal-remap]** **What the tier does with each refusal `read_confined_source`
>    raises.** The helper does not return a status: it raises
>    `KnowledgeStoreError` with `confinement` for a bad path, a missing
>    file, a symlink, a non-regular file, a hard link or any `OSError`,
>    and `journal_capacity` above the byte budget. Two consequences
>    the **catalog-code** point does not reach, because it owes only the
>    code a refusal
>    *returns*. **Check 2's existence arm is already inside
>    `confinement`**, collapsed with traversal, so getting `AC-0002`'s
>    distinct missing-artifact refusal means catching and remapping —
>    and that `except` is where a fail-open "cannot read, so cannot
>    refuse" lands, bypassing check 1 by citing an unreadable path.
>    **And `journal_capacity` versus `confinement` already
>    distinguishes** "exists and is over the budget" from "missing",
>    which leaks whatever the **indistinguishability** point answers,
>    because the distinction is
>    the helper's and not the tier's. Settle propagate, collapse or
>    remap for each, bound to the **indistinguishability** point and to
>    check 2's existence arm.
> 8. **[residual-bit]** **The residual admit/refuse bit, which no answer to the
>    indistinguishability point removes.** Check 1 puts a file's **content** on the answer axis,
>    not merely its existence: the tier reads the cited artifact's
>    `Status:` and refuses only when it reads as frozen. Collapsing
>    every cause into one indistinguishable refusal still leaves the
>    admit-versus-refuse bit, which is the conjunction "the path
>    exists, is readable, is under the byte budget, and its `Status:`
>    is not frozen" — a one-bit read of a line in a file the
>    answering principal may not hold. It bites at the sites
>    the **indistinguishability** point names — however many that point's
>    conditional resolves to. The bit is **irreducible**,
>    because refusing is
>    the tier's whole purpose, so it cannot be settled the way the
>    causes can: bound it against the principal the **read-path** point
>    identifies,
>    or disclose it. Choosing disclosure **amends
>    `docs/specs/work-item-capture/spec.md`'s Durable Outputs security row** — the same obligation the **catalog-code** point carries
>    for `docs/specs/work-item-capture/spec.md` § D4 — because that row's list is closed as written and has no slot
>    the § D1 answer can fill. Without the amendment the branch lands
>    nowhere when the tier is built, and is absorbed by "absent mechanical
>    tier" when it is not, so the gap is invisible exactly when it is live. (References in this list name
>    points rather than numbering them: an insertion silently broke the
>    ordinals three times.)
> 9. **[replay-cost]** **What bounds the tier's aggregate filesystem work
>    if it runs at replay.** The **read-path** point asks which
>    principal's tree is read — the confidentiality half — and stops
>    there. `read_confined_source`'s byte budget bounds a *single*
>    read, not the aggregate: if the checks live in the v2 validator,
>    `docs/specs/work-item-capture/spec.md` `AC-0015` replays every record, so a merge-path submitter lands N
>    records each citing the largest readable file in the reader's
>    tree and every reader pays N budget-sized reads on paths they did
>    not choose. Conditional on the **read-path** answer, like the
>    **residual-bit** and **indistinguishability** points; void if the
>    tier is write-path-only, which that answer may simply state.
> 10. **[indistinguishability]** **Whether the refusal causes must be indistinguishable.**
>    `SAFE_DIAGNOSTIC_FIELDS` admits `path` and `line`, so distinguishable
>    refusals make the capture API an existence-and-shape oracle over
>    working-tree files. It is not vacuous: the submitter already holds the
>    tree, so this bites across the `docs/specs/work-item-capture/spec.md` § D10 merge path, where the record's
>    author and the close output's reader are **different principals** and
>    the reader may not hold the files being probed — **and, if the
>    read-path point puts the tier there, at every replay**, where `docs/specs/work-item-capture/spec.md` `AC-0015` makes
>    every reader a different principal from every record's author whether
>    the record arrived by merge or not. Answering this against the merge
>    path alone leaves the replay site uncovered.
>
> **Both checks read a record-supplied path**, which `docs/specs/work-item-capture/spec.md` § D10 discloses is
> attacker-influenced on the merge path, so whatever field is chosen the read
> goes through the repository's confinement surface — `store.read_confined_source`,
> as `project_knowledge.py` already does —
> never a fresh `open`. The surface is the **single** helper call: path
> validation happens inside `read_confined_source`, not as a step before it,
> so "validate then open the normalised path" is a bypass, not a compliance.
> `AC-0005` drives that as a **total** property over
> the tier's opens; stating it here alone would be a requirement no criterion
> could fail, and asserting it per call would pass on a check that confines
> one read and not another.

Comparing a recorded anchor digest against current bytes is **excluded** and
stays the registered freshness item's. This resolves the contradiction toward
the exclusion the spec already inherits rather than silently reversing it, and
no anchor-versus-file comparison exists anywhere in the store today.

The set is closed: `AC-0001`, `AC-0002`, `AC-0003`, `AC-0004` and `AC-0005` quantify
over these two checks and nothing else.

## Testing Strategy

Every criterion here is blocked until the field decision lands, so no mode is
declared yet: the mode depends on which field is chosen and whether the tier
runs on the read path. Declaring one now would pin a surface the decision may
move. What is already fixed:

- `AC-0001` and `AC-0002` are the two checks themselves — a frozen cited
  target, and an artifact that is missing or has no readable status. Both are
  driven separately so neither masks the other, and both depend on the field
  decision for something to cite.
- `AC-0005` is **one total assertion over the tier**, not a per-check drive. A
  per-check call-spy passes on a check that confines one read and not another.
- `AC-0003` and `AC-0004` must be driven against a real tier, not a stub. A
  stubbed tier satisfies both while proving nothing, which is why they were
  blocked rather than left drivable.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable: the owed list is the whole of this spec | This spec § Decisions | eugenelim | The gate approval | Every point in the owed list is settled, and the two rejected candidates stay recorded so neither is retried |
| Current architecture (security) | Applicable: this spec's absence is a gap the sibling ships with | `docs/architecture/security.md` | work-loop | `docs/specs/work-item-capture/spec.md`'s security Durable Outputs row is canonical for the gap list; landing this spec removes the absent-tier member from it | That row no longer lists the mechanical tier as absent |
| Interface compatibility | Applicable only if the field decision adds a record field | `contracts/jsonschema/knowledge-captured-observation.schema.json` | project-knowledge | An amendment to `docs/specs/work-item-capture/spec.md` § D2 | No field reaches the schema without that amendment |
| Reusable learning | Applicable: the split itself is the lesson | `docs/specs/work-item-capture/notes/resolve-vs-surface.md` | work-loop | The record of why nine rounds did not converge | A later author does not retry either rejected candidate |
| Maintainer procedure | Not applicable | — | — | — | No procedure changes until the tier exists |
| Current product truth | Not applicable | — | — | — | Adopters see no behaviour from an unbuilt tier |
| Release history | Not applicable | — | — | — | Nothing ships from this spec yet |

## Agent Rules

### Always do

- Read the two rejected candidates before proposing a field. Each cost a
  review round and both grounds still hold.
- Cite a criterion from another spec with that spec's path. Three ids in this
  document's history — `AC-0010`, `AC-0011`, `AC-0012` — are live ids with
  different meanings in `docs/specs/work-item-promotion-handoff/spec.md`.

### Ask first

- Adding a field to the record contract. That is an amendment to
  `docs/specs/work-item-capture/spec.md` § D2 and moves its per-shape
  criteria.
- Answering any owed point in a way that amends a pinned artifact — the
  **catalog-code** point moves § D4's table and count, the **privacy-scan**
  point moves the derived field set, the **residual-bit** point moves the
  security gap list.

### Never do

- Build this tier against an invented field. Two were tried; both are
  recorded as rejected with grounds.
- Drive `AC-0003` or `AC-0004` against a stubbed tier. Both are fail-closed
  controls and a stub satisfies them while proving nothing.
- Let this spec's absence weaken the sibling's floor:
  `docs/specs/work-item-capture/spec.md` `AC-0068` is that delivery's
  fail-closed rule and does not retire when this tier lands.

## Follow-ons

- work-item-capture: `docs/specs/work-item-capture/spec.md` — the record
  contract this tier validates, shipping without the tier.
- knowledge-freshness: `workspace.toml` `[backlog].open`, slug
  `knowledge-freshness-pins-bytes-and-the-pins-do-not-hold` — owns
  anchor-versus-bytes comparison, which this spec excludes.

## Assumptions

- Technical: the two checks are worth building at all. Nine review rounds
  settled the tier's scope and never tested the premise that a deterministic
  tier earns its cost against the reasoning tier alone. If the sibling ships
  and the reasoning tier proves sufficient, closing this spec unbuilt is a
  legitimate outcome (settled by: nothing yet).

## Acceptance Criteria

> **Stable identifiers.** Numbering is per-spec and restarts here. These five
> were `AC-0001`, `AC-0002`, `AC-0003`, `AC-0004` and `AC-0005` in
> `docs/specs/work-item-capture/spec.md`; that spec's Follow-ons records the
> mapping. All five are **blocked** on the field decision above.

- [ ] `AC-0001` A capture whose cited target is frozen is not written.

- [ ] `AC-0002` A capture whose cited artifact does not exist, or carries no
      readable status, is not written.
- [ ] `AC-0003` Both § D1 checks still refuse whenever the reasoning tier
      has not returned a recognized verdict — the property form
      `docs/specs/work-item-capture/spec.md` `AC-0068` states, and for the
      same reason: an enumerated mode list admits whatever mode nobody
      enumerated. "Degraded" means what that criterion defines it to mean,
      a well-formed timely response whose verdict is outside the expected
      set; expiry and an unconfigured tier are covered by the property and
      would not be by a three-mode list.
- [ ] `AC-0004` An item both § D1 checks admit is not written unless the
      reasoning tier returned a recognized verdict for it — the property
      form, not a mode list, per `docs/specs/work-item-capture/spec.md`
      `AC-0068`. This criterion is conditioned on an item both checks
      admit, which is why it never covers tier unavailability and never
      replaces `AC-0068`. The tier subtracts
      admissions; it never adds one by being unavailable.
- [ ] `AC-0005` **Every filesystem access the § D1 tier makes to a
      record-supplied path goes through `store.read_confined_source`** —
      opens, and also `stat`, `exists`, `glob` and any out-of-process
      read. The property is total over the tier, not per check, and the
      criterion states the property; the plan owns the mechanism,
      because the obvious one is self-defeating: patching `open`/`Path.open`
      inverts the assertion, since the helper itself reads through
      `path.open`. This spec's own plan owns the mechanism when it is
      written.

      Two shapes must fail. **A second read that bypasses:** a check
      reading the target confined and its derived sibling `spec.md`
      unconfined — which `project_knowledge.py` does for its own
      artifact check — passes a per-check call-spy and passes `is not
      written`. **An existence probe that never opens:**
      `(repo_root / target).exists()` performs no open, follows
      symlinks where `_assert_confined_components` refuses a reparse
      point per component, and never reaches `_expect_repo_path` — so
      an opens-only property misses the oracle § D1's
      **indistinguishability** point prices.

      What the helper adds over an unvalidated read: path validation,
      per-component **refusal** of symlinks and reparse points — it does
      not resolve them, and calling `.resolve()` on the path before handing
      it over collapses that refusal — regular-file and hard-link checks,
      root-relative anchoring, and a byte budget.
      A read that never called `_expect_repo_path` is traversal, not
      merely unresolved.
