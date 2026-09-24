# Spec: jira epic outcome view

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0126; ADR-0077
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration


> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

<!-- **Durable-spec fill.** This template governs work that needs a durable
behavior contract for one delivery slice. Fill Outcome, What Changes, Agent
Rules, Testing Strategy, and Acceptance Criteria to the depth the durable work
requires, and Assumptions only where something is unresolved. The sibling plan carries the implementation and verification strategy.
Eligible direct-light work does not create this artifact. -->

<!-- **Present tense, as-built.** Write every body section below as if the
feature already exists and always worked this way — no "will be", no
"previously X, now Y", no deprecation timelines, no version-stamped history.
The body describes the current contract; decision history lives in ADRs and the
release changelog. `plan.md` holds to the same rule: its `## Changelog` records
approvals, not how the approach evolved. -->


## Outcome

A team running Jira Software, having installed nothing else from this
repository, reads where its work stands and what that work was meant to
change, in one view, from its own tracker. Success is that the view is worth
opening a second time, and that the team can say what adopting an intent model
would add.

## What Changes

- A view groups a Jira scope's work by Epic and renders each Epic's delivery
  reading beside its declared outcome — `packs/atlassian/`
- Where an Epic has no outcome recorded in Jira, the view renders the Epic with
  an explicit nothing and offers text the team can paste into Jira themselves
  — `packs/atlassian/`
- The pack declares which of its skills are bridges, as ADR-0126 D4 requires —
  `packs/atlassian/pack.toml`
