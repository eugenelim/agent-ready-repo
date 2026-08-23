# RFC-0095: Changelog entry obligation and the release publication path

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** @eugenelim
- **Date opened:** 2026-08-20
- **Date closed:** 2026-08-20
- **Decision weight:** standard
- **Related:** RFC-0090 (change sizing — the written-but-nonbinding diagnosis this
  RFC reuses); `docs/CONVENTIONS.md`; `packs/core/seeds/docs/CONVENTIONS.md`;
  `docs/product/changelog.md`; `packs/core/seeds/docs/product/changelog.md`;
  `.github/pull_request_template.md`; `tools/repo/check_release_impact.py`;
  `docs/specs/site-now-surface/spec.md`

## Reviewer brief

| Item | Summary |
| --- | --- |
| Decision | An entry is owed when a PR bumps a released artifact's version — not when a maintainer can see a difference; and a section carrying a version and a date is released, so it is written free-standing, never nested under `[Unreleased]`. |
| Recommended outcome | Accept. Align the conventions to wording this repository already ships to adopters, and delete one asserted CI gate that does not exist. |
| Change if accepted | Edit the core conventions seed and regenerate its projection; align the seed changelog and the PR template to the same trigger; correct the live changelog's maintenance header; give the pack release pipeline the `Highlights` decision; add a ratchet test enforcing D3; release core 2.10.4. |
| Affected surface | `docs/CONVENTIONS.md` (generated projection) and its canonical seed; `packs/core/seeds/docs/product/changelog.md` (ships to adopters); `.github/pull_request_template.md` (repo-only); `docs/product/changelog.md` (live file, not a projection); `tests/roster/test_workspace_status_projection.py` (a widened correspondence check plus a new D3 ratchet); the generated `web/src/lib/now-highlights.generated.json`; `workspace.toml` (one backlog entry); `packs/AGENTS.local.md` (maintainer-only, unexported — the pack release pipeline); core's four version sites. |
| Stakes | Reversible. Wording, one deletion, and one new test; no new script, workflow, or CI gate. |
| Review focus | Whether the released-artifact test is the right trigger; whether the per-package tier deserves its own sentence; and whether the D3 ratchet is the right enforcement given the migration is deferred. |
| Not in scope | Building the CI gate the changelog currently claims; retro-adding entries to past PRs; promoting the 59 already-nested entries (registered follow-on); any other `CONVENTIONS.md` section. |

## The ask

**Accept the released-artifact test as the single trigger for a changelog entry,
and stop nesting released entries inside `[Unreleased]`.** Five decisions
follow. None adds a script, workflow, or CI gate; one adds a test.

Why now: the repository's own conventions carry the vague form of a rule that
the copy it *ships to adopters* already states more precisely. A peer session
correctly flagged a missing changelog entry for PR #1068 by reading the
conventions literally — the reading was sound and the conclusion was wrong,
which means the text is wrong. Separately, the public `/now/` page has been
showing a single four-day-stale release, and the cause is measurable.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | What triggers a changelog entry? | An entry is required in the PR that bumps a released artifact's version — a pack, or a published package. Repository tooling that ships in no release is exempt. | Mechanically checkable, satisfied by all 144 existing entries, and close to the seed's own wording. "User-visible" never says visible to whom. | RFC acceptance | Approve the trigger and the exemption. |
| D2 | One obligation or two? | Two, split by file rather than by scoping phrase: every released artifact gets an entry in `docs/product/changelog.md`; a published package *additionally* updates its own `CHANGELOG.md`. | The second tier is real — 10 of the last 10 package-changelog commits also touched the aggregate — and `CONVENTIONS.md` referenced it in exactly one place, ambiguously. | RFC acceptance | Approve two precisely-scoped rules replacing two overlapping ones. |
| D3 | Does a released entry belong under `[Unreleased]`? | No. A section carrying a version *and* a date is released by definition and is written free-standing at `##`. `[Unreleased]` holds only work with no version yet. | 59 entries are currently nested there and can never publish. This is less work per PR, not more. | RFC acceptance | Approve the structural rule and its ratchet; the one-time promotion is follow-on. |
| D4 | Is a `Highlights` block obliged, and who decides? | Obliged when the release changes what a consumer can do — judged by nature, not by semver level. The decision belongs to the pack release pipeline in `packs/AGENTS.local.md`, which now requires it on every pack release; a recorded *none* with its reason is a valid answer. | `Highlights` is the only content source for `/now/`, no model runs in the build, and nothing prompted for one — so 1 of 144 entries has one. An obligation with no owner is the failure this RFC diagnoses. | RFC acceptance | Approve the obligation, its owner, and the recorded-*none* escape hatch. |
| D5 | Should the changelog keep asserting a CI gate? | No. Delete the sentence. Do not build the gate. | No such gate exists in `.github/workflows/`. A document asserting absent CI behaviour teaches readers to distrust it, and building it would impose per-PR ceremony nobody asked for. | Settled before drafting | Confirm deletion over implementation. |

