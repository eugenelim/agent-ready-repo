# Plan: An intent's lifecycle state is a closed contract a lint can decide

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/AGENTS.md` (pack export boundary, test loader rule, version bump rule); `docs/AGENTS.md`; [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md); [ADR-0121](../../adr/0121-a-repository-intent-declares-its-altitude.md) D1

## Approach

One lint gains one refusal class. The state-coherence rules are pure predicates over a preamble the module already parses, so the work is additive inside an existing parse and needs no new module, script, or dependency.

The migration runs after the rules exist and before they ship, because the rule may not land leaving the corpus in a state it forbids. It is a per-artifact judgement for each intent the run refuses, not a sweep.

## Constraints

- `.apm/` is the runtime export boundary. Tests never live there, and every `.apm/` edit reprojects through `make build-self`.
- A non-cosmetic pack-content change bumps matching versions in `pack.toml` and `.claude-plugin/plugin.json`.
- The lint runs in `.github/workflows/docs.yml` against the real tree, and `tools/test_intent_corpus_gate.py` asserts a job invokes it. Both surfaces pin the invocation; neither may drift.
- Load the module under a name including its pack and skill. Several skills ship same-named scripts, and a bare import binds whichever directory reached the path first.

## Construction tests

Every rule in T1 and T2 is a fixture pair — one intent that conforms, one that does not — driven through the module's existing parse rather than a spawned interpreter. The suite is `packs/core/tests/skills/work-intake/test_intent_corpus_lint.py`.

The migration's oracle is the real-tree run, not a fixture: `--dir docs/product/intents --root .` exits 0.

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

Two preamble records, each an ISO 8601 calendar date `YYYY-MM-DD` optionally followed by free text carrying the decider and the evidence. The bare literal `no` is refused: unlike the progress fields, these record a fact rather than offer an opt-out.

### Behavior & rules

The spec's criteria own the rule set. This table is the implementation's dispatch shape, not a second statement of the contract:

| `Status` | requires `Accepted:` | `Fulfilled:` |
| --- | --- | --- |
| `Draft` | refused if present | refused if present |
| `Accepted` | not decided here | refused if present |
| `Fulfilled` | required | required |
| `Cancelled` | required | refused if present |
| `Withdrawn` | not required | refused if present |
| `Superseded by <slug>` | not decided here — see the spec's not-changed paragraph | not decided here |

### Failure, edge cases & resilience

- A record below the preamble reads as absent, so a body-positioned `Accepted:` does not satisfy AC-0001. The existing bounding stage gives this for free; the risk is adding a whole-file scan that bypasses it.
- Exit 2 for an unreadable corpus stays distinct from exit 1 for a non-conforming one.

## Tasks

### T1: A declared refusal registry

**Depends on:** none

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

**Depends on:** T1, T2

**Mode:** Goal-based check

**Approach:** A per-artifact judgement for each intent the run refuses, not a sweep. Two sets, both derived from a run: those owing a record, and within them those that never reached `Accepted`, which owe a status judgement at the parent's `Draft` → `Accepted` price or reclassification.

**Tests:**
- The real-tree run `--dir docs/product/intents --root .` exits 0 — AC-0014.

**Done when:** its `Tests:` pass, both derived counts are reported from the run, and `notes/migration-record.md` carries one entry per artifact in the second set naming the branch taken and the review or waiver it rests on.

### T4: Docstring, eval harness, version bump and changelog

**Depends on:** T1, T2, T3

**Mode:** Goal-based check

**Tests:**
- Every class this spec adds to the registry is named in `intent_shape.py`'s module docstring, compared registry-against-docstring so a later class added without a line fails — AC-0013.
- The core pack's eval harness covers the new refusal classes, per `packs/AGENTS.md`.
- `pack.toml` and `.claude-plugin/plugin.json` carry matching bumped versions, `make build-self` reprojects cleanly, and the changelog entry names what newly fails.

**Done when:** its `Tests:` pass.

## Rollout

- **Delivery:** big bang. The refusal classes are additive and removing them restores today's lint behaviour; the corpus edits T3 makes are not reversed by that. Nothing is flagged.
- **Infrastructure:** none.
- **External-system integration:** none.

## Changelog

- 2026-09-23 — drafted from `brief:intent-lifecycle-and-closure` slice 1, cut confirmed at three slices.
- 2026-09-23 — approved by eugenelim alongside the spec, on the basis its `Approved:` line records.
