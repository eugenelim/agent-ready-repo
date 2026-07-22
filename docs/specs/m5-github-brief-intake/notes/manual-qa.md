# Manual QA — github-brief-intake

Dry-run verification against `fixture-snapshot.json`. Traced 2026-07-22.
Covers plan.md steps 1–8 (manual verification).

## Fixture

Real milestone: **anthropics/claude-code "P1"** (14 closed, 0 open issues).
Synthetic additions: one open issue (#9999) and one empty milestone.

---

## Step 1 — Auth posture (AC-S3)

`gh auth status` path traced:

| Posture | Expected SKILL.md response | Verdict |
|---|---|---|
| Authenticated | Proceed normally | ✓ covered (normal path) |
| Unauthenticated + public repo | Note posture in brief Assumptions, continue | ✓ covered (§ Prerequisites) |
| Unauthenticated + 404 | Surface verbatim: "Repo or milestone not found — if this is a private repo, run `gh auth login` and retry; if it is public, check the owner/repo/milestone." Stop. | ✓ verbatim match to spec AC-S3 |

## Step 2 — Milestone list + issue enumeration (AC-S2)

Commands exercised:

```
gh api repos/anthropics/claude-code/milestones \
  --jq '[.[] | {number, title, description, html_url, open_issues, closed_issues}]'
```

Expected output matches fixture: title "P1", html_url "https://github.com/anthropics/claude-code/milestone/1", closed_issues 14.

```
gh issue list --repo anthropics/claude-code --milestone "P1" --state all \
  --json number,title,body,labels,url,state
```

`--repo` flag is present (Blocker 2 fix confirmed in SKILL.md). Returns 14 issues, all with `"state": "CLOSED"`.

## Step 3 — Closed-issue annotation (AC-S4)

Fixture issue #1522, state: `"CLOSED"` (uppercase, as returned by `gh issue list`).
SKILL.md now compares `state == "CLOSED"` (uppercase fix from Blocker 1).

Expected story line:
```
- **US-1.** (#1522) [BUG] `_claude_fs_right:/Users...` URL crashes rust-analyzer [closed]
```

(Title carried verbatim — not story-shaped, no invented role/benefit.)

## Step 4 — Open-issue annotation (AC-S4 — non-annotated path)

Synthetic open issue #9999, state: `"OPEN"`.

Expected story line:
```
- **US-n.** (#9999) As a developer, I want streaming responses from the MCP bridge, so that long-running operations give feedback progressively.
```

No `[closed]` annotation. ✓

## Step 5 — Empty milestone (AC-S9)

Synthetic empty milestone: "Future work", 0 open, 0 closed issues.

Expected behavior: SKILL.md Stage 2 empty-milestone edge case fires.

Expected brief fragment:
```markdown
## User stories

No issues found in this milestone — `receive-brief` will elicit user stories during the Elicit stage.
```

Empty `## User stories` section + elicit note. Skill does not abort. ✓

## Step 6 — Single-issue redirect (AC-S5)

Path: user provides a single issue URL with no milestone container.
Expected: Skill surfaces recommendation to use `new-spec` and confirms before proceeding. ✓ (SKILL.md Stage 1 last paragraph)

## Step 7 — Graceful degradation (AC-S7)

When `receive-brief` is absent:
- Skill produces the brief (normal Stage 2 mapping)
- Stage 4 fires: inline decompose/execute instruction with note that `new-spec` and `work-loop` may also be absent ✓

## Step 8 — Results summary

| AC | Result |
|---|---|
| AC-S1 (skill exists, frontmatter, manifest) | ✓ |
| AC-S2 (gh commands only, --repo flag, correct JSON fields) | ✓ (after Blocker 2 fix) |
| AC-S3 (auth posture check, verbatim 404 message) | ✓ |
| AC-S4 (story format, CLOSED uppercase, [closed] annotation, html_url → Epic:) | ✓ (after Blocker 1 fix) |
| AC-S5 (single-issue redirect) | ✓ |
| AC-S6 (receive-brief by name) | ✓ |
| AC-S7 (graceful degradation, new-spec/work-loop noted absent) | ✓ |
| AC-S8 (post-intake write-back offered, separate confirmation, no body edits) | ✓ |
| AC-S9 (empty milestone → empty Shape B + elicit note, not abort) | ✓ |
| Pack gate (lint-packs, agentbundle validate, make build, pytest) | ✓ |
| Guide (prerequisites, full flow, auth-degradation, redirect, write-back) | ✓ |
| Docs (overview.md, guides/README.md, changelog.md, specs/README.md) | ✓ |

All ACs: **PASS**.
