# Plan: An intent's lifecycle state is a closed contract a lint can decide

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/AGENTS.md` (pack export boundary, test loader rule, version bump rule); `docs/AGENTS.md`; [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md); [ADR-0121](../../adr/0121-a-repository-intent-declares-its-altitude.md) D1

## Approach

One lint gains one refusal class. The state-coherence rules are pure predicates over a preamble the module already parses, so the work is additive inside an existing parse and needs no new module, script, or dependency.

The migration runs first, and the rules land on a corpus that already conforms. `intent-preamble-lifecycle-records` shipped both records' value shape on 2026-09-23, so `_check_dated_evidence` validates each record as it is written — which is the as-it-lands check the original ordering put T1 and T2 ahead of the migration to supply. Running the migration first satisfies the parent's "the rule may not ship before it runs" more strictly than the original order did, because the rule never exists against a corpus it would refuse. The migration is a per-artifact judgement for each intent the rules will refuse, not a sweep.

## Constraints

- `.apm/` is the runtime export boundary. Tests never live there, and every `.apm/` edit reprojects through `make build-self`.
- A non-cosmetic pack-content change bumps matching versions in `pack.toml` and `.claude-plugin/plugin.json`.
- The lint runs in `.github/workflows/docs.yml` against the real tree, and `tools/test_intent_corpus_gate.py` asserts a job invokes it. Both surfaces pin the invocation; neither may drift.
- Load the module under a name including its pack and skill. Several skills ship same-named scripts, and a bare import binds whichever directory reached the path first.

## Construction tests

Every rule in T1 and T2 is a fixture pair — one intent that conforms, one that does not — driven through the module's existing parse rather than a spawned interpreter. The suite is `packs/core/tests/skills/work-intake/test_intent_corpus_lint.py`.

The migration's oracle is the real-tree run, not a fixture: `--dir docs/product/intents --root .` exits 0. It is verified at T4, because the refusals it exercises are T1's and T2's and the run cannot discriminate before they exist. T3 runs first and therefore carries a **pre-rule check** as well — an inline derivation over the same real corpus, listed in its `Tests:`. That is not a fixture and does not stand in for the oracle: it reads the live tree, and AC-0014's lint run still has to pass at T4 on the corpus T3 leaves behind.

## Durable-output map

| Durable output | Task | Evidence at closeout |
| --- | --- | --- |
| Decision rationale — `notes/migration-record.md` | T3 | One entry per artifact in the second set |
| Current architecture — `intent_shape.py` docstring | T4 | The docstring names state coherence as a refusal class |
| Release history — the changelog entry | T4 | One entry naming what newly fails |

## Design (LLD)

### Design decisions

- **The rule is decidable from one snapshot, which is why it is expressible at all.** A transition is a pair of states and the lint sees one, so the contract is a coherence rule between a state and the records beside it. `Fulfilled` is not "reached `Accepted` at some point"; it is "carries the `Accepted:` record". Ratification has to persist on the artifact for the snapshot to decide it, and that is the whole mechanism.
- **The rules are corpus-lint-only, mirroring `validate_supersession()`.** `intent_shape.py` is the single home both enforcement points read, so anything inside `validate_live_intent()` reaches the shaping reviewer as well. `validate_supersession()` is defined in that module and called from neither — the seam already exists and the new rules take it. Wiring them into the shared surface would make the shipped reviewer enumeration false and owe an amendment to a `Shipped` spec.
- **Value shape is not decided here.** Neither `_is_iso_date` (whole-string anchored) nor `_check_date_or_no` (accepts the bare `no`) fits these records, but choosing what does is an intent preamble field's shape and therefore `FEAT-0001`'s. This slice checks presence by state and consumes whatever shape that brief lands.
- **The parser already exposes the records, which is what makes this additive.** `read_preamble()` returns every preamble pair rather than a fixed list. Probed 2026-09-23: adding an `Accepted:` record to a real intent exits 0, and so does an invented `Sprocket:` field — only `RETIRED_FIELDS` are refused. Both records can therefore land on artifacts before the rules ship, which is what lets T3 migrate and be checked as it goes.
- **The refusal classes need a declared registry before a check can read them.** Reasons are constructed inline, so nothing enumerates them today. A module-level tuple of class names, with every new refusal built from a member, is what turns the docstring obligation from a sentence-exists check into a set comparison. Pre-existing classes stay out of scope: retrofitting them is a larger change than this slice carries.
- **`Withdrawn` is deliberately exempt.** Abandoning an unratified bet needs no ratification, so requiring `Accepted:` there would refuse a legitimate state.

### Data & schema

Two preamble records, whose value shape `intent-preamble-lifecycle-records` fixed and this spec consumes: an ISO 8601 calendar date `YYYY-MM-DD`, a space, then non-empty text carrying the decider and the evidence. The text is **required**, not optional — a bare date is refused, because the record exists to carry the evidence. The bare literal `no` is refused too: unlike the progress fields, these record a fact rather than offer an opt-out.

### Behavior & rules

The spec's criteria own the rule set. This table is the implementation's dispatch shape, not a second statement of the contract:

| `Status` | requires `Accepted:` | `Fulfilled:` |
| --- | --- | --- |
| `Draft` | refused if present | refused if present |
| `Accepted` | not decided here | refused if present |
| `Fulfilled` | required | required |
| `Cancelled` | required | refused if present |
| `Withdrawn` | not required | refused if present |
| `Superseded` | not decided here — see the spec's not-changed paragraph | not decided here |

### Failure, edge cases & resilience

- A record below the preamble reads as absent, so a body-positioned `Accepted:` does not satisfy AC-0001. The existing bounding stage gives this for free; the risk is adding a whole-file scan that bypasses it.
- Exit 2 for an unreadable corpus stays distinct from exit 1 for a non-conforming one.

## Tasks

### T1: A declared refusal registry

**Depends on:** T3

**Mode:** TDD

**Approach:** Ordered first because the rules are built from it. A module-level tuple of refusal-class names, and a third `Violation` field carrying the class with a default so the seven existing construction sites and the shipped tests keep working unchanged.

**Tests:**
- Every refusal this spec adds carries a class drawn from the registry tuple, asserted against the new field rather than by substring-matching a reason — AC-0012.

**Done when:** its `Tests:` pass.

### T2: State-coherence rules on a corpus-lint-only surface

**Depends on:** T1

**Mode:** TDD

**Approach:** The seam is the decision. The rules go in a function the corpus lint calls and `validate_live_intent()` does not, mirroring `validate_supersession()`.

**Tests:**
- Fixtures at `Fulfilled` without `Accepted:`, `Cancelled` without `Accepted:`, and `Fulfilled` without `Fulfilled:` are refused; one at `Withdrawn` without `Accepted:` is accepted — AC-0001, AC-0002, AC-0003, AC-0004.
- Fixtures at `Fulfilled` carrying both records, and at `Cancelled` carrying `Accepted:`, are accepted. Their own cases, not variants of the refusal fixtures: an implementation that refuses every `Fulfilled` intent passes all four above — AC-0005, AC-0006.
- Fixtures at `Draft` carrying each record, at `Accepted` carrying `Fulfilled:`, and at `Cancelled` and `Withdrawn` each carrying `Fulfilled:`, are refused — AC-0007, AC-0008, AC-0009.
- Each refusal asserts `violation.path` equals the corpus-relative name the lint already reports, matching the convention `test_ac0013_names_the_intent_and_the_field_at_fault` pins — AC-0011.
- Neither record name appears in the shaping reviewer's intent-mode rubric, asserted as a forbidden substring over that file. The existing contract test cannot serve: it checks conditions by positive substring and tokens with `in`, so it observes an addition not at all — AC-0010.

**Done when:** its `Tests:` pass.

### T3: Migrate the corpus

**Depends on:** none

**Mode:** Goal-based check

**Approach:** A per-artifact judgement for each intent the rules will refuse, not a sweep. Two sets, both derived from a run: those owing a record, and within them those that never reached `Accepted`, which owe a status judgement. **Owner decision, 2026-09-24 — the walk-backs rest on an owner waiver rather than a shaping review.** The parent's `Draft` → `Accepted` price is an independent intent-mode review plus human confirmation; the owner waived the review half for this one-off migration and confirmed each artifact directly. The waiver is recorded per artifact in `notes/migration-record.md`, which `## Durable Outputs` already admits by requiring "the review **or waiver** it rests on". No `Accepted:` value may describe a review that did not run.