## Problem & goals

Four findings sit in three documents. They share one shape: an obligation is
written down, nothing binds it, and readers either over-comply or ignore it.
RFC-0090 named this pattern in the same document while sizing changes — "the
exact written-but-nonbinding failure this RFC diagnoses" (RFC-0090, D2). This is
the same disease in four more corners.

**1. "User-visible" never says visible to whom.** `docs/CONVENTIONS.md` required
`changelog.md` to be "Updated in the same PR as any user-visible behavior
change." Read literally, that binds far more than intended. PR #1068 added four
CLI subcommands to `tools/repo/worktree_hygiene.py` and bumped its `scan --json`
`SCHEMA_VERSION` from 1 to 2; anyone running `make worktree-doctor` sees
different output, so a peer flagged the missing entry. The reading was correct.
The operative rule — visible to a *consumer of a release*, not to a maintainer
running repository tooling — was never stated. Worse, a literal reader has no
heading to write under, and is pushed toward inventing a `[repo]` or `[tools]`
section that has never existed on the shipped history.

**2. A second obligation, scoped differently, naming a bare path.** The same
document also said "Public-interface changes must be noted in `CHANGELOG.md`."
There is no root `CHANGELOG.md`. The path is not meaningless, though: it
resolves per-package, at `packages/agentbundle/CHANGELOG.md` (1,743 lines) and
`packages/credbroker/CHANGELOG.md` (143 lines). That tier is real and
consistently maintained, and this sentence was the *only* reference to it
anywhere in `CONVENTIONS.md`. So the defect is not a typo to correct but two
overlapping rules with two scoping phrases, one of which under-specifies a
genuine second obligation.

**3. The changelog asserted a CI gate that does not exist.** Its header claimed
"CI will warn (configurable: block) when a PR touches code that changes
user-visible behavior but does not touch this file." No workflow implements
this. `pages.yml` references the file only as a path trigger and for
release-anchor correspondence. The nearest mechanism,
`tools/repo/check_release_impact.py`, fires only when a release-impacting path
changes and then accepts an entry **or** a version bump **or** a no-release
declaration — and `tools/repo/` is on its explicit `NON_IMPACTING_PREFIXES`
list, as is `packs/`.

**4. Released entries are nested where they can never publish.** This surfaced
while verifying the above and is the most consequential finding. The `/now/`
machinery is sound — running `project_now_highlights` against the live file
returns a correct projection. The failure is authoring, in two compounding
layers:

- **59 versioned entries are nested under a `## [Unreleased]` heading.** Each
  carries a real version and a real date, and their versions are already live in
  `pack.toml` — `[core][2.10.2]` among them. The projection excludes them by
  enclosing structure. Critically, this is a **permanent** loss, not a dated
  one: `docs/specs/site-now-surface/spec.md` is explicit that "the projection
  applies no date window at all", and `launch_window` in `tools/build-site.py`
  is called only from tests, never by the generator. So a nested entry does not
  age out of `/now/` — it never appears, and nothing will ever move it out. The
  changelog's own header described a promotion step ("Move the entry out of
  `[Unreleased]` at release time") that no one performs and no gate checks.
