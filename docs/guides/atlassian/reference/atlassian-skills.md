# `atlassian` skills

Every skill in the `atlassian` pack. One entry each: purpose, primary inputs, outputs, and required credentials.

Credentialed skills resolve secrets in-process through the tier ladder (environment variable → OS keyring → `~/.agentbundle/credentials.env` dotfile); see [Credentialed skills](../../credential-brokers/explanation/credentialed-skills.md).

## `jira`

- **Purpose.** Read and mutate Jira (Atlassian Cloud or self-hosted Server / Data Center) via the REST API. JQL search with auto-pagination; fetch issues, projects, and users; create, update, delete, and transition issues; comment; attach; raw escape hatch. Auto-detects Cloud (REST v3, ADF, `nextPageToken`) vs Server / DC (REST v2, plain text, `startAt`) from the base URL host.
- **Primary inputs.** Subcommands: `check`, `whoami`, `get-issue`, `search`, `create-issue`, `update-issue`, `delete-issue`, `list-transitions`, `transition`, `comment`, `attach`, `get-project`, `list-projects`, `get-user`, `list-users`, `raw`. Global flags: `--format json|jsonl|csv`, `--output FILE`, `--verbose`, `--insecure`. `search` takes `--fields`, `--limit`, `--page-size` (≤ 100); write subcommands take repeatable `--field KEY=VALUE` (JSON-parsed) or `--data-file`; `delete-issue` requires `--yes`.
- **Outputs.** Issue / project / user JSON, JSONL, or CSV to stdout or `--output`. Read-only and mutating both available.
- **Required credentials.** `JIRA_BASE_URL` (required), `JIRA_API_TOKEN` (required), `JIRA_EMAIL` (Cloud only), `JIRA_FLAVOR` (optional — auto-detected). Cloud token from `id.atlassian.com → API tokens`; Server PAT from the user's profile.
- **Auth (dual).** `auth: sso-cookie` with a `creds` fallback (RFC-0035). On a Data Center instance behind corporate SSO where tokens are blocked, pre-bake `references/sso-config.toml` (`auth_default = "sso-cookie"`) and run `python scripts/setup_sso.py` once; reads then authenticate by a captured web session (no token). Absent SSO config, the token path above is unchanged. Cookie-path reads only (writes are refused pending XSRF design).
- **Source.** [`jira`](../../../../packs/atlassian/.apm/skills/jira/)

## `jira-align`

- **Purpose.** Read and mutate Jira Align (Cloud or self-hosted / on-prem) via REST API 2.0. Fetch individual records; paginate collections with OData-style `$filter` / `$select` / `$orderby` / `expand`; create, update (PUT or PATCH), and delete records; raw escape hatch. A separate product from Jira, with separate credentials.
- **Primary inputs.** Subcommands: `check`, `whoami`, `get`, `list`, `search`, `create`, `update`, `delete`, `raw`. Resources mirror the URL segment (`epics`, `features`, `stories`, `capabilities`, `themes`, `portfolios`, `programs`, `teams`, `users`, `sprints`, etc.). Global flags: `--format json|jsonl|csv`, `--output FILE`, `--verbose`, `--insecure`. `list` takes `--filter`, `--select`, `--orderby`, `--expand`, `--limit`; `update` takes `--method PATCH`; `create` / `update` take repeatable `--field KEY=VALUE` or `--data-file`; `delete` requires `--yes`.
- **Outputs.** Record JSON, JSONL, or CSV to stdout or `--output`.
- **Required credentials.** `JIRAALIGN_BASE_URL` (required), `JIRAALIGN_API_TOKEN` (required), `JIRAALIGN_FLAVOR` (optional — auto-detected). Personal API Token from the Jira Align Profile page.
- **Source.** [`jira-align`](../../../../packs/atlassian/.apm/skills/jira-align/)

## `confluence-crawler`

