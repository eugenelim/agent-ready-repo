# Example: lean-canvas — INI-003 AI-Assisted Developer Workflows

A product engineering lead runs `lean-canvas` after completing steps 5
(`place-bet`) and 6 (`map-capabilities`) for INI-003. Two upstream shaping
artifacts exist — a bet and a capability-map — so several Lean Canvas fields
are pre-populated. The team chooses simple mode (5 boxes) because the
initiative's hypothesis is clear enough; channels, cost, and buy-in are
deferred to strategy review.

---

# Initiative: AI-Assisted Developer Workflows

- **ID:** `INI-003`
- **Name:** AI-Assisted Developer Workflows
- **Status:** Active
- **Appetite:** 2–3 quarters
- **Owner:** engineering-lead
- **workspace.toml section:** `["ini-003"]` in `workspace.toml`

## Outcome

Engineers across all product squads spend less time on routine code-review
coordination and first-pass code quality triage. By end of initiative, the
median PR cycle time for non-urgent changes drops by 30%, and first-pass
review coverage reaches 100% of opened PRs — with AI-generated review comments
serving as the first filter before human reviewers engage.

## Value Proposition

*Elicited via simple-mode Lean Canvas (5 boxes). Pre-populated from upstream
bet and capability-map; user confirmed or overrode each field.*

**Problem**

Engineers spend 20–40% of their review cycle waiting for the first reviewer to
engage. Routine issues (style violations, missing docs, obvious logic gaps) are
caught late, making human review slower and harder to triage.

**Unique Value Proposition**

First-pass review coverage on every PR within minutes of opening — so human
reviewers spend their time on architectural and semantic concerns, not
mechanical checks.

**Solution**

1. An agent-powered review bot that runs on PR open, scans for patterns the
   team has defined as routine, and posts structured inline comments.
2. A triage summary posted to the PR description — what was found, what needs
   human attention, what was cleared.
3. A signal dashboard surfacing review-latency trends per squad and per repo.

**Customer Segments**

- Squads with >5 active PRs per week per engineer (highest latency)
- Engineering leads who set review SLOs but lack visibility into bottlenecks
- New contributors who get the least organic review bandwidth

**Key Metrics**

- Median PR cycle time (target: -30% at 90 days)
- First-pass review coverage rate (target: 100% within 15 min of PR open)
- Human reviewer time per PR (target: -25% routine-comment volume)

## Scope

**In scope:**

- PR review bot with configurable pattern library per repo
- Triage summary comment posted on PR open
- Review-latency signal dashboard (read-only, squad-scoped)
- Integration with GitHub PR events; no other VCS in scope

**Non-goals / out of scope:**

- Automated merging or auto-approval — human approval gate is unchanged
- Review bots for design artifacts, docs PRs, or infrastructure changes (v1)
- LLM-generated code suggestions or refactors — review-only in v1

## Capability areas

| Capability | Description | Status |
| --- | --- | --- |
| PR event ingestion | Subscribe to GitHub PR webhook events; route to review pipeline | shaping |
| Pattern-library engine | Configurable per-repo rule library; runs on PR diff | shaping |
| Comment authoring | Structure and post inline review comments to GitHub | shaping |
| Latency dashboard | Aggregate PR timing data; expose squad-scoped view | shaping |

## Milestone sequence

| Milestone | Scope summary | Target quarter |
| --- | --- | --- |
| M1 | PR event ingestion + pattern-library engine (internal only) | Q3 2026 |
| M2 | Comment authoring live on 2 pilot squads | Q3 2026 |
| M3 | Latency dashboard; expand to all squads | Q4 2026 |

## Links

- `workspace.toml` initiative section: `["ini-003"]`
- Parent: Developer Experience OKR, FY26 H2
- Shaping artifacts: `docs/product/shaping/ini-003/`
