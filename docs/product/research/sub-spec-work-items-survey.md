# Sub-spec work items — what they are, and how they are represented on disk

> Discipline: applied (practitioner-pattern survey)

Scope: the classes of work item that sit below a spec and a plan, how
practitioner systems name them, and what on-disk representation each gets.
Commissioned while moving this repository from a monolithic `workspace.toml`
registry to a workspace view rendered from repository state, under an explicit
constraint: **one file per defect or per TODO is overkill**.

Confidence tags follow `references/confidence-schema.md` with the applied-mode
overlay: `no peer review` is dropped as a downgrade factor, and
`survivorship bias` and `stale prior art` are added.

## 1. The item classes that actually exist

### Finding — an item enters as a claim, not as work

The strongest single finding in this survey. Every mature findings pipeline
treats a new item as **unvalidated until a human dispositions it**, and none of
them lets it enter a work queue by default.

GitLab's vulnerability model starts every scanner finding at **`Needs triage`**,
and the finding cannot be resolved until a human picks one of four reasons —
`Acceptable risk`, `False positive`, `Mitigating control`, `Used in tests`.
GitHub code scanning is the same shape with three reasons — `false positive`,
`won't fix`, `used in tests` — plus a free-text comment retained on the alert
timeline for audit. SARIF encodes this in the format itself: a
`result.suppressions[]` entry carries `kind` (`inSource` | `external`), a
`justification` string, and a `status` of `accepted` | `underReview` |
`rejected`. `underReview` is a first-class schema value. **[high]** — three
independent implementers (GitLab, GitHub, the OASIS SARIF TC) plus the standard
itself.

The consequence for this repository is direct. A `[backlog].open` entry is
accepted work by construction — there is no state in which an item exists but
has not yet been agreed to be real. Nothing represents a hypothesis awaiting
validation, which is the state a large share of agent-generated follow-ons are
actually in.

### Record — an item that is logged and will never be actioned

There is a recognised class for this, but it comes from safety engineering and
ITSM rather than from agile practice.

A **Hazard Log** is defined as a standing record of the formal decision process
about a risk: the hazard, its causes, residual-risk assessment, and an
acceptance decision with ALARP (As Low As Reasonably Practicable)
justification. A hazard may be closed as "formally ALARP" — accepted, nobody
will act further — without ever becoming a work item. UL 4600 likewise requires
logging *acceptably addressed* hazards alongside open ones. ITIL's **Known Error
Database** plays the structurally identical role: a problem with a documented
root cause and workaround, recorded precisely because it will not be fixed.
**[moderate]** — downgrade factor: `indirect domain`. The sources are
authoritative within safety and ITSM, but no source demonstrates the pattern
transferring to a software backlog.