- **Purpose.** Crawl an authenticated Confluence space (Cloud or Server / Data Center) by page hierarchy and convert each page to Markdown with YAML frontmatter. Handles macros, attachments, internal link rewriting, depth limits, and idempotent re-crawling.
- **Primary inputs.** `crawl_space.py` with `--check`, `--space KEY` (required), `--root PAGE_ID`, `--depth N`, `--output DIR` (default `./confluence-out`), `--force`, `--no-attachments`, `--concurrency N` (default 4), `--min-delay-ms N` (default 100), `--insecure`, `--verbose`.
- **Outputs.** `<output>/<slug>.md` per page (flat layout) with frontmatter (`confluence_id`, `version`, `space_key`, `updated`, `author`, `parent_id`, `labels`, `url`, `slug`); `<output>/attachments/<page_id>/<filename>` for attachments. Final log line `wrote N pages (failed: X, skipped: Y)`.
- **Required credentials.** `CONFLUENCE_BASE_URL` (required — Cloud must include `/wiki`), `CONFLUENCE_API_TOKEN` (required), `CONFLUENCE_EMAIL` (Cloud only), `CONFLUENCE_FLAVOR` (optional — auto-detected). Shares the `confluence` namespace with `confluence-publisher`.
- **Auth (dual).** `auth: sso-cookie` with a `creds` fallback (RFC-0035), like `jira`: on a Data Center instance behind corporate SSO, pre-bake `references/sso-config.toml` and run `python scripts/setup_sso.py` once to crawl by captured web session. Absent SSO config, the token path is unchanged.
- **Source.** [`confluence-crawler`](../../../../packs/atlassian/.apm/skills/confluence-crawler/)

## `confluence-publisher`

- **Purpose.** Publish content to a Confluence page (Cloud or Server / Data Center) by creating a new page or updating an existing one. Accepts Markdown (default), storage XHTML, or plain text. Handles optimistic-locking 409s with one retry.
- **Primary inputs.** `publish_page.py` with `--check`; target via `--page-id ID`, `--url URL`, `--from-frontmatter`, or `--space KEY --title TITLE [--parent-id ID]`; `--input PATH` or `-` (required); `--input-format markdown|storage|text`; `--version-comment TEXT`; repeatable `--attach PATH` and `--label LABEL`; `--dry-run`, `--insecure`, `--verbose`.
- **Outputs.** On success, a line naming the operation, page ID, new version, and URL: `OK: <create|update> page <id> (version N) — <url>`. `--dry-run` prints rendered storage XHTML and the planned operation without writing.
- **Required credentials.** Same `confluence` namespace and schema as `confluence-crawler`; configuring either skill satisfies both.
- **Source.** [`confluence-publisher`](../../../../packs/atlassian/.apm/skills/confluence-publisher/)

## `flow-metrics`

- **Purpose.** Compute DORA / Flow Framework metrics over a Jira scope — cycle time, lead time, throughput, WIP, flow load, rework rate, flow time, flow efficiency, flow distribution, defect ratio — from Jira changelogs, optionally joined with Jira Align for program / portfolio scope. Read-only; composes the `jira` and `jira-align` skills, never reads credentials itself.
- **Primary inputs.** `flow-metrics` shim (or `python -m flow_metrics`). Exactly one of `--project KEY`, `--program-id ID`, `--portfolio-id ID` (required). `--team NAME` (project scope only), `--from`/`--to ISO` (default last 90 days), `--jql`, `--align-filter`, `--cohort-jql`, `--metrics LIST` (default all ten), `--state-config`, `--issuetype-config`, `--team-field-override`, `--align-join-field`, `--align-teams-path`, `--include-subtasks`, `--format json|csv`, `--output FILE`, `--per-issue` (requires `--output`), `--no-cache`, `--verbose`, `--yes`.
- **Outputs.** Canonical JSON or CSV with `meta`, `aggregates`, optional `cohort_breakdown`, optional `per_team`, and `notes`; pinned by `references/output.schema.json`. `--per-issue` emits one JSONL row per issue. On-disk cache at `.context/flow-metrics/cache/`.
- **Required credentials.** None of its own — inherited through the `jira` skill (and `jira-align` for Align scope).
- **Source.** [`flow-metrics`](../../../../packs/atlassian/.apm/skills/flow-metrics/)

## `ai-adoption-report`

