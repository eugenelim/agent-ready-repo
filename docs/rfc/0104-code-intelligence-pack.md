# RFC-0104: The `code-intelligence` pack

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim <!-- repo owner. Author and approver are the same
  person, the shape RFC-0065 flagged for the same reason; here it also covers
  the D4 process deviation the author caused. Recorded rather than hidden. -->
- **Date opened:** 2026-09-30
- **Date closed:** 2026-09-30
- **Decision weight:** standard <!-- A new opt-in pack plus a new runtime
  dependency. No charter boundary is crossed: D5 finds the pack needs no
  exemption, and D3 finds the dependency policy already permits its
  installer. -->
- **Related:** [`docs/CHARTER.md`](../CHARTER.md) (the four principles), RFC-0065 (`iac-terraform`, the accelerator precedent this pack turns out not to need), `converters` (the tool-dependent non-accelerator precedent it follows instead), `propose-catalogue-pack` (the workflow this pack bypassed), `core` (required dependency), [`guides/_shared/how-to/author-a-skill.md`](../../guides/_shared/how-to/author-a-skill.md) (the three-tier dependency policy)

> **This record is retrospective.** The pack shipped in PR #1467 (squash commit
> `b1237654f`, 2026-09-30) before this RFC existed. `propose-catalogue-pack`
> routes a new pack area through the RFC workflow *before* scaffolding, and that
> did not happen. D4 disposes of the deviation. Nothing below is written as if
> the sequence were normal.

## Reviewer brief