Mainstream Scrum, SAFe and Kanban literature has **no first-class record type**
— everything defaults to a backlog item carrying a disposition. The nearest
approximations are Jira's `Won't Fix` / `Works as Designed` resolutions and
SAFe's ROAM `Accepted` state ("nothing more can be done"). **[moderate]** —
downgrade factor: `vendor documentation`; the ROAM description could not be
fetched directly and is relayed via search snippet.

There is no widely adopted noun for this class. The vocabulary splits by
domain — hazard-log entry, accepted risk, known error, won't-fix — which is
itself the finding: a repository adopting one must name it locally.

### Decision-needed — barely represented anywhere

**Architecture Decision Records are the only established artifact with a
first-class "awaiting a decision" state.** Nygard's template — still the de
facto standard — uses `Proposed` for a decision awaiting stakeholder agreement,
resolving to `Accepted`, `Rejected`, `Deprecated` or `Superseded`. Critically,
this state lives in its own artifact, **separate from the backlog**. **[high]**
— primary sources, community-maintained standard, and a convention this
repository already implements.

In ticketing and Kanban the state collapses into a generic `Blocked` column with
no semantics distinguishing "blocked on effort" from "blocked on a decision";
teams encode the difference in free-text block reasons. **[low]** — downgrade
factors: `thin sourcing`, `single practitioner`. One GitHub issue thread argues
Kanban lacks first-class waiting states for human approval gates; that is one
project's framing, not an established pattern.

Among static-analysis baselines the state does not exist at all: PHPStan,
Psalm, detekt and ESLint are binary — an item is in the baseline or it must be
fixed. **[high]** — confirmed by reading four independent tool documentations.

The one strong exception is **DefectDojo's Risk Acceptance**: a distinct
workflow object carrying a justification, a named approver, and an **expiration
date**, with automatic reactivation of the finding when the date passes. It is
not a priority field — it is a recorded decision with a forced re-review
trigger. **[high]** — primary vendor documentation.

### Debt — distinguished by authorial admission, not by content

The **Self-Admitted Technical Debt (SATD)** literature, founded by Potdar and
Shihab (2014) and still actively cited, defines debt as code the developer
*themselves* flags as incomplete, defective, temporary or sub-optimal. The
converged taxonomy is code/design, documentation, test and requirement debt.
The distinguishing test is **authorial admission, not content**: an identical
code smell is debt only if someone said so. **[high]** — founding paper plus
two recent (2024–2025) domain taxonomies, and active tooling.

Against any mechanical debt classifier: Google's own experiment found TODO
comments explained **less than 1% of the variance** in engineer-reported
technical debt. They abandoned the static signal and moved to quarterly
engineer surveys plus a named ownership framework. **[high]** — primary Google
research, corroborated secondarily. This is direct evidence that debt cannot be
derived from the artifact; it has to be human-judged.

SAFe's answer to debt-versus-feature is by **item type** — Enablers
(exploration, architecture, infrastructure, compliance) versus user-facing
Features — explicitly so non-user-facing work competes in the same backlog
without being framed as user value. Reported side effect: teams game the
framing to get work funded. **[moderate]** — downgrade factor:
`secondary summaries only`; SAFe's own glossary was not fetched directly.

### Spike, survey, manual QA — task modes, not backlog items

These are execution modes of a planned task rather than a class of deferred
item, and this repository already encodes two of them: `plan.md` records
`no stub (mode)` for goal-based and manual-QA tasks. A measurement or survey
produces a research artifact, which has its own home. **[moderate]** —
`[inference]` from repository convention plus the absence of any external
source treating spikes as backlog entries; SAFe classifies exploration as an
Enabler, which is a backlog item, so the two models disagree.

### Terminology cautions

- **Scrum "spillover"** means unfinished sprint work carried forward — a
  different sense from "follow-on". Term collision, not corroboration.
- **No established distinction** was found between "follow-on" and "follow-up"
  as relationship terms. Jira models a `Follows-from` link; no source draws a
  semantic line. **[high]** as a negative finding.
- **Google's `Nit:` / `FYI:` review prefixes** make a comment's obligation
  explicit inline — `Nit:` optional, unprefixed mandatory, `FYI:` requiring no
  action ever. A clean example of marking "this is a record, not a task" at the
  point of writing rather than by ticket type. **[high]** — primary, and a
  convention this repository already borrows.

## 2. The no-backlog position

Shape Up (Singer, 2019) refuses a backlog outright: it is "a growing pile that
gives us the feeling of always being behind", it never shrinks, and old ideas
compete with current reality even though the context that made them good has
expired. Nothing is stored — an idea is either pitched fresh at the betting
table during cool-down, or dropped. "If it's worth doing, it'll be worth
pitching again when the time is right." The two-week cool-down absorbs small
bugs and investigation work that would otherwise need entries.
**[moderate]** — downgrade factor: `single source triangulated by re-tellings`.
The primary chapter could not be fetched; three independent summaries describe
the same content, which is one source, not three.

Counter-arguments are thinly sourced but structurally sound: the model assumes
a small senior single-team organisation that can re-derive priorities every six
weeks, and has no answer for compliance-driven or externally imposed defects
that cannot wait for a pitch cycle. **[low]** — downgrade factors:
`tertiary sourcing`, `survivorship bias`. The frameworks appear to specialise
by organisation size and regulatory load rather than one being correct.

## 3. On-disk representations

### One file per item — the pattern that mostly died

Every first-generation distributed tracker used file-per-item or
directory-per-item: ditz (`bugs/issue-<uuid>.yaml`), bugs-everywhere, TicGit,
git-case, SD, DisTract. As of the 2011–2013 retrospectives, ditz is
abandonware and TicGit's own wiki calls itself dead. **[moderate]** —
downgrade factor: `stale prior art`; the domain has not materially moved, but
current liveness of the survivors was not re-verified.

**The cause of death was not the storage shape.** Three independent
retrospectives converge on the same root cause: these tools were built by and
for developers and excluded the non-developer participants a real tracker needs
— reporters, PMs, translators, designers. **[high]** — three genuinely
independent authors.

This matters for the repository in question, because that failure mode does not
bind: the participants here are agents and one maintainer, not a mixed
stakeholder population. The classic argument against in-repo tracking is
therefore weak evidence in this setting, and should not be cited as if it
were strong.

A secondary, storage-shaped failure *was* reported directly by a practitioner:
filing bugs to the wrong branch and losing them, plus commit history polluted
by UUID-laden metadata churn. **[moderate]** — single practitioner report.

Modern continuations survive at small scale: git-issue
(`.gitissues/issues/{ID}/` with `meta.yaml` + `description.md`), SIT, and
tissue (gemtext files, stateless web UI with Xapian search, running a real
production tracker). **[high]** — primary project documentation.

### One file per scope — the pattern that is alive

The Linux kernel runs exactly the shape proposed here: per-driver `TODO` files
under `drivers/staging/<driver>/`, and per-subsystem lists such as
`Documentation/gpu/todo.rst`. These are coarse, one-file-per-scope,
hand-maintained prose lists of pending work plus a contact list — not
one-file-per-task. They are not rendered into a dashboard; they are read as
documentation or compiled into the Sphinx docs. **[high]** — primary kernel
documentation, and current practice rather than history.

This is the closest available precedent for a per-area work-item page, and it
has run at kernel scale for over a decade. Its known weakness is that nothing
renders or aggregates them, so no one sees the whole picture without looking.

### Append-only logs — the conflict-free family

git-bug (`refs/bugs/*`), Fossil tickets, and Radicle Collaborative Objects all
store an item as an append-only operation log rather than a mutable file.
Concurrent edits merge as a union of the log rather than by three-way text
merge, so conflicts are structurally impossible. State is computed at read
time, so there is no index to go stale. **[high]** — primary documentation for
all three; all alive.

The cost is that the store is not human-readable without the tool.

### Item identity — three strategies, all with a named failure

| Strategy | Example | Survives | Breaks on |
|---|---|---|---|
| Content/context hash | SARIF `partialFingerprints`, versioned keys | line shift, some edits | rename across files |
| Structural name | detekt `RuleID:Signature`, SpotBugs XML `Match` | line shift | rename of the class or method |
| Coarse bucket count | ESLint `eslint-suppressions.json` — file + rule + bare count | line shift and motion within the file | loses per-instance precision; over/under-suppresses when counts drift |
| Minted external ID | `TODO(crbug.com/#####)`, issue URL written back into the comment | everything | nothing — identity is not in the code |
| Content-addressed ref | git-bug, Radicle, Fossil | file moves and deletes | — identity was never the path |

**[high]** — all five confirmed against primary tool or standards documentation.

Two results deserve emphasis. SARIF versions its fingerprint *keys*
(`prohibitedWordHash` vs `prohibitedWordHash/v1`) so the hashing algorithm can
evolve without invalidating old baselines. And Chromium mandates
`TODO(crbug.com/#####)` rather than `TODO(username)` specifically because a
username goes stale when people change teams while a bug ID does not — identity
is deliberately outsourced, and the comment is only a pointer. **[high]**.

No tool surfaced in this survey uses a content hash as TODO identity. The two
strategies that work in practice are *mint an ID and write it back*, or *do not
claim per-item identity at all*. **[moderate]** — downgrade factor:
`absence of evidence`; a tool may exist that was not surfaced.

### Inline marker versus sidecar file

Every source discussing both reports the same trade-off. **[high]** — four
independent tool ecosystems.

Inline markers (`# noqa`, `// nosemgrep`, `@ts-ignore`, `NOLINT`) stay attached
to the exact line and travel with it through refactors, but they scatter the
accepted-debt ledger across the codebase, are invisible to any central audit,
and can silently detach when a code-generation or templating step shifts line
numbers between source and compiled representations.

Sidecar baselines (PHPStan, Psalm, detekt, ESLint bulk suppressions) centralise
the ledger for audit and enable the **ratchet** — a count that may shrink but
never grow, enforced in CI. They decay differently: coarser granularity
survives line shift but masks which specific new violation broke the count.

### Expiry — three mechanisms, and one that does not exist

1. **Correctness-triggered.** `@ts-expect-error` becomes an error itself
   ("Unused '@ts-expect-error' directive") the moment the line it guards stops
   erroring. mypy's `--warn-unused-ignores` does the same. The suppression
   self-invalidates when its reason disappears, with no calendar and no
   external ratchet. **[high]** — primary vendor docs for both.
2. **Calendar with forced re-review.** DefectDojo Risk Acceptance reopens the
   finding at its expiration date. `eslint-plugin-unicorn`'s
   `expiring-todo-comments` fails the build once a `// TODO [2026-12-01]` date
   passes. Feature-flag hygiene tooling fails CI on flags older than a
   threshold. **[high]**.
3. **The ratchet**, which substitutes for expiry in the static-analysis space.

**No mainstream static-analysis baseline carries a built-in calendar expiry** —
not PHPStan, Psalm, detekt, or SARIF. **[high]** — this was chased
specifically and the hypothesis is refuted for those tools.

Mechanism 1 is the most valuable result in this survey for the question at
hand, because it makes staleness *detectable* rather than relying on anyone
remembering to look.

### Regenerating a view without destroying human input

Renovate's Dependency Dashboard is the load-bearing precedent: a single issue
fully rewritten on every run, over scanned repository and registry state, that
nonetheless preserves human decisions. Two distinct mechanisms, both in
`lib/workers/repository/dependency-dashboard.ts`. **[high]** — primary source
code plus vendor documentation.

1. **Parse back, re-apply by key.** The rendered body is never treated as the
   state store. Before overwriting, Renovate parses the previous body with a
   regex keyed on an HTML-comment token — `- [x] <!--type-branch=name-->` —
   recovering which boxes a human checked into an in-memory map keyed by
   **branch name**, independent of row position. After rendering fresh content,
   it re-applies each remembered check by key.
2. **A slot the generator never touches.** `dependencyDashboardHeader` and
   `dependencyDashboardFooter` are injected verbatim. The scanner owns only the
   middle.

Machine-derived and human-entered content are distinguished by **spatial
separation of ownership zones**, not by per-row tagging. No source surfaced a
tagged interleaved list. **[moderate]** — downgrade factor:
`single implementation`; Renovate is one tool, and Dependabot does *not* mirror
this pattern — it opens individual PRs and has no equivalent dashboard.

GitLab's changelog practice is the adjacent case: many small YAML files
compiled into one rendered Markdown file at release, after which the source
files are deleted. The rendered artifact is disposable and never hand-edited.
**[high]** — primary.

### Why structured inline tags were rejected

PEP 350 proposed exactly the rich structured-comment scheme that a per-item
inline representation would need — `# FIXME: Loop should be finite. <MDE,CLE
d:14w p:2>` with assignee, due date, priority and tracker fields. **It was
rejected.** The PEP records the objections: it duplicates what a tracker
already does; it clutters source; the fields do not self-verify so comments go
stale anyway; and the authoring burden discourages adoption. **[high]** —
primary; the PEP documents its own rejection.

The rejection reasoning matters more than the outcome: it was not "structured
tags are impossible" but "the authoring cost and residual staleness did not
beat linking to a tracker" — consistent with what actually won, Chromium's
minimal `TODO(bug-id)`.

### Empirical decay of comment-scraped registries

- Mean time from TODO introduction to removal: **166.31 days**.
- **46.7%** of TODO comments are low-quality — ambiguous, uninformative, or
  useless to a reader.
- Self-admitted technical debt comments are removed only **26.3–63.5%** of the
  time.
- A separate research line exists solely to *detect and remove obsolete TODOs*,
  because manual removal does not happen reliably.

**[high]** — peer-reviewed, ACM TOSEM and arXiv, recent.

## Known unknowns

- **Known-unknown:** whether a per-area work-item page degrades the way a
  monolithic registry does, at this repository's item volume. Would be closed
  by: instrumenting merge-conflict rate and staleness rate on the area pages
  for one quarter after migration. No source benchmarked a backlog registry
  against a derived view at comparable scale — this is the single largest gap
  relative to the question asked.
- **Known-unknown:** the current (2026) liveness of Bugs Everywhere and SIT.
  Would be closed by: checking their repositories directly.
- **Known-unknown:** how GitHub maps alert dismissal onto SARIF `baselineState`
  and `suppressions` internally. Would be closed by: GitHub publishing the
  storage model. The UI behaviour is documented; the plumbing is not.
- **Unknowable from available evidence:** whether an agent-generated follow-on
  decays faster or slower than a human-written TODO. The TODO decay figures
  above are measured on human-authored comments in human-paced repositories.
  No corpus of agent-generated backlog items has been studied, because the
  practice is younger than the measurement literature.
- **Unknowable as posed:** whether the distributed-tracker adoption failure
  would recur here. Its established cause — exclusion of non-developer
  participants — does not apply to an agent-and-maintainer population, so the
  evidence does not transfer in either direction.

## Repository inventory

### The pattern already exists in prototype

`docs/product/findings/` holds two grouped Markdown table registers, each with
the same six columns — `Problem`, `Source`, `Surfaced by`, `Date`, `Priority`,
`Disposition`:

- `roadmap-intents.md` — future features and improvements, 4 rows.
- `rfc-candidates.md` — recurring patterns, gaps and design questions needing
  community input, 8 rows.

Both already carry an explicit arrival and departure contract in their own
prose ("when an owner explicitly decides to record an out-of-scope finding
that looks like a future feature"; "when an item is scoped into a brief and
spec, update `Disposition` to `→ spec/<slug>`"). Both are **already scan
inputs**: `workspace-status` reads and prints them, `rfc-status` counts their
rows. **[high]** — direct file reads.

This is grouped-register-with-disposition, keyed by destination rather than by
area, working today. It is the strongest argument against inventing a new
format: the repository solved this for two narrow classes and never
generalised it.

A third instance exists at delivery scope: three `docs/specs/*/notes/
follow-ons.md` files use H2 slug headings with owner fields and prose evidence.
Their lifecycle ownership is inconsistent — an older file says status lives in
`workspace.toml`, while current `work-intake` says state changes in the owning
artifact and the workspace entry only indexes it. **[high]**.

### Class-by-class homes and gaps

| Class | Durable home today | Gap once `workspace.toml` stops being the registry |
|---|---|---|
| Follow-on feature | spec `Follow-ons`; `roadmap-intents.md`; `rfc-candidates.md` | **None** — already grouped and scan-friendly. The missing piece is consistent status ownership across the three, not a new format |
| Deferral | spec `Follow-ons`; `review-verdict.v1.deferrals[]`; `notes/follow-ons.md`; historical `(deferred: slug)` markers | Usable; new AC deferral markers are forbidden, and a follow-on must point at a stable artifact |
| Finding | `review-verdict.v1.findings[]`; the two product registers once promoted | **No universal committed home.** Verdict persistence is normally the PR or handoff |
| Hazard / standing exception | Bandit, Semgrep, Ruff, mypy directives; CodeQL paths; Gitleaks fingerprints; CI disposition tables; `_NO_RUNNER`; `blind_spots[]` | No unified register, but the mechanism-specific homes are more enforceable than a generic list would be |
| Decision-needed | spec `Assumptions` with `settled by`; `Durable Outputs` closeout blockers; `rfc-candidates.md` | **A small decision with no owning spec and no RFC-scale question has no home** |
| Defect | **A live route.** `work-intake`'s classify table sends cited defect evidence to `bug-fix`, and `intake_router.py` materialises a `defect` artifact and registers a `backlog.open` entry | The route exists; what is absent is a step that reaches it from a captured item. **Correction, 2026-09-19:** an earlier revision of this table said there was no registry-independent home, citing a path found only in a test corpus. That was read from fixtures rather than from the live router, and it was wrong |
| Debt | Described as a defect, a roadmap intent, or a TODO pointer | **No dedicated type.** Whether it needs one is answered below: its required field set does not differ from an improvement's, so it is a provenance marker rather than a kind |

**[high]** — every row verified against a named file.

### Adjacent existing mechanisms

- `plan.md` records `no stub (mode)` for goal-based and manual-QA tasks, so
  those execution modes already have a home and are not backlog items.
- `work-loop` splits light from full mode on risk triggers — the same
  distinction as mechanical-versus-shaping, applied when work starts rather
  than when an item is raised.
- `workspace.toml` comments adjudicate mechanicality by hand ("Not mechanical,
  despite the note file naming the exact two-line edit"), a human judgement
  stored where nothing can read it.
- `docs/knowledge/` topics are learnings, not work. The authority boundary is
  explicit: a topic may carry imperative advice but **cannot own an open
  obligation**, which stays with briefs, RFCs, ADRs, specs and plans.

**[high]** — direct file reads.

### What this implies

Three holes survive the migration, and only three: a defect and debt
representation independent of `workspace.toml`, a small decision outside any
spec, and committed persistence for ordinary review findings. Everything else
already has a grouped, scannable home. The work is generalising the
`docs/product/findings/` register — adding a triage state it lacks and
re-keying it by area — not designing a new item format.


## Refuted approaches

Negative results, kept because they are the expensive half to re-derive and the
easy half to re-propose. Each was tested and failed; none is a matter of taste.

### Path proximity cannot find a covering artifact

**Proposed:** match the scope paths a captured observation carries against the
artifact corpus, to surface artifacts that may already cover the item.

**Refuted by probe**, one command over this repository's own backlog:

```
python3 -c "
import tomllib,collections,os
o=tomllib.load(open('workspace.toml','rb'))['backlog']['open']
b=collections.Counter(os.path.dirname(x['path']) for x in o if x.get('path'))
n=sum(b.values()); top=b.most_common(1)[0]
print(n,'entries;',len(b),'directories; largest',top[1],'in',top[0],
      '; singletons',sum(1 for v in b.values() if v==1))"
