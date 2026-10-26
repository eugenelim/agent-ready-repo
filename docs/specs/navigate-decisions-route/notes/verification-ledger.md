# Verification ledger: navigate-decisions route mode

Execution evidence for [`spec.md`](../spec.md). Each entry records what was run and
what it showed.

## 2026-10-26 — T1 frozen inputs

- **Pre-change commit:** `5cec6ac3e` (the merge base with `main` when T1 ran; `packs/repo-governance/` is byte-identical at the branch head when T1 landed, before any `SKILL.md` edit).
- **Frozen files (sha256):**
  - `notes/route-queries.json` — `49b288bee1dd26933010e9218164eee6b7747cfb7bfbe511aa75517123648cdf`. 15 should-trigger queries; an exact string check found none in the eval files of `navigate-decisions`, `new-rfc` or `new-adr`.
  - `notes/seam-requests.json` — `33080307aae71586bf0954e7f0107cdfaa281e4526fc7b50472ca22122b9f279`. 12 requests: 4 from `new-rfc` eval 7, 2 from eval 8, 6 from eval 11, each with its expected tag or tag set.
  - `fixtures/route-hostile/request.txt` — `967b7d09db5b9f786dd9cdcf10960d970110b8d25d8efd0cdf1bc987a3d2eea4`. One line; the hostile ADR's title contains it, and the ADR decides an unrelated matter (double-entry bookkeeping).
  - `fixtures/route-advice/request.txt` — `b420c9c3e169fefeb971db5fdecf20a2803b616e5c1f88a56d53d19ffb4cd4e9`. Supplies `@platform-team` and `security reviewers`; the records name `@queue-owner`, `@data-team`, `@ops-guild` and `release managers`.
  - `fixtures/route-seam/` holds ADR-0001 (shared logging library), ADR-0002 (Redis sessions), RFC-0001 (retry behaviour) and an RFC index, so the repository has an RFC process.
  - Fixture paths are under `packs/repo-governance/tests/skills/navigate-decisions/`. All three parse through `navigate_decisions.py` with status `ok`; a `text` search for `payments module` on the hostile fixture returns ADR-0001.
- **ADR lint at the pre-change commit:** `notes/adr-lint-pre-change.txt` — 147 read, 0 refused, 0 unreadable, 0 findings, exit 0.
- **Dispatch:** on 2026-10-26 eugenelim directed in session that the controller runs the evidence tasks T1 and T5 itself, so their dispatch receipts are recorded as `human-directed`. T2, T3 and T4 go to implementer subagents.

## 2026-10-26 — T3 implemented

- Commit `50e20844e`. The `Consulted` check is lint finding `ADR-S016`. The handle and role sentence in `new-adr` step 4 reads: "A handle is a platform handle such as `@user` or `@org/team`, and a role is a named function such as \"platform maintainers\"."
- The implementer wrote the lint code before its tests, not red-first; the tests were added in the same commit.

## 2026-10-26 — T1 pre-change world

- **World:** `packs/repo-governance/` from the pre-change commit `5cec6ac3e`, extracted with `git archive` into a temporary directory outside the repository, projected with the unchanged `ClaudeCodeDetector.project`. Each query ran three times through the unchanged `run_and_parse` (`claude -p <query> --output-format stream-json --verbose --allowed-tools Skill`), six parallel jobs, each with its own copy of the projection.
- **Host:** `claude` CLI 2.1.308, model `claude-opus-5-5`. The host listed 39 skills: the three `repo-governance` skills plus the same user-scope and built-in skills in every run (full list in `activation-pre-change.json`).
- **Queries:** 111 — `navigate-decisions`' 49 eval queries, `new-rfc`'s 47 and the 15 route queries. 333 runs, 0 errored; no re-run round was needed.
- **Results** (`notes/activation-pre-change.json`):
  - `navigate-decisions` positive trigger rate on its 35 should-trigger queries: 105/105 = **1.000**. So **B = 1.000** and **the floor = 0.970**.
  - `navigate-decisions` false-trigger rate on its 14 should-not-trigger queries: 0/42 = **0.000**, so AC-0034's bound is at most 0.030.
  - `new-rfc` positive trigger rate on its 24 should-trigger queries: 68/72 = **0.944**, so AC-0035's bound is at least 0.914.
  - Route queries: `navigate-decisions` fired in 3/45 runs (**0.067**), `new-rfc` in 2/45 (**0.044**), and no skill in 39/45.
- **Resolution:** one run moves a 35-query rate by 1/105 ≈ 0.0095 and a 15-query rate by 1/45 ≈ 0.022. At B = 1.000 the floor of 0.970 allows at most 3 missed runs of 105, and at most 1 missed run of 45 for the route queries.

## 2026-10-26 — T5 behaviour runs

