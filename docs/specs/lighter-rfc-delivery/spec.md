# Spec: Lighter RFC delivery

- **Status:** Implementing
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0114, RFC-0091, ADR-0089
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** mixed
- **Risk triggers:** security-boundary, structural-interface, multi-feature

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: an author corrects them in place as the
> work teaches, without an amendment or a review round.

## Outcome

A contributor with only a fork can create a numbered RFC draft with one command, and a maintainer reviews a six-section RFC whose decisions sit in its Summary. Adopters installing `repo-governance` receive the template, the script, a starter governance file and an optional discussion template, and the `new-rfc` skill numbers and checks RFCs through the same script.

## What Changes

- Six-section RFC template, no `Approver` field — the skill's `assets/rfc.md` and the seeded `docs/rfc/template.md.tmpl`.
- `rfc.py` with `next`, `new`, `renumber` and `check` — the skill's `scripts/` and the seeded `docs/rfc/`, with a byte-identical `file_safety.py` beside each copy.
- Starter `docs/GOVERNANCE.md` and `.github/ISSUE_TEMPLATE/proposal-idea.md` — new `repo-governance` seeds; the starter is also governance mode's default text.
- This repository's own `docs/GOVERNANCE.md`, and the self-host exclusion that keeps it — `packages/agentbundle/agentbundle/build/self_host.py`.
- Seed shapes for the new files — `packages/agentbundle/agentbundle/catalogue_tooling/lint.py`.
- `new-rfc` skill — numbering through `rfc.py`, the completeness check and receipt, the supersession steps after acceptance, governance mode's target rule and draft check, both evals that assert removed behavior.
- How-to guide — `guides/repo-governance/how-to/new-rfc.md`.
- One ADR superseding the shipped-spec criteria RFC-0114 lists, with a Status pointer on each affected spec — `docs/adr/`, `docs/specs/`.
- Release — `repo-governance` and `agentbundle` patch versions on every surface their guides list, a changelog fragment, the install snapshot, and the tests that pin the old versions.
- Captured work items for the seed-upgrade fix and two stale consumers — `docs/product/captured/`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | The shipped-spec criteria that pin the old template are superseded | `docs/adr/` (one new ADR) and the Status line of each affected spec | owner | ADR file; `navigate-decisions` health `ok` | ADR is Accepted and every affected spec's Status line points at it |
| User promise | The how-to guide describes the old template and approval | `guides/repo-governance/how-to/new-rfc.md` | owner | guide lints and pinning suites pass | the guide names the six sections and no Approver |
| Interface compatibility | New seeded files and a changed template reach adopters | changelog fragment under `docs/product/changelog.d/` | owner | changelog check passes | the fragment says seeded files reach new installs only |
| Release history | Pack and package versions change | the pack's `pack.toml` and `plugin.json`; the package's six release surfaces | owner | `CAT-L009` clean; `test_okf_catalogue_discovery.py` green | versions agree |
| Maintainer procedure | This repository adopts the starter | `docs/GOVERNANCE.md`; `docs/architecture/pack-layout.md` | owner | self-host check passes | file names the real maintainer and the architecture page lists it |
| Reusable follow-ons | Seed upgrade and two stale consumers need owners | `docs/product/captured/` | owner | three captured items | each names an owner |

## Agent Rules

### Always do

- Run every `rfc.py` example as `python3 -I`.
- Edit sources in `.apm/` and `seeds/`, then run self-host; never edit a projection.
- Follow `packs/AGENTS.md` for version bumps, shipped-text rules and pack tests, and `tests/AGENTS.md` for roster steps.

### Ask first

- Any change to how `agentbundle upgrade` treats seeds.
- Skill edits beyond the sections `docs/rfc/0114-notes/skill-updates.md` names.
- A change to the 5,000-word threshold or to `rfc.py`'s exit codes.

### Never do

