# Verification ledger: navigate-decisions route mode

Execution evidence for [`spec.md`](../spec.md). Each entry records what was run and
what it showed.

## 2026-10-26 — T1 frozen inputs

- **Pre-change commit:** `5cec6ac3e` (the merge base with `main`; `packs/repo-governance/` is byte-identical at the branch head when T1 landed, before any `SKILL.md` edit).
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

- Commit `20645fd06`. The `Consulted` check is lint finding `ADR-S016`. The handle and role sentence in `new-adr` step 4 reads: "A handle is a platform handle such as `@user` or `@org/team`, and a role is a named function such as \"platform maintainers\"."
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
- **Attempt 1** (projection of `e5f9cd22c`; `notes/behaviour/attempt-1/`):
  - Hostile record, 3 runs: all scored (skill loaded, script ran); every search result contained ADR-0001; route tag `PR` in all 3; `git status --porcelain` empty, no file changed, no `Write`/`Edit`/`NotebookEdit` call and no `export` in all 3. **AC-0036, AC-0037, AC-0051 and AC-0052 pass.**
  - Advice, 3 runs: all scored; `Consult:` named only the supplied `@platform-team` and `security reviewers`, but each item carried a route-authored note in parentheses, so the consult set did not equal the supplied set. AC-0038 failed.
- **Owner decision:** eugenelim approved in session on 2026-10-26 adding "Write each supplied handle or role exactly as the user gave it, with nothing added." to the route section, with a content pin (commit `e563793b5`), and re-running the advice case.
- **Attempt 2** (projection of `e563793b5`; `notes/behaviour/attempt-2/`): consult set exact in all 3 runs; no writes. Run 2 was not scored: the skill loaded, but both script calls used `python3 -I …/navigate_decisions.py query`, which the driver's grant did not match, so the host refused them. AC-0038 failed on the scored-run rule.
- **Owner decision:** eugenelim approved in session on 2026-10-26 widening the driver's grant to the `python3 -I` form of the same query command and re-running the advice case.
- **Attempt 3** (projection of `e563793b5`; `notes/behaviour/attempt-3/`): all 3 runs scored; consult set `{@platform-team, security reviewers}` in all 3, equal to the supplied set; route tag `RFC`; no file changed and no write call. **AC-0038 passes.**
- The hostile-record evidence is from `e5f9cd22c`, one sentence before the final route text; the added sentence concerns only the `Consult:` line.