- **`Highlights` is carried by 1 of 144 entries** (0.7%). It is the projection's
  only content source, so `/now/` currently renders exactly one release —
  `[governance-extras][0.9.7]`, dated 2026-08-16 — and has done since.

The "two heading eras" that make this file hazardous to append to are not a
historical accident: they *are* this finding. 85 entries are free-standing `##`
and publishable; 59 are nested and are not. The seed prescribes the
free-standing form and always has, so this is drift in the self-hosted copy
rather than an open question about which form is right.

**Goals.** State one trigger for an entry, in one place, that a contributor can
apply without judgement and a reviewer can check. Keep the wording correct for
adopters as well as for this repository, since the seed ships. Make D3 bind
mechanically rather than adding a fifth unenforced rule.

**Non-goals.** Building the promised CI gate (D5 rejects it deliberately, not
for lack of time). Requiring narrative prose on every patch release. Revisiting
the `/now/` projection's contract, which is `spec/site-now-surface`'s decision
and is working as specified. Changing `check_release_impact.py`, which is
correct for what it guards.

## Proposal

### D1 — the released-artifact test

`docs/CONVENTIONS.md` § 5b replaces the "any user-visible behavior change"
clause with the released-artifact test. An entry is owed when the PR bumps a
released artifact's version; the artifact set is *every pack* plus the two
published packages. Repository tooling that ships in no release — `tools/`, CI
workflows, the `Makefile` — is exempt, and the exemption is stated rather than
left to inference.

`contracts` is a pack (`packs/contracts/` exists and has shipped a
`## [contracts]` entry), so the non-pack members of the artifact set are
`agentbundle` and `credbroker` and no others.

Two existing headings release several artifacts at once — `[core][2.7.4] and
[architect][0.14.5]`, and `[atlassian][0.8.4], [linear][0.2.3],
[github][0.1.4]` — and `tools/build-site.py`'s parser handles that form
deliberately. The wording is therefore "one section per release, naming every
artifact that release covers", not one section per artifact.

The same trigger is written into `.github/pull_request_template.md`, which
carried the old "any user-visible behavior change" phrasing verbatim. Leaving it
would have reproduced PR #1068's misfire from the highest-traffic surface in the
repository while `CONVENTIONS.md` said something else.

### D2 — two tiers, split by file

The § 5b bullet owns the aggregate obligation, the section shape *including its
heading level*, and the per-package path. The PR-hygiene sentence keeps a short,
actionable reminder, cross-references § 5b, and states the package duty
conditionally so it reads correctly for an adopter whose repository *is* a single
published package:

> CI must be green. Specs must match implementation. A released-artifact version
> bump carries its changelog entry (see *`docs/product/` — for maintainers*); if
> the repository publishes packages separately, each also updates its own
> `CHANGELOG.md`.

### D3 — released sections are free-standing, and a ratchet enforces it

§ 5b and both changelog headers state the rule with the heading level made
explicit — `## [<artifact>][<version>] — YYYY-MM-DD` — because the level is the
whole defect. An earlier draft of this RFC stated the shape *without* the `##`
marker, which would have shipped adopters the corrected instruction minus the
one token that matters.

D3 is not left as prose. `tests/roster/test_workspace_status_projection.py` gains
`test_no_new_release_is_nested_under_unreleased`, a **ratchet** pinned at the
current 59. A new release written as `### [artifact][version]` under
`[Unreleased]` takes the count to 60 and fails, with a message naming the fix.
The count may only ever decrease. Both directions were mutation-checked: adding
a nested release fails it, rewriting this RFC's own entry as nested fails it, and
the unmodified tree passes.

The neighbouring correspondence check (`_product_release_heading_version`)
deliberately accepts either heading level. A `##`-only match cannot work yet
because some artifacts' *current* release is itself nested — `agentbundle`
0.38.5 is, so a strict match reads a stale free-standing 0.30.1. Version
correspondence and D3 compliance are therefore checked by two assertions rather
than conflated into one.

