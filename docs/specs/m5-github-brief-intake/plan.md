# Plan: m5-github-brief-intake

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Pure prose-choreography, modelled file-for-file on the atlassian pack's
`jira-brief-intake`. The work is:

1. **Scaffold the `github` pack** (`packs/github/`) — `pack.toml`, `README.md`,
   `.claude-plugin/plugin.json`. No existing pack to copy verbatim; use atlassian
   as the structural template (strip all Atlassian-specific references).
2. **Author the skill** at `packs/github/.apm/skills/github-brief-intake/` —
   `SKILL.md` (procedure + lifecycle + graceful-degradation branch) and
   `manifest.json` (naming the `receive-brief` soft dependency by name).
3. **Author the guide slice** at `docs/guides/github/` — `README.md` and
   `how-to/intake-a-github-milestone-as-a-brief.md` (end-to-end user-facing
   walkthrough).
4. **Update cross-cutting docs** — `docs/architecture/overview.md` pack table,
   `docs/guides/README.md` pack-index row, `docs/product/changelog.md`
   `[Unreleased]` entry.
5. **Run the pack gate** — `lint-packs`, `agentbundle validate`, `make build`,
   agentbundle package pytest.

There is no executable code: no Python, no scripts, no tests beyond the
standing pack gate. The riskiest part is **boundary discipline** — keeping the
`SKILL.md` thin so it does not bleed into `receive-brief`'s Elicit stage. The
second risk is **`gh` command shape**: `gh milestone` is not a native subcommand;
milestone data comes from `gh api repos/{owner}/{repo}/milestones`, and issue
enumeration from `gh issue list --repo {owner}/{repo} --milestone <title-or-number> --state all --json
number,title,body,labels,url,state`. The skill must use exactly these commands so the
dry-run trace in manual QA can verify they exist and return the right fields.

## Constraints

- **RFC-0019 (Accepted):** own-the-repo-slice only; `Epic:` pointer as the
  cross-repo bridge; no hub. (RFC-0019 contains no read-only mandate.)
- **`jira-brief-intake` precedent + user confirmation:** read-only is the
  `jira-brief-intake` spec's own choice, not an RFC-0019 requirement; this
  skill departs from it with bounded, opt-in write-back (comment / label /
  close — never body edits), per user confirmation 2026-07-22.
- **tracker-projection.md precedent:** GitHub Milestone = brief level; single
  GitHub Issue = leaf/spec level → redirect to `new-spec`.
- **jira-brief-intake structural precedent (in-pack):** same cross-skill-by-name
  contract, same `manifest.json` `deps` shape, same prerequisite-gate model.
- **`github` pack shape follows atlassian:** user-scope-default; non-projected
  (no `build-self` step); gate = `lint-packs` + `validate` + `build` +
  package pytest.
- **P4 phase-slice doctrine (workspace.toml):** tooling (skill) and guide ship
  in the same PR.

## Construction tests

No new executable logic. Verification is goal-based + manual QA.

**Integration tests:** none beyond the pack gate.

**Activation evals:** out of scope for v0.1.0. The `pack-eval-coverage-rollout`
backlog item covers extending activation evals to new packs once the
ANTHROPIC_API_KEY secret is configured in CI (see `workspace.toml [backlog]`
entry `pack-eval-coverage-rollout`). Add `evals/eval_queries.json` and a
`[pack.evals].skills` entry in the follow-on PR when that gate is available.

**Manual verification** (pinned fixture: `anthropics/claude-code` milestone
"P1" — confirmed reachable via `gh api` probe 2026-07-22; has 14 closed issues
and 0 open issues — satisfies the closed-issue fixture requirement):
1. Reading-level dry-run: confirm `gh api repos/anthropics/claude-code/milestones`
   returns milestone "P1" with `title`, `description`, `html_url`; confirm
   `gh issue list --repo anthropics/claude-code --milestone "P1" --state all --json
   number,title,body,labels,url,state` returns issues with all six fields
   including `state` (uppercase `"CLOSED"`/`"OPEN"`); confirm the produced brief
   maps milestone title → Outcome draft, issues → `US-n (#NNN) <text>` each
   annotated `[closed]` where `state == "CLOSED"`, milestone `html_url` → `Epic:`.
2. Auth path: (a) unauthenticated + public → read succeeds, posture noted;
   (b) unauthenticated + 404 → ambiguous message surfaced (not a binary
   auth/not-found decision). Confirm the SKILL.md ambiguous-404 message matches
   the AC-S3 verbatim text.
