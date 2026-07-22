# When to use `linear-brief-intake` vs `linear-brief-sync`

**Use `linear-brief-intake` when:** you have a Linear Issue (with sub-issues)
or a Project and want to create a product brief from scratch.

**Use `linear-brief-sync` when:** a brief already exists at
`docs/product/briefs/<slug>.md` and the Linear Issue has changed since the
brief was written.

Never use `linear-brief-sync` to create a brief — it diffs an existing brief
against Linear. Never use `linear-brief-intake` on a brief that already exists
without confirming you want to overwrite or merge it.

## The sync lifecycle

A brief created by `linear-brief-intake` goes through this lifecycle:

1. **Intake** — `linear-brief-intake LIN-123` creates the brief draft and
   registers it under `[brief_queue].draft` in `workspace.toml`.
2. **Elicit / Decompose / Execute** — `receive-brief` fills gaps, decomposes
   into specs, and chains `new-spec` → `work-loop`. Brief Status moves to
   `Ready`, then `Executing`.
3. **Review round** — once ACs are drafted, they are pasted back into the
   Linear issue for stakeholder review. Reviewers may update the issue.
4. **Delta catch-up** — run `linear-brief-sync LIN-123` against the brief. It
   diffs only the Linear-sourced fields (Outcome and User stories), shows
   before/after for each change, and writes only what you approve.
5. **Lock** — while the brief is `Status: Executing`, sync refuses to run.
   Wait until execution completes before syncing.

## Prerequisites

### 1. Generate a Personal API Key

Linear → Settings → API → Personal API keys → Create key.

Copy the key — Linear only shows it once.

### 2. Store the key with `credential-setup`

```
credential-setup
```

Select namespace `linear` and key `API_KEY` when prompted. The key is stored
in `~/.agentbundle/credentials.env` (POSIX) or the OS keyring — it never
passes through the model.

### 3. Verify connectivity

```
linear: check
```

- Exit 0 → proceed.
- Exit 2 → re-run `credential-setup`; the key may have been revoked.

## `linear-brief-intake` — first-time brief from a Linear Issue

**When to use it:** You have an Issue (e.g., `LIN-123`) with at least one
sub-issue and want to turn it into a brief.

**What it does:**
1. Fetches the Issue and its sub-issues via `linear get-issue`.
2. Maps per the fixed table: issue title + description (verbatim) → `## Outcome`;
   sub-issues → `US-n` stories tagged `(LIN-NNN)`; `issue.project.url` → `Epic:`.
3. Confirms the slug before writing if a brief already exists at that path.
4. Writes `docs/product/briefs/<slug>.md`.
5. Registers the brief under `[brief_queue].draft` in `workspace.toml`.
6. Hands off to `receive-brief`.

**Invoke it:**

```
linear-brief-intake LIN-123
```

**Project intake.** For a Linear Project, pass the project UUID. If the project
has >10 issues, the skill surfaces the count and asks you to filter before
mapping to stories.

**Single-issue without children.** If the issue has no sub-issues, the skill
recommends `new-spec` instead and waits for your confirmation.

## `linear-brief-sync` — catch up an existing brief

**When to use it:** The Linear Issue has changed (Outcome, description, or
sub-issues) and you want to propagate those changes into the brief.

**What it does:**
1. Checks the brief's Status (refuses on Executing; confirms on Draft/Shipped).
2. Re-fetches the Issue via `linear get-issue <LIN-identifier>`.
3. Diffs only the **Linear-sourced fields**: `## Outcome` and `## User stories`.
4. Shows you a before/after for each changed section and waits for your approval.
5. Writes only the sections you approved.

**Invoke it:**

```
linear-brief-sync LIN-123 docs/product/briefs/my-feature.md
```

**Linear-sourced fields (the only ones diffed):**
- `## Outcome` — issue title + description (verbatim)
- `## User stories` — child issue identifiers and titles

**Protected fields (never changed by sync):** Scope/Non-goals, Appetite, Rabbit
holes, Instrumentation, Success metrics. These were either elicited by
`receive-brief` or written by PE — sync has no record of ever importing them
from Linear.

**Executing-lock.** Sync refuses when `Status: Executing` because a live build
may have AC-linked stories. Run sync after execution completes.

## Deciding which to use

| Situation | Skill |
|---|---|
| No brief exists yet; have a Linear Issue with sub-issues | `linear-brief-intake LIN-123` |
| No brief exists yet; have a Linear Project | `linear-brief-intake <project-uuid>` |
| Brief exists; Linear Issue Outcome or description changed | `linear-brief-sync LIN-123 docs/product/briefs/<slug>.md` |
| Brief exists; sub-issues added or removed in Linear | `linear-brief-sync LIN-123 docs/product/briefs/<slug>.md` |
| Brief Status is Executing | Wait until execution completes, then sync |
| Brief exists; want to change Appetite or Scope | Edit the brief directly — these are PE-authored |