**The one-time promotion of the 59 nested entries is deliberately follow-on
work, not part of this PR**, and is registered in `workspace.toml
[backlog].open` as `changelog-promote-marooned-entries` with `source = "rfc/0095
D3"`. It was scoped as a Tier 1 reproducible sweep under RFC-0090's bundled-fix
rule and then measured, and it does not qualify. `[Unreleased]` holds two
different things, interleaved: versioned entries that are nested, and bare
`### Added` / `### Fixed` / `### Changed` / `### Removed` sections that are
genuinely unreleased and correctly placed. There are **48** of the latter,
spread across **three** separate `## [Unreleased]` regions (12, 5 and 31). They
sit at the same heading level as the entries, so a uniform level-shift would
graft them onto whichever versioned entry precedes them — a bare `### Fixed`
describing `agentbundle pack evals run` sits directly below the
`[atlassian][0.9.0]` entry, and promoting mechanically would republish an
agentbundle fix under atlassian's heading.

Separating the two needs per-section judgement about which artifact each
orphaned block belongs to, and re-ordering rather than re-levelling. That is a
data migration with its own verification burden, in a 4,500-line file. It gets
its own change, where a botched promotion cannot take the wording decisions down
with it. That work also restores Keep a Changelog ordering, with `[Unreleased]`
first; until it lands, this release's entry sits above `[Unreleased]` so that it
is the newest `core` heading the correspondence check finds.

### D4 — `Highlights` obligation

An entry carries a `Highlights` subsection when the release changes what a
consumer can do. The test is the *nature* of the change, not its semver level: a
patch that changes an adopter's obligations earns one, and a minor that only
moves code does not. An earlier draft of this decision said "an internal,
mechanical, or patch release carries none", which conflated those two axes and
would have told the next author to skip a consumer-facing patch.

**The decision has an owner, because an unowned obligation is this RFC's own
diagnosis.** `packs/AGENTS.local.md` — the maintainer-only instruction surface
that any agent editing under `packs/` reads, and which already owned the pack
release pipeline — gains the step. On every pack release the agent reads the
diff and its verification evidence, answers whether a consumer of the pack can
now do something new, and either drafts the outcome-led bullets or records the
*none* verdict and its reason in the PR's *What did you not change that you
considered?* answer. A silent omission is no longer an available outcome.

That placement is deliberate on two counts. It does not touch `work-loop`:
pack-release concerns do not belong in core's generic repository-change loop,
which ships to adopters who release no packs. And `packs/AGENTS.local.md` is
maintainer-only and unexported, so this mechanism carries no adopter-facing
contract change and no pack version bump.

The decision stays at authoring time, never in the build.
`docs/specs/site-now-surface/spec.md` is Shipped with a checked criterion that
"no model or nondeterministic editorial operation runs in CI, release
automation, or site generation", and the adjacent criterion explicitly permits
"AI-assisted drafting from the implementation diff and verification evidence"
under ordinary PR review. So the agent that wrote the diff decides — which is
also the only party that knows — and `/now/` stays a pure function of the file's
bytes.

### D5 — delete the asserted gate

The sentence is deleted from `docs/product/changelog.md`. Nothing replaces it.
`check_release_impact.py` remains the only mechanical enforcement of release
impact, and the header no longer describes CI behaviour at all.

### Where this lands

The false sentence existed **only** in this repository's live
`docs/product/changelog.md` — zero occurrences in the seed at
`packs/core/seeds/docs/product/changelog.md`, which is a 65-line starter template
and a different file with a different hash. So D5 needs no seed edit and has no
adopter impact.

D1, D2 and D3 are the opposite: `docs/CONVENTIONS.md` is a generated projection,
byte-identical to its seed. The seed is edited and the projection regenerated; a
direct edit to the projection would be reverted by the next `make build-self`.
The seed changelog's own maintenance header is corrected in the same pass,
because its trigger disagreed with § 5b — it said "bumps `pack.toml`", covering
packs only, with no published packages and no exemption clause. Shipping two
adopter-facing documents with two different triggers is the defect this RFC
exists to remove.

