# Agent Skill Engineering Foundation — QA record

All results below were produced on the branch after it was rebased onto
`origin/main` at `dda204fc8785d8c5cba4b0ff021da5f5e0ec7bdc`, in a
cleanup-capable environment. The table was re-run on that base. Nothing here
is pending: every gate named ran to completion and its exit code was read
unfiltered.

## Repository gates

| Surface | Command | Result |
| --- | --- | --- |
| Foundation pack + OKF roster contracts | `pytest packs/agent-skill-engineering/tests tests/roster/test_okf_contracts.py` | 120 passed |
| Repository test suite | `python3 -m pytest tests/ -q` | 767 passed, 46 subtests passed, exit 0 |
| Shared OKF compiler | `pytest packs/catalogue-curation/tests/skills/compile-okf` | 150 passed |
| OKF pack-profile contract fixtures | same suite, `-k "contract or profile or schema"` | 6 passed of 150, 144 deselected |
| Generated-output drift | `compile_okf.py --check` for all four OKF packs | `OKF000 check clean` ×4, exit 0 |
| Self-host projections | `catalogue self-host --root . --check` | ok, exit 0 |
| Pack verification | `catalogue verify --root . --pack agent-skill-engineering` | ok, exit 0 |
| Catalogue lint | `catalogue lint --root .` / `--deep` | clean; deep exit 0 with 68 findings, all warnings, 0 errors |
| Static quality | `make lint-ruff`, `make lint-mypy` | clean; mypy 125 source files |
| Documentation entry links | `pytest tools/test_documentation_entry_links.py` | 2 passed |
| Spec metadata | `lint-spec-status.py --root .` | `spec metadata clean`, exit 0 |
| Brief coverage | `lint-brief-coverage.py --root .` | exit 0; resolves this spec as `Implementing` |
| Whitespace | `git diff --check` | exit 0 |
| Build chain | `SKIP_SAST=1 make build-check` | exit 0 |
| SAST/SCA | `make sast` | exit 0 — bandit, `audit-npm` (2 lockfiles), semgrep, and the 8/8 semgrep rule self-test |

`build-check` prints an explicit banner that a `SKIP_SAST` run is not a full
pass, and this diff touches `tools/`, `packs/`, and `Makefile`, all of which
trigger the SAST leg in CI. `make sast` was therefore run separately rather
than left for CI to discover.

The local `make build-check` chain (`tools/repo/build_gate_chain.py`) does not
chain the whole `tests/` tree; it chains individual modules. `make test`
(`Makefile:422`) and the build-check workflow (`.github/workflows/build-check.yml:365`)
run `python3 -m pytest tests/ -q`, covering the AC17 seven-adapter projection
proof and the pack-metadata conformance checks.

## Activation — headless, observed

`agentbundle pack evals run --pack agent-skill-engineering --mode headless
--runs 1`, iteration 14: **18 of 18 queries passed** — 8 of 8 positives, 10 of
10 negatives, **zero harness errors**, and **zero generated-reference
exclusivity violations**. `tests/fixtures/activation-results.json` records that
run, bound to the exact skill and query-fixture digests that produced it, and
its construction test asserts `errored_runs == 0` and an empty
`exclusivity_violations` on every negative.

The artifact previously carried a self-reported in-harness claim of a perfect
classification that the observed gate contradicted. It now records
`evaluation_mode: headless-observed`, transcribed from the summary the eval
runner wrote at `.eval-workspace/agent-skill-engineering/iteration-<n>/summary.json`.

**How to reproduce it, and what the suite does not check.** Run the command
above; it writes that summary. Copy each skill's per-query outcome into
`activation-results.json`, setting `actual` to the skill that fired (or
`null`), and re-stamp `skill_digest` and `query_fixture_digest` from the files
the run projected.

The transcription is manual and the suite cannot verify it. The construction
test in `tests/pack/test_pack_boundary.py` compares the transcribed JSON only
against itself — `actual == expected`, `errored_runs == 0`, bounded
`exclusivity_violations` — and its digests bind the *inputs* (`SKILL.md`,
`eval_queries.json`), never the run. So it catches an honestly transcribed
failing run, and it does not catch a transcription that flatters a failing one.
What stops that is the digest binding forcing a fresh run whenever a workflow
file changes, plus this record naming the iteration the numbers came from.