**Tests:**
- A derivation over `docs/product/intents/` returns the empty set of violations, taking one predicate per state directly from the spec's criteria rather than restating them: `Fulfilled` requires both records (AC-0001, AC-0004); `Cancelled` requires `Accepted:` and forbids `Fulfilled:` (AC-0002, AC-0009); `Withdrawn` requires no `Accepted:` and forbids `Fulfilled:` (AC-0003, AC-0009); `Draft` forbids both (AC-0007); `Accepted` forbids `Fulfilled:` (AC-0008). `Accepted`'s own `Accepted:` record is not decided here, per the spec's *Not changed here* paragraph. This is T3's **pre-rule check**, and it is the only check that can fail while T3 runs before T1 and T2. It is an inline derivation over the corpus, not a new script — `## Agent Rules` → *Never do* forbids adding one — and the migration record carries the command and its output. **It reads fields through `intent_shape.read_preamble()`, the corpus lint's own parser**, rather than scanning the file. That is what makes it agree with the lint on placement by construction instead of by assertion: a whole-file scan would accept a body-positioned record the lint treats as absent, which is how 22 misplaced fields landed earlier in this family, and a hand-rolled boundary would only be claimed equivalent. Proven differentially — the same record bytes read as present in the preamble and as absent one line below the first `##` heading. It reports both sets the spec's `## What Changes` names: the artifacts the rules would refuse, and within them the artifacts that never reached `Accepted` in history. The historical half states its own evidence rather than assuming it — a revision carrying no `Status:` field is counted and reported, because "never ratified" and "the parser could not read it" are the same verdict on different grounds. It refuses rather than guessing on every path where it has not actually read the evidence: a git failure, an empty revision list, a present-but-empty field value, an absent `Status:`, and any status outside the criteria's set other than the deliberately deferred `Superseded`. It scans every revision rather than stopping at the first `Accepted`, so the coverage it reports is of the whole history. Measured over all 14 offenders: one, `rendered-page-visual-inspection`, has 3 of 5 revisions predating the `Status:` field; the other thirteen parse at every revision, and none of the strict refusals fires on today's corpus.
- **AC-0014 is verified at T4, not here.** The real-tree lint run cannot serve as T3's oracle under this task order: the refusals AC-0014 exercises are T1's and T2's, so before they exist the run exits 0 on an unmigrated corpus and the criterion holds without the migration having happened. Measured on `6e89061c3` before any artifact was edited: `intent_corpus_lint.py --dir docs/product/intents --root .` reported `clean — 150 entries, 150 live, 0 tombstone, 0 unreadable` and exited 0. T4 re-runs it once the rules exist, which is the first point at which it discriminates.

