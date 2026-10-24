# RFC-0110: Widen governance-extras into repository governance and rename it repo-governance

- **Status:** Draft
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-10-23
- **Date closed:**
- **Decision weight:** heavy (renaming a released 1.x pack breaks the name adopters install it by, another pack depends on it, and two new stages write agent-guidance and review-authority files; heavy adds a compatibility analysis, a security review and a validation plan to the normal RFC checks)
- **Related:** [RFC-0091](0091-right-size-rfc-governance.md) (lists the decisions that need the strongest route an adopter has), [ADR-0038](../adr/0038-rename-design-craft-pack-to-experience.md) (an earlier pack rename), [governance-extras-without-core](../specs/governance-extras-without-core/spec.md) (shipped in PR #1609: the pack installs and works without core)

A few terms used throughout:

- A **pack** is an installable bundle of agent skills, scripts and templates. The `agentbundle` command-line tool installs packs into a repository from this repository's **catalogue**, the published list of packs. **Adopters** are the repositories that install them.
- **Core** is the base pack. It holds the work loop, the build workflow with its light and full modes. It also seeds starter files into an adopter's repository.
- A **frozen** record is one whose body no longer changes (defined exactly under D3).
- A **one-way door** is a decision that is costly to undo. A **two-way door** is cheap to undo.

## Reviewer brief

- **Decision:** Whether the `governance-extras` pack becomes a repository-governance pack covering how a repository decides and stays governed, and is renamed `repo-governance`.
- **Recommended outcome:** Accept D1 to D6.
- **Change if accepted:**
  - The pack covers five stages: who decides, how to decide, record, enforce, and keep current. Today it covers record and the rule for when to write an RFC.
  - The pack becomes `repo-governance` 2.0.0. The installer learns one thing: when asked for a renamed pack, it says so and prints the migration steps instead of "not found".
  - Each new stage ships as its own spec after the rename, under the trust-model rules below.
- **Affected surface:** listed under D3. That is 122 tracked files outside `docs/`, plus live specs and product documents, and the installer's not-found message.
- **Stakes:** The rename is a one-way door for adopters. The new stages are two-way doors, but stages 1 and 4 write files that steer agents and reviews.
- **Review focus:** the migration path (D3), whether stage 4 belongs in the pack (D5), and the trust-model rules.
- **Not in scope:**
  - automatic pack aliases that install or upgrade the new name for you;
  - moving ownership of core's starter files `AGENT_RULES.md`, `CHARTER.md` or `AGENTS.md`;
  - AI-agent policy, guardrail or compliance tooling;
  - editing frozen records that name `governance-extras`.

## The ask

**Recommendation:** accept all six decisions. The pack already holds the RFC routing rule, the ADR and RFC formats, and a read-only navigator for them. ADRs already record how a decision is checked (`Confirmation`) and when to revisit it (`Revisit if:`).

What is missing:

- who holds decision rights;
- a front door for deciding;
- a way to turn decisions into checks;
- a way to notice decisions that have gone stale.

The name `governance-extras` describes none of that. "Extras" also implies an add-on to core, which stopped being true when PR #1609 made it work without core.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Which stages does the pack cover? | All five | Each missing stage reads fields ADRs already carry, so one pack keeps them consistent | 2026-11-06 | Accept or narrow |
| D2 | What is it called? | `repo-governance` | Covers all five stages; the `repo-` prefix separates it from AI-agent governance | 2026-11-06 | Accept or name another |
| D3 | How is it renamed? | Rename to 2.0.0, plus a catalogue rename map that turns "not found" into the migration steps | The current installer cannot carry adopters across a rename on its own | 2026-11-06 | Accept or choose another path |
| D4 | Who owns core's starter files? | Core keeps them; this pack proposes edits the user confirms | No second owner for one file, and the pack still works without core | 2026-11-06 | Accept or choose text-only |
| D5 | What does each new stage ship? | One skill or operation per stage, each its own spec | Small reviewable units that reuse existing ADR fields | 2026-11-06 | Accept or cut stage 4 |
| D6 | In what order? | Rename, then stages 2, 5, 1, 4 | New skills land under their final name once | 2026-11-06 | Accept or reorder |

## Problem & goals

A repository makes decisions all the time, and most never reach an ADR. Someone has to know who may decide, and which route fits: a PR, a spec, an ADR or an RFC. Someone has to know whether the decision is still followed, and when to revisit it.

This repository already pays for part of that loop:

- `new-rfc` routes each request before anything is written. Its "When to invoke" section and step 0 choose between skip (no record needed), reuse of an existing record, an ADR, a spec, a PR, or a time-boxed trial.
- An ADR can carry a `Confirmation` block, and 88 of the 146 ADRs in `docs/adr/` do. It has three fields:
  - `Mode`: reviewer-checked, lint/CI, architecture fitness test, periodic audit or none;
  - `Signal`: the check or observation that shows the decision is followed;
  - `Owner`.
- Every ADR has a `Revisit if:` trigger. There are 239 such lines across 146 files in `docs/adr/`. A lint rule checks each one is present and not empty, but nothing checks whether one has come due.

Three gaps follow:

- **Decision rights are undocumented when a project outgrows one maintainer.** Core's seeded charter rightly says small projects need no `GOVERNANCE.md`, and that forcing governance ceremony on them "produces theater". It also sends roles, voting and decision-making to `GOVERNANCE.md` "if and when" a project grows. RFC-0091 requires "the strongest route the adopter has" (an RFC where a process exists, an explicit recorded owner decision otherwise) for changes to "maintainer authority, approval process, or governance model". Nothing helps draft that file when the time comes.
- **Decisions are not turned into checks.** `Confirmation: Mode: lint/CI` stays prose unless someone writes the check by hand.
- **Stale decisions go unnoticed.** Three kinds are found only by accident: a due trigger, a superseded ADR that live records still cite, and a `Confirmation` signal that no longer exists.

**Goals:**

- One pack answers who decides, how to decide, what was decided, whether it is followed, and whether it is still current.
- The pack keeps working with or without core.
- The name says what the pack does.

**Non-goals:**

- Live dashboards, notifications or issue-tracker sync. The navigator stays an on-demand, read-only view.
- Enforcing decisions by itself. The pack proposes a check; the repository decides whether to adopt it.
- Approval workflows that circulate a document or collect sign-off.
- AI-agent governance: policy engines, guardrails or audit logging for agents.

## Proposal

### D1 — Five stages in one pack

The pack's job becomes "how this repository decides and stays governed":

1. **Who decides:** decision rights, maintainers, escalation, and how a vote works.
2. **How to decide:** choosing the route and doing the minimum to decide well.
3. **Record:** ADRs and RFCs, as today.
4. **Enforce:** turning an accepted decision into a check.
5. **Keep current:** finding decisions that are due, superseded or drifting.

Boundaries with other packs stay where they are:

- `architect` owns technical design choices.
- `product-engineering` owns de-risking a product bet.
- `release-engineering` owns release policy.
- Core owns the work loop and its starter files.

### D2 — Name: `repo-governance`

`repo-governance` names all five stages. The `repo-` prefix matters because "governance" on its own now mostly means AI-agent policy and compliance. No pack in this catalogue uses the bare word. The manifest's human-readable `display_name` becomes "Repository Governance".

### D3 — Rename, with a rename hint in the installer

**Why the earlier rename pattern is not enough on its own.** ADR-0038 renamed `design-craft` to `experience` with no migration aid. That was acceptable for three reasons: the pack was pre-stable at 0.1.1, it installed per user by default, and it was cheap to move early.

`governance-extras` differs on each point:

- it is at 1.0.2;
- it installs into repositories only;
- `iac-terraform` requires it at `^1.0`;
- it is part of the `full-ceremony` install profile, a preset list of packs.

Today the installer cannot carry an adopter across a rename. `agentbundle upgrade` stops with `pack 'governance-extras' not found in catalogue`, and that message does not say where the pack went. `upgrade` checks no dependencies. Installing `repo-governance` while `governance-extras` is still installed is refused, because both packs claim the same skill paths. Only uninstalling first avoids the clash.

**What ships:**

1. `packs/governance-extras/` moves to `packs/repo-governance/` at 2.0.0. Every live surface is renamed (the list follows).
2. The catalogue gains a rename map, owned by the catalogue: `governance-extras` → `repo-governance`.
   - When `install` or `upgrade --pack` is asked for a name that appears only in the map, it prints that the pack was renamed, prints the three migration steps below, and exits without changing anything.
   - In `upgrade --all`, the renamed pack's row gives the same message instead of a bare `pack-not-found`. The run stays blocked as it is today, so nothing upgrades halfway.
   - The installer never installs or upgrades the new name by itself.
   - The map travels with every catalogue source shape: the Git checkout, a local path, and the release archive. The release archive currently strips `catalogue.toml`, so the map cannot live only there.
   - The hint needs the agentbundle release that adds it. Adopters on an older CLI still see the plain "not found" message, and for them the changelog and the `repo-governance` README carry the steps.
   - `upgrade --all` re-reads each pack's recorded source. An install recorded from an older release archive therefore upgrades unchanged under `--all`, because that archive still contains `governance-extras`. `upgrade --pack` instead resolves the catalogue from the command's own source chain: an explicit source, `[settings].source`, an organisation bootstrap, editable detection, then the packaged default. It shows the hint when that resolved catalogue is at or after the rename release; if any layer pins a pre-rename catalogue, the pack upgrades unchanged from there.
3. `iac-terraform` changes its requirement to `repo-governance ^2.0` and takes a minor version bump.
4. `profiles/full-ceremony.toml` lists `repo-governance`.
5. The old name stays in the rename map permanently. That keeps it reserved, so no other pack can claim it later.

**Adopter migration order.** These are the steps the hint prints, and each one runs with today's commands and no `--force`:

1. `agentbundle uninstall --pack governance-extras`
2. `agentbundle install --pack repo-governance`, from the catalogue that reported the rename (the hint prints that source, or a placeholder when it carries credentials)
3. `agentbundle upgrade --pack iac-terraform`, from the catalogue that reported the rename, because only a catalogue with the rename has an `iac-terraform` that requires `repo-governance`. When `iac-terraform`'s recorded source differs from that catalogue, the hint presents this step as a move between catalogues for the reader to choose, and names the source being left in a credential-free form. When it has no recorded source, the hint says so. When the reporting catalogue's source carries credentials, `upgrade` cannot record it, so `iac-terraform` keeps its old recorded source; the hint says so. Only adopters who have `iac-terraform` installed need this step. Between steps 1 and 3, the installed `iac-terraform` lists a requirement that nothing satisfies. No command checks that between installs, and step 3 clears it.

**Live and frozen sets.** Status decides which set a file is in, not its folder.

- **Frozen** (keeps the old name):
  - ADRs and RFCs whose status is Accepted, Rejected or Withdrawn;
  - specs and plans whose status is Shipped, Done, Archived, Complete or Recorded;
  - dated changelog history, in `docs/product/changelog*` and `packages/*/CHANGELOG.md`;
  - the generated `README.md` index rows for frozen records.
- **Fixtures** (keep their name): the build-pipeline fixture pack under `packages/agentbundle/tests/build_pipeline/fixtures/packs/governance-extras/` models a generic pack. Renaming it would test nothing new.
- **A file with no status of its own** (notes, review rounds, verification ledgers, baselines) takes the status of the record or spec folder that holds it. So `docs/specs/<slug>/notes/...` follows `docs/specs/<slug>/spec.md`, and `docs/rfc/NNNN-notes/...` follows RFC-NNNN.
- **Live** (renamed): everything else. That includes Draft, Approved, Drafting, Executing and Implementing specs, and live product documents such as `docs/product/roadmap.md`, journeys and intents.

The rename spec's completion check is a search for `governance-extras`. It must return only frozen files, fixtures and the rename-map entry.

**Live surfaces outside `docs/`.** `git grep -l governance-extras -- . ':!docs'` finds 122 tracked files, generated skill copies included. They include:

- the pack itself;
- its guides under `guides/`;
- its web and journey pages (the journey page is a generated summary of the pack's user steps);
- `packs/iac-terraform/pack.toml`, and its `generate-iac` skill, which points into the pack's `seeds/` folder;
- `profiles/full-ceremony.toml`;
- core's `navigate-intents` skill, which tells readers to install `governance-extras` for ADR and RFC lookups;
- references in the `catalogue-curation`, `desk-research`, `product-documentation` and `agent-skill-engineering` packs;
- build and site code: `packages/agentbundle/agentbundle/build/self_host.py`, `packages/agentbundle/agentbundle/build/recipes/self-host.toml`, `site.toml`, `.github/workflows/docs.yml` and `.github/workflows/build-check.yml`.

Readers who meet the old name in a frozen record find the new one through the rename map's hint and through this RFC. No erratum is added to frozen records.

### D4 — Core keeps its starter files

Core seeds three starter files:

- `AGENT_RULES.md`, a table of rules that tells agents which extra files to read for which kinds of work;
- `CHARTER.md`;
- `AGENTS.md`.

This pack never takes them over. Stage 4 may propose an `AGENT_RULES.md` row. Stage 1 may propose a charter link to `GOVERNANCE.md`. In either case the skill shows the exact edit and writes it only under the confirmation rules in the trust model below. Without core, the default is to return the edit as text. The skill writes to another file only when the user names it.

### D5 — What each stage ships

Each skill stays whole on its own: it does its job when the others are not installed or not invoked.

- **Stage 1 — who decides.** A skill that drafts or amends `GOVERNANCE.md`.
  - It runs when asked, or when the user tells it the project has more than one maintainer and no recorded decision rights.
  - Its default model matches core's charter: a single maintainer, or a small group deciding by consensus.
  - A larger project can choose lazy consensus (agreement by silence), with a vote on disagreement. Changing the governance model itself needs a two-thirds majority. This follows the CNCF maintainer template.
  - It may draft `CODEOWNERS`.
  - Changing an existing model takes the strongest route the adopter has, as RFC-0091 requires: an RFC where a process exists, an explicit recorded owner decision otherwise.
  - It drafts; maintainers adopt.
- **Stage 2 — how to decide.** A front-door decision aid. It holds the same routing as `new-rfc` step 0 and adds two things:
  - an advice step: consult the people affected and those with relevant expertise, and record whom, using only handles or roles the user supplies;
  - a reversibility check: is this a one-way or two-way door?

  `new-rfc` keeps its own step 0, so it stays whole. `new-adr` keeps its own "When to invoke" checks. Both mention the decision aid as the place to start when the route is unclear.
- **Stage 3 — record.** `new-adr` and `new-rfc` stay as they are, except that stage 2's advice step fills the ADR's existing `Consulted` field. No new field is added.
- **Stage 4 — enforce.** A skill that reads an accepted ADR's `Confirmation` block, when it has one, and proposes the matching check. That is one of three things: an `AGENT_RULES.md` row, a lint rule, or a fitness test (an automated test that an architecture property still holds). It never runs proposed code. It writes only under the trust model below.
- **Stage 5 — keep current.** A read-only `health` operation on the pack's `navigate-decisions` skill. It reports four things:
  - a `Revisit if:` trigger that names a date or version which has passed (prose-only triggers are listed as "needs a person to judge");
  - a superseded ADR that an Accepted record still cites as current;
  - an ADR whose `Confirmation` signal names a check file or test that does not exist in the repository;
  - a count of ADRs with no `Confirmation` block, which stage 4 cannot act on.

  It never runs checks.

### D6 — Order

1. Rename and rename map (D3), in one PR that changes names, paths, versions and the not-found message only.
2. Stage 2, because stages 1 and 3 refer to it.
3. Stage 5, because it is read-only and shows where stages 1 and 4 matter most.
4. Stages 1 and 4.

Each step is its own spec, built through core's work loop.

### Trust model

The pack reads repository records, which are untrusted input, and some stages write files that steer agents or reviews. These rules bind the follow-on specs.

**What crosses a boundary:**

- **Writes to authority files.** Stage 4 writes `AGENT_RULES.md` rows, which steer every later agent session. Stage 1 writes `GOVERNANCE.md` and `CODEOWNERS`, and `CODEOWNERS` decides who must approve which paths.
- **Reads of untrusted records.** Stages 2, 4 and 5 read ADR and RFC text that any contributor can write.

**Rules for every follow-on spec:**

1. Record text is data. It never gains instruction authority, and a record cannot change a skill's scope, permissions or targets.
2. Confirmation means the user's own explicit reply to the exact bytes and target path that were previewed. Every preview shows control and bidirectional-text characters visibly rather than raw, and flags proposed code or file content that contains them. A record, an agent message or a standing approval is not confirmation. A declined confirmation writes nothing.
3. The bytes written are the bytes previewed. The write stops if the target changed after the preview.
4. Every path taken from record text, a proposal or a user answer is checked to stay inside the repository with the blessed `agentbundle.catalogue_tooling.file_safety` helpers before it is read. A path that fails is reported as invalid, not as missing.
5. Every write target, fixed targets such as `AGENT_RULES.md`, `GOVERNANCE.md` and `CODEOWNERS` included, is opened with confinement that refuses links, non-regular files and identity changes at open time. Rule 3's comparison is made on that same opened file. `file_safety` has no write operation today; the first spec that writes adds one there, and records it in `AGENTS.md`, rather than rolling its own.

**Rules for specific stages:**

- **Stage 4:**
  - A proposed `AGENT_RULES.md` row may only point its `read` column at an existing regular file inside the repository that Git tracks and does not ignore. The preview names the file and shows its whole content, or says plainly that it is cut short and gives the total size. Confirmation covers the file's content hash as well as the row.
  - Proposed lint and test code may only be written to an allowed set of locations that the stage-4 spec names. That set never includes `.git/`, an ignored path, or an authority file: `AGENTS.md`, `AGENT_RULES.md`, `GOVERNANCE.md`, `CHARTER.md`, or `CODEOWNERS` at any location GitHub reads (the root, `.github/` or `docs/`). Authority files are written only under the rules for the stage that owns them. A target outside the set is refused before the preview.
  - Its cells are rejected if they contain a table separator, a newline, a control or bidirectional-text character, or a link.
  - The preview shows the whole rendered row and the source ADR.
  - Proposed lint or test code is shown in full and never run by the skill.
- **Stage 1:**
  - Owner identities come only from handles the user supplies, never from Git history or email addresses.
  - Any `CODEOWNERS` change that adds, removes, narrows, widens or reassigns ownership counts as a governance-model change and takes the RFC-0091 route.
  - Patterns and handles come only from user input, never from record text. Each handle must match `@user` or `@org/team`. Each pattern must be one line with no unescaped whitespace, no `#`, and no control or bidirectional-text characters. Anything else is rejected before the preview, and the preview shows each line as GitHub would read it, as pattern and owners.
  - Before writing an ownership change, the skill requires the user to name the accepted RFC or recorded owner decision that approves it. Text inside a record never counts as that approval.
  - Drafts list `GOVERNANCE.md`, `CODEOWNERS` and `AGENT_RULES.md` among the owned paths.
- **Stage 5:**
  - Paths from `Confirmation` signals are checked under rule 4 before any existence check.
  - Reported record text has control and bidirectional-text characters removed.
- **Stage 2:** `Consulted` entries come only from handles or roles the user supplies, never from record text, Git history or email addresses.
- **D3:**
  - The rename map holds names only. Both names must match the pack-name grammar before anything is printed.
  - The map is read only from the catalogue that reported the pack as not found, which is the catalogue the command is already installing from. A map target must be a pack in that same catalogue, or the hint is refused.
  - Every printed step that resolves a catalogue (steps 2 and 3; `uninstall` resolves none) names its catalogue source explicitly, so none can resolve through a different default. Those steps name the catalogue that reported the rename. When the source cannot be printed, the step carries an explicit placeholder that cannot run as written, and the hint says that leaving it out sends the step to a different catalogue.
  - When a dependent pack's recorded source differs from the reporting catalogue, the hint does not print its upgrade as a routine step. It calls it out as a move between catalogues that the reader must choose, and names the origin being left in a credential-free form. An absent recorded source is stated as absent.
  - Every value printed in those steps goes through the installer's existing shell-quoting helper. These rules apply to every source the hint prints. If the reporting catalogue's source is empty or contains control or bidirectional-text characters, the whole hint is refused, as `upgrade` already refuses an unusable stored source. A dependent pack's old source is shown only in a credential-free form with unsafe characters made visible.
  - The hint never prints credential material from any source it prints. One detector covers every printed source, and it is at least as strict as the installer's stored-source canonicalisation: any user-info, and any query or fragment key that contains a credential term, is treated as credential-bearing. A credential-bearing source is printed in a credential-free form or replaced by the placeholder.

**Security passes.** The specs for stages 1, 2, 4 and 5, and the rename spec, each get a spec-stage security pass before they are built.

**Accepted risk.** Required-dependency checks match a pack by name and version only. Another catalogue's `repo-governance` would therefore satisfy `iac-terraform`. This RFC does not change that matching. A catalogue-qualified check would be a separate decision.

## Options considered

**D1 — scope.** Axis: which missing stages the pack takes on.

- Do nothing: record and routing only.
- Add stage 5 only. Cheapest, and it reads data that already exists.
- Add stages 2 and 5. Deciding and keeping current both work on existing records.
- Add all five. Recommended. Stages 1 and 4 are where most of the value sits for teams that outgrow one maintainer. They are also the only stages that write outside `docs/adr` and `docs/rfc`, and D5 lets a reviewer cut stage 4.

**D2 — name.** Axis: how much of the pack the name promises.

- Keep `governance-extras`. No churn, but "extras" is wrong once the pack stands alone, and "governance" collides with AI-agent governance.
- `decision-records`. Exact for stage 3 only.
- `decisions`. Covers stages 2, 3 and 5. It is vague next to `product-strategy`, and says nothing about decision rights.
- `repo-governance`. Covers all five. Recommended.

**D3 — rename path.** Axis: how much the installer helps adopters.

- Do nothing: keep the name.
- Clean break, documentation only. `upgrade` still says "not found", and adopters must find the changelog.
- Rename map with a hint. Recommended. It is one small, read-only installer change, and it reserves the old name.
- An empty stub release of `governance-extras`. Rejected: `upgrade` checks no dependencies, so the stub would install silently and satisfy `iac-terraform` with nothing.
- Automatic aliases. That is a distribution change of its own, and it would block this RFC.

**D4 — starter-file ownership.** Axis: who writes core-seeded files.

- Do nothing: the pack never writes them and returns every proposed edit as text. This is safe, but stage 4's main output, an `AGENT_RULES.md` row, would always need copying by hand.
- Propose and confirm; core keeps ownership. Recommended. The trust model's confirmation rules make the write safe.
- Move ownership to this pack. This creates a second owner for one file and a dependency in the other direction.

**D5 — stage 4's form.** Axis: how far stage 4 goes.

- Leave stage 4 out. The `Confirmation` field stays prose.
- Link only: point an ADR at a check that already exists, and write nothing else. Smallest, but it does not help ADRs whose check was never written.
- Propose checks under the trust model. Recommended. Falls back to "link only" if the validation below fails.

D6 has one clearly dominant order, which follows from the dependencies between stages.

## Risks & what would make this wrong

- **The rename hint is missed.** Wrong if: an adopter on the rename release's CLI runs `upgrade --pack governance-extras` or `upgrade --all` against a catalogue that has the rename (a Git, local-path or archive source at or after the rename release) and sees anything other than the renamed message and the three steps. The rename spec tests each source shape against the real command. Adopters on older CLIs are outside this check and rely on the changelog.
- **Rename churn hides real change.** Wrong if: the rename PR diff changes anything besides names, paths, versions, the rename map and the not-found message. Review checks the diff for that.
- **Stage 4's proposals are too generic to adopt.** Wrong if: maintainers reject more proposals than they adopt for this repository's accepted ADRs with `Mode: lint/CI`. Then stage 4 falls back to "link only".
- **Stage 2 conflicts with core's work loop.** Core's work loop picks light or full mode for building. The decision aid picks which record to write. Wrong if: the same request gets contradictory instructions from the two. The stage-2 spec names the seam and tests it.
- **Stage 1 adds ceremony.** Wrong if: it drafts a `GOVERNANCE.md` for a single-maintainer repository that did not ask for one. The stage-1 spec tests that it stays silent there.
- **An authority-file write is abused.** Wrong if: a crafted ADR leads stage 4 to write a row that points outside the repository or carries extra table rows. The trust-model rules are acceptance criteria in the stage-4 spec, and its security pass tests them.

## Experiment / validation

Each check runs in the follow-on spec for its stage, before that stage ships.

- **Rename hint (D3).**
  - Hypothesis: on a repository with `governance-extras` 1.0.x and `iac-terraform`, both `upgrade --pack governance-extras` and `upgrade --all`, run against a catalogue at or after the rename release (Git, local-path and archive sources), print the rename and the three steps, and change nothing. Under `upgrade --all`, an install recorded from a pre-rename archive upgrades unchanged. Running those steps then completes without `--force`.
  - Measure: observed command output and installed state.
  - Pass: the message names `repo-governance`, the three steps succeed in order, and `iac-terraform` ends on its new requirement. This includes an `iac-terraform` recorded from a pre-rename archive or with no recorded source, where the hint states the source change.
- **Stage 4 usefulness.**
  - Hypothesis: for this repository's accepted ADRs with `Confirmation: Mode: lint/CI` or `architecture fitness test`, the skill proposes a check a maintainer would merge.
  - Measure: maintainer verdict on a sample of 10.
  - Pass: at least 6 of 10 can be adopted with minor edits.
- **Stage 5 accuracy.**
  - Hypothesis: `health` finds real due triggers and missing signals without noise.
  - Measure: run it on this repository's `docs/adr/` and check each finding by hand.
  - Pass: every reported item is real, and every "needs a person to judge" item really is prose-only.
- **Stage 2 seam.**
  - Hypothesis: the decision aid and core's work loop never give conflicting routes.
  - Measure: run both on the routing examples in `new-rfc`'s evals.
  - Pass: no contradiction.

## Evidence & prior art

- **ADR-0038** renamed a pre-stable, user-scope pack with no migration aid. D3 explains why this pack needs more.
- **RFC-0091** requires the strongest route the adopter has for changes to "maintainer authority, approval process, or governance model".
- **Core's seeded charter** (`packs/core/seeds/docs/CHARTER.md`) keeps governance documents for projects that need them, and warns against ceremony for small ones.
- **The installer today:**
  - `upgrade` reports an unknown pack as not found (`packages/agentbundle/agentbundle/commands/upgrade.py`) and checks no dependencies.
  - `install` refuses paths owned by another pack (`packages/agentbundle/agentbundle/commands/install.py`).
  - `uninstall` does not check dependents.
- **CNCF Maintainer Council template** ([contribute.cncf.io](https://contribute.cncf.io/projects/best-practices/governance/templates/governance-maintainer)):
  - most decisions by lazy consensus;
  - votes on disagreement, or on major or irreversible decisions;
  - two thirds for removing a maintainer or changing the charter.
- **Architecture advice process** ([InfoQ](https://www.infoq.com/articles/decentralized-architecture-advice-process)): anyone may decide after seeking advice from those affected and from experts, and the ADR records the advice received.
- **Architectural fitness functions** ([Thoughtworks Technology Radar](https://www.thoughtworks.com/radar/techniques/architectural-fitness-function)): objective, automated, continual checks of architectural characteristics.

## Follow-on artifacts

- **Rename spec:** rename to `repo-governance` 2.0.0; add the catalogue rename map and the installer's renamed-pack message; update `iac-terraform` (D3).
- **Stage 2 spec:** the decision aid.
- **Stage 5 spec:** the `navigate-decisions` `health` operation.
- **Stage 1 spec:** the governance-model skill.
- **Stage 4 spec:** the decision-to-check skill.