An earlier revision of this record claimed the artifact had a generator that
"refuses to write at all unless the run is clean". No such script is committed;
the transcription is manual and the construction test is the only check. That
sentence asserted a control a reader could not find, which is the failure mode
this record exists to prevent, and it is corrected here rather than quietly
dropped.

Reaching that result required two source repairs, both driven by controlled
probes rather than by adjusting expectations. No fixture, threshold, or
expected result was changed.

**The generated router was outcompeting the workflows on its name.** Under
`agent-skill-engineering-reference`, prompts such as "design the trigger
boundary for an agent skill" selected the inert router instead of
`author-or-update-agent-skill`. Three rounds of description hardening — ending
with a description that explicitly said "Never select this skill for a user
request … must never be chosen to satisfy a user's question on any subject" —
did not move it (15, 15, 14 of 18). A probe then held the projected tree and
the description byte-identical and varied only the router's `name`: under the
original name the runtime chose the router; under a name carrying no domain
vocabulary it chose the workflow and entered `frame`. The router is now
`ase-okf-reference`, and `pack.toml` records the measurement so it is not
renamed back. A separate control proved the description edits changed only
`SKILL.md` and the manifest digest that mirrors it — every
`references/okf/**` byte is untouched, so the router-precision evidence below
remains valid for the current tree.

**"Activation boundary" was routing update requests to the review workflow.**
"Update this existing SKILL.md without changing its activation boundary"
selected `review-or-optimize-agent-skill` in three consecutive runs. A
two-arm probe isolated the cause exactly: the same query without the trailing
clause selected the authoring workflow, and with it selected review, because
the model read a constraint on a change as the subject of a review. The review
description now says that keeping a property intact is still an update; two
confirming probes and the full run route it correctly.

## Router precision

An independent read-only sub-context routed all 24 predeclared cases: 24 exact
set matches, precision and recall both 100%, at most three topics returned, and
no topic bodies for any of the six no-topic integration and near-miss cases.
The durable result is bound to the exact router, source, and generated-tree
digests. Those digests were re-stamped when the router's discovery description
and name changed; the routing-relevant bytes did not change, and the control
described above is what establishes that rather than an assumption.

## Behavior and review quality

The supported B-lite in-harness grader passed 4 of 4 cases, re-deriving
required output markers from prepared workspaces and combining them with
independent assertion judgments. All four results are durable and bound to the
digests of the eval fixtures they consumed — not to the workflow `SKILL.md`
files, so the description repairs above did not invalidate them. The two review
candidates report all ten seeded defect identifiers, and the hostile helper was
inspected but never executed.