**Done when:** its `Tests:` pass, both derived counts are reported from the derivation, and `notes/migration-record.md` carries one entry per artifact in the second set naming the branch taken and the review or waiver it rests on.

### T4: Docstring, eval harness, version bump and changelog

**Depends on:** T1, T2, T3

**Mode:** Goal-based check

**Tests:**
- Every class this spec adds to the registry is named in `intent_shape.py`'s module docstring, compared registry-against-docstring so a later class added without a line fails — AC-0013.
- The core pack's eval harness covers the new refusal classes, per `packs/AGENTS.md`.
- `pack.toml` and `.claude-plugin/plugin.json` carry matching bumped versions, `make build-self` reprojects cleanly, and the changelog entry names what newly fails.
- The real-tree run `--dir docs/product/intents --root .` exits 0 — AC-0014. Verified here rather than at T3, because the refusals it exercises do not exist until T1 and T2 land; running it earlier passes on an unmigrated corpus.

**Done when:** its `Tests:` pass.

## Rollout

- **Delivery:** big bang. The refusal classes are additive and removing them restores today's lint behaviour; the corpus edits T3 makes are not reversed by that. Nothing is flagged.
- **Infrastructure:** none.
- **External-system integration:** none.

## Changelog

- 2026-09-23 — drafted from `brief:intent-lifecycle-and-closure` slice 1, cut confirmed at three slices.
- 2026-09-23 — approved by eugenelim alongside the spec, on the basis its `Approved:` line records.
- 2026-09-24 — **amended by eugenelim, on explicit instruction, while `Approved`. Task order: T3 runs first.** `T3` takes `Depends on: none` and `T1` takes `Depends on: T3`; `T2` and `T4` are unchanged, and no task's physical position in `## Tasks` moved. § Approach was rewritten to match. The original order existed to make each migration edit checked as it was made; `intent-preamble-lifecycle-records` shipped both records' value shape on 2026-09-23 and its `_check_dated_evidence` now supplies that check, so the reason for sequencing T1 and T2 ahead of the migration no longer holds. The new order satisfies the parent's "the rule may not ship before it runs" more strictly, because the rules never exist against a corpus they would refuse. **`T3`'s Approach also records an owner waiver** taken the same day: the walk-backs set their terminal state directly and are confirmed by the owner, without the independent intent-mode shaping review the parent's `Draft` → `Accepted` gate names. `## Durable Outputs` already admits a waiver as evidence. **Verification moved, and the first draft of this entry wrongly claimed it had not.** An independent adversarial review of the amendment raised it as a Blocker: T3's only stated test was AC-0014's real-tree lint run, whose refusals are T1's and T2's, so running T3 first left the task with an oracle that passes on an unmigrated corpus. Confirmed by measurement on `6e89061c3` before any edit — the run reported `clean — 150 entries` and exited 0. T3 now carries an inline corpus derivation that can fail while it runs first, and AC-0014 moved to T4, where the rules exist and it discriminates. A second review round then caught two defects in that repair, both now fixed: the derivation had required both records on `Cancelled`, which AC-0002 and AC-0009 together forbid, so its predicates are now taken one per state from the criteria themselves; and § Construction tests still called the real-tree run the migration's only oracle, so it now distinguishes T3's pre-rule check from AC-0014's delivery-time run. A third round caught one more: the derivation scanned the whole file, so a body-positioned record would have satisfied it while the corpus lint read the same line as absent — the defect § Failure, edge cases & resilience already warns about. A fourth round rejected the first fix for that — a hand-rolled boundary is only *claimed* equivalent to the lint's — and found that the derivation reported one violation count rather than the two sets `## What Changes` names. Both are now closed by the same change: the derivation reads fields through `intent_shape.read_preamble()`, so it agrees with the lint by construction, and it reports both sets. A fifth round found the historical half silently treating an unreadable revision as an unratified one; it now counts and reports revisions carrying no `Status:` field and raises on a git failure. Measured on the unmigrated corpus: 14 artifacts refused, 10 of them never `Accepted`, exit 1 — against the lint's exit 0 on the same tree. A sixth round found three residual soundness gaps in that repair, all closed together: an empty revision list returned a verdict without reading anything, a present-but-empty field value collapsed to absent, and the all-revisions coverage claim outran a function that stopped at the first `Accepted`. **The class all six rounds share:** each time, the plan's prose claimed a property the instrument did not yet have. The repair each round was to make the instrument carry the claim, not to soften the sentence — which is why the counts never moved while the evidence behind them got stronger. No acceptance criterion or task scope changed, and `Status` stays `Approved`.
- 2026-09-24 — **amended by eugenelim, on explicit instruction, while `Approved`.** Two lines in `## Design (LLD)` were stale against the value shape this plan defers to `intent-preamble-lifecycle-records`, which shipped that shape on 2026-09-23. `## Data & schema` called the evidence text optional when it is required and a bare date is refused; the behaviour table's last row named the retired `Superseded by <slug>` status form, which no longer exists — the status is the bare token `Superseded` beside a separate `Superseded by:` field. Wording only: no criterion, task, scope or verification changes, and `Status` stays `Approved`. **`spec.md` § What Changes was amended the same way and on the same instruction**, for the same reason: its *Not changed here* paragraph named the retired `Superseded by <slug>` form and described both handed-off shapes as still pending, when both had landed. Its deferral was always correct — only the description of what it defers to was stale. No criterion changed there either, and that spec's `Status` stays `Approved`.