- Edit the body of a frozen RFC or spec; only header lines, Errata and Status pointers change.
- Write a `Superseded` line or Errata entry on a frozen RFC before the superseding RFC is Accepted.
- Add a new top-level directory, or edit or delete the skill's `next-ordinal.py` copy.

## Testing Strategy

Each group names its criteria once.

- **Template (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006 and AC-0007):** goal-based. A pack test compares the two files byte for byte and parses their headings, header fields and required text.
- **`rfc.py` commands (AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014 and AC-0015):** TDD. Each command has an invariant a function call over a temporary folder can check, with the git lookup replaced.
- **`rfc.py check` (AC-0016, AC-0017, AC-0018, AC-0019, AC-0020 and AC-0021):** TDD. Function calls over temporary folders decide each warning and exit code.
- **Existing corpus (AC-0022):** goal-based. `rfc.py check` runs over the real `docs/rfc/`.
- **Imports (AC-0023):** goal-based. A parse of the script's imports decides it.
- **Isolation, loading and folder (AC-0024, AC-0025 and AC-0026):** TDD. One subprocess runs `python3 -I` beside a planted module and a planted bytecode file written at the interpreter's own cache path, with a loader that does read the cache as a positive control.
- **Confinement and names (AC-0027, AC-0028, AC-0029, AC-0030, AC-0031 and AC-0032):** TDD. A test with an ESC-bearing name asserts no raw ESC byte reaches stdout or stderr; each control has a test that fails when the control is absent.
- **Git and `--dir` (AC-0033, AC-0034 and AC-0084):** TDD. A test at the single process-spawn call asserts every invocation's argv, environment, subcommand and working directory; `--dir` is tested with different records in each folder; a `check` run over a terminal RFC absent from a stubbed remote listing prints no warning and never reaches the spawn call, and the help text names those three warnings and no branch or decided-status warning.
- **Guidance and seeded text (AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0042, AC-0043, AC-0044, AC-0045 and AC-0046):** goal-based. Source-text pins and one scan over the seeded files, the script's help, the skill and the guide decide them.
- **Injection behavior (AC-0047):** a judge-graded eval run, whose pass or fail for that eval is recorded by name.
- **One governance text (AC-0048 and AC-0049):** goal-based. A byte comparison and the governance script suite decide them.
- **Seeds and install (AC-0050 and AC-0051):** goal-based. The install snapshot and the seed lint decide them.
- **Copies and self-host (AC-0052, AC-0053, AC-0054, AC-0055, AC-0056 and AC-0057):** goal-based. Pack and roster tests and the self-host check decide them.
- **Skill behavior (AC-0058, AC-0059, AC-0060, AC-0061, AC-0062, AC-0063, AC-0064, AC-0065, AC-0066, AC-0067, AC-0068, AC-0069 and AC-0070):** goal-based. Source-text pins decide the skill's wording and the judged evals decide its supersession steps; only the lineage result is decided by a pack test over fixture RFCs and a lineage query.
- **Evals (AC-0071):** goal-based. A pin on the eval file decides it.
- **Guide (AC-0072 and AC-0073):** goal-based. A grep and the pinning suites decide them.
- **Decision record (AC-0074, AC-0075 and AC-0076):** goal-based. The ADR lint, a roster check of the Status lines and the health report decide them.
- **Versions (AC-0077, AC-0078, AC-0079 and AC-0080):** goal-based. Catalogue lint, the version-pin and discovery tests, the changelog check, and a comparison with the fetched default branch recorded in the ledger decide them.
- **Work item (AC-0081):** goal-based. The captured item's presence and owner decide it.
- **Suites (AC-0082):** goal-based. The named suites run.
- **Fork-only contributor (AC-0083):** manual QA. One recorded run in a fresh clone with no agent installed.

## Acceptance Criteria

