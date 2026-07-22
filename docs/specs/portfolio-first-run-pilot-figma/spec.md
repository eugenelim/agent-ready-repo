# Spec: portfolio-first-run-pilot-figma

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Mode:** Full (security boundary: tutorial describes credentialed auth setup flow)
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 Amendment #4 (2026-07-21) — credentialed read-only archetype pilot; `portfolio-pack-first-value-contract` spec (Shipped)
- **Brief:** none
- **Discovery:** none

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The Figma pack's `[pack.first-value]` contract is authored and shipped
(`portfolio-pack-first-value-contract`). That contract declares the Figma pack
as the **credentialed read-only archetype** for the first-value overlay: a
non-technical user (a designer) installs the pack, supplies a Figma Personal
Access Token, and reads structure from a file they already own. The contract
describes the path. This spec proves it.

The deliverable is a step-by-step tutorial at
`docs/guides/figma/tutorials/figma-first-session.md` that a designer with no
terminal workflow can follow to reach the first visible result (a list of pages
and top-level frames from their own Figma file). The tutorial adds the `tutorial`
field to the Figma pack's `[pack.first-value]`, making the contract independently
verifiable: a fresh evaluator follows the tutorial, reaches the result, or names
a reproducible blocker.

This spec also corrects one factual error in the existing contract: the `verification`
field currently describes asking the agent to "list files in my Figma workspace,"
a capability the figma CLI does not have. The correct verification path is
`figma check` (exits 0 = authenticated) followed by `figma whoami` (returns
the account name). This is a factual correction, not a substantive design change;
it is in scope for this PR.

Three constraints shape this spec:

1. **No credential in any doc, prompt, fixture, or transcript.** The figma skill
   deliberately refuses token-on-the-command-line flags. The tutorial must never
   show, prompt for, or suggest embedding a real token.
2. **No new test harness.** The figma skill already has Tier-A activation coverage
   (`evals/eval_queries.json`). Live-auth behavior testing depends on the
   `behavior-check-for-backend-skills` backlog item. This spec reuses existing
   evidence; it does not invent a cassette or mock backend.
3. **Figma file content is untrusted data.** Page names, frame names, layer names,
   and comment text are author-controlled. The tutorial must note that the agent
   treats file content as data, not instructions. This boundary is owned by the
   figma skill's SKILL.md security rules; the tutorial acknowledges it.

## Boundaries

### Always do

- **Direct the user to install `credential-brokers` separately.** The figma pack
  requires `credbroker>=0.1.0` (pip), but the `credential-setup` skill ships in
  the `credential-brokers` pack, which is not auto-installed. The tutorial must
  include this as a prerequisite install step.
- **Describe credential-setup as user-initiated, not agent-chained.** The figma
  skill must not automatically invoke credential-setup when credentials are missing.
  The user asks Claude Code to "Set up credentials for Figma"; the agent then
  invokes the credential-setup skill. The token is entered at the `getpass`
  terminal prompt — not typed into the chat. The tutorial must make this clear.
- **Use `figma check` + `figma whoami` as the machine-level auth verification.**
  `check` is the documented entry point (SKILL.md Step 1); `whoami` returns the
  account name as human-visible confirmation. Exit 0 = proceed; exit 2 = user
  must act.
- **Tell the user to supply their own Figma file URL.** The starter-prompt in the
  contract does not embed a file URL. The tutorial must explain that the user
  pastes the URL from their browser. No synthetic or example URL.
- **Grade evidence honestly.** If a live transcript is absent, record
  `notes/surface-evidence.md` with grading "Limited" and a reproducible
  blocker, citing `behavior-check-for-backend-skills`. Do not invent a transcript.
- **Soft-wrap the tutorial.** One logical line per paragraph, blank line between,
  list items one line each (per AGENTS.local.md house style for `docs/guides/`).

### Ask first

- **If the `figma whoami` output shape seen live differs materially from what the
  tutorial implies.** The tutorial can describe the expected output in prose without
  quoting exact JSON; if live evidence shows a different shape, surface before
  finalising.
- **If the starter-prompt produces a different agent flow than described.** The
  contract starter-prompt has no embedded file URL; the agent may ask for it, or
  may attempt a workspace listing and fail. If the actual agent response path is
  materially different from the tutorial narrative, surface and wait.

### Never do

- **Embed a real Figma token, a `credentials.env` snippet, or any credential
  value anywhere in the tutorial, the spec, or the notes.**
- **Invent a `cassette/` directory, a mock Figma server, or any replay harness.**
  That belongs to `behavior-check-for-backend-skills`.