- **Purpose.** Pair `flow-metrics` JSON outputs and render a Markdown comparison report. Three modes: `baseline` (one scope, two windows), `cohort` (within-window AI vs control), `program` (roll up many scopes for one window). Read-only; makes no upstream calls.
- **Primary inputs.** `ai-adoption-report` shim (or `python -m ai_adoption_report`) plus a mode. `baseline`: `--baseline PATH`, `--current PATH`, `--include-cohort-breakdown`. `cohort`: `--input PATH`. `program`: `--inputs DIR`, `--window FROM..TO`, `--include-cohort-breakdown`. Common: `--output FILE`, `--format markdown|json|both` (default `both`), `--overwrite`, `--title`, `--verbose`. Input paths are literal; absolute paths outside CWD exit 2.
- **Outputs.** A Markdown report at `--output` and (by default) a JSON sidecar at the same path with `.md` replaced by `.json`. Markdown sections: title, header line, `## Summary`, `## Metric deltas`, `## Per-scope rows` (program), `## Cohort breakdown` (when requested), `## Notes`, `## Provenance`.
- **Required credentials.** None — consumes local JSON files only.
- **Source.** [`ai-adoption-report`](../../../../packs/atlassian/.apm/skills/ai-adoption-report/)

## `jira-align-brief-intake`

- **Purpose.** Turn a Jira Align Feature into a product brief and shippable specs. Fetches the Feature and its child stories, tasks, and defects via the `jira-align` skill, maps them onto a Shape B product brief (Feature title/description → Outcome, children → `US-n` user stories tagged with their Jira Align IDs, Feature ID → `Epic:` provenance pointer), writes it to `docs/product/briefs/<slug>.md`, and hands off to the `receive-brief` skill to elicit gaps, decompose, and build. 1-way intake only — never writes to Jira Align. Requires one-time customisation of the field mapping reference (`references/field-mapping.md`) for org-specific workflow state names and Program Increment cadences.
- **Primary inputs.** A Jira Align Feature ID. Composes sibling and host skills by name: `jira-align` (reads only — `check`, `get features`, `list stories`/`tasks`/`defects` with `featureID eq` filter) and `receive-brief` (soft dependency — degrades gracefully when absent).
- **Outputs.** A Shape B product brief at `docs/product/briefs/<slug>.md`, then a hand-off to `receive-brief` (or an inlined decompose/execute instruction in the degraded path).
- **Required credentials.** None of its own — Jira Align access is inherited through the `jira-align` skill (`JIRAALIGN_BASE_URL`, `JIRAALIGN_API_TOKEN`).
- **Source.** [`jira-align-brief-intake`](../../../../packs/atlassian/.apm/skills/jira-align-brief-intake/)

## `jira-defect-flow`

- **Purpose.** Handle a Jira defect end-to-end. Pulls the ticket via the `jira` skill, hands the fix to the `bug-fix` skill, opens a PR linking back to Jira, then comments and transitions the ticket. Stops at PR-opened by default; runs a dev-deploy step only when the consumer repo provides one. For defects, not stories, tasks, or feature work.
- **Primary inputs.** A Jira issue key. Composes sibling and host skills by name: `jira`, `bug-fix`, and the reviewer subagents. Branch naming via `scripts/branch_name.py $KEY "$SUMMARY"` (override prefix with `--prefix` or `JIRA_DEFECT_FIX_PREFIX`). Optional dev-deploy via `$DEPLOY_DEV_CMD` or an executable `.context/deploy_dev.sh`.
- **Outputs.** A triage brief at `.context/defects/$KEY.md`, a feature branch, a PR whose `Why?` section carries `Closes: $KEY`, and Jira comments plus transitions on the ticket.
- **Required credentials.** None of its own — Jira access is inherited through the `jira` skill. Requires `gh auth` for PR opening.
- **Source.** [`jira-defect-flow`](../../../../packs/atlassian/.apm/skills/jira-defect-flow/)

## `jira-story-triage`

