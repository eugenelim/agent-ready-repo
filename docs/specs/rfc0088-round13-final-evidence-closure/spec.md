# Spec: rfc0088-round13-final-evidence-closure

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0088](../../rfc/0088-web-pilot-foundation.md) — Experimental; this spec
    closes or explicitly disposes the round-12 residuals, consolidates the prior
    rounds and spikes, and assembles the approver's decision package. It changes no
    disposition and does not move the status field.
  - [RFC-0093](../../rfc/0093-intent-scoped-completion.md) — the accepted intent is
    this whole round; it is delivered as four review units in one session.
- **Contract:** none for production interfaces — this spec produces evidence, an
  evidence digest, and an RFC amendment-layer section, and changes only the
  existing out-of-repository evidence apparatus named in the plan.
- **Shape:** service

## Objective

Round 13 is commissioned as the final evidence round. Its purpose is to make the
approver's outstanding RFC-0088 decisions *possible*, not to take them.

**It does not reach final, and says so up front rather than discovering it at the
end.** Of the thirteen open `rfc0088-*` register slugs, five close with evidence, two close but
retain their register membership as frozen lint anchors, one converts to a named
implementation concern, and **five are carried** — two because their own unblock conditions
are unmet, two because no single round can measure them, and one because it needs a
toolchain that is a new dependency. The verdict is therefore **NOT FINAL**, with a materially shorter tail than the
round started with. Task D exists to make that statement checkable instead of
rhetorical, and a round that relabels an unmeasurable residual in order to declare
itself final defeats the point.

Three things must be true at the end, each separately verifiable:

1. **Every open slug has exactly one disposition** — closed with the evidence named,
   converted to a named implementation concern recorded where it survives into the
   build, or carried with the reason it cannot close and what would close it.
2. **One document carries every prior round and spike.** One entry per enumerated
   member, withdrawals and reversals included. That is the observable; "readable in
   one sitting" is the intent behind it, not the test.
3. **The approver can rule from one section**, which names each of open questions 1
   through 6, states each one's status, and links the registered document holding its
   measured basis.

## Review units

The accepted intent is the whole round. It is delivered as four independently
reviewable units, each of which leaves the repository and the apparatus working.
Units 1 through 3 reach their human gate with `spec.md` at `Status: Implementing`
and declare the boundary explicitly; only unit 4 marks the spec `Shipped`.

| Unit | Tasks | Why it is separable |
| --- | --- | --- |
| 1 | T0 | Relocation and path independence. Every later unit's evidence depends on it, and it is the unit that makes the other three trustworthy. |
| 2 | T1–T3, T5 | Apparatus corrections and mutation coverage. Depends only on the relocated tree. |
| 3 | T6 | The one net-new measurement arm. |
| 4 | T4, T7–T9 | The deliverables: digest, RFC section, disposition partition. Each is a single coherent artifact. T4 rides here because dropping the bearer secret left it with no apparatus change, and it writes into the digest T7 creates. |

## Boundaries

### The RFC evidence layer, by anchor

"Evidence layer" means **everything at or below the `## Amendments` heading** of
`docs/rfc/0088-web-pilot-foundation.md`. Everything above it is frozen body.

This matters because `## Follow-on artifacts` sits *above* that heading and is
therefore body, and its own text says no follow-on artifact is created while the RFC
is Draft or Experimental. Adding named concerns to its Spec 1/2/3 descriptions would
change what those artifacts are scoped to do — a meaning-changing body edit. Converted
concerns are therefore recorded in this round's **amendment entry**, not in the body,
and a check confines the RFC diff to the anchored range.

### Forbidden identifiers and privacy corpus

No round-13 artifact, note, digest entry, commit, PR title, or PR body may contain a
real vendor, product, employer, tenant, account, or organisation identifier; a
signing-team identifier; a non-loopback URI; a credential value; a home directory; a
per-user temporary path; or a hostname. Role labels, booleans, and counts only.
Targets come from the environment and are never persisted.