- **Add a `tutorial` field pointing to a path that does not exist on disk.**
  `lint-first-value-contract.py` fails the build if the path is absent; the
  tutorial file must exist before the pack.toml field is committed.
- **Change any other first-value contract field beyond `verification` (factual
  correction) and the added `tutorial` field.** `starter-prompt`, `recovery`,
  `starter-task`, `expected-result`, `next-action`, `prerequisites`, and
  `audience-posture` are frozen. Substantive contract changes are a separate RFC.
- **Duplicate first-value facts into the tutorial's prose.** The tutorial may
  reference what the user should see; it must not carry a separate
  audience/surface/prerequisite table that duplicates `[pack.first-value]`.

## Testing Strategy

**Tutorial file (AC1–AC10):** Visual / manual QA. Read the tutorial against the
AC1–AC10 checklist: each required section present, no credential embedded
(`.github/workflows/ci-security.yml` gitleaks is the authoritative PR gate; author-time aid: `grep -r "figd_\|FIGMA_API_TOKEN=" docs/guides/figma/tutorials/` scoped to the tutorial only — the spec itself references the pattern in AC prose).

**Contract wiring and factual correction (AC11–AC14):** Goal-based checks.
- `python3 tools/lint-first-value-contract.py --root .` exits 0.
- `git diff packs/figma/pack.toml` shows only the added `tutorial` line, the
  corrected `verification` line, and the version bump — no other field modified.
- Both `pack.toml` and `.claude-plugin/plugin.json` carry version `0.1.6`.

**Build (AC15):** Goal-based.
- `make build-self FORCE=1` exits 0.
- `make build-check` exits 0.

**Surface evidence (AC16):** Visual / manual QA of the evidence document.
- `notes/surface-evidence.md` exists with grading and a dated entry.

## Acceptance Criteria

### AC1 — Tutorial file exists

- [x] `docs/guides/figma/tutorials/figma-first-session.md` exists.
- [x] The file opens with a one-sentence outcome statement: what the reader
  will have accomplished by the end.

### AC2 — Prerequisite disclosure

- [x] The tutorial names the two prerequisites from `[pack.first-value]`:
  (1) a Figma Personal Access Token, (2) access to a Figma file with at
  least view permission.
- [x] The tutorial tells the user where to generate a PAT (Figma → Settings →
  Security → Personal access tokens) without embedding a token value.
- [x] The tutorial states that the `credential-brokers` pack must be installed
  before the `credential-setup` step, and that it is a separate install from
  the figma pack.
- [x] The tutorial includes a one-time `pip install` step for the figma skill's
  Python dependencies (`credbroker`, `httpx`), documented as a prerequisite or
  in the recovery section.

### AC3 — Credential setup path

- [x] The tutorial tells the user to invoke `credential-setup` by asking Claude
  Code to "Set up credentials for Figma" — the user initiates the skill; it
  does not auto-run from the figma skill when credentials are missing.
- [x] The tutorial includes an explicit user-facing caution: the token lives in
  the credential file; the user must never type or paste it into the chat
  with the agent.
- [x] The tutorial does not show any command that passes `--token` or any
  credential flag to the figma CLI.
- [x] The tutorial does not quote or show the contents of
  `~/.agentbundle/credentials.env`.

### AC4 — Check verification step

- [x] The tutorial tells the user to ask the agent to verify the Figma connection
  (the agent runs `figma check` and, on success, `figma whoami`).
- [x] The tutorial describes the two outcomes: connection confirmed with account
  name → proceed; authentication error → see recovery (AC8).
- [x] The tutorial does not describe exit codes to the user; it describes
  the user-visible agent response.

### AC5 — Starter task

- [x] The tutorial walks the user through the starter task: asking the agent
  to read a Figma file's structure and list page names and top-level frames.
- [x] The tutorial tells the user to include their Figma file URL (or bare
  file key) in the message.
- [x] The tutorial does not embed a specific file URL or key.

### AC6 — Expected result

- [x] The tutorial describes what a successful result looks like: the agent
  returns a list of page names and top-level frame names from the specified file.
- [x] The description matches the `expected-result` value in `[pack.first-value]`:
  "A list of pages and top-level frames from your Figma file, showing the design's
  navigation structure."

### AC7 — Untrusted content note

- [x] The tutorial notes (at least once) that the agent treats file content —
  page names, frame names, layer names — as data to report, not as instructions
  to follow. This is consistent with the figma skill's security rules.

### AC8 — Recovery path

- [x] The tutorial covers the recovery path for a failed auth (exit 2 from
  `figma check`): regenerate the PAT at Figma → Settings, re-run
  `credential-setup`, then retry.