- `flow-metrics` gains a fully inert cache mode, because its current
  `--no-cache` still cleans stale temps and materialises a cwd-relative
  `.context/` — `packs/atlassian/.apm/skills/flow-metrics/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable — the view is a skill an adopter runs, and the outcome convention is what a team has to follow | the new skill's `SKILL.md` | this spec | the skill, stating where it reads an outcome from and what it renders when there is none | the convention is stated in one place a team can follow without reading code |
| User promise | Applicable — this is the pack's first-value surface for a team that has adopted nothing | the established user-documentation surface | this spec | what the view answers, and what it does not | drafted before implementation approval |
| Interface compatibility | Applicable — ADR-0126 D4 requires the pack to declare its bridge skills | `packs/atlassian/pack.toml` | this spec | the declaration, with this skill absent from it | the pack declares bridges and this skill is not one |
| Release history | Applicable — `atlassian` changes | `packs/atlassian/CHANGELOG.md` | this spec | one entry | the pack leads its own entry |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Read the outcome from the location in Jira the skill documents, and render
  it verbatim.
- Render an Epic whose outcome is absent, with an explicit statement that none
  is recorded, and the exact text the team can paste into Jira to record one.
- State the moment each reading was taken.
- Compose the state and flow readings from the skills that already ship rather
  than recomputing them.
- Satisfy ADR-0126 D3 by carrying no coupled capability, and the parent
  intent's contract by returning value with no repository artifact present.
  D1 is a pack-level existential that `packs/atlassian` already satisfies
  through its other standalone skills; it is not this skill's obligation.

### Ask first

- Reading an outcome from anywhere other than the documented location.
- Adding a second delivery system, which is a later slice rather than part of
  this one.

### Never do

- Write anything to Jira, including a comment, a label, a transition or a
  field edit.
- Write any repository artifact, including a mapping keyed by an Epic.
- Author an outcome. Where none exists the view says so; it never supplies one.
- Reference `docs/product/`, an intent tree, `workspace.toml` or the
  `work-intake` route, which ADR-0126 D2 confines to declared bridge skills.
- Grade, score or judge a recorded outcome.
- Introduce a daemon, control plane, database or scheduler.

## Testing Strategy

- **Outcome rendering: goal-based check.** Rendered output is compared against
  the source Jira text for verbatim reproduction; a paraphrase fails.
- **Scope completeness: TDD.** The expected Epic set is derived from the
  completed Jira result and compared for exact equality; each member is then a
  failing removal control. A fixture-derived list proves only the fixture's
  members, and an Epic dropped before rendering is never a removal candidate.
- **Absent-outcome visibility: TDD, universally.** Every in-scope Epic with an
  empty outcome location is asserted to carry both the explicit nothing and
  the paste-ready text, against a fixture holding several. Quantifying over
  one lets a second render blank.
- **Authorship: TDD.** A fixture where the feature would supply outcome
  substance must fail. The paste-ready text is a fixed scaffold or the team's
  own words, never an invented outcome.
- **Read-only: goal-based check.** The filesystem is hashed before and after
  a run, with a populated `.context/flow-metrics/cache/` seeded first
  including a stale `*.tmp`, and asserted byte-identical. "Creates no new
  file" would pass a run that rewrites a cache entry or deletes a stale temp,
  and `flow-metrics` as shipped does the second even under `--no-cache`.
- **Zero coupling: goal-based check plus a call-graph walk.** The sources are
  scanned for the machinery ADR-0126 D2 confines to bridges, and
  `packs/atlassian/pack.toml` is asserted not to list this skill as one. A
  token scan is not sufficient on its own, so the skill's dependency and
  invocation graph is walked for any path reaching a declared bridge, with a
  bridge-calling fixture that must fail.
- **Artifact-free operation: goal-based check.** The view is run from a
  non-repository working directory with every adopter-repository path denied,
  and asserted to return a correct non-empty answer. Naming three absent
  artifacts would let a hidden workspace dependency pass.
- **Composition: TDD.** The state and flow figures the view renders match what
  the shipping skills return for the same scope.

## Acceptance Criteria

- [ ] The view groups a Jira scope's work by Epic and renders, for each Epic,
      both a delivery reading and an outcome position.
- [ ] The state and flow figures match what `jira-team-status` and
      `flow-metrics` return for the same scope and window.
- [ ] An Epic's recorded outcome is reproduced verbatim from the documented
      Jira location.
- [ ] The expected Epic set is derived from the completed Jira result for the
      requested scope, not from a hand-written fixture list.
- [ ] The rendered view's Epic set equals that expected set exactly. An Epic
      dropped before rendering fails, as does one Jira omitted for
      permissions without saying so.
- [ ] Removing any single member of the expected set from the rendered view
      fails the check.
- [ ] Every in-scope Epic whose documented outcome location is empty renders
      an explicit statement that none is recorded, rather than a blank or an
      omitted row.
- [ ] Every such Epic also renders the exact text a team can paste into Jira
      to record one, at the documented location.
- [ ] A fixture carrying several outcome-less Epics fails if any one of them
      is rendered without both.
- [ ] The view renders no score, grade or judgement of a recorded outcome.
- [ ] Text is called paste-ready only when it carries outcome substance the
      team supplied in this session. A fixed scaffold with no team input is
      rendered as an elicitation prompt and is never labelled paste-ready.
- [ ] A run that offers invented outcome substance fails, because the
      parent's guardrail makes authorship non-waivable.
- [ ] A run where the team supplies nothing renders the prompt and no
      paste-ready text, and still renders the Epic with its explicit
      nothing.
- [ ] Running the view issues no Jira write verb of any kind.
- [ ] Running the view leaves the filesystem byte-identical, including when a
      populated `.context/flow-metrics/cache/` holds a stale `*.tmp` older
      than an hour.
- [ ] `flow-metrics` gains a mode that performs no cache read, no cache write,
      no stale-temp cleanup and no cache-directory creation. `--no-cache`
      today is insufficient: `cleanup_stale_tmps(cache_dir)` runs at
      `__init__.py:517`, before the `--no-cache` branch at 544, and
      `cache_dir` is `Path.cwd()`-relative so it materialises `.context/`
      wherever the view is invoked.
- [ ] The view composes `flow-metrics` only through that mode.
- [ ] Invoked from a working directory that is not a repository and contains
      none of this repository's artifacts, the view returns a correct,
      non-empty answer.
- [ ] With every adopter-repository path denied, the view still returns that
      answer. A run that reads any repository file fails.
- [ ] The skill's sources contain no reference to `docs/product/`, an intent
      tree, `workspace.toml`, canonical intent, a delivery brief or the
      `work-intake` route.
- [ ] No path in the skill's dependency and invocation graph reaches a skill
      the pack declares as a bridge. A token scan alone does not establish
      this: a skill can invoke `jira-refresh` while containing none of those
      terms, and would pass every other check here while violating ADR-0126
      D3.
- [ ] `packs/atlassian/pack.toml` declares the pack's bridge skills, and this
      skill is not among them.
- [ ] Every rendered reading states the moment it was taken.
- [ ] The view renders no percentile. `flow-metrics` computes percentiles
      through `statistics.quantiles` and nulls them only for an empty cohort;
      it applies no sample-size threshold, so rendering one here would put a
      median over four completions in front of a reader.
- [ ] The view renders throughput as a count with its window, and the
      non-distributional observations — work in flight, age, blocked and since
      when, what moved — which need no sample at all.
- [ ] The view runs only when invoked and leaves no resident process.

## Follow-ons

- eugenelim: a second delivery system for this view. The parent intent records
  it as a later cut rather than a condition of this one working, and neither
  `linear` nor `github` ships a standalone skill to compose from today.
- eugenelim: the ADR-0126 D1-D4 conformance lint. The ADR names `lint/CI` as
  its Confirmation and none exists; it cannot land green until `linear` and
  `github` each ship a standalone skill.

## Assumptions

- Whether a team will paste an outcome into Jira once shown where. The parent
  intent's de-risk measured the analogous act at 153 of 154 in this
  repository's own corpus, but that population is prompted by a skill,
  motivated, and one maintainer. The parent carries the `to-validate` hook and
  the activity that would settle it.
