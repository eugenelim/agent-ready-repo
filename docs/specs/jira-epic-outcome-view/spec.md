# Spec: jira epic outcome view

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
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
  an explicit nothing and asks the team for one; what the team states comes
  back as text they paste into Jira themselves — `packs/atlassian/`
- The pack declares which of its skills are bridges, as ADR-0126 D4 requires —
  `packs/atlassian/pack.toml`
- `flow-metrics` gains a fully inert cache mode, because its current
  `--no-cache` still unlinks stale temps from a cwd-relative cache directory
  — `packs/atlassian/.apm/skills/flow-metrics/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable — the view is a skill an adopter runs, and the outcome convention is what a team has to follow | the new skill's `SKILL.md` | this spec | the skill, stating where it reads an outcome from and what it renders when there is none | the convention is stated in one place a team can follow without reading code |
| User promise | Applicable — this is the pack's first-value surface for a team that has adopted nothing | `guides/atlassian/` | this spec | what the view answers, and what it does not | drafted before implementation approval |
| Interface compatibility | Applicable — ADR-0126 D4 requires the pack to declare its bridge skills | `packs/atlassian/pack.toml` | this spec | the declaration, with this skill absent from it | the pack declares bridges and this skill is not one |
| Maintainer procedure | Applicable — this slice changes a skill other callers share | `flow-metrics`' `SKILL.md` | this spec | the inert cache mode, stated as default-off and named as the only mode this view composes through | the mode is documented where an existing `flow-metrics` caller would find it |
| Release history | Applicable — `atlassian` changes | `docs/product/changelog.md` — a `## [atlassian][<version>] — <date>` entry. A pack keeps no `CHANGELOG.md` of its own; that convention is for published packages | this spec | one entry at the version both manifests carry | the entry sits at the bumped version and names the new view |
| Interface compatibility | Applicable — a new primitive and a changed skill are a non-cosmetic pack change | `packs/atlassian/pack.toml` and `packs/atlassian/.claude-plugin/plugin.json` | this spec | matching minor version bump in both, and the new skill listed in the eval harness | both versions match and the eval harness covers the new skill, as `packs/AGENTS.md` requires |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Read the outcome from the block under the Epic description's `Outcome`
  heading, and render it verbatim.
- Render an Epic whose outcome is absent, with an explicit statement that none
  is recorded, and a prompt asking the team for one. Where the team answers,
  render their words back as paste-ready text naming that same fixed location.
- State the moment each reading was taken.
- Compose the flow reading by running `flow-metrics --per-issue` once and
  aggregating its rows by count. Read state and parent links through the
  `jira` client, and state both moments rather than implying one snapshot.
- Satisfy ADR-0126 D3 by carrying no coupled capability, and the parent
  intent's contract by returning value with no repository artifact present.
  D1 is a pack-level existential that `packs/atlassian` already satisfies
  through its other standalone skills; it is not this skill's obligation.

### Ask first

- Reading an outcome from anywhere other than the fixed documented location,
  or making that location configurable per invocation.
- Adding a second delivery system, which is a later slice rather than part of
  this one.

### Never do

- Write anything to Jira, including a comment, a label, a transition or a
  field edit.
- Issue a mutating call on any client in the skill's declared dependency and
  invocation graph, Confluence and Jira Align included. The pack ships
  `confluence-publisher`, so "no Jira write verb" does not by itself make the
  view read-only.
- Cite this repository's internal records in shipped pack content — no ADR
  number, no acceptance criterion, no repository-only path in a `SKILL.md` or
  any other file under `packs/`. State the rule directly instead, as
  `packs/AGENTS.md` requires. The ADR citations in this spec govern the
  implementing agent, not the artifact it ships.
- Write any repository artifact, including a mapping keyed by an Epic. The
  per-issue JSONL is not an exception: it is transient, lives outside both
  named roots, and is removed before the view returns.
- Recompute cycle time, lead time or flow efficiency per Epic. Counting rows
  `flow-metrics` already derived is composition; deriving the metric again is
  the second definition this slice exists to avoid.
- Author an outcome. Where none exists the view says so; it never supplies one.
- Reference `docs/product/`, an intent tree, `workspace.toml` or the
  `work-intake` route, which ADR-0126 D2 confines to declared bridge skills.
- Grade, score or judge a recorded outcome.
- Introduce a daemon, control plane, database or scheduler.

## Testing Strategy