Because the seed ships to adopters, D1–D3 are an adopter-facing contract change,
which under D1's own rule obliges a `[core]` entry and a version bump. Core is
`2.10.3` on `main` (RFC-0094 released it), so this takes **2.10.4** across all
four places that hold it: `packs/core/pack.toml`,
`packs/core/.claude-plugin/plugin.json`, and two assertions in
`tests/roster/test_security_checklists_okf_projection.py`. The fix is
self-obligating, which is a useful proof that the rule works.

## Options considered

Only D1 and D2 had genuinely contested option spaces; D3, D4 and D5 each had a
dominant answer recorded in the table above.

**D1 — axis: what scope of change obliges an entry.**

| Option | Trade-off |
| --- | --- |
| Do nothing — keep "any user-visible behavior change" | Zero cost, but it has already misfired once, over-binds on a literal read, and leaves a literal reader with no heading to write under. |
| **Released-artifact test (recommended)** | Mechanically checkable; satisfied by all 144 existing entries. Cost: says nothing about a maintainer-visible change, which is the intent. |
| "Consumer-visible behaviour" prose test | Narrower than before, but still a judgement call with no check and no stated exemption — it restates the ambiguity in better words. |

**D2 — axis: how many rules survive.**

| Option | Trade-off |
| --- | --- |
| Keep both, fix the path to `docs/product/changelog.md` | Cheapest edit, but leaves two rules with two scoping phrases — the defect itself. |
| Delete the clause as a duplicate | Smallest surface, but erases the only written reference to the per-package tier, which 10 of 10 recent package commits observe. Rejected once the tier was confirmed real. |
| **Two tiers, split by file (recommended)** | Two sentences to keep in sync, but each states one thing about one file, and the actionable reminder stays in the PR checklist where it is what people forget. |

## Risks & what would make this wrong

**The released-artifact test could under-bind.** A change that alters
maintainer-facing tooling behaviour now provably needs no entry. That is the
intent, and `git log` remains the record for tooling changes — but if this
repository later ships `tools/` to anyone, the test silently stops matching the
artifact set. The mitigation is that the trigger is phrased against *released
artifacts* rather than against a path list, so it follows the artifact set
rather than needing an edit.

**D4 still rests on a judgement, and now names who makes it.** "Changes what a
consumer can do" is not mechanically decidable, so the pipeline step obliges the
call and its recording rather than guaranteeing the answer. If the judgement
drifts permissive, `/now/` fills with internal noise; if it drifts strict, the
page stays near-empty. What changed is that a *silent* omission is no longer
available: a *none* verdict has to be written down with its reason, which makes
the drift visible in review instead of invisible in an empty page. There is
deliberately no gate, for the same reason D5 declines to build one — and a gate
is impossible here anyway without a model in CI, which a Shipped spec forbids.

This RFC's own release is the first exercise of that step, and it is a fair test
because the release is *only* prose: core 2.10.4 ships two edits, to § 5b and to
the shipped changelog template's maintenance header. Running the question against
the diff — can a consumer of the pack now do something they could not? — the
answer is yes: an adopter now has a decidable rule for when an entry is owed,
where before they had "any user-visible behavior change" and no heading to write
under. Core's product *is* its prose, so a prose change is a product change. A
reviewer who reads that as noise should say so, because it sets the precedent.

**The trigger touches four shipped documents.** § 5b, the seed changelog header,
the live changelog header and the PR template all speak to it. This RFC reduces
that to one statement of *when* an entry is owed (§ 5b) plus file-format rules
elsewhere, and the live header now cross-references § 5b rather than restating
the trigger. The seed changelog necessarily repeats the shape, so that pair must
move together.

**D3 leaves 59 entries unpublished until the migration lands.** Accepting the
rule does not refill `/now/`. That is a deliberate trade: the promotion needs
semantic judgement rather than a level-shift, and shipping it half-verified
alongside a wording change would risk republishing entries under the wrong
artifact. The ratchet stops the backlog growing in the meantime, and the
follow-on is registered rather than assumed.

