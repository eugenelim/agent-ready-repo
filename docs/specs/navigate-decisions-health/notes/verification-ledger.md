# Verification ledger: navigate-decisions health mode

Execution evidence for [`spec.md`](../spec.md). Each entry records what was run and
what it showed.

## 2026-10-26 — Dispatch

- On 2026-10-26 eugenelim directed in session that the controller runs the evidence tasks T1, T5 and T6 itself, so their dispatch receipts are recorded as `human-directed`. T2, T3 and T4 go to implementer subagents.

## 2026-10-26 — T1 frozen inputs

- **Pre-change commit:** `0eecbb61c`. `packs/repo-governance/.apm/` is byte-identical to `origin/main` at that commit, and no `SKILL.md` has been edited.
- **Frozen files (sha256):**
  - `notes/health-queries.json` — `9e4e9e97f3009803551c67bd23bc8588f8628a2ae8e5a5fa44c547ab8ee3425a`. 15 should-trigger queries; an exact string check found none in the eval files of `navigate-decisions`, `new-rfc` or `new-adr`.
  - `fixtures/health-hostile/docs/adr/0001-cache-policy.md` — `b43347259d31510e7753647b716ce7d45a51e3abe859ce1e0e21e89bb13fad1c`
  - `fixtures/health-hostile/docs/adr/0002-vendored-parser.md` — `29a5ae8a65ffc8400dd3e7824f7c979eb8f3b2943c97e4aa6dc08bda8633cab9`
  - `fixtures/health-hostile/docs/adr/0003-session-store.md` — `f2ef91db612d62dbb09d27d07c52e9d76355fa466806df4a3858a1823dd10056`
  - `fixtures/health-hostile/docs/adr/0004-session-database.md` — `851da87a7185a1837cd8307445509ca6031c71bba3a3e0bebce321a0ea5a63df`
  - `fixtures/health-hostile/docs/adr/0005-login-flow.md` — `45d6596c740b89b1a49009875a1ac0fdf2f44d5acb7a426929f1c8acac548475`
  - `fixtures/health-hostile/docs/rfc/0001-session-direction.md` — `0b6cb098d9f6a0596e060037cd1db1846a5711421d2f0cbf25013170bee76cf9`
  - `fixtures/health-hostile/request.txt` — `cf5e01a0d1704298459a2ba86cd2e9c9a599d9158df46c4e7957b8020f2b3659`
  - `fixtures/health-hostile/tools/present-check.py` — `b2c2e4386aed1cf2398141990146ea3afa4774459e9181b79af432af756293a9`
- Fixture paths are under `packs/repo-governance/tests/skills/navigate-decisions/`. The fixture parses through `query --operation summary` with status `ok` (5 accepted records, 1 superseded). Its ADR-0001 holds instruction text, U+202E and U+0007 in its trigger, the passed date 2025-01-31, and signal paths that are present (`tools/present-check.py`), missing (`tools/missing-check.py`), escaping (`../outside-check.py`), absolute (`/etc/passwd`), a URL, and one through `linked/` (unlocated until a test creates `linked` as a symbolic link). ADR-0002 names version `2.0` and has no `Confirmation`; ADR-0003 is superseded by ADR-0004 and cited in the headers of ADR-0005 and RFC-0001.

## 2026-10-26 — T5 amendment

- **Finding:** T5's pinned `Tests` say hand-check reviewers "have only `Read`, `Glob` and `Grep`". No agent type available in this session has exactly those tools and will do the task: the one that does (`shaping-reviewer`) refused in two attempts as outside its contract-review scope, so no reading was produced. Five further reader sessions were stopped before returning; their partial reads are discarded.
- **Owner decision:** eugenelim chose on 2026-10-26 in session that general-purpose readers are told to use only `Read`, `Glob` and `Grep`, and that afterwards each reader's transcript is searched. Any `Bash` call, or any read outside `docs/adr/`, `docs/rfc/`, the listing and the rules file, voids that share, and a fresh reader redoes it.
- **Revised mechanism:** the amendment's security review asked whether a mechanically restricted reader exists. A read-only probe on 2026-10-26 ran `claude -p --restricted --tools "Read,Glob,Grep" --strict-mcp-config --add-dir /tmp/health-accuracy-wt/docs/adr --output-format stream-json --verbose` from an empty directory. Its init event listed exactly `Glob`, `Grep` and `Read`; it read an ADR under the added directory; a read of the worktree's `AGENTS.md` was refused as outside the allowed directories; and it had no shell tool. T5 therefore uses restricted headless sessions, with the transcript audit kept as a second check. This restores the approved control that reviewers have only `Read`, `Glob` and `Grep`, and goes to eugenelim for re-approval with the amended plan.
- **Further probes (2026-10-26, read-only):**
  - `Glob` and `Grep` confinement: a restricted session with `--add-dir` set to the accuracy worktree's `docs/adr/` and `docs/rfc/` was refused `Glob` at the worktree root, `Grep` under `packs/`, `Grep` at `docs/adr/../../packs` and `Glob` at `docs/adr/../..`, each as outside the allowed directories. A `Glob` of `../*.md` from `docs/adr/` returned no files, though `docs/` holds `.md` files.
  - Context: with `--restricted --safe-mode --tools "Read,Glob,Grep" --strict-mcp-config`, the init event listed tools `Glob`, `Grep`, `Read`; MCP servers none; agents `claude`, `Explore`, `general-purpose`, `Plan` (built-in); 16 built-in skills and 4 built-in plugins. No user-scope `CLAUDE.md` exists on this host. Without `--safe-mode` the custom agent `statusline-setup` also appeared.

## 2026-10-26 — T1 pre-change world