- **Outcome rendering: TDD.** Verbatim reproduction is asserted against the
  reader that produces it, across both description shapes — ADF from Cloud v3
  and plain text from Server v2 — because a reader that handles one silently
  returns nothing on the other, which is indistinguishable from an Epic with
  no outcome. T2 owns this criterion and is its only completion gate. T6's
  installed-CLI pass exercises the same path end-to-end, but it verifies that
  the artifact runs as documented; it is not a second owner of verbatim
  reproduction, and a criterion with two owning gates has none.
- **Scope completeness: TDD, bounded to what the caller can see.** The
  expected Epic set is derived from the fully paginated Jira result for the
  calling credential and compared for exact equality; each member is then a
  failing removal control. A fixture-derived list proves only the fixture's
  members, and an Epic dropped before rendering is never a removal candidate.
  Equality between two sets drawn from the same query cannot detect an issue
  Jira withheld for browse permissions, so the disclosure is asserted as
  present on every run rather than inferred from an upstream signal:
  `flow-metrics` defines a project-scope undercount note at
  `notes.py:118` and never calls it.
- **Absent-outcome visibility: TDD, universally.** Every in-scope Epic with an
  empty outcome location is asserted to carry both the explicit nothing and
  the prompt, against a fixture holding several. Quantifying over one lets a
  second render blank.
- **Authorship: TDD.** A fixture where the feature would supply outcome
  substance must fail. Paste-ready text carries the team's own words, never an
  invented outcome.
- **Elicitation: TDD, both directions.** A run where the team answers the
  prompt is asserted to render their exact words as paste-ready text; a run
  where the team declines is asserted to render the prompt and no paste-ready
  text. Only asserting the declining case would pass a design that never asks.
- **Broker-write attribution: goal-based check.** `~/.agentbundle/` is outside
  the hashed roots, because the credential broker resolves an SSO session into
  an on-disk cookie jar there and an authenticated read may legitimately change
  it. The view is held instead to issuing no write there itself, asserted by
  attributing every write under that root to the broker seam.
- **Outbound mutation: goal-based check.** The client set is derived from the
  sources — the same traversal the coupling walk uses — and each client in it
  is exercised against a recording transport and asserted to have issued read
  methods only. `deps.skills` is not the enumeration source: it is compared
  against the derived set for equality, so an undeclared call is caught rather
  than excused.
  Checking Jira verbs alone leaves a Confluence or Jira Align write reachable.
- **Read-only: goal-based check.** The two named roots — the invocation
  working directory tree and the installed pack tree — are hashed before and
  after a run, with a populated `.context/flow-metrics/cache/` seeded first
  including a stale `*.tmp`, and asserted byte-identical. "Creates no new
  file" would pass a run that rewrites a cache entry or deletes a stale temp,
  and `flow-metrics` as shipped does the second even under `--no-cache`.
- **Installed-CLI happy path: visual / manual QA.** The built skill is invoked
  as an adopter would invoke it, against a real Jira scope, and the session
  records the command, stdout, exit code and what was rendered for one Epic
  with an outcome and one without. A passing unit gate never stands in for
  real invocation, and this view's whole claim is that a team opens it twice.
- **No resident process: goal-based check.** The process table is compared
  before and after a run, and the view's exit is asserted to leave nothing
  behind. A run that returns output while leaking a watcher satisfies every
  other check here.
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
- **Composition: TDD.** Every per-Epic flow figure is checked to be an
  aggregation by count over `flow-metrics`' own per-issue rows for the same
  scope and window. A fixture whose rows are recomputed rather than counted
  fails, and so does any figure that would need a percentile.
- **Scratch-file hygiene: goal-based check.** The per-issue JSONL path is
  asserted to sit outside both hashed roots and to be absent after the run,
  including when the run raises.

**Stub coverage.** Of 57 criteria, 26 are TDD-mode: 15 carry a
validated red stub in the plan (AC1, AC2, AC3, AC5, AC6, AC9, AC12, AC15, AC16, AC21, AC22, AC26, AC39, AC54, AC55)
and 11 carry `no stub (implementation-discovered)` with a discovery predicate
and a proof obligation (AC8, AC11, AC17, AC18, AC19, AC20, AC24, AC25, AC27, AC28, AC29). 30 are
goal-based checks, and AC57 is the installed-CLI visual / manual-QA pass.

The plan's `## Criterion disposition` table is the binding record — one row per
criterion, total and disjoint by construction. This paragraph is derived from
it. Earlier rounds kept the two in step by hand and they drifted three times.

## Acceptance Criteria

- [ ] The view groups a Jira scope's work by Epic and renders, for each Epic,
      both a delivery reading and an outcome position.