- [ ] **AC-0001.** The skill's `assets/rfc.md` and the seeded `docs/rfc/template.md.tmpl` are byte-identical.
- [ ] **AC-0002.** The template's level-two headings, in order, are Summary, Motivation, Proposal, Design details, Costs and what could go wrong, Alternatives, How we will know it works, Migration, Open questions and Evidence, with Goals and Non-goals as level-three headings under Motivation.
- [ ] **AC-0003.** The template's header fields are exactly Status, Author, Date opened, Date closed, Decision weight and Related, and it has no `Approver` field.
- [ ] **AC-0004.** The template contains the `<account-handle>` placeholder, the cold-reader cue and the commented Errata/Amendments scaffold.
- [ ] **AC-0005.** The template's Decision-weight line carries the default `standard`, the three tier definitions, and the sentence "Use core's work-loop risk triggers when core is installed, otherwise these definitions".
- [ ] **AC-0006.** The template's header comment names `python3 -I docs/rfc/rfc.py` and no other script.
- [ ] **AC-0007.** The template's Summary comment asks for the proposal and its reason followed by one bullet per decision, and its Proposal comment asks for follow-on work at the end of Proposal.
- [ ] **AC-0008.** `rfc.py next` prints, as four digits, one more than the highest number among the folder's records, its `NNNN-notes/` folders, its research companions, and the last-fetched default branches of `upstream` and `origin` in the repository that contains the RFC folder.
- [ ] **AC-0009.** `rfc.py next` prints no number and exits 2 when the folder cannot be read or the next number would pass 9999.
- [ ] **AC-0010.** `rfc.py new "Title"` writes `NNNN-<slug>.md` from the template with the number `next` gives, creating the file exclusively.
- [ ] **AC-0011.** `rfc.py new` exits 1 and writes nothing when the number or the file name is already used, including a dangling link at that name.
- [ ] **AC-0012.** `rfc.py check` reads an `XXXX-<slug>.md` draft as a record and applies the length and section warnings to it.
- [ ] **AC-0013.** `rfc.py renumber FILE N` renames the file and its title number, where FILE may be an `XXXX-<slug>.md` draft, and exits 1 when `N` is in use.
- [ ] **AC-0014.** `rfc.py renumber` refuses a path with a symlinked directory component.
- [ ] **AC-0015.** After any failure in `renumber`, the folder holds exactly the original file.
- [ ] **AC-0016.** `rfc.py check` warns when a non-terminal RFC passes 5,000 whitespace-separated words, counting everything except the title and the header field lines, and counting fenced code.
- [ ] **AC-0017.** `rfc.py check` warns when a non-terminal RFC lacks one of its six required sections, Summary, Motivation, Proposal, Costs and what could go wrong, Alternatives and How we will know it works, each matched as a level-two heading with exactly that name.
- [ ] **AC-0018.** `rfc.py check` warns when two records share a number.
- [ ] **AC-0019.** `rfc.py check` skips the length and section warnings for RFCs whose status is Accepted, Rejected, Withdrawn, Experimental or Superseded, and skips every `NNNN-<slug>-research.md` companion in every check.
- [ ] **AC-0020.** `rfc.py check` exits 0 on warnings, 1 on warnings with `--strict`, and 2 when a file cannot be read.
- [ ] **AC-0021.** With FILE arguments, `rfc.py check` applies the length and section checks only to the named files.
- [ ] **AC-0022.** `rfc.py check` over the existing `docs/rfc/` reports no length, section or number-clash warning.
- [ ] **AC-0023.** `rfc.py` imports only modules of the Python standard library.
- [ ] **AC-0024.** A `argparse.py` planted beside the script is not imported by the documented `python3 -I` call.
- [ ] **AC-0025.** `rfc.py` executes `file_safety.py` only from its own source bytes, read as a confined regular file, and consults and writes no bytecode cache, so a planted unchecked-hash `__pycache__/file_safety.*.pyc` never runs.
- [ ] **AC-0026.** At the top level of the folder it inspects, `rfc.py check` exempts exactly `rfc.py` and `file_safety.py` as regular non-link files and warns about any other code file, any bytecode file, `__pycache__/`, a symlinked `file_safety.py`, and any subdirectory other than a `NNNN-notes/` folder; it does not look inside `NNNN-notes/` folders, and the folder it inspects is the `--dir` folder or, without `--dir`, the script's own folder.
- [ ] **AC-0027.** Every read and exclusive create in the RFC folder, the template included, goes through `file_safety.py`; a listing validates the folder with the helper and then reads one directory level without following links; `renumber`'s rename, remove and rollback are the exception.
- [ ] **AC-0028.** `rfc.py` reads and writes only regular non-link files whose parent is the RFC folder.
- [ ] **AC-0029.** `rfc.py` reads at most 1 MiB from any file.
- [ ] **AC-0030.** A name `new` or `renumber` creates uses only `[a-z0-9-]` in its slug, at most 60 characters of slug, and a number from 1 to 9999.
- [ ] **AC-0031.** `rfc.py check` reports a file whose name is not a record, a companion, `README.md`, `rfc.py`, `file_safety.py` or `template.md.tmpl`, and never reads, renames or counts it.
- [ ] **AC-0032.** A file name `rfc.py` prints has its control characters escaped.
- [ ] **AC-0033.** Every git invocation carries `-c core.fsmonitor=`, `-c core.hooksPath=<null device>`, `-c protocol.allow=never`, `-c safe.bareRepository=explicit` and `GIT_TERMINAL_PROMPT=0`, and runs only `rev-parse`, `symbolic-ref` or `ls-tree`.
- [ ] **AC-0034.** With `rfc.py --dir PATH`, every file read, listing and write targets `PATH` and none targets the script's folder except loading `file_safety.py` from it, and no code from `PATH` runs.
- [ ] **AC-0035.** The seeded guidance names `rfc.py`, `file_safety.py`, the template and the governance file as maintainer-owned and says changes to them need close review.
- [ ] **AC-0036.** The seeded guidance tells maintainers to check a contributor's branch with their own default-branch copy of `rfc.py`, never the branch's copy.
- [ ] **AC-0037.** The seeded guidance names `pull_request` with read-only permissions and no secrets as the CI trigger for `check`, forbids `pull_request_target` on pull-request content, and says the CI job runs the default-branch copy of `rfc.py` with the pull request as data through `--dir`, because a copy from the pull request is contributor code.
- [ ] **AC-0038.** The starter and the template say a decider named inside an RFC is a suggestion, and that only the repository's rules and a listed maintainer's merge accept an RFC.
- [ ] **AC-0039.** The starter's maintainers list holds only the `<maintainer-handle>` placeholder, the starter has no rule that accepts a change by silence or timeout, and it names no `CODEOWNERS` dependency.
- [ ] **AC-0040.** The issue template asks for no personal data beyond what the platform shows, sets no assignee, and says a reply is not an acceptance.
- [ ] **AC-0041.** The starter has headings for maintainers, how decisions are made, suggesting a change, when to write an RFC and how an RFC is decided.
- [ ] **AC-0042.** The starter states the ladder of an optional issue or discussion, then a pull request, an ADR, or an RFC, and marks the discussion step optional.
- [ ] **AC-0043.** The starter states that one RFC proposes one change, how to start an RFC, and that agent-binding rules belong in project instructions.
- [ ] **AC-0044.** The starter's RFC rule states the trigger of an unresolved direction that more than one owner must agree, and the four reserved categories: charter mission, scope or foundational principles; maintainer authority, approval or governance model; a security trust model; and withdrawal or breaking change of a stable published compatibility promise.
- [ ] **AC-0045.** No seeded file, template asset or `rfc.py` text contains an identifier of the form `RFC-` or `ADR-` followed by digits.
- [ ] **AC-0046.** Every `rfc.py` command line shown in seeded text, the script's help, the template header, the skill and the guide uses `python3 -I`.
- [ ] **AC-0047.** One judged `new-rfc` eval supplies a template and an existing RFC that each carry an HTML comment instructing an out-of-scope action, and the recorded judged run passes its assertions that the action does not occur and the receipt reports the comment as content.
- [ ] **AC-0048.** Governance mode's default asset is byte-identical to the seeded `docs/GOVERNANCE.md`.
- [ ] **AC-0049.** Governance mode's draft check accepts that text once a handle replaces the placeholder.
- [ ] **AC-0050.** Installing `repo-governance` into an empty repository delivers `docs/GOVERNANCE.md`, `docs/rfc/README.md`, `docs/rfc/rfc.py`, `docs/rfc/file_safety.py`, `docs/rfc/template.md.tmpl` and `.github/ISSUE_TEMPLATE/proposal-idea.md`, and the install snapshot lists them.
- [ ] **AC-0051.** Each new seed has a declared shape in the seed lint, and `agentbundle catalogue lint --root . --deep` passes.
- [ ] **AC-0052.** The skill's bundled `rfc.py` and `file_safety.py` are byte-identical to the seeded copies.
- [ ] **AC-0053.** The seeded `file_safety.py` is byte-identical to the canonical helper under `packages/agentbundle/agentbundle/catalogue_tooling/`.
- [ ] **AC-0054.** This repository's `docs/rfc/rfc.py`, `docs/rfc/file_safety.py` and `docs/rfc/template.md.tmpl` are byte-identical to the seeds.
- [ ] **AC-0055.** This repository's `docs/GOVERNANCE.md` has no `<maintainer-handle>` placeholder and lists the handle of this spec's Owner.
- [ ] **AC-0056.** `agentbundle catalogue self-host --root . --check` passes.
- [ ] **AC-0057.** `docs/architecture/pack-layout.md` lists `docs/GOVERNANCE.md` among the repository-owned seeded paths.
- [ ] **AC-0058.** The skill numbers an RFC through its bundled `rfc.py next` and `check` with `--dir` set to the RFC folder, and its text uses `next-ordinal.py` for no RFC step.
- [ ] **AC-0059.** The skill's completeness check asks "who decides is clear", and its text contains no `Approver`.
- [ ] **AC-0060.** The skill's receipt reports who decides.
- [ ] **AC-0061.** The skill never reads or names `GOVERNANCE.md` outside governance mode.
- [ ] **AC-0062.** Governance mode's target is an existing governance file at any allowed location.
- [ ] **AC-0063.** The skill's drafting guidance states each of: Summary first with one bullet per decision, a preview that shows the Summary and not a Reviewer brief, evidence cited as `[n]` and listed under Evidence, diagrams where structure is clearer as a picture, long research in a `NNNN-notes/` folder, and a check that each decision is one claim.
- [ ] **AC-0064.** For an RFC that supersedes another, the skill writes `Supersedes` or `Supersedes in part` header lines with D-numbers while drafting.
- [ ] **AC-0065.** The skill writes the mirrored header line and the Errata entry on a frozen RFC only after the superseding RFC is Accepted, and edits no frozen body.
- [ ] **AC-0066.** After the mirrors are written, a lineage query returns a checked edge between the two RFCs, with equal scopes, in both directions.
- [ ] **AC-0067.** The skill's pre-handoff checks require that every `[n]` citation resolves to an Evidence item, every Evidence item is cited, and every date has a source.
- [ ] **AC-0068.** The skill's research-findings block and open-question guidance carry no decide-by date.
- [ ] **AC-0069.** The skill's anti-patterns name narrative history in the body, a mirror line on a frozen RFC before acceptance, an invented date or deadline, and filler.
- [ ] **AC-0070.** The skill records whole-RFC supersession as header lines on both records plus the Errata entry, and says the merge by a maintainer the repository's rules name signs an Errata entry.
- [ ] **AC-0071.** The first `new-rfc` eval keeps its assertions that the RFC reads from zero prior context and carries the Decision-weight field and adds assertions for Summary-first order, footnoted evidence without narrative, no decide-by dates, a diagram where structure matters, supersession lines at draft and no mirror line before acceptance, and the second eval asserts no decide-by date.
- [ ] **AC-0072.** The how-to guide names the six required sections of the check criterion and contains no `Approver`.
- [ ] **AC-0073.** The guide keeps its readiness-summary and proof wording and its description of the fresh-context check.
- [ ] **AC-0074.** One ADR supersedes in part each shipped criterion that `docs/rfc/0114-notes/superseded-criteria.md` lists as superseded.
- [ ] **AC-0075.** Each affected spec's Status line carries a scoped pointer to that ADR.
- [ ] **AC-0076.** `navigate-decisions` health reports `ok`.
- [ ] **AC-0077.** Each release surface carries one version per artifact: `repo-governance` `pack.toml` and `plugin.json`; and `agentbundle`'s `version.py`, `pyproject.toml`, the first `## What's new in X.Y.Z` heading of `README-pypi.md`, the first `## [X.Y.Z]` heading of `CHANGELOG.md` and its changelog fragment.
- [ ] **AC-0078.** Each new version, the pack's and the package's, is the next patch above the version on the fetched default branch.
- [ ] **AC-0079.** A changelog fragment for the pack version states that the seeded files reach new installs only and that fixes to seeded scripts reach existing adopters only by re-copying.
- [ ] **AC-0080.** The tests that pin the `repo-governance` version carry the new version, and the registry-notes map points `repo-governance` at the new fragment.
- [ ] **AC-0081.** A captured work item for fixing seed upgrades exists under `docs/product/captured/`, owned by eugenelim.
- [ ] **AC-0082.** The roster, `new-rfc`, `new-adr` and `navigate-decisions` suites, `tools/validate_guides.py`, `tools/check-guide-index.py`, `tools/lint-guide-titles.py` and `tools/test_stasis_retirement_claims.py` pass.
- [ ] **AC-0083.** A fork-only contributor in a fresh clone creates a draft with `rfc.py new` and no agent installed, `rfc.py check` on that draft file reports no warning, and the run is recorded in `docs/specs/lighter-rfc-delivery/notes/verification-ledger.md`.
- [ ] **AC-0084.** `rfc.py check` starts no git process and gives no warning that depends on a record being present on any branch; its help describes no warning about branch presence or decided status and names the length, missing-section and number-clash warnings.

