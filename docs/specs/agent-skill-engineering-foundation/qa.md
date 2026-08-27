# Agent Skill Engineering Foundation — QA record

All results below were produced on the branch after it was rebased onto
`origin/main` at `155545c3`, in a cleanup-capable environment. Nothing here is
pending: every gate named ran to completion and its exit code was read
unfiltered.

## Repository gates

| Surface | Command | Result |
| --- | --- | --- |
| Foundation pack + OKF roster contracts | `pytest packs/agent-skill-engineering/tests tests/roster/test_okf_contracts.py` | 94 passed |
| Shared OKF compiler | `pytest packs/catalogue-curation/tests/skills/compile-okf` | 135 passed |
| OKF pack-profile contract fixtures | same suite, `-k "contract or profile or schema"` | 6 passed of 135 |
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
`evaluation_mode: headless-observed`, and its generator refuses to write at all
unless the run is clean, so this evidence cannot ratify its own premise.

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

## Compiler prerequisites

Both canonical entries are closed with regression evidence and removed from
`workspace.toml [backlog].open`. Hostile `title`, `status`, and `type` values
now escape to stable text that cannot create Markdown structure or
destinations, and display metadata that cannot be represented as one safe line
is refused. A forced repeated-render divergence reports `OKF012` with exit
class 2 and leaves the source tree unchanged.

## Delivery surface

`agentbundle render packs/agent-skill-engineering --output <guarded tmp>` into a
fresh `/private/tmp` root emitted the complete 30-file APM package and a
`claude-plugins/marketplace.json` of `{"plugins": []}` — the expected empty
projection, since the pack ships no `.claude-plugin/plugin.json`. The rendered
tree carries the declared `metadata.boundaries` for all three skills and
contains no authored OKF source or source path. Only that exact temporary root
was removed afterwards.

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