- [ ] The flow reading is `flow-metrics` run once in `--per-issue` mode. Every
      per-Epic figure is an aggregation by count over that skill's own emitted
      rows, never a recomputation of a metric it defines.
- [ ] Per-Epic throughput applies that skill's own counting rule, not a plain
      count of delivered rows: a row counts when `delivered_in_window` is true
      **and**, unless `--include-subtasks` was passed, its `issuetype_bucket`
      is not `subtask` — where any bucket outside `feature`, `defect`, `debt`,
      `risk`, `subtask`, `other` normalises to `other` first. With
      `--include-subtasks` the same rows count, so the view reports the larger
      number rather than holding the excluded count fixed. Counting every
      delivered row would report a larger number under the same name.
- [ ] Per-Epic work in flight counts rows whose `wip_at_to` is true, with no
      further filter, which is that skill's own rule unchanged. `flow-metrics`
      emits no per-Epic breakdown: its output carries `aggregates`,
      `per_team` and a `--cohort-jql`-driven `cohort_breakdown`, so a per-Epic
      figure has to be grouped here or not exist.
- [ ] Rows are grouped to Epics by the view's own read of each issue's parent
      link, resolved to the Epic rung. Jira Software nests Epic > Story >
      Subtask, so a subtask's immediate parent is a Story and reaching its
      Epic takes two hops.
- [ ] An issue whose parent chain does not terminate at an in-scope Epic is
      rendered in a named unattributed group, with its key and the reason the
      chain ended, and the run still exits zero. Dropping it silently would
      shrink the delivery reading without saying so; failing the run would
      make one unparented issue withhold the whole view, which is worse than
      the partial answer a reader can see and act on. A per-issue row carries `key`, `team` and the derived times but no
      Epic or parent field, so the join cannot come from `flow-metrics`.
- [ ] Because percentiles are not rendered, every per-Epic figure is a count
      or a non-distributional observation. No per-Epic aggregation redefines
      cycle time, lead time or flow efficiency, and a criterion or task that
      would compute one fails this spec.
- [ ] The state observations come from the same Jira read that supplies the
      parent links, and each has one defined source and anchor. Work in
      flight is the `wip_at_to` row count above and is not re-derived here.
      Age is now minus the issue's status-category-changed timestamp, per
      in-flight issue. Blocked is Jira's flagged field where the instance has
      one, and since when is that field's last-changed timestamp; where the
      instance has no flagged field the view says so rather than reporting
      zero blocked. What moved is the set of issues whose status category
      changed inside the flow window, which is the same window the throughput
      count uses. An Epic with no in-flight issues renders each observation as
      an explicit none, not a blank.
- [ ] The view states the moment of the flow reading and the moment of the
      Jira read. They are two passes over Jira and the view does not claim
      otherwise; a single rendered timestamp implying one atomic snapshot
      fails. `jira-team-status` is deliberately not composed: its first stage
      reads the working directory's git remote, which the artifact-free
      criteria forbid, and its declared dependencies route to `new-spec`, core
      machinery this slice must not reach. Its own value — the readiness rule
      and pick-up routing — is what this view is forbidden to render.
- [ ] The outcome location is the Epic's `description` field, specifically
      the block under a top-level `Outcome` heading. It is fixed, documented
      in `SKILL.md`, and not configurable per invocation. `description` is one
      of only two free-form multi-line system fields Jira ships, and the only
      one meant for prose; no system field represents a goal or outcome, and a
      custom field would need per-instance admin setup — per-space in
      team-managed projects, where custom fields cannot be reused across
      spaces — which the parent forbids as a prerequisite in disguise.
- [ ] The same location is what the prompt and the paste-ready text instruct
      the team to write into.
- [ ] The heading is located in both description shapes: Atlassian Document
      Format on Cloud REST v3 and plain or wiki text on Server/DC REST v2. A
      reader that handles only one shape fails on the other deployment.
- [ ] The heading grammar is fixed, so one reader is determinate. In ADF, a
      node of `type` `heading` at any `level`. In text, a line matching either
      a Markdown ATX heading (`#` to `######` followed by a space) or a
      Confluence wiki heading (`h1.` to `h6.` followed by a space); Setext
      underlining is not recognised. In both, the heading's trimmed text must
      equal `Outcome` case-insensitively — "top-level" describes the block's
      position in the description, not a required heading level.
      The block runs to the next heading of any level or the end of the
      description. Where more than one such heading exists the first opens the
      block and the rest are ignored rather than merged, because merging would
      silently concatenate two authors' answers. A nested heading inside the
      block terminates it like any other.