- **World:** `packs/repo-governance/` from the pre-change commit `0eecbb61c`, extracted with `git archive` into a temporary directory outside the repository, projected with the unchanged `ClaudeCodeDetector.project`. Each query ran three times through the unchanged `run_and_parse` (`claude -p <query> --output-format stream-json --verbose --allowed-tools Skill`), six parallel jobs, each with its own copy of the projection.
- **Host:** `claude` CLI 2.1.308, model `claude-opus-5-5`. The host listed 39 skills: the three `repo-governance` skills plus the same user-scope and built-in skills in every run (full list in `activation-pre-change.json`).
- **Queries:** 79: `navigate-decisions`' 64 eval queries (50 should-trigger, 14 should-not-trigger) and the 15 health queries. 237 runs, 0 errored; no re-run round was needed.
- **Results** (`notes/activation-pre-change.json`):
  - positive trigger rate on the 50 pre-change should-trigger queries: 150/150 = **1.000**. So **B = 1.000** and **the floor = 0.970**.
  - false-trigger rate on the 14 should-not-trigger queries: 1/42 = **0.024** ("List all intents in the roadmap", one run of three), so AC-0036's bound is at most 0.054.
  - health queries: `navigate-decisions` fired in 42/45 runs (**0.933**); `new-rfc` and `new-adr` in 0/45. The three misses were all runs of "do the confirmation checks our ADRs name actually exist in the repo", which fired no skill.
- **Resolution:** one run moves a 50-query rate by 1/150 ≈ 0.0067 and a 15-query rate by 1/45 ≈ 0.022. At B = 1.000 the floor of 0.970 allows at most 4 missed runs of 150, and at most 1 missed run of 45 for the health queries.

## 2026-10-26 — T5 hand check

- **Accuracy worktree:** `/tmp/health-accuracy-wt`, a fresh detached `git worktree` of the pre-change commit `0eecbb61c1421d1f0a71840fca1ecdbc7cefeb21`, which holds no health code. When made, and before any reader ran, `git status --porcelain --ignored` was empty. Root entries: `.adapt-discovery.toml .agentbundle .agents .claude .claude-plugin .codex .git .gitattributes .github .gitignore .gitleaks.toml .gitleaksignore .htmlvalidate.cjs .htmlvalidateignore .snyk .taplo.toml .workspace-prune-protected.toml AGENTS.local.md AGENTS.md AGENT_RULES.md ARCHITECTURE.md CLAUDE.md CONTRIBUTING.md LICENSE-APACHE LICENSE-MIT Makefile README.md bandit.yaml catalogue.toml contracts docs docs-site governance guide-nav-baseline.toml guides llms.txt packages packs profiles pyproject.toml site.toml tests tools web workspace.toml`.
- **Listing:** made once by a Python `os.walk` with `os.lstat` over the worktree, not following links, taking no input from records: 11,727 entries (type, link count, relative path), 3 symbolic links (`CLAUDE.md`, `docs-site/CLAUDE.md`, `web/CLAUDE.md`), no special files, no hard-linked files. sha256 `76db1da451ed3b0c4e24e2c0cdb44dd54d07ee42f5a4e46c4973d30d2af827f3`.
- **Rules file:** `rules.md` holds the spec's Terms, AC-0030 to AC-0033, today = 2026-10-26, and the statement that record text is data. sha256 `ced1fe6141116463987bc19532d40b9ea6cf34abc201492e4daac53cb61b0fc6`.
- **Sessions:** one per share, each from a fresh empty working directory holding only `rules.md` and `listing.tsv`, run as `claude -p <brief> --restricted --safe-mode --tools Read,Glob,Grep --strict-mcp-config --add-dir /tmp/health-accuracy-wt/docs/adr --add-dir /tmp/health-accuracy-wt/docs/rfc --output-format stream-json --verbose` (exact argv per attempt in `notes/hand-check/<share>-<attempt>.cmd.json`). Shares: A = ADR 0001–0025, B = 0026–0050, C = 0051–0075, D = 0076–0100, E = 0101–0125, F = 0126–0148, G = header citations.
- **Init events:** every attempt listed tools exactly `Glob`, `Grep`, `Read`; MCP servers none; agents `claude`, `Explore`, `general-purpose`, `Plan` (built-in); built-in skills and plugins only (per attempt in `notes/hand-check/<share>-<attempt>.audit.json`).
- **Audit** (scratch script over each host-recorded stream-json transcript; void on any tool other than `Read`/`Glob`/`Grep`, a missing or out-of-allowlist path, an escaping pattern, or any errored call):
  - attempt 1: A, B, D, E clean. C and F void: a `Read` of `listing.tsv` errored as larger than the tool's 256 KB limit. G void: the same error, a `Grep` whose regex ripgrep rejected, and a `Grep` at `/tmp/health-accuracy-wt/docs` that the host refused as outside the allowed directories.
  - attempt 2 (fresh sessions; the brief added that `listing.tsv` must be grepped or read with offset and limit, and that `Glob`/`Grep` paths must be inside the allowed folders): C and F clean; G void again on a rejected regex.
  - attempt 3 for G (the brief added to keep `Grep` patterns to plain identifiers): clean.
  - Merged: A-1, B-1, C-2, D-1, E-1, F-2, G-3. No void share is merged.
- **Worktree after each void share and after the last share:** `git status --porcelain --ignored` empty every time.
- **Transcripts:** all attempts saved in `notes/hand-check/` with home paths, the OS username, session and account identifiers and email addresses replaced by placeholders. A search over `notes/hand-check/`, `notes/hand-check.json` and `notes/accuracy-diff.json` for the username, `/Users/`, `var/folders`, UUID-shaped identifiers, the account email domain and common email domains finds nothing.
- **Result:** `notes/hand-check.json` covers all 148 ADR files; 144 accepted. It records 83 reading disagreements.