The authoring half of that record is now bound to what the eval declares, not
only to truthiness. Review round 3 demonstrated the gap by mutation: rewriting
`frame-new-skill`'s recorded markers to `Mode: create` / `Write status:
AUTHORIZED` — the exact negation of AC2's read-only frame — and its four
assertions to one left all pack tests green, because the construction test
asserted only `all(result["assertions"])` and marker truthiness while the
digests bound the eval *inputs*. `test_independent_behavior_results_cover_both_authoring_cases`
now compares recorded markers to the eval's declared `expect.output_contains`,
mirroring the `actual_findings` comparison the review side already performed,
and additionally pins the recorded assertion count to the declared count.
Re-running that same mutation against the repaired suite fails it.

Round 4 then found the mirror had the same class of hole: the review loop
asserted only `all(result["assertions"])`, and `all([])` is `True`, so a record
claiming that none of the five declared checklist assertions were confirmed was
indistinguishable from one claiming all five. The count check is therefore new
on both sides, not mirrored from one. Both loops also require a result's
`source_files` to be an exact set
rather than merely a subset — `<=` is satisfied by the empty set, so a result
could previously record no provenance at all. Both rules are now the same
shape: the files the case declares, plus the `evals/evals.json` that declares
them. The two digest tests are each scoped to their own skill's results,
because `source_files` keys are skill-relative while this fixture is
pack-global, so an unscoped sweep reads one skill's `evals/evals.json` as a
second digest for the other's.

Round 5 then found that the review records were bound to no digest of the
declaration they were recorded against: rewording a prompt in the review
`evals.json` left all tests green, so a recorded result could be silently
re-pointed at a declaration it was never run against. The review eval payload
is now recorded and digest-bound, as the authoring one already was.

**What this record does not attest.** The review evals declare a `Mode: review`
marker in `expect.output_contains`. The grader enforces it at run time —
`output_ok` requires every declared substring to appear in the captured output
(`packages/agentbundle/agentbundle/commands/pack_evals.py:905-910`, feeding
`passed` at `:922`) — but the durable fixture records findings and assertions
for review cases and carries no marker, no `passed`, and no `output_ok`. An
earlier revision of this record filled that gap by *deriving* the marker from
the run having passed. That derivation was circular: the fixture records none
of the three conjuncts the argument appealed to, so the premise was the
conclusion. The derived values have been removed rather than disclosed. The
marker is therefore declared and enforced during a graded run, and is not
re-checkable from the committed artifact — a genuine limit of this layer,
stated here rather than closed with a value nobody measured.

That leaves the declaration and the durable binding disagreeing, which review
round 4 raised and left as an owner decision between two options: record the
marker, or drop it from `expect.output_contains` so the eval declares only what
the evidence attests. The decision taken is neither: the declaration stays,
because dropping it would weaken what a future graded run checks in order to
tidy a record, and the value stays unrecorded, because the only honest way to
record it is to measure it. The gap is therefore deliberate and named. Closing
it needs one graded review run, which `agentbundle pack evals run --check
behavior` can grade once a driver supplies the attested report it requires.

AC4's absence clause was checked for three of its six modes against one of the
two activation descriptions. It now runs pack-scoped in
`tests/pack/test_pack_boundary.py`, deriving all six mode names from
`tests/fixtures/unsupported-mode-cases.json` — the fixture that already defines
the closed vocabulary — and asserting each is absent from both descriptions.
The exact-count assert beside it is an anti-vacuity floor pinned to AC4's closed
six-mode enumeration: a seventh mode reddens it deliberately, so extending
coverage stays an AC4-synced decision instead of happening silently.

That check was defeated twice by the next surface form a reviewer tried.
`\b<mode>\b` missed the plural: "use for plugins, hooks, and subagents"
advertises three forbidden modes and passed, because `s` is a word character.
`\b<mode>s?\b` then missed the space-separated spelling of the hyphenated
modes — "use for knowledge providers and runtime packages" — and the split
spelling of a closed one, "sub-agents". Rather than grow the pattern a third
time against whichever form was tried last, the predicate changed category:
`_names_mode` splits the description at punctuation, tokenizes each segment to
alphanumeric runs, and matches only when a window of at most one more token
than the mode has parts joins to exactly the mode's letters, allowing one
trailing plural `s`. An unbounded first attempt at this over-matched ordinary
prose — "plug into" read as `plugin`, "unhook" as `hook`, and the comma list
"a runtime, profile, and package review" as `runtime-profile`. Bounding the
window and splitting at punctuation removed all three while keeping every
forbidden form.

Six controls, each the exact string injected into a description: `subagent`
into the review description fails it; `plugin` into the authoring description
fails it; `use for plugins, hooks, and subagents` fails it; `use for knowledge
providers and runtime packages` fails it; `handles sub-agents too` fails it;
and the negative control `Use when a user asks` — a reworded opening naming no
mode — passes. Both shipped descriptions name no mode under the new matcher,
so this closed unproven coverage rather than a live violation.

## Compiler prerequisites

Both canonical entries are closed with regression evidence and removed from
`workspace.toml [backlog].open`. Hostile `title`, `status`, and `type` values
now escape to stable text that cannot create Markdown structure or
destinations, and display metadata that cannot be represented as one safe line
is refused. A forced repeated-render divergence reports `OKF012` with exit
class 2 and leaves the source tree unchanged.

## Delivery surface

`agentbundle render packs/agent-skill-engineering --output <guarded tmp>` into a
fresh `/private/tmp` root emitted three projected trees: `apm/` (30 files),
`claude-plugins/` (30 files), and `agent-plugins/` (26 files), for 86 files in
total. `claude-plugins/marketplace.json` carries one `agent-skill-engineering`
plugin entry with eleven keys — `author`, `category`, `description`,
`displayName`, `homepage`, `keywords`, `license`, `name`, `repository`,
`source`, and `version`, the last being what pins which pack version an
advertised install resolves and one of the three the entry schema requires.
At line 7, `ase-okf-reference/SKILL.md` carries
`source-path: okf/agent-skill-engineering-foundation` in all three projected
trees, as AC8 requires and `tests/pack/test_foundation_corpus.py` asserts. The
rendered tree carries the declared `metadata.boundaries` for all three skills;
`tests/roster/test_agent_skill_engineering_projection.py` proves that for every
adapter in `install.allowed-adapters`, not only the one rendered here. AC21's
publication evidence is the pack's `.claude-plugin/plugin.json`, that
marketplace entry, and `tools/lint-plugin-roster` `PUBLISHED` membership;
`lint-plugin-roster`, `check-site-plugin-offers`, and
`lint-site-scope-parity` bind those records. Only that exact temporary root was
removed afterwards.

Both user-facing skills and the generated router pass the external
`quick_validate.py` from the `skill-creator` plugin, with descriptions of 734,
777, and 457 characters against its 1024 limit.

Two repository gates that fire on the existence of any pack were red and are
now green under the owner's decision of 2026-08-27, recorded in AC21: the pack
has a catalogue-parity site page, and its guide is deferred to a later planned
documentation slice through `GUIDE_OPTIONAL_PACKS` with backlog entry
`agent-skill-engineering-guide-and-docsurl`.

## Test coverage that CI actually runs

The pack's four test directories were named by no runner, so CI would have
executed none of its tests while every local invocation passed. All four are
now wired into the Makefile's pack-test target. Twelve pack tests also composed
paths by joining a pack root with a loop variable, which the pack-test boundary
lint cannot prove stays in-pack; they are rewritten to parametrize over literal
route lists, and the two sibling-skill routes are anchored from the pack root
rather than through `..`. A faithfulness test proves each mapped target really
is the route the skill writes, and was confirmed to fail when a target is
mismatched.

## Security and failure evidence

The local provider matrix covers absence, ambiguity, stale contract, malformed
ownership, authority widening, identity conflict, over-cap results, prompt
injection, credential-shaped diagnostics, malformed/generic/overbroad requests,
and an eligible independent provider whose selected reference is absent from
its ownership manifest. Accepted responses carry compiled guidance, exact
contract and provider provenance, profile dates where applicable, and bounded
warnings. Every refusal continues the baseline and records zero topic-content
reads. The generated router exposes deterministic discovery metadata for the
v1 capability while retaining explicit-only invocation and generated-manifest
ownership; its domain and purpose live in that metadata rather than on the
activation surface. Skill instructions keep authentication external, require
confinement before candidate reads and writes, and prevent provider output from
changing authority.

## Review verdict

```json review-verdict.v1
{
  "schema_version": "review-verdict.v1",
  "state": "READY_WITH_RESIDUAL_RISK",
  "mode": "full",
  "review_unit": "spec/agent-skill-engineering-foundation INI-009 M0",
  "warranted_reviewers": [
    {"role": "adversarial-reviewer", "mandatory": true, "outcome": "clean", "report_ref": ".context/reviews/8dfb6e8d-e1b9-4ac2-83ab-07a0d81654dc/5-post-gates-adversarial-reviewer-adjudication.md"},
    {"role": "quality-engineer", "mandatory": true, "outcome": "findings", "report_ref": ".context/reviews/8dfb6e8d-e1b9-4ac2-83ab-07a0d81654dc/5-post-gates-quality-engineer-adjudication.md"},
    {"role": "security-reviewer", "mandatory": true, "outcome": "clean", "report_ref": ".context/reviews/8dfb6e8d-e1b9-4ac2-83ab-07a0d81654dc/3-post-gates-security-reviewer-adjudication.md"},
    {"role": "experience-reviewer", "mandatory": false, "outcome": "clean", "report_ref": ".context/reviews/8dfb6e8d-e1b9-4ac2-83ab-07a0d81654dc/3-post-gates-experience-reviewer-adjudication.md"},
    {"role": "finding-adjudicator", "mandatory": true, "outcome": "clean", "report_ref": ".context/reviews/8dfb6e8d-e1b9-4ac2-83ab-07a0d81654dc/"}
  ],
  "named_skips": [],
  "findings": [
    {"id": "r4-adv-1", "source_role": "adversarial-reviewer", "severity": "blocker", "effective_severity": "blocker", "citation": "packs/agent-skill-engineering/tests/skills/review_or_optimize/test_contract.py", "text": "Review half of AC6's behavior record had no assertion-count binding and no Mode: review binding; all([]) is True so an emptied assertion list stayed green.", "status": "resolved"},
    {"id": "r4-qe-1", "source_role": "quality-engineer", "severity": "blocker", "effective_severity": "blocker", "citation": "packs/agent-skill-engineering/tests/skills/review_or_optimize/test_contract.py", "text": "Same defect reproduced independently by mutation: assertions:[] on detect-script-contract-failure left 77 tests green.", "status": "resolved"},
    {"id": "r4-qe-2", "source_role": "quality-engineer", "severity": "blocker", "effective_severity": "blocker", "citation": "docs/specs/agent-skill-engineering-foundation/qa.md", "text": "The QA record's delivery-surface paragraph described the pre-reversal state: no plugin manifest, empty marketplace projection, no source path.", "status": "resolved"},
    {"id": "r4-adv-2", "source_role": "adversarial-reviewer", "severity": "concern", "effective_severity": "concern", "citation": "packs/agent-skill-engineering/tests/pack/test_pack_boundary.py", "text": "The AC4 absence guard could not match the plural form of any mode name.", "status": "resolved"},
    {"id": "r4-adv-3", "source_role": "adversarial-reviewer", "severity": "concern", "effective_severity": "concern", "citation": "docs/specs/agent-skill-engineering-foundation/qa.md", "text": "The delivery-surface record enumerated ten marketplace-entry keys against eleven emitted, omitting the schema-required version.", "status": "resolved"},
    {"id": "r4-adv-8", "source_role": "adversarial-reviewer", "severity": "concern", "effective_severity": "concern", "citation": "docs/specs/agent-skill-engineering-foundation/plan.md", "text": "Rollout stated no rollback disposition for the catalogue-curation provider-capability delta this branch also ships.", "status": "resolved"},
    {"id": "r4-qe-4", "source_role": "quality-engineer", "severity": "concern", "effective_severity": "concern", "citation": "docs/specs/agent-skill-engineering-foundation/qa.md", "text": "The QA gate table omitted the suite carrying AC17's seven-adapter projection proof and the conformance suite.", "status": "resolved"},
    {"id": "r4-qe-5", "source_role": "quality-engineer", "severity": "concern", "effective_severity": "concern", "citation": "packs/agent-skill-engineering/tests/skills/author_or_update/test_contract.py", "text": "AC4's absence clause was verified for three of six modes on one of two workflow descriptions.", "status": "resolved"},
    {"id": "r4-adv-9", "source_role": "adversarial-reviewer", "severity": "nit", "effective_severity": "nit", "citation": "packs/agent-skill-engineering/tests/pack/test_pack_boundary.py", "text": "The mode-guard docstring and QA record claimed automatic coverage the exact-count assert prevents; the assert is correct and the prose was wrong.", "status": "resolved"},
    {"id": "r4-qe-6", "source_role": "quality-engineer", "severity": "nit", "effective_severity": "nit", "citation": "packs/agent-skill-engineering/tests/skills/author_or_update/test_contract.py", "text": "A recorded result could carry no source binding at all, because the empty set satisfies the subset relation.", "status": "resolved"},
    {"id": "r5-qe-1", "source_role": "quality-engineer", "severity": "blocker", "effective_severity": "blocker", "citation": "packs/agent-skill-engineering/tests/fixtures/behavior-results.json", "text": "The two review actual_markers values were derived from a premise the fixture does not carry; the derivation was circular and the assert reading them mirrored its own setup.", "status": "resolved"},
    {"id": "r5-qe-2", "source_role": "quality-engineer", "severity": "blocker", "effective_severity": "blocker", "citation": "packs/agent-skill-engineering/tests/skills/review_or_optimize/test_contract.py", "text": "The review records were bound to no digest of their own declaration; rewording a review eval prompt left all tests green.", "status": "resolved"},
    {"id": "r5-qe-3", "source_role": "quality-engineer", "severity": "concern", "effective_severity": "concern", "citation": "packs/agent-skill-engineering/tests/pack/test_pack_boundary.py", "text": "_names_mode over-matched ordinary prose: plug into read as plugin, unhook as hook, and a comma list as runtime-profile.", "status": "resolved"},
    {"id": "r5-qe-4", "source_role": "quality-engineer", "severity": "concern", "effective_severity": "concern", "citation": "packs/agent-skill-engineering/tests/skills/review_or_optimize/test_contract.py", "text": "The two source_files predicates had different shapes; the review one raised KeyError or inverted on a workspace-less case.", "status": "resolved"},
    {"id": "r5-qe-5", "source_role": "quality-engineer", "severity": "nit", "effective_severity": "nit", "citation": "packs/agent-skill-engineering/tests/skills/author_or_update/test_contract.py", "text": "The surviving authoring subset assert lost the comment stating why it is not redundant with the equality above it.", "status": "resolved"},
    {"id": "r5-adj-1", "source_role": "quality-engineer", "severity": "concern", "effective_severity": "concern", "citation": "docs/specs/agent-skill-engineering-foundation/qa.md", "text": "The QA record still credited a review-side Mode: review marker binding that the same commit removed, contradicting its own disclosure paragraph.", "status": "resolved"}
  ],
  "required_gates": [
    {"name": "pack + OKF roster contracts", "outcome": "passed", "evidence": "pytest packs/agent-skill-engineering/tests tests/roster/test_okf_contracts.py -> 120 passed"},
    {"name": "shared OKF compiler", "outcome": "passed", "evidence": "pytest packs/catalogue-curation/tests/skills/compile-okf -> 150 passed"},
    {"name": "repository roster + conformance", "outcome": "passed", "evidence": "pytest tests/ -> 767 passed, 46 subtests"},
    {"name": "static quality", "outcome": "passed", "evidence": "make lint-ruff clean; make lint-mypy 125 source files, no issues"},
    {"name": "spec metadata", "outcome": "passed", "evidence": "lint-spec-status.py --root . -> spec metadata clean"},
    {"name": "build chain", "outcome": "passed", "evidence": "SKIP_SAST=1 make build-check -> exit 0, 0 errors"},
    {"name": "SAST/SCA", "outcome": "passed", "evidence": "make sast -> exit 0, 8/8 semgrep rule self-test"},
    {"name": "activation eval, headless observed", "outcome": "passed", "evidence": "18 of 18 queries, 0 harness errors, 0 exclusivity violations, iteration 14"},
    {"name": "whitespace", "outcome": "passed", "evidence": "git diff --check -> exit 0"}
  ],
  "deferrals": [
    {"slug": "agent-skill-engineering-guide-and-docsurl", "reason": "No guides/ tree this slice; the pack is the only member of GUIDE_OPTIONAL_PACKS and its docsUrl points at the guides index until the planned docs slice lands.", "accepted_by": "owner", "residual_eligible": true},
    {"slug": "language-extension-seams-unpopulated", "reason": "The retrieval contract recognizes language extension points but ships no populated seam in M0.", "accepted_by": "owner", "residual_eligible": true},
    {"slug": "review-mode-marker-unbound", "reason": "Mode: review is declared in the review evals and enforced by the grader at run time, but the durable fixture records findings and assertions only. The declaration was kept rather than weakened, and the value left unrecorded rather than derived; closing it needs one graded review run.", "accepted_by": "owner", "residual_eligible": true}
  ],
  "blind_spots": [
    {"surface": "behavior eval outcomes", "reason": "agentbundle pack evals run --check behavior requires a driver-supplied attested report, so no fresh graded run was made in this slice.", "evidence_limit": "The four recorded behavior results are bound to their declarations by digest and by assertion count, but the run itself was not re-observed here.", "accepted_by": "owner", "residual_eligible": true},
    {"surface": "activation transcription", "reason": "The headless activation result is transcribed by hand from the runner's summary.json.", "evidence_limit": "The construction test compares the transcription only against itself; its digests bind the eval inputs, never the run. Recorded at qa.md under 'How to reproduce it, and what the suite does not check'.", "accepted_by": "owner", "residual_eligible": true},
    {"surface": "review rounds 1-3 findings", "reason": "Sustained findings from the first three post-gates rounds were resolved and superseded by rounds 4 and 5, which re-reviewed the repairs.", "evidence_limit": "Their full text lives in the paired raw and adjudication artifacts under .context/reviews/8dfb6e8d-e1b9-4ac2-83ab-07a0d81654dc/ rather than in this record.", "accepted_by": "owner", "residual_eligible": true}
  ],
  "human_gate_status": "pending",
  "non_authoritative_score": null
}
```