- [ ] Verbatim means the block's text with leading and trailing blank lines
      removed and nothing else changed — no reflowing and no Markdown
      rendering. From ADF the traversal takes each descendant text node in
      document order, joining sibling block nodes (paragraphs, list items)
      with a single newline, rendering a `hardBreak` as a newline, and
      concatenating inline nodes with no separator. Without those three rules
      two readers produce different text and both call it verbatim.
- [ ] An Epic whose description has no `Outcome` heading, and one whose
      heading is present with an empty block, both count as no outcome
      recorded and render the explicit nothing and the prompt. Absent and
      empty are the same answer to the reader, and treating only the first as
      absent would render a blank for the second.
- [ ] An Epic's recorded outcome is reproduced verbatim from that block, and
      the rest of the description is not rendered as outcome text.
- [ ] The expected Epic set is derived from the fully paginated Jira result
      for the requested scope and the calling credential, not from a
      hand-written fixture list.
- [ ] The rendered view's Epic set equals that expected set exactly, and an
      Epic dropped before rendering fails.
- [ ] Every run states that the set covers only what the calling credential
      can browse and that Jira omits the rest silently. Exact equality is
      asserted between two sets drawn from the same query, so it cannot detect
      a withheld issue and the disclosure is unconditional rather than
      triggered.
- [ ] Removing any single member of the expected set from the rendered view
      fails the check.
- [ ] Every in-scope Epic whose outcome location is empty renders an explicit
      statement that none is recorded, rather than a blank or an omitted row.
- [ ] Every such Epic also renders a prompt asking the team to state an
      outcome, naming the location to write it into.
- [ ] The answer-input boundary is one observable surface, documented in
      `SKILL.md`: a repeatable `--outcome EPIC-KEY=<text>` argument, which a
      deterministic script can accept without an interactive session and a
      test can drive without a terminal. Absent the argument the Epic is
      treated as declined.
- [ ] Three cases are decided rather than left to the implementation. A key
      outside the queried scope is refused with a non-zero exit naming the
      key, because silently ignoring it loses the team's words. The same key
      given twice is refused the same way, since choosing first or last would
      discard one of two answers. `EPIC-KEY=` with empty text is a decline and
      renders the prompt, matching omission.
- [ ] The view accepts an outcome the team states in response to that prompt
      and renders those exact words back as paste-ready text, naming the
      location. A design that prints the prompt and never accepts an answer
      fails this criterion, and eliciting the outcome is in the parent's
      scope.
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
- [ ] The set of sibling skills the sources actually invoke is derived from
      the sources, and that derived set — not a declaration — is what the two
      checks below traverse. A declaration cannot carry a read-only guarantee
      on its own, because an undeclared invocation is exactly what it fails to
      mention.
- [ ] The skill's `manifest.json` declares that same set under `deps.skills`,
      each by name and purpose, as `flow-metrics` already does for `jira` and
      `jira-align`, and the declaration is asserted equal to the derived set.
      `deps.skills` is the pack convention — 13 of 19 skill manifests use it —
      but it sits outside the published `skill-manifest.schema.json`, whose
      `deps` admits only package-manager keys. The equality assertion is what
      makes the field trustworthy here; the schema gap is recorded as a
      follow-on rather than resolved by this slice.
- [ ] Every client reached from that derived set issues read methods only.
      The derived set, not the set of skills the pack ships, is the boundary.
      A run that publishes to Confluence passes every Jira-verb and filesystem
      check while breaking the parent's read-only guardrail.
- [ ] A sibling skill invoked by the sources but absent from `deps.skills`
      fails the check. Otherwise the boundary is self-reported and an
      undeclared invocation is invisible to both checks.
- [ ] Running the view leaves two named roots byte-identical: the invocation
      working directory tree and the installed pack tree.
- [ ] `--per-issue` requires `--output FILE` and exits 2 without it, so the
      view writes that JSONL to a scratch path outside both named roots and
      removes it before returning. The write is disclosed rather than denied:
      the read-only guarantee is that no repository artifact, no Jira object
      and neither named root changes — not that the process writes no byte
      anywhere.
- [ ] A run that leaves the per-issue JSONL behind fails, as does one that
      writes it under either named root. The cache case is
      included — a populated `.context/flow-metrics/cache/` holding a stale
      `*.tmp` older than an hour. Naming the roots is what makes the check
      runnable; "the filesystem" names no comparison.