- **Decision:** Retroactively admit `code-intelligence`, an opt-in, repo-scope
  pack that teaches a coding agent to query a
  [Wicked Estate](https://github.com/mikeparcewski/wicked-estate) code graph —
  an indexer that turns a repository into queryable symbols and relationships —
  and to report what that index could not resolve.
- **Recommended outcome:** accept.
- **Change if accepted:**
  - The pack stays, and **its shipped references carry the per-surface maturity
    label and provenance rule** D2 requires — applied in this PR, and a
    condition of acceptance rather than a description of what already existed.
  - Nothing else changes: the Charter and the dependency policy both already
    accommodate this pack (D5, D3).
- **Affected surface, this PR:** this RFC and its index row, the pack's two
  capability references, its eval harness, a patch version bump, and the
  changelog. The registration table in Evidence enumerates the pack's total
  footprint across both PRs, not this one's. Nothing in `core` changes and the
  Charter is untouched.
- **Stakes:** reversible throughout. The pack is opt-in, absent from every
  profile, and read-only; removing it is deleting a directory and reverting its
  registrations. Nothing here binds a future pack.
- **Review focus:** D5 — whether the pack really clears principle 1 unaided,
  since if it does not, the accelerator path and its Charter problem return.
  Then D1: whether a pack wholly contingent on one third-party binary belongs
  here at all.
- **Not in scope:** changing Wicked Estate; MCP dependency declaration in
  `pack.toml` (no schema field exists); the guide home and journey, which are
  follow-on artifacts, not decisions.

## The ask

**Recommendation.** Accept the pack, label its two provider surfaces
separately rather than as one, and record the process deviation without
normalising it. No amendment to the Charter or to the dependency policy is
needed.

**Why now.** `propose-catalogue-pack` routes every new pack area through an
RFC before scaffolding. This pack merged without one. Leaving it unratified is
not neutral: it makes the admission path optional in practice, and the next
pack author will reasonably read the precedent as "ship first".

**Accepted 2026-09-30.** All five recommendations below are ratified as
written; the `Decide by` and `Reviewer action` columns record what was asked of
the approver, not outstanding work.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D5 | Does this pack need the accelerator carve-out, whose scope clause it does not fit? | **No — it is stack-neutral, so principle 1 is not in tension and no exemption is required** | The exemption exists for packs that are *stack*-specific: Terraform, a CI platform, a named SaaS. This pack is **tool**-specific and stack-neutral — it serves a Python, Rust, TypeScript or COBOL adopter alike. `converters` corroborates the current state — a tool-dependent pack sitting outside the carve-out — but does not decide it, and § Charter admission says why | 2026-10-07 | **Decide first.** Accept, or find the pack stack-specific — which returns it to the accelerator path and its scope problem |
| D1 | Admit `code-intelligence`? | **Accept as shipped** | Clears all four principles (§ Charter admission). 91 pack tests pass locally, 20 of them executing the real binary; the merged PR's 38 green checks are the repository gates, which do not run these suites — see Experiment | 2026-10-07 | Accept, or name the principle it fails |
| D2 | One maturity label, or per-surface? | **Per-surface: CLI `validated`, MCP `contract-complete`, with the split marked in the shipped references** | The CLI is exercised against real indexes in two ways: the 20 automated tests build a purpose-built three-file micro-repository so their assertions are deterministic, and a manual run indexed this repository (65,981 nodes) to walk the documented patterns end to end. The MCP surface has neither — it is mapped from upstream conformance schemas and has never been executed here. A label only an RFC carries is invisible to the agent reading the pack, so `capability-map.md` now states maturity per surface and `gaps.md` opens with a three-provenance rule — executed, schema-derived, source-read — that classifies every claim in it | 2026-10-07 | Confirm the split **and that marking it in the pack is a condition of acceptance** |
| D3 | Is `cargo` acceptable as a Tier-2 install manager? | **Yes, under the policy as written — no amendment** | The Tier-2 criterion is "a package manager the user **demonstrably already has**", with `uv`/`npm`/`pipx`/`brew` following an em-dash as examples of that criterion rather than bounding it. `cargo` is detected before use and the install refuses outright when it is absent, so the criterion is met. Upstream publishes only to crates.io with zero release assets, so no other manager could reach it anyway | 2026-10-07 | Confirm the reading, or rule the list closed — in which case this pack narrows to Tier 1 detect-and-stop |
| D4 | How is shipping before the RFC disposed of? | **Record as a one-off deviation; do not normalise** | The Charter's admission path stays mandatory. This RFC is the correction, not the precedent | 2026-10-07 | Accept the disposition |

## Problem & goals

Coding agents answer structural questions about code by guessing from a text
search. "What calls this?" and "what breaks if I change it?" are answered from
grep output that cannot resolve which `handle()` was meant and cannot report
what it missed.

Wicked Estate already solves the indexing half: it builds a graph of symbols
and relationships, and — unusually — reports what it could not resolve. What it
does not supply is the discipline for using that well: which question maps to
which command, when to stop traversing, and how to carry a completeness caveat
through to the user instead of rounding it away.

**Goals.** Give an agent that discipline. Keep the integration workflow-neutral
so a migration, debugging, or security pack can consume it without any of them
knowing about each other. Be explicit about what the provider cannot do.

**Non-goals.** Changing Wicked Estate. Becoming a migration or modernization
workflow. Wrapping the CLI in scripts.

## Proposal

**One skill, two subagents, no wrapper scripts.**

| Primitive | Kind | What it does |
| --- | --- | --- |
| `code-intelligence` | skill | Five reusable investigation patterns (understand an entity, analyze change impact, investigate behavior, analyze architecture, assemble task context), a capability map from tool-neutral intent to the exact command, evidence and provenance handling, and a fourteen-point assessment of what the provider does and does not expose |
| `code-investigator` | subagent | Forked-context, read-only evidence gathering. Reports findings labelled observed / verified / unestablished |
| `impact-analyst` | subagent | Forked-context, read-only change-impact analysis. Leads with its own completeness limits |

One script ships, `estate_preflight.py`, and only because the three-tier
dependency policy *requires* a `--check` verb. It is a preflight, not a query
wrapper: every actual question goes to the CLI directly.

**The architectural boundary**, which is the pack's main design claim:

| Layer | Answers |
| --- | --- |
| Wicked Estate | *What is true about this software estate?* |
| This pack | *How should an agent use that intelligence effectively?* |
| Consuming workflow packs | *What are we trying to accomplish with it?* |

The test, when placement is unclear: **does this describe the software estate,
or a job being performed on the software?** Entities, relationships, blast
radius, lineage, rules, hotspots, provenance and confidence describe the
estate. Migration phase, cutover readiness, bug triage status and release
approval describe a job, and belong to the pack that owns that job. A pack test
enforces the boundary against the vocabulary, with negative controls proving
the check can fail.

**CLI-first, MCP optional.** Wicked Estate ships both. The MCP server
advertises 29 tool schemas that stay resident in the agent's context for a
whole session; the CLI costs nothing until called and accepts 34 subcommand
names, several with no MCP equivalent. Four capabilities are MCP-only —
`Lineage`, `RulesInventory`, `rules.recall`, and the memory and knowledge
domains — and are marked per row rather than implied.

**Dependency.** `wicked-estate >= 0.16` from crates.io, declared in
`[[pack.runtime-dependencies]]` with `ecosystem = "cargo"`. Detected before any
work; installed only on explicit consent, **pinned to an exact version on
install** — the declared dependency range is a floor, `>=0.16`, so an adopter
who already has a newer binary is not held to the pinned one — never with
sudo, and only when `cargo` is already present. `wicked-estate-mcp` is
declared optional.

## Charter admission

Accelerator packs are exempt from principle 1 (Universal) and must clear every
other applicable principle, plus three named gates.

| Bar | Disposition |
| --- | --- |
| **Is this an accelerator pack?** | **No, and it does not need to be (D5).** The carve-out names infrastructure tooling, CI/CD platforms and SaaS integrations, and a local code indexer is none of the three. That only matters if the pack needs the exemption the carve-out grants — it does not |
| 1. Universal across tech stacks | **Clears unaided, on stack-neutrality.** The principle targets packs that serve one framework or language; the accelerator exemption exists for exactly those. This pack is tool-specific and stack-neutral — upstream's language manifest carries 114 entries with 103 wired for extraction (`FEATURES.md` §2, Wicked Estate 0.16.7), so it serves a Python, Rust, TypeScript or COBOL adopter alike. **What that count does and does not establish:** it shows the tool is not aimed at one stack; it is not evidence of comparable extraction quality per language, and the only executed evidence in this repository is against Python and TypeScript. **One reading to foreclose:** that the principle's "(core layer)" heading limits it to `core`, making the question moot. It does not hold — if it did, the Charter's "each accelerator pack is exempt from the Universal principle" would have nothing to do — so this row rests on stack-neutrality instead |
| 2. Substantive, not duplicative | **Clears.** No pack encodes code-graph querying. The nearest neighbours are `architect` (designs systems, does not query them) and `core`'s `bug-fix` (a workflow that would *consume* this) |
| 3. A habit, not a tool | **Clears, with a concession stated.** The pack is not a Wicked Estate manual: it is the habit of resolving before reading, reading source before concluding, stopping when the question is answered, and carrying the index's own limits into the answer. That habit survives the provider — but *this pack* may not, and retirement trigger 3 says so: if a provider-neutral capability arrives, the patterns relocate and the mapping is deleted. Most of what ships today is the mapping. The admission argument is "the habits are worth having now, sited where the provider that enables them lives", not "this pack is permanent." Siting them in `core` was rejected as a judgement, not a rule: no document forbids it, and `core` already declares an optional third-party dependency (`jsonl-otlp-exporter`). The judgement is that `core` installs by default, so a habit sited there would present commands most adopters cannot run |
| 4. Used often enough to stick | **Clears.** "What calls this" and "what breaks if I change this" are asked continuously during implementation, review and refactoring |
| Named maintainer | **eugenelim.** Owns upstream-version tracking and the capability map's accuracy against each release |
| Maturity scope | **Split (D2): CLI `validated`, MCP `contract-complete`** |
| Archiving / deprecation path | **Stated below** |

**The `converters` comparison, and what it is worth.** `converters` is the
closest structural analogue — a non-core, opt-in pack requiring a third-party
binary and sitting outside the accelerator clause.

**It is corroboration, not precedent.** RFC-0007 was accepted 2026-05-24; the
accelerator clause entered the Charter on 2026-07-18 in `dc0f5a157`, about
eight weeks later. `converters` cannot have declined a carve-out that did not
exist, and its RFC mentions "principle", "universal" and "charter" zero times,
so nobody adjudicated principle 1 for it. What it shows is that the catalogue
already carries a tool-dependent pack outside the clause without anyone
treating that as a problem. **D5 has to stand on the Charter text itself**,
and does: the exemption is written for stack-specific packs, and this one is
not stack-specific.

Three further differences are worth naming rather than leaving for a reviewer
to find. It declares no `[[pack.runtime-dependencies]]` at all; its `mmdc`
dependency serves one skill of six, so the pack still works without it, where
this pack is worthless without its provider; and it is Tier 1 detect-and-stop,
explicitly refusing to install, where this pack is Tier 2 install-on-consent.
None of the three bears on principle 1, which asks whether a pack is tied to a
tech stack, not how hard it leans on a tool or how it installs one. They do
mean `converters` is precedent for *tool-dependence not invoking the carve-out*,
and not for this pack's dependency depth or install tier — which D3 and the
Risks table own separately.

The last three are the Charter's *accelerator* gates. This pack is not an
accelerator, so they are not required of it — it adopts them anyway, because a
pack whose value is wholly contingent on one third-party binary should carry a
named owner and a retirement path whatever category it sits in.

**What holds it to them, honestly: only this record, and nothing mechanical.**
No lint checks that a pack has a maintainer, and none checks that a maturity
label matches its evidence.

Nor does anything detect upstream drift, and the vocabulary guard is the
thing most likely to be mistaken for a control that does. It compares the
pack's prose against a **hand-transcribed allowlist in the test file**;
`VERIFIED_AGAINST` is a string in its failure message, not a query against a
release. It catches an author inventing a verb. It cannot catch upstream
removing or renaming one, because nothing in it reads upstream. The only check
that touches the real binary lives in the suite that skips wherever the binary
is absent, which is everywhere in CI.

So every gate in this row depends on a human re-deriving the allowlist and
running the suite locally at each release. A reviewer who wants more should say
so; the cheapest real controls are a lint asserting every pack declares a
maintainer, and a CI job that installs the binary.

**Maturity, precisely.** *Validated* means a worked example passes against the
real tool. The CLI surface qualifies: 20 tests build a real index and assert
the documented JSON shapes, and they skip rather than pass when the binary is
absent, so an environment without it reports unrun instead of green. The MCP
surface does not qualify: its rows were mapped from upstream conformance
schemas and registered tool names, and nothing here has executed the server.
Labelling the pack *validated* outright would bless a surface with zero
coverage — the failure RFC-0065's D5 split exists to avoid.

**Archiving and deprecation.** The pack is retired when any of three conditions
hold, and the maintainer owns the check at each upstream minor release:

1. Wicked Estate is archived upstream, or publishes no release for 12 months.
2. The capability map cannot be brought back into agreement with a current
   release — the integration suite is the detector, because it executes the
   documented surface rather than describing it.
3. The catalogue gains a provider-neutral code-intelligence capability that
   subsumes this one, at which point the pack's patterns move and the
   provider-specific mapping is deleted.

Retirement follows `user-guide-diataxis`'s actual shape, which closes the
plugin route rather than leaving it open — see `packs/user-guide-diataxis/pack.toml`
and `web/src/content/packs/user-guide-diataxis.md`: `display_name` suffixed
`— Deprecated`, `description` rewritten to name the successor or say there is
none, a `deprecated` keyword, `pluginInstallable: false`, and the consequent
removal from `.claude-plugin/marketplace.json` on the next self-host run. The
`agentbundle install --pack` route survives so existing installs keep working;
the Claude-plugin route does not.

**Who can observe a trigger.** Triggers 1 and 3 are observable by anyone —
an archived upstream and a new catalogue capability are both public facts.
Trigger 2 is not: the integration suite skips wherever the binary is absent,
which is every hosted runner, so today only the maintainer can see the map go
stale. That is a real single-person dependency. If the maintainer's release
check lapses for two consecutive upstream minor releases, the pack drops to
`experimental` and the capability map gains a staleness banner naming the last
verified version — a consequence a second person can apply by reading
`VERIFIED_AGAINST` in `tests/pack/test_estate_surface_vocabulary.py` against
the current crates.io release.

**Stated plainly: that consequence is unenforced today.** The vocabulary guard
catches an author naming a verb outside its own hand-maintained allowlist; it
does not read upstream, so it cannot notice a removal or rename, and it checks
neither the maturity label, nor the maintainer, nor how many releases have
passed. Nothing outside this record can fire the drop-to-`experimental`. The
follow-on names a maintainer lint with an owner; until it lands, the gate is a
commitment rather than a control.

## Options considered

| Option | Trade-off | Verdict |
| --- | --- | --- |
| Accept unconditionally | Ratifies a pack that bypassed the admission workflow, and asks nothing of it | Rejected — the D2 markers are worth requiring, and requiring them is what the row below does |
| **Accept with conditions** | The conditions are the D2 maturity labels and provenance rule, applied in this PR. The bypass is a process defect disposed of in D4, not evidence about the pack's merit | **Recommended** |
| Reject and remove | Would cost the catalogue a capability that clears every applicable principle, to punish a sequencing error | Rejected — disproportionate |
| Do nothing (leave unratified) | Today's state. Costs nothing immediately and makes the Charter's admission path optional by demonstration | Rejected — this is the failure mode the RFC exists to prevent |

**D3 — why no amendment.** The Tier-2 manager list reads as closed at a
glance, and generalising it would then look necessary. It is not closed. The
policy's third condition is "it uses a package manager the user **demonstrably already has**",
and `uv`, `npm`, `pipx`, `brew` follow an em-dash as examples of that criterion.
`cargo` satisfies it when detected, which `estate_preflight.py` does before any
install and refuses without. Proposing to generalise a rule that is already
general would have been a self-serving amendment answering a problem that did
not exist.

**The reading is genuinely ambiguous, and that is worth fixing.** The policy
writes "— `uv`, `npm`, `pipx`, or `brew` *if detected*" with no "e.g.", and
the pack's own `pack.toml` called cargo a deviation at ship time, so its author
read the list as closed. This RFC now reads it as illustrative. Whichever a
reviewer prefers, the sentence should not stay ambiguous: the follow-on adds
"for example" to it. That is a clarification of an existing rule, not a widening of it.

What a reviewer checks either way, all readable from the install path: the
manager is detected before use; the version is pinned exactly; no sudo is
assumed; and absence of the manager causes refusal rather than bootstrap. This
pack satisfies all four.

**Two design options settled without a taxonomy**, because one choice dominated:

- **Vendor-named vs capability-named pack.** Shipped first as `wicked-estate`,
  renamed to `code-intelligence` before merge. Capability-first wins on the
  pack's own boundary argument: named for the vendor, every consumer writes
  `dependencies.required = "wicked-estate"` to obtain a capability, which is
  exactly the coupling the three-layer split exists to prevent.
- **Splitting out `engineering-memory` / `engineering-knowledge` skills.** The
  14 memory and knowledge tools are MCP-only. A skill that fires only when an
  optional server is registered triggers unreliably, so they are documented in
  the capability map instead of split into skills nobody can run by default.

## Risks & what would make this wrong

| Risk | Why it is tolerable | What would change the answer |
| --- | --- | --- |
| **Single-provider dependency.** The pack is worthless without Wicked Estate | Opt-in, in no profile, and degrades to labelled repository search | Upstream archived or stalled — a retirement trigger, stated above |
| **Upstream drift.** The patch version `0.16.7` is stamped in `pack.toml`, the README, both subagents, `estate_preflight.py`, the integration suite's run instruction and skip reason, and `gaps.md`'s provenance rule, but `capability-map.md` and the vocabulary guard's `VERIFIED_AGAINST` pin only the minor `0.16`, so prose can rot within it | Partially mitigated only. The integration suite executes the documented surface, but it skips wherever the binary is absent — including the dispatch-only corpus run, which installs neither cargo nor the binary, so it skips all 20 there. **The maintainer's local run is the sole detector**, with the lapse consequence stated under Archiving | Nothing further; this is already the weakest control in the proposal, and a reviewer may reasonably require the corpus job install the binary before accepting |
| **Adopter version skew.** `runtime-dependencies` declares `>=0.16` and the preflight checks a floor only; the exact pin binds the install command, so an adopter with a newer binary gets no warning | The pack's claims are version-stamped in one place, and a newer release is more likely to add than remove | Evidence of a breaking upstream change within 0.x — at which point the preflight needs a verified ceiling, not just a floor |
| **The pack over-trusts the index.** An agent presents a blast radius as complete | Three completeness caveats are load-bearing in the skill, and the gap analysis names the unreported depth-12 horizon | A finding that agents ignore the caveats in practice |
| **The install path.** `cargo install` compiles from source for minutes | Consent-gated, pinned, no sudo, refuses outright if cargo is absent | A supply-chain incident in the crate, or evidence agents install without consent |

**What would make D1 wrong:** evidence that agents reach for this pack and get
worse answers than from plain repository search — most plausibly by treating a
stale index as current, which the skill can warn about but cannot prevent.

## Evidence & prior art

**The pack works, and that claim is executed rather than asserted.** 91 tests,
20 of which run the real binary.

Two different indexes appear in the evidence and they are not interchangeable.
The **canonical manual measurement** is this repository at commit `b1237654f`
on 2026-09-30: 65,981 nodes, 104,379 edges, 4,634 files, indexed in ~15s — that
is the run the investigation patterns were walked against. `gaps.md` cites an
earlier index of the same repository taken before the pack was added (65,807 /
104,113 / 4,625), and the 20 automated tests use a deterministic three-file
micro-repository instead.

**Three rounds of correction, each finding what the previous could not:**

1. *Adversarial review* — 20 findings, 6 blockers. Every CLI finding was
   confirmed by **executing the binary**. The MCP findings could not be: they
   were confirmed by reading upstream's registered tools and conformance
   schemas — the *schema-derived* category the pack's provenance rule now
   names. The most
   notable of those corrected the pack **in the provider's favour** — MCP
   `BlastRadius` returns per-dependent depth, a confidence envelope and
   PageRank-ranked dependents, which the draft claimed were absent — and it
   remains unexecuted, which is precisely why D2 splits the label.
2. *Live end-to-end run* — three documented commands did not survive contact,
   including `source`'s bulk selectors, which are **silently ignored** without
   `--json`. That one returned a plausible wrong answer rather than an error:
   an ambiguous name yielded every match while appearing pinned to one. The
   same round found that the pack's own path-confinement fix reported a real
   out-of-repo graph as `index-absent`.
3. *CI* — the registration surfaces below.

The lesson generalises beyond this pack: static tests, deep lint **and** an
adversarial reviewer all passed a pack whose documented happy path was broken.
Only running it found that.

**Capability gaps in the provider.** The pack ships a fourteen-point assessment
against a general code-intelligence contract, classifying each as available
directly, by composition, partially, not today, or unclear. One capability —
**path between two symbols** — is absent on both surfaces. Seven of the
fourteen are partial when read over the CLI, the surface an adopter gets by
default; two of those seven resolve to Direct on the unexecuted MCP surface,
and the gap analysis marks them so rather than counting them as won.
None require a change to Wicked Estate, and the pack works within all of them.
The full analysis is at
`packs/code-intelligence/.apm/skills/code-intelligence/references/gaps.md`.

**The registration surfaces a new pack obliges.** None is discoverable from
the pack directory; each announced itself as a red gate. This table is the
part of the RFC most useful to the next pack author.

| # | Surface | What it obliges |
| --- | --- | --- |
| 1 | `.claude-plugin/marketplace.json` | Generated — regenerate with `catalogue self-host --write`. A rebase dropped it twice as "already upstream" when it was not |
| 2 | `web/src/content/packs/<pack>.md` | **Hand-authored**, not generated by `build-site.py` |
| 3 | `site.toml` | Sidebar group, else the pack lands in "Other" |
| 4 | `web/src/lib/catalogue-navigation.ts` | Outcome membership; every active pack needs one |
| 5 | `tools/lint-plugin-roster.py` | `PUBLISHED` set, for a user-capable pack |
| 6 | `tools/test-lint-plugin-roster.py` | The hand-built allowlist expectation and its pack count |
| 7 | `.github/workflows/publish-claude-plugins.yml` | Trigger path — an allowlist that fails unsafe |
| 8 | `Makefile` | `run-test-suite` lines, else no runner names the suites |
| 9 | `tools/lint-ci-parity.py` | A `SUITE_DISPOSITION` per new runner target |
| 10 | `tools/lint-plugin-route-docs.py` | The live pack-count literal in the install doc guard |
| 11 | `tools/test_local_ci_shared_test_deduplication.py` | Two plan digests, with sole-cause and prior-pins-live evidence |
| 12 | `packages/agentbundle/tests/build_pipeline/` | Agent Plugins projection exclusion, for any pack shipping subagents |
| 13 | `packs/agent-skill-engineering/tests/fixtures/skill-census.json` | Family classification and `population_size` |
| 14 | `docs/product/changelog.md` | A versioned entry — and `core` must stay directly beneath `[Unreleased]` |

One further obligation lives *inside* the pack but is imposed from outside: a
`cognitive-load-output-quality` eval scenario plus its prose fixture, required
of every publishable pack by `tests/roster/`.

**Repository precedent.** `converters` is the closest structural analogue: a
non-core, opt-in pack that requires a third-party binary (`mmdc`, via Node)
and sits outside the accelerator clause — though it was admitted before that
clause existed, so it corroborates rather than decides.
RFC-0065 contributes the per-surface maturity split this RFC reuses, though
its accelerator framing does not apply here (D5). `figma` and `atlassian` establish
opt-in tool-specific packs with credentialed boundaries. `user-guide-diataxis`
establishes the deprecation shape.

## Experiment / validation

Already run; no further experiment is proposed. Locally: `make sast`,
`make lint-ruff`, `make lint-mypy`, `agentbundle catalogue lint --deep`,
`agentbundle catalogue verify`, seven registration linters, and 91 pack tests
all green.

**What CI did and did not cover.** The merged PR reported 38 passed, 4 skipped,
0 failed. Those are the repository's own gates — build-check, the gate chain,
SAST, the agentbundle suites — and they cover the pack's *registrations*, not
its behaviour: `tools/lint-ci-parity.py` records **both** code-intelligence
suites as `NO_PR_GATE`, so none of the 91 tests ran on the pull request. The
green result says the pack is correctly registered and breaks nothing; it says
nothing about whether the pack works.

The standing validation is therefore local. The 20 integration tests are
`NO_PR_GATE` deliberately — they execute the real binary, no hosted runner has
it, and gating on a suite that always skips records a pass proving nothing —
but so is the 71-test remainder, which *could* be PR-gated and is not. The
dispatch-only `test-corpus.yml` installs neither cargo nor the binary, so the
integration half skips there too.

**The maintainer runs the suite locally at each upstream minor release**, and
that run is what keeps the capability map honest. A reviewer who finds that
too thin has two proportionate asks: PR-gate the 71 non-integration tests,
which need nothing installed, and have the corpus job install the binary.

## Open questions

| ID | Question | Owner | Needed by |
| --- | --- | --- | --- |
| Q1 | The registration surfaces become a follow-on checklist either way. Open: checklist prose, or a lint that reddens when a pack misses a surface? | eugenelim | Before the next pack |
| Q2 | Does `code-intelligence` need `guides/code-intelligence/` and a `JOURNEY.md`? 20 of 23 packs have a guide home; the pack's `docsUrl` currently points at the generic guides index | eugenelim | Next release |

## Security review

Not obliged at `standard` weight, and included because the boundary is real:
**dependency trust**. The pack executes a third-party binary and can trigger a
consent-gated network install.

Already in place and verified: the install detects `cargo` first and refuses
rather than bootstrapping it, pins an exact version, never assumes sudo, and
re-verifies afterwards rather than trusting PATH. The pack is read-only by
default and names every mutating verb. `WICKED_ESTATE_DB` is confined to the
repository root, after `resolve()` so a symlink cannot escape, with the
refusal surfaced as exit 6 rather than silently swallowed — a defect the live
run found and this PR fixes.

Residual, accepted and larger than a single crate. `cargo install --locked`
resolves and compiles Wicked Estate's **full transitive crate tree** and
executes any `build.rs` build script in it, at install time, on the adopter's
machine. No SCA leg covers any of it: `make sast` runs bandit, semgrep, four
`pip-audit` legs and an npm leg, and nothing audits cargo. The controls that
bound this are the exact version pin and `--locked`, which makes the build
reproducible from the crate's shipped lockfile rather than re-resolving — both
in `estate_preflight.py`'s `INSTALL_COMMAND` — plus the fact that the install
happens only on explicit consent. A reviewer may reasonably require a
cargo-audit leg before accepting; the pack works without the install path if
the adopter prefers to install the binary themselves.

## Follow-on artifacts

- **Disambiguate the Tier-2 manager sentence** in
  `guides/_shared/how-to/author-a-skill.md` — add "for example" before the
  manager names so the closed-versus-illustrative reading D3 turned on cannot
  recur. Owner: eugenelim.
- **A lint asserting every pack declares a maintainer**, which is what would
  make this proposal's voluntary gates enforceable. Owner: eugenelim.
- **A new-pack registration checklist**, from the registration table, sited
  wherever Q1 lands.
- **`guides/code-intelligence/`** and a pack `JOURNEY.md`, subject to Q2.
- **Upstream issues** for the provider gaps, filed against
  `mikeparcewski/wicked-estate` after re-verification against its current
  release. Not a catalogue artifact, and not blocking.

## Errata

Append-only. A later entry supersedes an earlier one by being later.

### 2026-09-30 — Q1 and Q2 answered

Both open questions are closed by the approver.

**Q1 — the registration surfaces stay prose.** No lint is built. The table in
this RFC is the record a future pack author reads; nothing will redden when a
surface is missed. The cost is known and accepted: this pack found all of them
as failing CI, and the next pack may too.

**Q2 — the pack gets a guide home and a journey.** Delivered alongside this
entry: `guides/code-intelligence/` with a README, tutorial, how-to and
reference, plus `packs/code-intelligence/JOURNEY.md`. The pack's `docsUrl`
moves from the generic guides index to its own home, and `journeyUrl` is
populated for the first time.

This entry answers the questions; it does not reopen any decision. D1 through
D5 stand as accepted.
