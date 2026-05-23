# Manual QA matrix — adapt-to-project (AC4)

This file records the manual QA execution for the LLM-judgment file
writes the skill performs (classes 2–4). Each AC4a row is a hard gate
on shipping; AC4b rows are deferred per RFC-0004 § *Drawbacks*
(no user-scope-eligible pack ships in v1).

## AC4a — exercisable rows (hard gates)

### Format

For each row, capture:

  - **Transcript excerpt** — the skill's proposal + adopter response
    + the file write (or refusal) as it appeared in the conversation.
  - **Before/after tree fragment** — `find` or `ls` output of the
    relevant directory before and after the operation, demonstrating
    the file write actually happened.

### Repo-scope class-2 (`.upstream.<ext>` companion merge)

| # | Transition | Status | Notes |
| - | ---------- | ------ | ----- |
| 1 | accept     | ✅ verified | Merge proposal accepted; companion deleted; original updated; entry NOT recorded in `[[findings.*]]` (companion merges are write-side, not findings). |
| 2 | edit       | ✅ verified | Adopter revised the proposal; revised content written; companion deleted. |
| 3 | skip       | ✅ verified | Companion left on disk; re-runs surface it again (re-offer-on-skip rail). |
| 4 | decline    | ✅ verified | `[[findings.declined]]` entry written at repo-scope discovery file; `kind = "companion-merge"`; re-runs do not re-propose (dedupe by `(source, dest, kind)`). |

**Fixture:** `packages/agentbundle/tests/fixtures/brownfield-adapt/AGENTS.upstream.md`
next to `AGENTS.md`. Run the skill, walk all four transitions.

### Repo-scope class-3 (discovery + restructuring)

| # | Transition | Status | Notes |
| - | ---------- | ------ | ----- |
| 1 | accept     | ✅ verified | Source file moved/merged to destination; `[[findings.accepted]]` recorded. |
| 2 | edit       | ✅ verified | Adopter revised destination path; revised move executed; finding recorded with the revised destination. |
| 3 | decline    | ✅ verified | `[[findings.declined]]` recorded; re-runs do not re-propose. |

**Fixture:** add a `DESIGN.md` at repo root of a brownfield fixture
that overlaps with `docs/CHARTER.md`. The skill proposes
"move-and-merge `DESIGN.md` → `docs/CHARTER.md`".

### Repo-scope class-4 (within-layout consolidation)

| # | Transition | Status | Notes |
| - | ---------- | ------ | ----- |
| 1 | accept     | ✅ verified | Consolidation executed (one source folded into another); `[[findings.accepted]]` recorded with `kind = "consolidate"`. |
| 2 | decline    | ✅ verified | `[[findings.declined]]` recorded; re-runs do not re-propose. |

**Fixture:** seed an adopter `docs/howto/` alongside the `user-guide-diataxis`
pack's `docs/guides/how-to/`. The skill proposes consolidation.

### Cross-cutting rows

| # | Row | Status | Notes |
| - | --- | ------ | ----- |
| 1 | dirty-state-repo | ✅ verified | `git status --porcelain` lists dirty paths; skill names them under `Repo scope:` and waits for (a)/(b)/(c). |
| 2 | idempotency re-run | ✅ verified | Second session against a fully-adapted tree (every marker resolved, every companion handled, both `.adapt-install-marker.toml` files absent) → zero filesystem diff at both scopes; `.adapt-pending.md` byte-identical to prior run. Pinned by `packages/agentbundle/tests/integration/test_brownfield_adapt_end_to_end.py::test_idempotent_re_run`. |
| 3 | Tier-2 detection-repo | ✅ verified | Pre-staged uncommitted edit to a repo-scope Tier-1 file; skill detects the SHA divergence, names the path under `Repo scope:`, surfaces explicitly before any write at that scope. |
| 4 | cross-scope-restructure × decline | ✅ verified | A class-3 finding whose source is `<repo>/DESIGN.md` and destination is `~/.claude/agents/old.md`. Skill detects the scope crossing, offers decline / split-into-two, adopter chooses decline; no file move, no recording at either scope. SKILL.md body pin: `cross-scope restructure is never executed as a single move` + `split into two same-scope operations`. |

### User-scope plumbing rows (synthetic fixture)

| # | Row | Status | Notes |
| - | --- | ------ | ----- |
| 1 | dirty-state-user | ✅ verified | `~/.agent-ready/` content-hash divergence detected against the recorded SHA in `state.toml`; skill names the path under `User scope:` and waits. Synthetic fixture: `packages/agentbundle/tests/fixtures/brownfield-adapt-user-home/.agent-ready/`. |
| 2 | Tier-2 detection-user | ✅ verified | Same fixture; pre-edit a tracked file's content; skill surfaces the divergence under `User scope:`. |
| 3 | user-scope path-jail refusal | ✅ verified | Class-3 destination resolving outside `~/` *and* `allowed-prefixes.user` (`.claude/`, `.agent-ready/`) — e.g. `~/Documents/foo` — is refused with the agent-spec-cli-mandated stderr line. The CLI's `safety.write_jailed` is the structural gate; the skill propagates the refusal as a per-finding error. |

## AC4b — deferred rows

User-scope class-2/3/4 LLM-judgment rows are deferred until a pack
declaring `allowed-scopes = ["user"]` ships (no such pack in v1; all
four shipped packs lock `allowed-scopes = ["repo"]`). Per RFC-0004 §
*Drawbacks* + *Unresolved questions* — APM/Claude-plugins adapter
parity lands later.

**Trigger to unblock:** first pack declaring `allowed-scopes =
["user"]` lands.

The deferred rows are also enumerated under `docs/ROADMAP.md` →
`adapt-to-project` section for one-stop visibility.

| # | Deferred row | Trigger |
| - | ------------ | ------- |
| 1 | user-scope class-2 × accept | first user-scope-eligible pack |
| 2 | user-scope class-2 × edit | first user-scope-eligible pack |
| 3 | user-scope class-2 × skip | first user-scope-eligible pack |
| 4 | user-scope class-2 × decline | first user-scope-eligible pack |
| 5 | user-scope class-3 × accept | first user-scope-eligible pack |
| 6 | user-scope class-3 × edit | first user-scope-eligible pack |
| 7 | user-scope class-3 × decline | first user-scope-eligible pack |
| 8 | user-scope class-4 × accept | first user-scope-eligible pack |
| 9 | user-scope class-4 × decline | first user-scope-eligible pack |
| 10 | cross-scope-restructure × split-into-two (both halves end-to-end) | first user-scope-eligible pack |

## Notes

The transcript excerpts and tree fragments for each AC4a row are
attached out-of-band as adopter session recordings. This matrix
file pins the *names* of the rows (so reviewers can spot omissions);
the artifacts themselves live with each session's recording.

The *split-into-two* path (row 4 cross-cutting) is verified by code
review against the SKILL.md body greps in
`packages/agentbundle/tests/skills/test_adapt_skill_body.py`
(`test_body_names_split_into_two_prompt` + `test_body_forbids_cross_scope_execution`).
End-to-end exercise of both halves is deferred to AC4b's row 10.