- [ ] The broker's `~/.agentbundle/` is excluded from that comparison, and
      the view is asserted instead to issue no write there itself. The
      credential broker resolves an SSO session into an on-disk cookie jar
      under that root, so an authenticated read can legitimately change it.
      Holding the view to byte-identity there would fail on a path the view
      does not control and does not own.
- [ ] `flow-metrics` gains a mode under which no cache operation of any kind
      occurs, stale-temp cleanup included. The residual defect `--no-cache`
      leaves is exactly one: the stale-temp cleanup runs ahead of the flag's
      branch and unlinks `*.tmp` files older than an hour from an existing,
      `Path.cwd()`-relative cache directory. Deleting a file is a write, so a
      read-only view cannot reach `flow-metrics` through that flag. The flag
      does already skip the cache read and the cache write, and the cache
      directory is created only on the write path, so a bypassed run does not
      materialise `.context/`. The plan holds the source coordinates, because
      this criterion's own task edits the file they point into.
- [ ] The view composes `flow-metrics` only through that mode.
- [ ] Invoked from a working directory that is not a repository and contains
      none of this repository's artifacts, the view returns a correct,
      non-empty answer.
- [ ] With every adopter-repository path denied, the view still returns that
      answer. A run that reads any repository file fails.
- [ ] The skill's sources contain no reference to `docs/product/`, an intent
      tree, `workspace.toml`, canonical intent, a delivery brief or the
      `work-intake` route.
- [ ] No file this slice ships under `packs/` cites an ADR number, an
      acceptance criterion or a repository-only path. `packs/AGENTS.md`
      confines shipped pack content to portable guidance.
- [ ] No path from that derived set reaches a skill
      the pack declares as a bridge. A token scan alone does not establish
      this: a skill can invoke `jira-refresh` while containing none of those
      terms, and would pass every other check here while violating ADR-0126
      D3.
- [ ] `packs/atlassian/pack.toml` declares the pack's bridge skills as
      `[pack.metadata]` key `bridge-skills`, a list of skill names. The table
      is intentionally open, so nothing infers the key — naming it here is
      what lets a later conformance check and a consumer find the same
      declaration. This skill is not among them. That table is the
      schema's open extension table, so the declaration needs no schema
      change and no `agentbundle` release: every version that has shipped
      since the enriched pack manifest accepts arbitrary keys there. A new
      top-level table would instead fail `CAT-L006` with `additional property
      not allowed`, because the schema is otherwise closed under `pack`.
- [ ] The `docs/product/changelog.md` entry is free-standing at `##` and
      carries a `### Highlights` subsection of outcome-led bullets, because
      this slice changes what a pack consumer can do. `/now/` is a pure byte
      parser over that file, so an unwritten block is a release the public
      page never mentions.
- [ ] `packs/atlassian/pack.toml` and
      `packs/atlassian/.claude-plugin/plugin.json` carry the same bumped
      version — minor, because this slice adds a new primitive.
- [ ] The pack's eval harness covers the new skill, which `packs/AGENTS.md`
      requires of any non-cosmetic pack update.
- [ ] `.claude-plugin/marketplace.json` carries the bumped version. It
      aggregates every `packs/*/.claude-plugin/plugin.json`, so the bump
      changes it. This pack's skills are not projected into the repository's
      own `.claude/` or `.agents/` trees, so those are not the regenerated
      output to check here.
- [ ] Every generated output is regenerated by its build rather than edited,
      and re-running that build leaves a zero diff.
- [ ] `agentbundle catalogue lint --root . --deep` and
      `agentbundle catalogue verify --root .` pass.
- [ ] Every rendered reading states the moment it was taken.
- [ ] The view renders no percentile. `flow-metrics` computes them through
      `statistics.quantiles`, which needs at least two points, so it nulls
      them when `n < 2` and computes them for every larger sample. That is a
      floor, not a confidence threshold: at `n = 2` a p90 is returned as fact.
      Rendering one here would put a median over four completions in front of
      a reader.
- [ ] The view renders throughput as a count with its window, and the
      non-distributional observations — work in flight, age, blocked and since
      when, what moved — which need no sample at all.
- [ ] The view runs only when invoked and leaves no resident process.
- [ ] The installed CLI is exercised end-to-end through its documented happy
      path, and the recorded observation is **asserted against** that path,
      not merely logged: the command, its stdout, its exit code, and the
      rendering for one Epic with a recorded outcome and one without. A
      passing unit gate does not stand in for the real invocation.
      The record states where the session ended and names what was documented
      but not exercised — repeat use across two sittings, which is the
      parent's success signal and not settled by one run.

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