```

It reports a corpus where most entries sit in one directory and most directories
hold exactly one entry, so a match returns most of the corpus or none of it.
Run on two days a fortnight apart it gave different counts and the same shape,
which is why the command is recorded rather than the numbers.

**Why, beyond this corpus:** an artifact's path does not encode what it covers.

**What was also wrong about the first explanation:** the failure was initially
attributed to code paths and documentation paths being separate namespaces. That
is false — `_validate_project_scope` accepts any repository-relative path, and
documentation paths are the most common root in the live corpus. A wrong
explanation for a right result would have sent the next probe in the wrong
direction.

### A prevalence threshold does not test acceptability

**Proposed:** kill a route that refuses governance items when the pack is
absent, if governance items exceed a third of captures.

**Refuted on reasoning.** Prevalence does not measure tolerance: a rare
permanently stuck item may be intolerable, and a common hold may be fine where
installing the pack is routine. The threshold was also anchored near a figure
already observed in a different population, which is a fitted line rather than
a derived one.

### Recall without precision is a control that cannot fail

**Proposed:** measure a coverage check by whether the covering artifact appears
among the surfaced candidates.

**Refuted on reasoning.** Returning the whole corpus satisfies it while
discriminating nothing. Capping the list length does not fix it either — a
short list of consistently wrong entries still costs a reader more than it
saves. Precision is about what is in the list, not how long it is.

### A reviewer-scoped rule is not routing authority

**Proposed:** settle whether a core classifier may reach an optional pack by
analogy to how the loop handles an absent reviewer pack.

**Refuted on scope.** That rule governs fired reviewers. All of core's
optional-pack references are reviewer-related, and none creates an artifact, so
the analogy establishes nothing about routing.

### Not every decision is a decision record

**Proposed:** route a route's absent-pack degradation behaviour to a decision
record, on the test that the decision is the deliverable.

**Refuted on threshold.** That test alone admits almost any design choice. A
question that is not architecturally significant, not expensive to reverse, and
does not constrain work beyond the feature that raised it is spec content
however cleanly it fits the definition. The kind needs a threshold, not just a
definition — recorded as an open question on the capture intent.