- **Purpose.** Review a Jira backlog, sprint, or JQL-scoped set of work items for readiness to hand to engineering, and improve the weak ones. For every item that is not ready, it explains *why* — which of the five-question bar's questions failed (self-contained change, reachable repo scope, checkable ACs, no mid-flight decision, right-sized for one PR) and the specific gap — rather than a bare tier label. On request it drafts the fix (acceptance criteria, a clearer outcome, a tighter scope) and writes it back via `update-issue` **only after the user approves the exact drafted payload**. Read-only until an approval; the write flow is opt-in and per-item. Use this to judge and fix item quality; use `jira-team-status` for a read-only status snapshot and what to pick up next.
- **Primary inputs.** A Jira project key + optional sprint or JQL filter; optional repo URL for grounding.
- **Outputs.** A reason-first readiness review: one row per item with an outcome (Ready for engineering / Gated / Not ready — needs shaping / Needs detail), complexity for Ready items, and a "Why not ready" column naming the failed question(s) and gap. Followed by an opt-in improve flow (draft → approve → `update-issue`, one confirmation per item).
- **Required credentials.** None of its own — inherited through the `jira` skill.
- **Source.** [`jira-story-triage`](../../../../packs/atlassian/.apm/skills/jira-story-triage/)

## `jira-team-status`

- **Purpose.** A read-only status view of a team's Jira work, organized by the dimensions people ask about — **Ready to pull, In progress, Blocked, Unassigned, and Needs detail (product attention)**, plus recently-changed and stale markers — for sprint, stand-up, and team-status summaries. "Ready to pull" is a documented, team-overridable rule (in scope + eligible backlog state, default `statusCategory = "To Do"` + no known blocker + meets the five-question readiness bar); signals it can't read are labelled "needs confirmation" rather than asserted. Ends in a read-only pick-up hand-off: start delivery on a ready item (routing to `jira-defect-flow` for bugs or `new-spec` for tasks/stories) or route an item that needs detail to `jira-story-triage`. Read-only by default; its only write is a confirmed bare pass-through to the `jira` skill's `update-issue` when the user explicitly asks to set a field. Use `jira-story-triage` instead to judge readiness in depth or improve weak items.
- **Primary inputs.** A Jira project key (one or several) + optional sprint (default: open sprints), team name, JQL filter, or whole-backlog scope; optional repo URL for grounding.
- **Outputs.** A five-section snapshot: §1 Ready to pull (grouped Quick/Standard/Involved), §2 In progress, §3 Blocked, §4 Unassigned, §5 Needs detail — plus a recently-changed note, stale markers, and a coverage-disclosing summary line. Followed by a read-only pick-up hand-off (start-delivery routing, or a route to `jira-story-triage` for improvement). A confirmed bare pass-through `update-issue` only on an explicit user request.
- **Required credentials.** None of its own — inherited through the `jira` skill.
- **Source.** [`jira-team-status`](../../../../packs/atlassian/.apm/skills/jira-team-status/)

## `jira-brief-intake`

- **Purpose.** Turn a Jira epic (or a board / sprint / JQL selection) into shippable specs. Pulls the epic and its children via the `jira` skill, maps them onto a Shape B product brief (epic → Outcome, child issues → `US-n` user stories tagged with their Jira key, epic key → `Epic:` provenance pointer), writes it to `docs/product/briefs/<slug>.md`, and hands off to the `receive-brief` skill to elicit gaps, decompose, and build. Read-only against Jira; gracefully degrades to an inlined decompose/execute instruction when `receive-brief` is absent. For an epic or multi-feature body of work — a single feature goes through `new-spec`, a defect through `jira-defect-flow`.
- **Primary inputs.** A Jira epic key, or a JQL / board / sprint selection. Composes sibling and host skills by name: `jira` (reads only — `check`, `get-issue`, `search` with a flavor-correct child query) and `receive-brief` (soft dependency — degrades gracefully when absent).
- **Outputs.** A Shape B product brief at `docs/product/briefs/<slug>.md`, then a hand-off to `receive-brief` (or an inlined decompose/execute instruction in the degraded path).
- **Required credentials.** None of its own — Jira access is inherited through the `jira` skill.
- **Source.** [`jira-brief-intake`](../../../../packs/atlassian/.apm/skills/jira-brief-intake/)