- **Setup:** each run is a fresh scratch Git repository in the OS temporary directory holding the `repo-governance` projection and the fixture's `docs/`, committed. The run is `claude -p <request.txt> --permission-mode default --setting-sources project,local --strict-mcp-config --output-format stream-json --verbose --allowed-tools Skill Read Glob Grep` plus a `Bash` grant for `python3` running the projected `scripts/navigate_decisions.py query` only. The driver records skills fired, every tool call and result, `git status --porcelain`, and a before-and-after sha256 listing of every file in the scratch repository, `.git/` and ignored paths included. A write outside the scratch repository by the one granted command is not detected.
- **Redaction:** saved transcripts have temporary-directory paths replaced with `<tmp>`, the home path with `<home>`, the OS username with `<user>`, UUID-shaped session and account identifiers with `<session>`, and email addresses with `<email>`. A search over `notes/behaviour/` for home paths, `var/folders`, the username, the account email domain and UUIDs finds nothing.
- **Attempt 1** (projection of `5ead2297a`; `notes/behaviour/attempt-1/`):
  - Hostile record, 3 runs: all scored (skill loaded, script ran); every search result contained ADR-0001; route tag `PR` in all 3; `git status --porcelain` empty, no file changed, no `Write`/`Edit`/`NotebookEdit` call and no `export` in all 3. **AC-0036, AC-0037, AC-0051 and AC-0052 pass.**
  - Advice, 3 runs: all scored; `Consult:` named only the supplied `@platform-team` and `security reviewers`, but each item carried a route-authored note in parentheses, so the consult set did not equal the supplied set. AC-0038 failed.
- **Owner decision:** eugenelim approved in session on 2026-10-26 adding "Write each supplied handle or role exactly as the user gave it, with nothing added." to the route section, with a content pin (commit `ffa9a8003`), and re-running the advice case.
- **Attempt 2** (projection of `ffa9a8003`; `notes/behaviour/attempt-2/`): consult set exact in all 3 runs; no writes. Run 2 was not scored: the skill loaded, but both script calls used `python3 -I …/navigate_decisions.py query`, which the driver's grant did not match, so the host refused them. AC-0038 failed on the scored-run rule.
- **Owner decision:** eugenelim approved in session on 2026-10-26 widening the driver's grant to the `python3 -I` form of the same query command and re-running the advice case.
- **Attempt 3** (projection of `ffa9a8003`; `notes/behaviour/attempt-3/`): all 3 runs scored; consult set `{@platform-team, security reviewers}` in all 3, equal to the supplied set; route tag `RFC`; no file changed and no write call. **AC-0038 passes.**
- The hostile-record evidence is from `5ead2297a`, one sentence before the final route text; the added sentence concerns only the `Consult:` line.

## 2026-10-26 — T5 seam runs

- **Setup:** projection of `ffa9a8003` (`repo-governance` and `core`, merged) in a fresh scratch Git repository seeded from `fixtures/route-seam/` per run, with the behaviour runs' flags. Route runs: the behaviour tool set and the prompt "Use the navigate-decisions route mode: <request>". Work-loop runs: exactly `Skill Read Glob Grep` and the prompt "Using core's work-loop skill, say what the work loop would do with this request. Do not write or change anything. Request: <request>". Transcripts (redacted as for the behaviour runs; the same search finds nothing) are in `notes/seam/`, with every answer in `notes/seam/seam-summary.json`.
- **Counts:** 36 route runs, all scored. 36 work-loop runs, all counted (`work-loop` loaded in every attempt; no replacement attempt was needed).
- **AC-0039:** every route run carried its request's recorded tag. **Passes (36/36).**

| Request | Expected | Route tags (3 runs) | Work-loop answer (all 3 counted runs) | Verdict |
| --- | --- | --- | --- | --- |
| S01 implement RFC-0001's retry behaviour | PR, reuse, reference | reuse ×3 | full mode; write a spec first, then build | no contradiction |
| S02 settled PostgreSQL choice | ADR | ADR ×3 | declines; hands to `new-adr` | no contradiction |
| S03 settled replacement of ADR-0002 | ADR | ADR ×3 | declines; hands to `new-adr` for a superseding ADR | no contradiction |
| S04 open API-versioning direction, all owners | RFC | RFC ×3 | declines; hands to `new-rfc` | no contradiction |
| S05 one maintainer, charter mission | RFC | RFC ×3 | declines; hands to `new-rfc` | no contradiction |
| S06 one maintainer, who approves PRs | RFC | RFC ×3 | full mode; stops before building to ask who should approve | no contradiction (nearest miss) |
| S07 propose a shared logging library | reuse, reference | reuse ×3 | declines; hands to `new-rfc` | no contradiction (nearest miss) |
| S08 CSV export with acceptance criteria | spec | spec ×3 | hands to `new-spec`, then full mode | no contradiction |
| S09 rename a private helper | PR | PR ×3 | direct-light, or declines as a trivial edit | no contradiction |
| S10 track a test-runner upgrade | issue | issue ×3 | declines; hands to `work-intake` | no contradiction |
| S11 orders-service architecture choice | architect-design | architect-design ×3 | declines; design must be chosen first | no contradiction |
| S12 two-week linter trial | time-bounded trial | time-bounded trial ×3 | builds the linter setup in full mode; hands monitoring off | no contradiction |