A numeric uid is permitted in results provenance on the round-12 terms. Where an arm
records a boolean instead, its field is named `runnerUidMatchesProfileUid`, so the
phrase "same-uid" stays reserved for the claim and a phrase-level control over it
cannot collide with a field name.

**Role labels here are singleton by necessity, and that is a stated bound.** A
sign-in surface, a mail surface and a real-time collaboration surface have *opposite*
worker dependencies, and that contrast is the entire content of open question 4.
Generalising them into a non-singleton label would delete the finding rather than
protect it. Identity is withheld; the role is not.

The **round-13 privacy corpus** is what the sweep can actually read: the RFC, the
notes and spikes directory, every round-scoped spec resolved from the declared
source, `workspace.toml`, and any base64 payload block inside those documents.
Round-13 drivers and results live in the out-of-repository tree and reach no scanner;
that exclusion is an **accepted bound**, stated rather than implied, because this
round adds no promotion task that would manifest them.

The out-of-repository apparatus is outside every repository scanner — SAST, secret
scanning, and dependency audit all stop at the repository boundary, and relocating
the tree does not change that. Also an accepted bound.

The inherited exemption-table rules from round 12 continue unchanged: a changed
member loses its exemption, and the set cannot widen without a spec amendment.

**Declared shared-tool edits for round 13.** Every task in this round edits manifested
archive members, so every unit trips that rule; the exception exists for exactly this case
and requires the edits to be *declared* rather than discovered. Round 13 declares them:
`r10-fact-negative-tests.py` and `run-r12.sh` and `r12-fact-negative-tests.py` (T0),
`verify-note-figures-r7.py` and `r9-privacy-sweep.py` (T1), `build-archive.py` and the new
shared reader `privacy_terms.py` (T2), `s3/r12-page-resident-token.mjs` (T3, T5), `r9-gates.sh` and
`r9-promote.sh` (T5, and T2's anchor capture step), one new `s3` driver (T6), and `corpus_docs.py` plus every consumer of that derivation as
enumerated by search (T7). The deliverable-side controls are declared too, because they
are new manifested members rather than edits: `figure_boundary.py` and
`r13-digest-coverage.py` (T7), `r13-decision-surface.py` (T8), and
`r13-disposition-partition.py` (T9). A digest is re-recorded **only** after a
scan confirms that member's allowed occurrence count is unchanged; a changed count, a new
member, or a widened set refuses and surfaces instead. The comparison is per member on
occurrence counts, not on the table as a whole — comparing the table wholesale reports a
spurious widening the first time any digest moves.

### Always do

- Treat the relocated evidence tree as the only tree. Every script resolves its own
  root from its own location, and every artifact refers to the tree only by a
  tree-relative path — never by an absolute one.
- Make every selector name the set its claim is about, **in the direction that fails
  closed**. A verifier's selectors become closed member lists, because a verifier
  that over-selects fails closed. A detector's discovery stays greedy plus a
  minimum-membership assertion, because a detector that under-selects fails open.
- Give every new control a mutation or planted failure that makes it report a
  failure, and admit the control only when that flip was observed. This applies to
  the deliverable-side checks too, not only to the apparatus ones.
- **Check multi-home facts mechanically, not by eye.** Every review finding after the
  first round was one shape: a fact stated in N places and updated in N−1. Six passes
  caught those one round behind each fix, which is a cycle rather than convergence. A
  cross-document consistency control therefore asserts the classes that recurred —
  task-to-unit assignment across its three homes, an acyclic dependency graph, no prose
  restatement of a count whose home is a control's own enumeration, every implemented
  failure branch enumerated, and every member the plan says it touches present in the
  declared shared-tool-edit list. It runs in the gate chain, and it is
  discrimination-proven like any other control.
- Where a mutation refuses to discriminate, ask whether the guard is redundant before
  writing a fixture for it.
- Restate every carried risk at the width the **code** supports, naming which
  listener, endpoint or component the bound is about. Two components with a similar
  bound are corrected separately so no phrase-level sweep spans both.
- Run subprocesses under an explicit environment allowlist; record variable names
  and presence booleans only.
- Route every purge through the single manifested `s1/confined-remove.mjs` helper. **One
  declared exception:** a run temporary root the runner itself created may have its symlinks
  unlinked first, because the helper refuses a symlink-bearing tree and a browser profile
  always contains one, so the rule as written makes teardown impossible and leaves the
  profile — and the token in it — at rest. The exception is bounded to a child proven owned,
  `0700`, and directly beneath the runner's own parent; the unlink cannot follow a link; and
  the helper still performs the removal. It does not extend to any tree whose contents came
  from outside the runner.
- Read state back from results rather than asserting requested state.

### Ask first

- Adding a dependency, toolchain, or compile step.
- Creating a local OS account or performing an administrator operation.
- Using a credential, account, or live authenticated session at a destination.
- Extending the round beyond the tasks in `plan.md`.
- Changing an RFC decision, disposition, blocker item, or status field.

### Never do

- Implement production packs, runtime code, dependencies, contracts, catalogue
  entries, adapters, or top-level directories.
- Create any RFC-0088 follow-on artifact: no ADR, no `auth: browser-session`
  convention amendment, no Spec 1, 2, or 3.
- Edit the RFC's frozen body — everything above `## Amendments`.
- Move RFC-0088 to Accepted, close a blocker item, or revise a disposition — **including
  by widening the actor set of an already-accepted risk.** Widening a bound inside an
  accepted disposition's scope retroactively treats the wider exposure as accepted, which
  is a ruling. Record the wider fact in the evidence layer as new evidence requiring
  re-ruling and leave the disposition's text verbatim. An earlier draft of this spec
  carried a "factual width correction is not a disposition revision" exemption; it was an
  exemption invented to permit exactly what this rule forbids, and it is withdrawn.
- Edit `EXPECTED_FAILING_ROW_IDS`, or any equivalent declared-prior-finding list, to
  clear a failure. It is the only gate that catches a result silently *improving*.
- Convert a characterisation fixture, inspection-only result, hard-coded literal,
  missing expected row, or failed security precondition into a Pass.
- Put an apparatus headline figure — coverage percentage, claim-accounting total,
  mutation-corpus size, or harness count — into the digest or the round-13 RFC
  section. Those live in gate output and artifacts.
- Add a bearer credential to page-resident code. The init script is built by the
  driver, so any such credential makes the driver hold a token-equivalent capability
  and lands in the recorded surfaces this round scans.
- Attempt to close open question 3. It is not a measurement question.

## Testing Strategy

| Outcome | Mode | Verification |
| --- | --- | --- |
| Tree relocation and path independence | Goal-based | Walks of both trees compared as sets in both directions; the pre-correction form refused under a simulated sweep and the post-correction form passed, both observed |
| Apparatus code changes | Visual / manual QA | Each runs in the declared gate chain and its mutation was observed to flip |
| New measurement arm | Visual / manual QA | Control failed in the same run that admitted the arm |
| Digest and RFC section | Goal-based | Registered corpus derivation passes; a planted figure inside the anchor is caught and one outside it is not; all five derivation consumers re-run |
| Disposition coverage | Goal-based | Every failure branch the partition control enumerates is planted and observed to fire; the control prints its own branch list, so no document restates a count |
| Nothing decided, nothing unlocked (AC13) | Goal-based | Status field unchanged; RFC diff confined to the anchored range; a planted decoy follow-on artifact is caught |

**Gate order**, and it must name every tool this round modifies — a control living in
a script the chain never invokes is the round-12 "manifested but never invoked"
defect verbatim:

1. `rm -rf dist && make build` — before any build-check, or CAT-V-014's leg is
   vacuous on a fresh worktree where `dist/` is absent. A skip is not a pass.
2. `build-archive.py` and its self-tests
3. `verify-note-figures-r7.py`
4. `r10`, `r11`, `r12` fact-negative harnesses
5. `r9-promote.sh`
6. `r9-gates.sh` — the outer chain
7. `make ci` with `SKIP_SAST` **unset**, so SAST actually runs. `SKIP_SAST=1` is
   admissible only for an intermediate `make build-check` and never for the terminal
   gate.

`PYTHONDONTWRITEBYTECODE=1` throughout. Heavy gates run singly and nice'd. A kill
under load is "no result" — never a failure and never a pass.

## Acceptance Criteria

- [x] **AC1 — The evidence tree survives the volume that swept its predecessor, and its path independence is proven rather than asserted.** The tree is relocated off the temporary volume to a durable per-user location with a space-free path. Equivalence is proven per member on **type, size, mode and SHA-256**, compared as sets **in both directions** so a file the destination gained is caught as well as one it lost, with any unexpected symlink refused. Equal path names are not equivalence: a truncated, substituted or type-changed member would pass a name-only comparison while the source tree is still the only copy. No script carries an absolute tree path; every one resolves its own root from its own location, and the single script that did carry one is corrected. The correction is proven load-bearing: under a simulated sweep of the old location the pre-correction form refuses and the post-correction form passes, both observed, and the observation is made **before** the old tree is removed because it is the only surviving copy of the pre-correction form. The operator term file is a **sibling** of the tree, never a descendant. The run temporary root stays **ephemeral** and `0700`, created per run **on the operating system's temporary volume** so the platform sweeps what a kill leaves behind, with the signing requirement copied in per run at `0600` and dying with the root. Startup cleanup is lease-guarded: an atomic parent-level lease is acquired, concurrent runs are refused rather than queued, and only verified-owned direct children are swept after proving no active lease holds them — an unguarded "sweep stale predecessors" would delete a peer run's root, and the removal helper confines a target but cannot distinguish stale from active. If cleanup cannot complete, the run aborts **before** any token is created rather than proceeding over unswept residue. Cleanup handles the one thing the removal helper refuses, and does so narrowly. Every browser profile carries a `SingletonLock` **symlink**, and the helper refuses a symlink-bearing tree by design — so routing teardown straight at it fails every arm that launched a browser, which is strictly worse for the at-rest property this cleanup exists to protect, because the unremoved profile is exactly where a measured control proves the live token is written. Symlinks are therefore **unlinked before** the confined removal, with a mechanism that unlinks the link and never follows it to its target, and only inside a child already proven to be a real directory owned by the runner at mode `0700` directly beneath the runner's own parent. The helper still performs the tree removal. If either step fails, the run reports cleanup incomplete and aborts rather than proceeding over residue — the failure mode is refusal, not force. Because the durable location is under a home directory, every artifact refers to the tree by a tree-relative path, and a control plants the absolute root into a member and observes the archive builder **refuse**. The refusal, not which detector produces it, is the claim under test: a planted home path widens the derived exemption set, so the exemption gate fires before the privacy scan and an assertion naming the sweep specifically could never be observed. What must hold is that no path lets a home path reach a promoted artifact, and two independent gates enforce that; the control asserts the conjunction it can actually see.
- [x] **AC2 — Every selector names the set its claim is about, in the direction that fails closed.** The figure verifier's live filesystem globs become explicit closed member lists, and it re-derives identical facts for its earlier inputs. The privacy sweep keeps greedy discovery but gains a positive-membership assertion: every round-scoped spec present on disk appears in the scanned set, against a declared minimum count, and the zero-files guard is computed over the derived portion alone rather than over a list two unconditional literals make non-empty. The flip is observed by deleting the round-13 spec from the declared source and seeing the sweep name it absent — not by deleting a file and hoping a smaller list fails. Each replacement asserts anchor uniqueness before substitution.
- [x] **AC3 — Mutation coverage is closed by class, not by instance.** The four enumerated round-12 mutations exist and run, **plus one per control row this round adds**. The token-encoding mutation becomes structurally reachable by widening the mutable region to admit the encoding table while still excluding the harness's own case literals. Uniqueness becomes an **in-code assertion inside `run()`**: occurrences are counted within the sliced region and the harness throws unless exactly one, which is what a one-time manual check cannot hold — and the pre-existing needle that already occurs twice in the region is given a unique longer form in the same task rather than left as a silent non-mutation. Each new needle is proved to match the intended side, server-side check versus client-side send. A **meta-check** enumerates every `--self-test-*` flag implemented in the archive builder and asserts each is invoked by the outer chain, closing the class rather than the two instances currently callerless; it is proved by adding a decoy flag and observing the failure. Row-inventory and case-list order stay consistent, because the inventory drift guard hard-fails otherwise.
- [x] **AC4 — The staged-member decoy search proves its detector on the corpus it makes a claim about.** Promotion plants a labelled per-run decoy in a staged member and publishes the plant to the searching process. The **positive control comes first**: promote once with the decoy still planted and assert it *is* recovered from the promoted state, because a restore-then-assert-absent sequence is guaranteed by the restore and tests nothing about whether promotion carries transient mutations. Then restore, re-promote, and assert absence; absence is recorded as unverifiable if the first promotion did not recover the plant. A sentinel file precedes the plant and only a digest-verified restore removes it. Ordinary promotion refuses while the sentinel exists; the positive control runs in a **narrowly scoped diagnostic promotion mode** that requires both the sentinel and the plant, permits only that diagnostic build, and leaves ordinary promotion refusing until verified restoration — without which the sentinel and the positive control are mutually exclusive and the sequence cannot execute — the builder has no staging area, reads members straight from the tree, and the promote cycle builds twice, so a kill between plant and restore would otherwise manifest the decoy with an internally consistent digest. Restoration is verified by re-reading from disk against a digest captured from a fresh pre-plant read.
- [x] **AC5 — Each loopback bound is stated at the width its own code supports, and neither statement revises a disposition.** There are two listeners and conflating them would import one's claim onto the other. **(a)** The round-12 synthetic issuer's HTTP listener is *already* stated as "any local process able to connect", in both the round-12 note and the round-12 spec, so nothing is rewritten for it; the digest inherits that wording and adds the widening the code supports — the unauthenticated scan route is a live **oracle**, answering for caller-chosen bytes, and the page route serves the run decoy. The bound is completed by stating what the exposure *is not*: the issuer's token is a synthetic per-run value with no meaning outside the run, so the exposure carries no confidentiality consequence and what it bounds is **measurement validity** — whether another local process could have influenced the observation — not secrecy. This round therefore abandons, explicitly, any reading in which the fixture models a real credential boundary; it models the architecture only, and that abandonment is recorded rather than left implicit. **(b)** The browser's unconfined bind endpoint is the subject of the register slug and of the RFC's same-uid corrections. Its recorded bound is narrower than the exposure, because that endpoint is also loopback TCP with no client authentication and the platform grants no uid restriction on loopback TCP — **but its narrow phrasing is part of an accepted disposition's scope, so it is not rewritten.** Widening an accepted actor set would retroactively treat a wider exposure as already accepted, which is a ruling this round may not make. The wider factual bound is recorded in the evidence layer as **new evidence requiring re-ruling**, and the historical disposition text is preserved verbatim. No bearer credential is added to either listener.
- [x] **AC6 — The measurement scan endpoint is bounded without removing scan coverage or breaking the truncation control.** The cap is derived from the largest **observed** surface file in a recorded run plus headroom, and is a declared constant strictly greater than the base64 expansion of the truncation control's own payload plus envelope — the surface scan cap bounds what is *scanned*, not what is *received*, and the driver deliberately posts one byte above it to prove truncation while posting whole trace, archive and profile files whose size is unbounded. Bytes are counted on summed chunk lengths before any decode, so the cap is a byte cap and not a code-unit count, and the connection is destroyed on exceedance. The body schema is declared exactly — a closed object with no extra properties, `surface` and `role` as length-bounded strings drawn from an enumerated label set, and `payload` as a strict canonical base64 string of declared maximum length validated **before** any decode. A malformed or schema-invalid body is refused with a declared status and must not terminate the listener. A refused request is recorded as a **distinct third state** — not truncated, not clean — with its own check row **outside** the declared-prior-finding list, because the only row that would otherwise fail is already an expected failure and a surface that silently stopped being scanned would have no signal anywhere. **Both** a maximum active-request count **and** an aggregate in-flight-byte budget are bounded, with bounded queuing and a distinct fail-closed refusal state — every surface is dispatched at once, and either bound alone still permits memory amplification.
- [x] **AC7 — One privacy-term reader, one detector authority, and an anchor that claims only what it proves.** The two fail-closed term readers are replaced by one separately reviewed shared reader, which is added to the archive's explicit member roster and covered by a new **Python** import-closure check proved by a planted omission — the existing closure check covers only ESM imports, so an archived privacy control could otherwise depend on an unmanifested helper; both consumers keep their fail-closed contract, re-proved per consumer for absent, empty, unreadable, and count-mismatched input, and the reader additionally refuses a sanctioned placeholder term, and refuses a term that already matches the corpus in its clean state — a term that hits legitimate historical text makes every future run fail and is therefore not a detector but a permanent outage. That replaces an arbitrary minimum length, which is a proxy for the property rather than the property: a short term is only a problem when it collides, and collision is directly checkable. The member and document scan loops **abort rather than skip** on an unreadable input, because a perfectly fail-closed reader inside a loop that swallows read errors still fails open. The sweep consumes the richer pattern set and identifier classes from the same single authority it already parses its placeholder literals from, so the digest is checked by the stronger detector rather than the weaker one, with a planted-hit negative test per class. The **gate-chain term-file anchor** is an HMAC whose key comes from a CSPRNG, with key and record stored `0600` inside the active run root. It is captured once per gate-chain invocation and both consumers assert against that single captured value, each computing the HMAC and parsing from **the same single-read byte buffer** — digesting and then reopening the file would leave a substitution window between the two operations. It refuses when a prior record is absent unless an explicit first-run flag is passed, and that flag is accepted only in the gate-chain capture step, not by an arbitrary caller. No term-derived digest is committed or promoted: with a small declared term count a whole-file digest is a confirmation oracle for a guessed list. The residual is stated as "same file within this chain" — cross-round term identity remains operator-trusted and is carried, not closed.
- [x] **AC8 — Worker-purge blast radius is inventoried over a synthetic tree, with bounds at the width the helper's code supports.** A removed/retained inventory over files and directories is recorded through the confined-removal helper. The artifact states that it characterises the helper's traversal over a **synthetic tree the test itself populated** and makes no claim about a real profile's contents, and it infers no credential location and no credential survival. Bounds are stated as the code supports them: hard links are unresolvable by the helper's stat-based validation, symlink-bearing trees are **refused rather than escaped**, and the time-of-check/time-of-use window is a concurrent-rename window. The two preconditions the existing harnesses rely on are criteria here: the helper never receives a tree containing a symlink, and bootstrap grants are siblings of the confined area, never descendants. The synthetic profile is built with no navigation to a non-loopback origin, and inventory entries are emitted from a **closed generic taxonomy that rejects an unknown label** rather than as raw relative paths — an unconstrained "structural label" can preserve an origin fingerprint under a renamed category. An origin-shaped-filename pattern joins the detector set. Where this round introduces a *new* per-destination distinction it uses opaque per-round aliases with an operator-held mapping, preserving the behavioural contrast between aliases without carrying a semantic quasi-identifier.
- [x] **AC9 — The digest covers two declared sets, and every consumer of the shared derivation is re-run.** Two sets are declared and both are checked: a recursive document set over the notes tree with the digest itself excluded **by path**, since the digest is written into that tree and would otherwise be required to carry an entry about itself; and an explicit committed roster of the rounds, because a document-keyed set structurally cannot cover the rounds that have no dated note of their own. Each has a positive control — delete one member, observe the mismatch. Every enumerated document has exactly one entry giving what was asked, what was measured, and what it changed. Withdrawn, reversed and narrowed results are recorded **qualitatively**, naming what was claimed and that it was withdrawn, with no restated numeral — a digest that restates a figure the current artifacts no longer support would turn this criterion into a gate failure against the figure verifier. The digest is **appended** to the shared derivation, never inserted, because the promotion path consumes that list positionally. The consumer list is derived by search rather than hand-written, and its command and output are recorded as the enumeration's evidence; it includes the promotion path, not only the fact-negative harnesses.
- [x] **AC10 — No apparatus headline figure is a deliverable, checked within a scoped anchor.** Neither the digest nor the round-13 RFC section contains a coverage percentage, claim-accounting total, mutation-corpus figure, or harness count. The RFC check is scoped to the round-13 section by anchor, because the RFC's existing amendment text already contains such figures and a whole-file check would fail on frozen history. The scoping is proved by planting a figure inside the anchor and observing the catch, and planting one outside it and observing no catch.
- [x] **AC11 — The approver can rule from one section, and the section's coverage is checkable.** The section names each of open questions 1 through 6 by number, states each one's status — ruled, outstanding, or not measurable — and links the registered document holding its measured basis; a check parses six unique question records and validates each one's status against the allowed vocabulary and its resolving evidence link, with a missing-status control and a missing-link control observed to fail. It states open question 4's recommended candidate as contradicted and names the per-group re-drafting the approver is asked to make; open question 5's cache directive as a construction requirement with the unverifiable-not-clean absence boundary; and open question 6's anchor as signing identity with update survival unmeasured — **stating the adoption cost of each candidate**, because the approver is selecting between two friction profiles rather than between friction and none: signing identity implies a recurring per-adopter burden to express and maintain a requirement expression, including re-deriving it when a vendor rotates a team identifier, while digest pinning implies a per-update burden and is what open question 6 exists because it is unachievable for an auto-updating provisioned browser. Neither cost is currently recorded anywhere in the RFC. Open question 3 is presented **as the question**: its recommended default would block acceptance, and the approver must either accept that bar or lower it explicitly — phrased as the choice and cited to the open-question text, not asserted as an operative gate, because the RFC's own stated acceptance condition is the answered A–D set. Every accepted risk carried forward is restated at the width the code supports.
- [x] **AC12 — Finality is a per-slug disposition over a pinned set, in one of four declared states.** The set is entries of `workspace.toml [backlog].open` whose **`slug`** matches `^rfc0088-`, of declared cardinality — not entries merely containing the string, which over-covers by one via a `source` field. The two `type = "shape"` slugs are **not members of this table at all**; they live in the shaping queue and are listed separately as shaping-queue follow-ups rather than filtered by a type field the register entries do not carry. Every member appears exactly once across closed, closed-retained, converted, and carried. The four lists live in the digest as a machine-readable block, and the check partitions a committed pre-round snapshot, because closing a slug deletes it and the set would otherwise be unre-derivable the moment the round succeeds. Every failure branch the control enumerates is planted and observed to fire before the check is admitted. The branch list lives in the control and nowhere else, and the control prints it on request — a prose count is a second home that goes stale the moment a branch is added, which is exactly how three review passes found a stale one here. Converted concerns are recorded in the RFC's round-13 amendment entry. No acceptance criterion of *this* spec carries a deferral token, deliberately: every AC here describes work that lands, and each carried slug's only home is its register entry, which gains the "Unblocks when:" comment the uncommented entries currently lack. **Two closures are `closed-retained`, which is a fourth declared state and not a hedge.** The round-12 spec carries live `(deferred: …)` markers naming two slugs whose work this round completes. The deferral lint iterates every spec and resolves each marker against `[backlog].open` **only**; `[backlog].closed` admits solely `kind = "defect"`; the marker lives in the body of a frozen Shipped spec, which the frozen-document rule forbids editing — only its `Status` field is mutable; and widening the invariant is a published-interface change requiring an RFC. All four escapes are therefore closed, and the repository has already settled this exact deadlock: a satisfied slug **retains its membership as a frozen deferred-reference lint anchor**, annotated as satisfied, on the model of the `starlight-migration-rfc` and `architect-review-diagram-knowledge-surfaces` entries. Those two slugs are consequently recorded as `closed-retained` — work complete, membership retained, annotation naming what satisfied them — and the partition control admits that state only for a slug that is **all three of** still present, named by a `(deferred: …)` marker in a frozen Shipped spec, and carrying a register annotation asserting both satisfaction and retention. Presence alone would admit every undispositioned slug. A marker alone is still not enough, because a marker explains why a *satisfied* entry cannot leave the register and says nothing about whether the work happened — one of the three pinned slugs here is pinned and unfinished. Satisfaction is a claim, so it must be made where a reader of the register will see it, in the entry's own summary, on the precedent's wording. The **final / not final verdict and what remains** is recorded in the digest and the amendment entry, with the PR description pointing at them rather than being their only home.
- [x] **AC13 — Nothing is decided and nothing is unlocked.** RFC-0088 remains `Experimental`. No ADR, convention amendment, or follow-on spec is created, and no disposition, blocker item, or open-question ruling changes. The RFC diff is confined to the anchored evidence layer, checked mechanically. The absence assertion is proved rather than assumed, but **without performing the act the Boundaries forbid**: the detector is exercised against a synthetic path-set fixture outside the repository, observed to catch a decoy entry there, rather than by creating an RFC-shaped artifact in the live tree.

## Assumptions

- Technical: the relocated tree is the evidence-tree locator for this round and every
  later one; the round-11 spec's locator assumption is superseded on the path only.
- Technical: the operator term file and the signing requirement file are supplied by
  the approver from outside this session. Their values never enter an artifact, a
  commit, or the transcript; only their paths do.
- Technical: the out-of-repository apparatus is outside the reach of the repository's
  blessed credential helper, so operator secrets are passed by path only. Recorded so
  the question is not re-litigated every round.
- Technical: worker blocking is context-shaped while persisted worker storage is
  profile-shaped; round 12 measured that distinction and round 13 inventories its
  consequence.
- Product: consumer context is read-only; this round writes nothing to that pack.
- Process: **the five carried slugs and why**, declared now rather than discovered at
  the end. *Signing-identity update survival* — one installation cannot observe an
  update; closed by a second dated observation across a real update. *Destination
  group split cost* — needs an attended interactive sign-in per group, which is not
  commissioned. *Same-uid attach exposure* — its own unblock condition requires an
  authorised second-uid mechanism or a non-administrative execution boundary, and
  neither exists this round; AC5(b) corrects the claim's width, which is documentation
  rather than measurement. *Privacy-term identity anchor* — AC7 closes it only within
  a gate chain, and cross-round term identity stays operator-trusted. *Native-addon
  confinement bypass* — measuring it needs a compiler toolchain in the evidence tree, which
  is a new dependency and outside a pre-acceptance spike; it is carried rather than
  converted because a frozen Shipped spec pins it with a `(deferred: …)` marker, so removing
  it from the register would dangle that marker.
- Process: **the one converted slug.** *Confined-removal time-of-check/time-of-use* is a
  design property rather than a measurable residual — it bounds the filesystem-policy
  contract — and no frozen spec pins it, so it can leave the register. It is recorded as a
  named implementation concern in the round-13 amendment entry, against the follow-on spec
  that will own it. Conversion is available only to an unpinned slug: the disposition
  removes the entry, and a pinned entry cannot be removed.
- Process: open question 3 is not a measurement question and is not attempted.