- [x] The recovery section covers the wrong-scope PAT case: a 403 maps to exit 2
  (user must act). For basic file/page reading, no specific scope is required
  beyond a valid PAT; `file_dev_resources:read` scope is only needed for Dev
  Resources (not the starter task). The recovery section does not claim a specific
  scope name is required for basic file access.
- [x] The tutorial does not tell the user to share their token with the agent
  or paste it into a chat message.

### AC9 — Next steps

- [x] The tutorial ends with a next-step pointer matching the `next-action`
  value from `[pack.first-value]`: asking the agent to export a specific frame
  as a Markdown description.
- [x] The tutorial links to the existing how-to guide
  (`docs/guides/figma/how-to/inspect-a-figma-file.md`) for more operations.

### AC10 — No credential in any authored artifact

- [x] `gitleaks` (`.github/workflows/ci-security.yml`, PR-gated) is the
  authoritative gate for credential detection.
- [x] Author-time aid: `grep -r "figd_\|FIGMA_API_TOKEN=" docs/guides/figma/tutorials/` returns zero matches (scoped to the tutorial only; the spec itself references the pattern in AC text).
- [x] No hardcoded Figma file key or URL appears in the tutorial.

### AC11 — tutorial field added to pack.toml

- [x] `packs/figma/pack.toml` `[pack.first-value]` section gains:
  `tutorial = "docs/guides/figma/tutorials/figma-first-session.md"`

### AC12 — verification field corrected in pack.toml

- [x] The `verification` field in `[pack.first-value]` is updated from the
  non-functional workspace-listing prompt to an accurate description:
  "Ask the agent to check your Figma connection; it should confirm your account
  name is visible with no authentication error." (≤ 160 chars)
- [x] No other `[pack.first-value]` fields are modified. `git diff packs/figma/pack.toml`
  shows only the added `tutorial` line, the corrected `verification` line, and
  the version bump.

### AC13 — lint-first-value-contract passes

- [x] `python3 tools/lint-first-value-contract.py --root .` exits 0 with the
  `tutorial` field present and the `verification` field updated.
- [x] The tutorial path resolves on disk relative to the repo root.

### AC14 — Pack version bumped

- [x] `packs/figma/pack.toml` version is `0.1.6` (was `0.1.5`).
- [x] `packs/figma/.claude-plugin/plugin.json` version is `0.1.6`.

### AC15 — build-check passes

- [x] `make build-self FORCE=1` exits 0 after all pack edits.
- [x] `make build-check` exits 0.

### AC16 — Surface evidence document

- [x] `docs/specs/portfolio-first-run-pilot-figma/notes/surface-evidence.md`
  exists and contains:
  - A dated entry (2026-07-22).
  - An honest grading: "Verified" if a live transcript exists, "Limited" with
    a reproducible blocker if it does not.
  - The specific blocker for a live transcript: no Figma PAT available in this
    authoring session; live-auth behavior testing blocked on
    `behavior-check-for-backend-skills`.
  - A note that any future "Verified" transcript must redact `whoami` PII
    (name, email) and any credential value before it is committed.

## Assumptions

1. `credential-brokers` does not auto-install with the figma pack.
   **Confirmed 2026-07-22:** `packs/figma/pack.toml [pack.install]` has no
   dependency mechanism; credential-brokers is a separate install. The tutorial
   must list it as a prerequisite install step (AC2).
2. The `credential-setup` skill ships in the `credential-brokers` pack and is
   available after that pack is installed. If this is false, AC3 needs updating.
3. The figma skill ships `credbroker>=0.1.0` in `requirements.txt`; users run
   `pip install -r requirements.txt` once to install it (SKILL.md Step 1).
4. `figma check` is the documented auth verification step (SKILL.md Step 1);
   `figma whoami` returns the account name as human-visible confirmation. Both
   work after credentials are set up via `credential-setup`.
5. The `tutorial` field validator checks path existence relative to `--root`
   (confirmed from `portfolio-pack-first-value-contract` AC2).
6. The `behavior-check-for-backend-skills` backlog item owns live behavior
   testing for backend-credentialed skills. This spec does not duplicate it.
7. No live Figma PAT is available in this authoring session. The surface
   evidence grading will be "Limited" with the documented blocker.
8. The `verification` field correction is a factual fix, not a substantive
   design change: the workspace-listing prompt described a capability the figma
   CLI does not have (no workspace file-list subcommand or REST endpoint is
   wrapped). The correction uses the accurate `check`/`whoami` path confirmed
   in SKILL.md Step 1 and the `figma.py` `check` + `whoami` subcommands.

## Changelog

<!-- Add an entry under [Unreleased] in docs/product/changelog.md when this
     spec is implemented. Format: feature bullet, one line. -->