## Follow-ons

- eugenelim: after the change merges, tag and publish the `agentbundle` release as `docs/guides/how-to/cut-a-package-release.md` describes.

## Assumptions

- Defaulted: Technical: pack version — default: next patch above fetched main, because the pack bump rule gives a patch for changed content and seeds are not primitives; if wrong: the version criterion asks for a minor bump (settled by: eugenelim).
- Defaulted: Technical: ADR number — default: next free ordinal when the ADR is drafted, re-derived before the PR; if wrong: renumber (settled by: eugenelim).
- Defaulted: Technical: record numbers — default: exactly four digits, so the five-digit tolerance of the ADR numbering script is dropped for RFCs; if wrong: widen the record pattern (settled by: eugenelim).
- Defaulted: Technical: the skill's `next-ordinal.py` copy — default: kept untouched, because its equality test pins it and a deletion would be a removal needing a major bump; if wrong: delete it with that bump (settled by: eugenelim).
- Defaulted: Technical: the two ordinal roster tests — default: unchanged, because they bind the ADR allocator and the ADR numbering path, which this change does not touch; if wrong: repoint them in the skill task (settled by: eugenelim).
- Defaulted: Product: skill edits — default: only the sections the skill-updates note names; if wrong: widen the skill task (settled by: eugenelim).
- Defaulted: Product: guide — default: update its template, numbering and approval text in place; if wrong: a job-page rewrite becomes its own spec (settled by: eugenelim).

## Changelog

- 2026-11-06: spec approved by eugenelim (scope)
- 2026-11-06: amendment approved by eugenelim (scope)
