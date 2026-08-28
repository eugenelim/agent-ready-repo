# Agent Skill Engineering Foundation — QA record

All results below were produced on the branch after it was rebased onto
`origin/main` at `dda204fc8785d8c5cba4b0ff021da5f5e0ec7bdc`, in a
cleanup-capable environment. The table was re-run on that base. Nothing here
is pending: every gate named ran to completion and its exit code was read
unfiltered.

## Repository gates

| Surface | Command | Result |
| --- | --- | --- |
| Foundation pack + OKF roster contracts | `pytest packs/agent-skill-engineering/tests tests/roster/test_okf_contracts.py` | 119 passed |
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
now compares recorded markers to the eval's declared `expect.output_contains`
and the recorded assertion count to the declared count, mirroring the check the
review side already performed. Re-running that same mutation against the
repaired suite fails it. No recorded value changed: the record already agreed
with the declaration, so the binding was addable without restating any result.

AC4's absence clause was checked for three of its six modes against one of the
two activation descriptions. It now runs pack-scoped in
`tests/pack/test_pack_boundary.py`, deriving all six mode names from
`tests/fixtures/unsupported-mode-cases.json` — the fixture that already defines
the closed vocabulary, so a seventh mode is covered the day it is declared — and
asserting each is absent from both descriptions on a word boundary. Three
controls: injecting `subagent` into the review description fails it, injecting
`plugin` into the authoring description fails it, and injecting `evaluation
hooks` does not, which is what the word boundary is for. All six were already
absent, so this closed unproven coverage rather than a live violation.

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
plugin entry with `author`, `category`, `description`, `displayName`,
`homepage`, `keywords`, `license`, `name`, `repository`, and `source`.
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