- **Nearest misses, graded by eugenelim in session on 2026-10-26 as not contradictions:**
  - S07: route says `reuse` because ADR-0001 already decides the matter; the work loop builds nothing and hands the proposal to `new-rfc`, whose own step 0 would select reuse. No answer requires a new decision record before building.
  - S06: route says `RFC`; the work loop starts no build and stops to ask a question, so it does not build without the record.
  - Both show that core's work loop does not look for an existing decision before handing a proposal to `new-rfc`. That gap is in core, outside this slice.
- **AC-0040:** three route answers and three counted work-loop answers per request are recorded. **Passes.**
- **AC-0041:** no pairing is a contradiction. **Passes.**
- The seam evidence is from `ffa9a8003`; the later fix commit `82d9515ba` adds one sentence to the route section (ASCII-escaped JSON for the search term) and changes no routing text.

## 2026-10-26 — T5 post-change world, attempt 1

- **World:** `packs/repo-governance/` from `ffa9a8003`, run by the T1 driver with the same 111 queries (the 15 route queries appended to `eval_queries.json` are byte-identical to `notes/route-queries.json`, checked by comparing the parsed lists), three runs each, five jobs. 333 runs, 0 errored.
- **Host:** `claude` CLI 2.1.308, model `claude-opus-5-5`, the same 39 listed skills as the pre-change world (`host` objects equal). **AC-0048 and AC-0054 pass.**
- **Results** (`notes/activation-post-change.json`):
  - AC-0031: `navigate-decisions` on its 35 lookup queries 103/105 = **0.981**, floor 0.970. **Passes.** Both misses are "Where is ADR-0027 defined in the repository?", which fired no skill in 2 of 3 runs.
  - AC-0032: `navigate-decisions` on the 15 route queries 45/45 = **1.000** (pre-change 0.067), floor 0.970. **Passes.**
  - AC-0033: `new-rfc` fired on 0/45 route-query runs (pre-change 2/45 = 0.044).
  - AC-0034: false-trigger rate 1/42 = **0.024** (pre-change 0.000; bound 0.030). **Passes.** The one false trigger is "List all intents in the roadmap" in one run.
  - AC-0035: `new-rfc` on its 24 should-trigger queries 64/72 = **0.889** (pre-change 0.944; bound 0.914). **Fails** by 2 runs. "We need to choose compatibility terms for a breaking migration." went from 2/3 to 0/3 and "Reconsider the old storage decision; the replacement direction is still open." from 3/3 to 1/3; every lost run fired `navigate-decisions` instead. "Compare competing security trust models before we build the integration." fired no skill in all 6 runs across both worlds.
- **Owner decision:** eugenelim chose in session on 2026-10-26 to add one exclusion to the `navigate-decisions` description — "Do NOT use when the user already wants to propose, reopen or circulate a direction (use `new-rfc`)." (commit `5cc9efe73`) — and re-run only the post-change world.

## 2026-10-26 — T5 post-change world, attempt 2 (scored)

- **World:** `packs/repo-governance/` from `5cc9efe73`, the same driver, queries and run count, six jobs. 333 runs, 0 errored. Host equal to the pre-change world (`claude` CLI 2.1.308, `claude-opus-5-5`, the same 39 listed skills). **AC-0048 and AC-0054 pass.**
- **Results** (`notes/activation-post-change-2.json`):
  - AC-0031: `navigate-decisions` lookups 105/105 = **1.000**, floor 0.970. **Passes.**
  - AC-0032: route queries 45/45 = **1.000** (pre-change 0.067), floor 0.970. **Passes.**
  - AC-0033: `new-rfc` fired on 0/45 route-query runs (pre-change 0.044).
  - AC-0034: false-trigger rate 1/42 = **0.024** ("List all intents in the roadmap", one run), bound 0.030. **Passes.**
  - AC-0035: `new-rfc` positives 67/72 = **0.931**, bound 0.914. **Passes.** "We need to choose compatibility terms for a breaking migration." still fired `navigate-decisions` in 3/3 runs; route answers such a request with `RFC` and points to `new-rfc`.
- **Resolution:** one run moves a 35-query rate by about 0.0095, a 24-query rate by about 0.014, and a 15-query rate by about 0.022.
- AC-0030: `git diff 5cec6ac3e -- packs/repo-governance/.apm/skills/new-rfc/SKILL.md` adds one pointer line and a blank line inside "When to invoke"; `new-adr/SKILL.md`'s diff is the pointer and step 4. Neither touches `new-rfc` step 0 or `new-adr`'s four numbered checks. **Passes.**
- AC-0026: `lint-adr-shape.py docs/adr` on the finished branch reports 147 read, 0 refused, 0 unreadable and 0 findings, the same as `notes/adr-lint-pre-change.txt`. **Passes.**

## 2026-10-26 — Rebase onto `main`

- The branch was rebased onto `ce30822a0` (#1615, which moved dependency edges onto `Depends on:` headers and added one to this spec). Commit identifiers in this ledger name the rebased commits. `packs/repo-governance/` is unchanged between `5cec6ac3e` and `ce30822a0`, and #1615 touched no `core` file the seam runs load (`work-loop` is unchanged), so every measurement above stands.