**What would make D3 wrong:** if `[Unreleased]` were genuinely being used as a
staging area — entries written at merge time and promoted in a later release
commit — then the rule pre-empts a real workflow. The evidence says otherwise:
the nested entries carry final versions and dates, their versions are already
live in `pack.toml`, and no promotion commit exists in the file's history.

## Evidence & prior art

- `packs/core/seeds/docs/product/changelog.md` — supplies the section *shape*
  (`## [pack-name][version] — YYYY-MM-DD`, free-standing) and the write-time
  rationale ("You know the version at write time because you are setting it"),
  which D1 adopts. Its *trigger* was narrower than D1's — a `pack.toml` bump,
  with no published packages and no exemption — so D1's artifact set and
  exemption are new here, not merely restated. The seed carries no
  `[Unreleased]` section at all, so it gives adopters nothing to drift from.
- `docs/product/changelog.md` — 144 dated release entries; every
  heading names a pack or one of `agentbundle`/`credbroker`. 85 free-standing,
  59 nested under `[Unreleased]`. 1 carries `Highlights`.
- `docs/specs/site-now-surface/spec.md` — "The projection applies no date window
  at all… A reader expecting a seven-day filter in the projection will not find
  one, and should not add one." `NOW_WINDOW_DAYS`/`launch_window` in
  `tools/build-site.py` are referenced only by `tools/test_build_site_routing.py`,
  and `web/src/pages/now/index.astro` renders the projection unfiltered. A nested
  entry therefore never publishes, rather than ageing out.
- `b37055ad` (3,789 insertions, the same worktree-hygiene tool), `fe26b042`
  (tools + docs-site) and `f9ddf0f6`/PR #1068 (`SCHEMA_VERSION` 1→2, four new
  subcommands) each shipped maintainer-visible tooling change with **no**
  changelog entry. Precedent is unambiguous.
- No `[repo]` or `[tools]` heading has ever existed on the shipped history. Three
  `[repo]` sections were authored once, in `a66a8878d`, which is not an ancestor
  of `HEAD` and is contained by no branch — the heading was tried and never
  landed.
- `tools/repo/check_release_impact.py` — `tools/repo/` and `packs/` are both on
  `NON_IMPACTING_PREFIXES`; the gate accepts an entry **or** a version bump **or**
  a no-release declaration, and its docstring describes its trigger paths as "a
  public interface change", the same phrase as the defective sentence.
- `.github/workflows/` — no workflow implements the asserted user-visible-behaviour
  gate.
- RFC-0090, D2 — the "written-but-nonbinding" framing this RFC reuses.
- `4c1a776e` (RFC-0091) — precedent for landing an RFC, the conventions edit, the
  seed edit and version bumps in a single accepted commit.

## Open questions

None. All five decisions are recommended and settled; D5 was settled before
drafting.

## Follow-on artifacts

- **Convention edit (this PR).** `packs/core/seeds/docs/CONVENTIONS.md` § 5b and
  the PR-hygiene sentence, with `docs/CONVENTIONS.md` regenerated; the seed
  changelog header aligned to the same trigger; `.github/pull_request_template.md`
  updated.
- **Changelog correction (this PR).** Delete the asserted CI gate, replace the
  restated trigger with a cross-reference, and state the free-standing rule.
- **Enforcement (this PR).** The D3 ratchet in
  `tests/roster/test_workspace_status_projection.py`, and the D4 `Highlights`
  decision step in `packs/AGENTS.local.md`'s release pipeline.
- **Migration (follow-on, registered).** `changelog-promote-marooned-entries` in
  `workspace.toml [backlog].open` — promote the 59 nested entries, separate them
  from the 48 interleaved bare sections across three `[Unreleased]` regions,
  lower the ratchet baseline as they land, and restore `[Unreleased]`-first
  ordering.
- **Release (this PR).** Core `2.10.4` across its four version sites, with the
  self-obligating `[core]` entry.
- No ADR: this records a conventions wording decision, not an architectural one.
- No spec: no new behaviour, script, or workflow is introduced.