3. Single-issue redirect: confirm a bare issue-number input recommends `new-spec`.
4. Absent-path: confirm the graceful-degradation branch names `new-spec` and
   `work-loop` as potentially absent.
5. Open-issue path: fixture "P1" has 0 open issues — add at least one synthetic
   open-issue entry to the `notes/fixture-snapshot.json` snapshot (e.g. a stub
   object with `"state": "open"`) and confirm it produces a story line without a
   `[closed]` annotation (AC-S4).
6. Empty-milestone path: construct a synthetic snapshot entry with an empty
   issues array; confirm the skill produces a brief with an empty Shape B section
   and an elicit note, rather than aborting (AC-S9).
7. Capture API snapshots: save `gh api repos/anthropics/claude-code/milestones`
   and `gh issue list --repo anthropics/claude-code --milestone "P1" --state all --json
   number,title,body,labels,url,state` outputs (plus the synthetic entries from
   steps 5-6) to `notes/fixture-snapshot.json` so the dry-run is reproducible if
   the live milestone drifts.
8. Record results in `notes/manual-qa.md`.

## Design (LLD)

Shape: `integration` → sub-sections: dependencies & integration, failure &
resilience. (The skill exposes no interface and owns no data schema.)

### Design decisions

- **New `github` pack (not core, not atlassian):** three alternatives considered:
  (a) *core* — rejected because `gh` CLI is not universally available on all
  adopter machines (unlike core's tooling which is stdlib-only), and RFC-0019
  §Decision 3 notes that tracker-specific work fails core's Universal principle;
  (b) *atlassian pack* — rejected because GitHub and Atlassian are unrelated
  vendors and the atlassian pack's `allowed-adapters` list and dependency set are
  already scoped to Atlassian credentials; (c) *new `github` pack* — chosen
  because it gives GitHub skills their own versioned namespace, allows the pack
  to declare `gh` as a system dependency without polluting other packs, and
  mirrors the jira precedent of keeping tracker adapters in their vendor's pack.
  Traces to: Pack ACs.
- **`gh` CLI as the read primitive (system dependency, not a pack skill; no
  credentialed flags):** no `github` skill exists; `gh` is a widely-available,
  officially-maintained CLI that handles its own auth and credential management.
  Declared in `manifest.json` as `deps.system` (not a Python package). The skill
  carries **no** credentialed-skill frontmatter (`credentialed`, `primitive-class`,
  `auth`) — `gh` owns its credential chain; the skill never touches a token.
  This exactly matches `jira-brief-intake`, which also delegates to its
  credentialed sibling and carries no credentialed flags. Adding
  `credentialed: cli` (non-boolean) would be silently skipped by
  `lint_credentialed_skills.py` (which keys on `credentialed: true`), and adding
  `credentialed: true` / `primitive-class: credentialed-cli` would require an
  argv-ban deny-set in `scripts/` that a scriptless skill cannot provide.
  Traces to: all skill-content ACs.
- **Milestone = brief level, Issue = leaf level:** grounded in
  `tracker-projection.md` (`spec / slice (leaf) → Linear Issue`; GitHub Issue
  maps to the same lean-tracker leaf level). Traces to: single-issue-redirect AC.
- **`--state all` + `state` field in JSON for issue enumeration:** closed issues
  are still in scope for the brief (they represent committed work that should
  appear in the story map, annotated as closed so `receive-brief` can triage
  them). The `state` field is included in `--json` so the story map can annotate
  each `US-n` with its current status. Traces to: Shape B user-story ACs.
- **Post-intake write-back is opt-in, per-action-type:** the `jira-brief-intake`
  precedent is read-only (its own spec choice); this skill departs from it with
  a bounded, always-confirmed surface. RFC-0019 does not mandate read-only.
  Body edits are permanently excluded — they mutate source-of-truth content the
  skill didn't author. Traces to: write-back AC.

### Dependencies & integration

- **`gh` CLI** (hard dependency, no degraded path for private repos without it).
  Verified via `gh auth status`; unauthenticated access attempted for public
  repos. `gh api` + `gh issue list` are the only verbs used.
- **`receive-brief` skill** (soft dependency; by-name dispatch). Detected at
  runtime; graceful-degradation path activates when absent.
- **`new-spec` skill** (soft dependency; by-name reference in redirect path).

### Failure & resilience

- **Unauthenticated + 404:** GitHub returns 404 for both a private repo and a
  nonexistent repo when called anonymously — the two are indistinguishable.
  The skill surfaces the verbatim ambiguous-error message (per AC-S3): "Repo or
  milestone not found — if this is a private repo, run `gh auth login` and
  retry; if it is public, check the owner/repo/milestone." It does not claim to
  know which case applies.
- **Empty milestone (no issues):** produce a brief with an empty Shape B section
  and a note for `receive-brief` to elicit stories.
- **`receive-brief` absent:** graceful-degradation branch runs. Note: `new-spec`
  and `work-loop` may also be absent; the branch acknowledges this.
- **Existing brief at slug:** require explicit overwrite confirmation before
  writing.

## Tasks

### T1: github pack skeleton

**Depends on:** none

**Touches:** `packs/github/pack.toml`, `packs/github/README.md`,
`packs/github/.claude-plugin/plugin.json`

**Tests:**
- `lint-packs` finds and validates `packs/github/pack.toml` without error
  (AC: Pack gate green).
- `agentbundle validate` passes for the new pack (AC: Pack gate green).

**Approach:**
- Create `packs/github/` directory.
- Author `pack.toml` using `packs/atlassian/pack.toml` as the template; set
  `name = "github"`, `version = "0.1.0"`, `default-scope = "user"`, update
  description, categories, keywords, adapter list (same set as atlassian).
- Author `README.md` (one-paragraph overview of the pack + skills table with
  `github-brief-intake`).
- Author `.claude-plugin/plugin.json` from the atlassian counterpart; update
  `name`, `description`, `version`.

**Done when:** `lint-packs` and `agentbundle validate` both pass for
`packs/github/`.

---

### T2: github-brief-intake SKILL.md + manifest.json

**Depends on:** T1

**Touches:** `packs/github/.apm/skills/github-brief-intake/SKILL.md`,
`packs/github/.apm/skills/github-brief-intake/manifest.json`

**Tests:**
- `lint-packs` passes with the skill directory present (AC: Pack gate green).
- Reading-level dry-run against `anthropics/claude-code` milestone "P1": `gh api
  repos/anthropics/claude-code/milestones` returns the milestone; `gh issue list
  --repo anthropics/claude-code --milestone "P1" --state all --json number,title,body,labels,url,state`
  returns issues including closed ones with `state` field present; the produced
  brief maps correctly (AC: skill pulls data via `gh` CLI only; AC: Shape B
  user stories; AC: `Epic:` pointer).
- Closed-issue annotation: at least one closed issue from "P1" appears in the
  story map annotated `[closed]` (AC: Shape B user stories, `--state all`).
- Auth path trace: (a) authenticated → proceeds; (b) unauthenticated + public
  repo → read succeeds, posture noted in brief Assumptions; (c) unauthenticated
  + 404 → ambiguous message surfaced verbatim: "Repo or milestone not found —
  if this is a private repo, run `gh auth login` and retry; if it is public,
  check the owner/repo/milestone." Confirm SKILL.md carries this exact string
  (AC-S3).
- Single-issue redirect trace: a bare issue-number input triggers the `new-spec`
  recommendation (AC: AC-S5).
- Absent-path trace: the graceful-degradation branch names `new-spec` and
  `work-loop` as potentially absent (AC: AC-S7).
- Write-back trace: the offer appears only after the brief is written, per-action-
  type confirmation is required, and no body-edit verb appears in the skill
  (AC: write-back AC-S8).

**Approach:**
- Model the skill structure on `jira-brief-intake/SKILL.md`.
- **Prerequisites section:** probe `gh auth status`; define exit paths (public
  degradation / private stop / `receive-brief` absent).
- **Lifecycle section — Stage 1 (Intake):**
  - Resolve `{owner}/{repo}` from the user's input or the current repo
    (`gh repo view --json owner,name`).
  - List milestones: `gh api repos/{owner}/{repo}/milestones --jq
    '[.[] | {number, title, description, html_url, open_issues, closed_issues}]'`.
  - If user provided a milestone title or number, match; else surface the list
    and ask.
  - Enumerate issues: `gh issue list --repo {owner}/{repo} --milestone <title> --state all --json
    number,title,body,labels,url,state` — include `state` (uppercase `"CLOSED"`) so
    closed issues are annotated in the story map.
- **Lifecycle section — Stage 2 (Map):**
  - Map milestone title → Outcome draft; description → context paragraph.
  - Map each issue → `US-n (#NNN) <story text>` in pinned format (reshape to
    *As a … I want … so that …* when title supports it; else verbatim).
  - Stamp `Epic: <milestone html_url>`.
  - Confirm slug; check for existing file.
- **Lifecycle section — Stage 3 (Hand-off):**
  - Write brief to `docs/product/briefs/<slug>.md`.
  - Hand off to `receive-brief` by name; include graceful-degradation branch.
- **Lifecycle section — Stage 4 (Post-intake write-back, optional):**
  - Offer comment / label / close per-action-type, each requiring explicit
    confirmation. Never offer body edits.
- Author `manifest.json` with:
  - `deps.skills = [{name: "receive-brief", source: "..."}]` — `receive-brief`
    is the only dispatched skill. `new-spec` is mentioned in the redirect path
    but only recommended, not dispatched; omitting it matches the dispatch-only
    precedent from `jira-brief-intake`.
  - `deps.system = [{name: "gh", minimum_version: "2.0", install_hint: "https://cli.github.com"}]`
    (hard system dependency; no degraded path for private repos without it).
  - **No credentialed frontmatter** — `gh` owns its credential chain; the skill
    never touches a token. Matches `jira-brief-intake` which also carries no
    credentialed flags.
  Structural shape follows jira-brief-intake's manifest.

**Done when:** reading-level dry-run passes all test traces above; `lint-packs`
still green.

---

### T3: how-to guide

**Depends on:** T2

**Touches:** `docs/guides/github/README.md`,
`docs/guides/github/how-to/intake-a-github-milestone-as-a-brief.md`

**Tests:**
- `ls docs/guides/github/how-to/` returns `intake-a-github-milestone-as-a-brief.md`
  (AC: guide file exists).
- `grep -c "gh auth status" docs/guides/github/how-to/intake-a-github-milestone-as-a-brief.md`
  ≥ 1 (AC: prerequisites covered).
- `grep -c "new-spec" docs/guides/github/how-to/intake-a-github-milestone-as-a-brief.md`
  ≥ 1 (AC: single-issue redirect documented).
- Manual read-through: a developer who has not read `SKILL.md` can follow the
  guide end-to-end without consulting it (AC: guide covers full intake flow).

**Approach:**
- Create `docs/guides/github/` with `how-to/` subdirectory.
- Author `README.md` (two-sentence pack overview; links the how-to guide).
- Author the how-to following Diátaxis task-orientation: prerequisites → steps
  → expected output → degradation paths → next step (link to `receive-brief`
  how-to). Write in present tense.

**Done when:** three `grep` checks above pass; manual read-through is
self-contained.

---

### T4: cross-cutting docs + pack gate

**Depends on:** T1, T2, T3

**Touches:** `docs/architecture/overview.md`, `docs/guides/README.md`,
`docs/product/changelog.md`

**Tests:**
- `grep -c "github" docs/architecture/overview.md` ≥ 1 and the row names
  `github-brief-intake` (AC: overview pack table updated).
- `grep -c "github" docs/guides/README.md` ≥ 1 (AC: guides index updated).
- `grep -c "github-brief-intake" docs/product/changelog.md` ≥ 1 (AC: changelog
  entry present).
- `make build` exits 0 and regenerates root `.claude-plugin/marketplace.json`
  (aggregate; per-pack source is `plugin.json` only — no per-pack `marketplace.json`)
  (AC: no build drift).
- `agentbundle pytest` (the package test suite) exits 0 (AC: pack gate green).

**Approach:**
- Add `github` row to the pack table in `docs/architecture/overview.md` (follow
  the atlassian row's format).
- Add `github` pack-index row to `docs/guides/README.md`.
- Add `[Unreleased]` entry to `docs/product/changelog.md` recording the new
  `github` pack and `github-brief-intake` skill.
- Create `docs/specs/m5-github-brief-intake/notes/fixture-snapshot.json` with
  the probed `gh api` milestone and `gh issue list` JSON outputs plus the
  synthetic open-issue and empty-milestone entries (per manual-verification
  steps 5-7 — keeps the dry-run reproducible if the live milestone drifts).
- Run `make build` to regenerate marketplace.json; verify no drift.
- Run `lint-packs`, `agentbundle validate`, and package pytest; fix any
  lint findings.

**Done when:** all five test checks above pass.

## Rollout

Prose-only change; no infra, no schema migration, no deployment sequencing.
Ships as a single PR. Reversible: remove `packs/github/` to roll back.

The new pack is user-scope-default (not repo-scope-default), so it does not
affect any existing repo unless the user explicitly installs it.

## Risks

- **`gh` CLI field-shape drift:** the JSON fields returned by `gh issue list
  --json ...` may change across `gh` versions. Risk is low (the CLI is stable);
  the manual-QA step in T2 verifies the current shape.
- **atlassian pack template drift:** if the atlassian pack's structure diverges
  significantly from the assumed shape between spec authoring and implementation,
  T1 may need adjustment. Review atlassian's `pack.toml` and `plugin.json`
  immediately before authoring T1.

## Changelog

- 2026-07-22: initial plan
