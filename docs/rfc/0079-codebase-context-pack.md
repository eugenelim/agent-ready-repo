# RFC-0079: `codebase-context` Pack — Semantic Graph Indexing as an Optional Add-On

- **Status:** Draft
- **Author:** eugenelim
- **Approver:** TBD
- **Date opened:** 2026-08-03
- **Date closed:** —
- **Decision weight:** heavy
- **Related:** ADR-0003 (credential-broker contract), RFC-0008 (install-route parity)

> **RESEARCH-BLOCKED — this file and its docs/rfc/README.md row must not merge
> to main until the viability spike is complete.** Transport architecture has
> been confirmed (stdio, not HTTP); bearer auth is not applicable. Remaining
> D4 prerequisites confirmed: env var delivery (Claude Code `~/.claude.json`),
> serena transport/startup contract, serena PyPI
> provenance (`serena-agent`). Remaining 9 blocking prerequisites — see Blocking OQs section for the canonical list. If the spike fails
> to confirm backend viability, this file and
> its index row must be removed from the branch.

## Reviewer brief

- **Decision:** Whether to accept a new optional user-scope pack that registers a stdio MCP subprocess (codebase-memory-mcp) and provides PLAN-time codebase graph queries.
- **Recommended outcome:** Accept as Draft — status stays Draft until all remaining nine design-acceptance prerequisites (D4) are confirmed; three are now CONFIRMED (env var delivery, serena transport, serena PyPI provenance) and rebuild idempotency is already CONFIRMED. Only then does the RFC move to Open for an approval vote. "Experimental" (a running trial) is not the right status here; the blocking OQs are the research spike that must complete before any trial can begin.
- **Change if accepted:** New `packs/codebase-context/` directory; two new skills (`codebase-context`, `setup-codebase-context`); user's `~/.claude.json` and `~/.agentbundle/` modified at setup time; git hooks in the configured repo modified.
- **Affected surface:** user MCP registration, git hooks, agentbundle state dir, pack catalogue, root `Makefile` (`build-self` target extension for pack-local pre-projection sync).
- **Stakes:** one-way door at git-hook and MCP registration write time; reversible via uninstall skill.
- **Review focus:** (1) security boundaries — `CBM_ALLOWED_ROOT` confinement, repository-scope enforcement (cross-repo read isolation, both backends), `codebase-memory-mcp` raw-source tool exposure, serena `find_symbol(include_body=True)` and `search_for_pattern` proxy requirement; (2) remaining 9 D4 prerequisites — see Blocking OQs section for the canonical list. CONFIRMED: env var delivery, serena transport/startup, serena PyPI provenance (`serena-agent`). Rebuild idempotency CONFIRMED.
- **Not in scope:** multi-repo indexing, per-worktree graphs, daemon auto-start, PreCompact hook.

## The ask

- **Recommendation (BLUF):** Accept the pack design as a user-scope opt-in with all remaining D4 prerequisites confirmed before implementation — see Blocking OQs section for the canonical list (9 remaining). CONFIRMED: transport architecture (stdio), env var delivery, serena transport/startup contract, serena PyPI provenance (`serena-agent`).
- **Why now (SCQA):** Agents on multi-worktree repos re-explore codebases they already know, wasting tokens and turns. `codebase-memory-mcp` (verified: stdio transport, internal daemon, 15 MCP tools, Windows/macOS/Linux support) provides persistent graph indexing with no auth complexity. No existing pack wraps it.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Accept pack design? | Accept as Draft pending viability spike — **do not move to Open or begin implementation** until all Blocking OQs (D4) are resolved and folded back into this document. The new-rfc research gate (spike the riskiest architectural assumption before handing to reviewers) has not been completed; reviewers are assessing the structural shape only, not implementation readiness. "Experimental" reserved for a running trial. Rebuild idempotency is CONFIRMED (serialized via `project_lock.c`) — no longer a blocker. | D4 OQs are unverified; backend viability is unconfirmed; CONVENTIONS.md reserves "Experimental" for a running trial, not a holding state for open prerequisites | This review | Confirm or reject |
| D2 | Default backend: `codebase-memory-mcp` or `serena`? | `codebase-memory-mcp` | Zero-dep C binary; simpler install; Windows CONFIRMED (PowerShell installer, Scoop/Winget/Chocolatey, `windows-amd64` + `windows-arm64` builds) | This review | Confirm default |
| D3 | Multi-project / knowledge-space isolation? | `CBM_ALLOWED_ROOT` confines indexing scope. Cross-project query isolation is gated on D4 prerequisite (5) (cross-repo query scope blocker) — defer to D4: do not confirm unrestricted cross-project queries until D4 prerequisite (5) is resolved. Per-project config profiles are the expected multi-project model. Context re-priming via session-start hooks is a future extension; see Open Questions. | Single-user pack; multi-user deployment is out of scope. | This review | Confirm scope |
| D4 | Design-acceptance prerequisites block implementation? | Yes — **9 remain open** (see Blocking OQs section). CONFIRMED: (a) env var delivery in `~/.claude.json` format; (b) serena transport (stdio, `serena start-mcp-server --context claude-code --project <path>`); (c) serena PyPI provenance (package is `serena-agent`, not `serena`). Still open: (1) `CBM_ALLOWED_ROOT` enforcement; (2) `codebase-memory-mcp` raw-source tool allowlist or proxy (not acceptable to document risk); (3) project-scoped purge / isolated fixture store; (4) snapshot-isolated reads; (5) cross-repo query scope; (6) repository-scope enforcement both backends; (7) `codebase-memory-mcp` offline CLI rebuild; (8) serena metadata-only proxy for `find_symbol(include_body=True)` and `search_for_pattern`; (9) serena read-only mode config-path verification (`.serena/project.yml` path must be verified against pinned `serena-agent` release). | Without blockers confirmed the design may expose raw source, write-capable tools, partially-rebuilt data, or cross-project data. | Before implementation | Confirm as blockers |

## TL;DR

AI coding agents on multi-worktree setups waste tokens and turns re-exploring
codebases they already know. This design proposes an optional user-scope pack
that registers a semantic graph MCP tool set — via stdio subprocess, sharing
an internal background daemon automatically — and gives agents a structured
habit for pre-loading codebase context at PLAN time. The core extension
alternative (hooks-based, per-session spawning) is the main
alternative; it is considered and deferred in Alternatives.

## Context

An AI agent exploring an unfamiliar codebase today works like a detective
arriving without a map: read a file, grep for a symbol, read another, backtrack.
Aider's repomap work ([aider.chat blog post, 2023-10-22](https://aider.chat/2023/10/22/repomap.html))
and GrapeRoot's self-reported benchmark directory (`benchmark/` in the
GrapeRoot GitHub repository — self-reported, unaudited, not independently
verified) both claim efficiency gains from pre-loaded symbol indexes; the
specific figures (3× turns, 40–50% tokens) are unaudited and cited only for
directional motivation, not as design constraints. The mechanism is
well-understood:
pre-scan the codebase into a semantic graph, expose it via MCP tools, and have
the agent query the graph before reaching for file reads.

The non-obvious constraint is **concurrent worktrees**. This repo runs up to
eight simultaneous worktrees, each on a different branch.
Any approach that spawns a server per Claude session — the default for stdio MCP
transport — yields N concurrent processes all trying to index the same files
simultaneously. Any approach that writes a per-session index file produces SQLite
write contention. Any approach that scans the current working tree produces a
graph of in-progress (partially broken) code rather than the stable base.

The open-source backend landscape has matured: `codebase-memory-mcp` (MIT,
zero-deps C binary, tree-sitter backed, source-available on GitHub) and
`serena` (MIT, LSP-backed Python, installable via `uv`) are the two evaluated
options. Neither is built into any existing pack in this catalogue. The `codebase-memory-mcp` transport model is confirmed from source
(v0.9.1-rc.1): stdio subprocess, internal background daemon, no HTTP MCP
endpoint, no bearer token. `serena` transport is **CONFIRMED** (stdio,
`serena start-mcp-server --context claude-code --project <path>`;
exact version tracked in D4 blocking OQ — see D4 CONFIRMED section above);
`read_only: true` in `project.yml` is also **CONFIRMED** in-principle;
exact version to be pinned before implementation (D4 blocking OQ).

**Backend selection criteria (for current and future backends):** When
evaluating a semantic graph backend, the key axes are: (1) MCP transport
model — stdio subprocess (confirmed for `codebase-memory-mcp`) or HTTP with
verified auth; (2) path-confinement primitive — `CBM_ALLOWED_ROOT` or
equivalent; (3) provenance and confidence metadata on query results — backends
that annotate each result with resolution method (static vs. heuristic) and
source location are preferred; (4) structural ranking support — `limit`/`top_k`
query parameters and results weighted by call-graph centrality rather than
keyword frequency; (5) read-only mode or tool allowlist — backends must not
expose write-capable tools to the skill; (6) rebuild idempotency — concurrent
rebuild calls must not corrupt the index.
These criteria apply unchanged if a third backend is evaluated in future.

## Goals and Non-goals

### Goals

- After pack setup and daemon start, a work-loop PLAN step can query the graph
  and receive relevant symbols without any prior file reads.
- Index freshness is maintained for the `codebase-memory-mcp` backend without
  manual intervention between git pull operations on the index root. For the
  `serena` backend, freshness equals the on-disk currency of the index root —
  the only control is keeping that checkout up to date via `git pull`.
- The `setup-codebase-context` skill detects the chosen backend and guides
  installation (printing exact install commands where the backend is absent,
  and auto-installing via `uv tool install` for `serena` with a consent gate),
  then registers the MCP daemon on macOS (arm64 + x86_64), Linux (x86_64 +
  arm64), and Windows. It does not auto-download binaries for Tier-1 backends.
- The pack degrades gracefully: when the daemon is unreachable, or when graph
  queries return zero useful results, the skill surfaces a named `GRAPH-FALLBACK`
  event (with a reason tag, e.g. `GRAPH-FALLBACK: daemon-unreachable` or
  `GRAPH-FALLBACK: no-results-for-query`) and guides the agent to fall back to
  direct file reads without aborting the work-loop. Named fallbacks are
  measurable: the eval set tracks fallback rate as a signal for coverage gaps
  in the index, and a high fallback rate on a specific query type is a priority
  input to the index improvement backlog.
- On a fixed benchmark task set (committed to
  `packs/codebase-context/.apm/skills/codebase-context/evals/evals.json`
  with per-task expected file targets — distinct from `eval_queries.json` which
  drives activation trigger detection), PLAN reaches the first correct file
  target **from graph output, before any fallback to direct file reads**, in ≤3
  graph queries per task on average. Any task where the correct target is reached
  only via fallback counts as a failure for this criterion — a fallback-only pass
  means the graph provided no useful signal. This is a release-acceptance check
  measured manually at first release, not an ongoing regression gate.
- Uninstalling the pack fully removes the MCP registration from `~/.claude.json`,
  the generated script (`normalise_remote.py` — `post-merge.py` is inlined into
  `setup.py` and has no separate copy), `pack_dir("codebase-context")/config.toml`,
  the staleness marker, and the pack's sentinel-delimited blocks from the current
  index root's git hooks.
  **`agentbundle uninstall` and `claude plugin uninstall` alone are
  insufficient** — they remove state-recorded Tier-1 projected files and the
  state row, but they do not know about the MCP registration, git hooks,
  markers, or custom-root data created by `setup.py`. Running them directly
  removes the teardown skill and state row first, leaving no mechanism to clean
  up the rest. The correct uninstall path is always the `setup-codebase-context`
  skill’s teardown flow, which performs the version-check preflight before
  staging the terminal command. Direct invocation of `uninstall.py` without
  going through the skill first is not a supported path: the skill detects
  whether the copied script and stamp are behind the projected pack’s version
  (the self-check in `uninstall.py` cannot detect this gap — it only detects
  copy-vs-stamp drift); skipping the preflight can run obsolete cleanup logic.
  The `agentbundle uninstall` command is called from within `uninstall.py`
  as a late step, before final state cleanup and self-deletion.
- When re-running setup with a different index root, `setup.py` removes the
  sentinel blocks from the *previous* root's hooks directory before chaining
  into the new one.

### Non-goals

- **Not building a graph engine.** The pack wraps external backends; it ships
  no indexing code of its own.
- **Not per-worktree indexing.** The daemon indexes a single configured root.
  Indexing in-progress branches is deferred to a future extension.
- **Not modifying `core` or any existing pack.** This ships as an independent
  user-scope pack with no required dependencies.
- **Not a `PreCompact` hook implementation.** Context re-priming at compaction
  is tracked separately; this design does not wire any adapter hook events.
- **Not a multi-repo solution.** One daemon registration covers one repo. A
  second setup cleans up the previous registration before overwriting.
- **Not exposing daemon management to the user.** `codebase-memory-mcp`
  manages its own background daemon internally. The pack does not expose
  daemon lifecycle commands to the user, but `setup.py` does control the
  daemon internally during the canary phase (stop → exclusion-verified build
  → restart) and during uninstall (`daemon stop` before graph purge).
  Failures at runtime surface as subprocess or MCP-tool errors; the skill
  falls back to direct file reads.

## Proposal

The pack ships two skills and a small Python utility layer. No hook wiring into
any existing pack. MCP registration and pack state (`config.toml`, scripts,
stale marker) are user-scope (`~/.agentbundle/codebase-context/`). The pack
also writes project-scoped configuration into the index root: `.cbmignore`
(exclusion rules) and, for Serena, `.serena/project.yml` (graph config). These
project files are managed as opt-in additions — tracked variants may require a
commit — and are reversed on uninstall or backend change.

```mermaid
flowchart TD
    subgraph "Setup (one-time)"
        S1[setup-codebase-context skill] --> S2[setup.py: detect OS + arch]
        S2 --> S3{backend?}
        S3 -- codebase-memory-mcp --> S4a[detect binary - fail-clean if absent]
        S3 -- serena --> S4b[detect uv; check uv tool list for serena==pinned; if absent prompt consent + run uv tool install; re-verify]
        S4a --> S5[user confirms index root - regularly-pulled main checkout]
        S4b --> S5
        S5 --> S6[normalise_remote.py records repo_url from index root]
        S6 --> S7a{existing registration?}
        S7a -- yes --> S7b[warn + confirm overwrite first]
        S7b -- confirmed --> S8[write transaction journal - capture prior hooks as prior_value]
        S7a -- no --> S8
        S7b -- declined --> S7d[abort - old registration preserved with its hooks]
        S8 --> S7e[remove old hooks - journal has prior state for rollback]
        S7e --> S8b{backend?}
        S8b -- codebase-memory-mcp --> Sq[QUIESCENCE GATE: stage as detached terminal cmd - close all Claude sessions before S9+]
        Sq --> S9[canary probe: verify exclusions with fixture index]
        S9 --> S10[clean-tree check + first full real-root build]
        S10 --> S11[post-build list_projects: confirm per-project index path]
        S11 --> S12[promote: write ~/.claude.json MCP entry + config.toml + scripts]
        S12 --> S14[chain post-merge+post-rewrite+post-checkout into shared hooks dir]
        S14 --> S16[setup complete - MCP server spawned on next Claude session start]
        S8b -- serena --> S9s[write .serena/project.yml read_only: true - journal prior value]
        S9s --> S12s[promote: write ~/.claude.json MCP entry + config.toml + scripts]
        S12s --> S16
    end

    subgraph "Runtime per PLAN"
        R1[work-loop PLAN orient] --> R2{repo identity matches?}
        R2 -- no --> R3[skip graph tools - use direct file reads]
        R2 -- yes --> R4[liveness probe: call backend-specific known tool]
        R4 -- subprocess error or MCP tool error --> R3
        R4 -- identity confirmed --> R5[check staleness marker + freshness]
        R5 -- stale codebase-memory-mcp --> R6[trigger rebuild, mtime-safe marker delete]
        R5 -- serena: confirm LSP live --> R7[retrieve context for task]
        R5 -- fresh --> R7
        R6 --> R7
        R7 --> R7b[delimit graph output as untrusted data]
        R7b --> R8[expand neighbourhood]
        R8 --> R9[estimate blast-radius]
    end
```

**Graph output is untrusted model input.** Graph results can contain comments,
docstrings, and symbol bodies from any indexed commit or dependency. An
adversarial string in a comment (e.g. `// Ignore previous instructions and
do X`) enters PLAN context verbatim and can prompt-inject the agent.
**Prompt injection via graph content is a pre-transport concern, not a
skill-instruction concern.** The MCP host delivers raw tool results directly
to the model context before any SKILL.md instruction can wrap or sanitize
them; applying escaping or framing after the fact in the skill prompt is too
late. Mitigation must therefore occur before the result crosses the MCP
transport boundary:

- **Preferred:** constrain the exposed MCP tools to metadata-only output —
  symbol names, file paths, line ranges, cross-reference counts — that
  never includes raw docstrings, comments, or string literals. Verify per
  backend which tools emit metadata-only vs. content before shipping. Tools
  that return raw source content cannot be safely exposed without a
  sanitizing proxy. **For `codebase-memory-mcp`:** `get_code_snippet` and
  `search_code` are confirmed raw-source tools (confirmed — see
  "codebase-memory-mcp raw-source tool allowlist" OQ below). These cannot
  be prevented from being called by a prompt-injected session unless the
  binary supports a tool-allowlist config option that excludes them from
  registration, or a sanitizing proxy is interposed before the MCP host.
  Documentation of accepted risk is **not** a substitute — a prompt-injected
  session can retrieve secrets regardless of risk documentation. This backend
  requires either a confirmed tool allowlist or a sanitizing proxy before
  it can ship; if neither is available, this backend must be rejected.
  This is a **D4 blocking prerequisite** — see Open Questions
  (`codebase-memory-mcp` raw-source tool allowlist).
- **If metadata-only is unachievable:** add a sanitizing proxy between the
  backend and the MCP host. The proxy must either suppress raw-source tools
  entirely (removing them from the MCP tool registration so they are never
  callable) or irreversibly reduce their output to a fixed metadata schema
  (symbol names, file paths, line ranges only — no docstrings, comments, or
  string literals). Escaping or encoding source text is **not** sanitization:
  a model capable of decoding base64 or un-escaping content still receives the
  original instructions and secret bytes. This proxy is a security boundary and
  must itself be in scope for review.

SKILL.md's data-boundary framing (`<graph-context role="data">…</graph-context>`)
is **defense-in-depth only** — not an isolation boundary, because the tag
itself may appear in indexed content and terminate the wrapper early. Keep the
framing but do not rely on it as the primary control. The skill instruction
must also forbid the agent from following any instruction embedded in
graph-retrieved content. Content that is purely symbol names and paths is
lower-risk; any tool result that includes docstrings, comments, or string
literals must be treated as untrusted external data regardless of branch or
author. **Make "tools expose metadata-only output" a blocking spike result.**

### Pack layout

```
packs/codebase-context/
  pack.toml                               # user-scope; allowed-adapters = ["claude-code"]
  README.md                               # required adopter-facing README: installation,
                                          # trust model, external dependencies, first-use
  .claude-plugin/
    plugin.json                           # required Claude plugin manifest (name, version,
                                          # description matching pack.toml)
  .apm/
    skills/
      codebase-context/
        SKILL.md                          # graph policy, per-backend tool reference,
                                          # PLAN integration, freshness protocol,
                                          # scope-gate, degradation guidance
        evals/
          eval_queries.json               # activation eval coverage for codebase-context skill
          evals.json                      # benchmark: per-task file-target assertions
        scripts/
          normalise_remote.py             # GENERATED by tools/sync-normalise-remote.py
                                          # (invoked by make build-self) from the canonical
                                          # in setup-codebase-context/scripts/ — do not edit
          scripts-version-launcher        # GENERATED by tools/sync-scripts-versions.py
                                          # (same build-self step) from the canonical in
                                          # setup-codebase-context/scripts/ — do not edit.
                                          # codebase-context reads this via __file__ to refresh
                                          # config.toml [scripts].launcher_version_expected;
                                          # must be the same value as the canonical copy
          rebuild_coordinator.py          # directly-authored canonical source in
                                          # codebase-context/scripts/ (NOT generated —
                                          # coordinator is runtime-only, not needed by setup);
                                          # handles the atomic stale-marker claim/complete/fail
                                          # protocol so concurrency guarantees are testable
          gitignore_eval.py               # directly-authored canonical source in
                                          # codebase-context/scripts/; pure-stdlib gitignore
                                          # evaluator (re, pathlib, os only); used by both
                                          # setup step 4b (read from pack source before
                                          # promotion) and rebuild_coordinator.py (runtime);
                                          # no third-party dependency; copied to
                                          # <stable-state-dir>/scripts/ at step 5c alongside
                                          # other runtime scripts; removed by uninstall
      setup-codebase-context/
        SKILL.md                          # setup instructions, backend choice, verification
        evals/
          eval_queries.json               # activation eval coverage for setup skill
        scripts/
          setup.py                        # install backend, write MCP registration
                                          # (command + args; CBM_ALLOWED_ROOT baked into
                                          # launch-backend.py, no env block), copy scripts, chain hooks
          uninstall.py                    # remove registration, toml, marker, scripts, hooks
          codebase-context-cleanup.py     # standalone deferred-purge cleanup helper; copied
                                          # to <stable-state-dir>/scripts/ at setup step 5c;
                                          # checks for cbmignore-cleanup.json and removes
                                          # retained .cbmignore sentinel blocks after a manual
                                          # graph purge; retained by teardown when cleanup is
                                          # pending, deleted by cleanup or subsequent setup
          # post-merge.py inlined into setup.py (single caller;
          #   no shipped copy, no version stamp)
          scripts-version-launcher        # canonical plain-text version token; synced to
                                          # codebase-context/scripts/ by tools/sync-scripts-versions.py;
                                          # setup writes this value into config.toml
                                          # [scripts].launcher_version_expected at install time (step 5b);
                                          # bump whenever launch-backend.py changes
          normalise_remote.py             # canonical source; called by setup.py to record
                                          # repo_url; tools/sync-normalise-remote.py copies
                                          # it to codebase-context/scripts/ — both copies
                                          # must be byte-identical (construction test)
          gitignore_eval.py               # GENERATED by tools/sync-gitignore-eval.py (same
                                          # build-self step as sync-normalise-remote.py) —
                                          # exact copy of codebase-context/scripts/gitignore_eval.py;
                                          # step 4b resolves it as __file__-relative within
                                          # setup-codebase-context/scripts/ (not via sibling
                                          # pack path) so setup remains self-contained when
                                          # only setup-codebase-context is projected
  tools/
    sync-normalise-remote.py             # pack-local sync step: copies the canonical
                                          # normalise_remote.py into codebase-context/scripts/;
                                          # requires Makefile build-self amendment (see below)
    sync-gitignore-eval.py              # copies codebase-context/scripts/gitignore_eval.py
                                          # into setup-codebase-context/scripts/ (so setup
                                          # is self-contained); run by make build-self; a
                                          # construction test asserts byte-equality of both
                                          # copies, blocking CI if they diverge
    sync-scripts-versions.py            # copies scripts-version-launcher (and any future
                                          # version stamps) from setup-codebase-context/scripts/
                                          # into codebase-context/scripts/; run by make build-self
                                          # so the runtime skill always has a current copy to read
```

### Transport: stdio subprocess per session

This is the load-bearing architectural choice, verified from source
(`src/daemon/frontend.c`, `src/daemon/host.c`, v0.9.1-rc.1): the backend
exposes an MCP endpoint exclusively over stdio — spawned as a subprocess by
the MCP client, not run as a persistent HTTP server. There is no HTTP MCP
endpoint and no bearer token.

```json
{
  "mcpServers": {
    "codebase-context": {
      "command": "/path/to/codebase-memory-mcp",
      "args": []
    }
  }
}
```

Each Claude Code session spawns its own `codebase-memory-mcp` subprocess.
That subprocess communicates with the binary's own internal background daemon
via IPC (`src/daemon/ipc.c`); the user does not manage this daemon directly.
Multiple sessions (e.g. 8 worktrees) each have their own subprocess connected
to the shared internal daemon — the index is not rebuilt per-session.

The security model is OS process isolation. No bearer token; no HTTP port;
no secret file. The pack does not generate or manage auth credentials.
The path-confinement primitive is `CBM_ALLOWED_ROOT`:

```bash
export CBM_ALLOWED_ROOT=/path/to/project-root
```

With `CBM_ALLOWED_ROOT` set, the daemon rejects index requests for paths
outside that tree. `setup.py` bakes `CBM_ALLOWED_ROOT` into `launch-backend.py`
(the minimal-environment wrapper) — it is not placed in the MCP registration's
`"env"` block; see the transport section for the full wrapper contract.

**How env vars reach stdio subprocesses.** Claude Code's `"command"` MCP
registration supports an `"env"` key alongside `"command"` and `"args"`:
```json
{
  "mcpServers": {
    "codebase-context": {
      "command": "/path/to/python3",
      "args": ["-I", "/path/to/pack_dir/scripts/launch-backend.py"]
    }
  }
}
```
The `launch-backend.py` wrapper (generated by `setup.py`) calls `os.execvpe`
with the backend binary and a minimal environment it constructs. `CBM_ALLOWED_ROOT`
is baked into the wrapper, not passed via the `"env"` block.
CONFIRMED: Claude Code's `~/.claude.json` mcpServers
format supports the `"env"` key and passes its contents to the spawned
subprocess. **However, MCP stdio subprocesses inherit the parent process
environment by default** — any secrets the user has in their shell environment
(`ANTHROPIC_API_KEY`, cloud credentials, tokens) are passed to the backend.
**`setup.py` must register a generated minimal-environment wrapper, not the
backend binary directly.** The MCP `"command"` is a **durable system interpreter**
recorded as `interpreter_path` — setup must probe for durability and compatibility: reject any candidate
interpreter that (a) is a virtualenv — invoke the candidate with
`<absolute-path> -c "import sys; sys.exit(0 if sys.prefix == sys.base_prefix else 1)"`
and reject on non-zero exit; this detects virtualenvs with arbitrary
directory names and resolves correctly on Windows paths, where
POSIX-substring heuristics (`/.venv/`, `VIRTUAL_ENV` prefix) are unreliable.
A candidate that is itself a virtualenv may be deleted when its parent
project is removed, leaving the stored interpreter path broken; (b) is a
pyenv shim or managed version (resolved path starts with
`os.path.expanduser("~/.pyenv/shims/")` or
`os.path.expanduser("~/.pyenv/versions/")` — use `os.path.realpath` to
normalize before comparing, not raw string prefixes);
or (c) is a `uv`-managed Python installation — detect by running
`uv python dir 2>/dev/null` (if `uv` is not on PATH the command fails and
this criterion cannot apply); if it succeeds, reject any candidate whose
realpath starts with its output (e.g. `~/.local/share/uv/python/` on
Linux/macOS, `~/AppData/Roaming/uv/python/` on Windows — a `uv python
uninstall` removes it, breaking the stored interpreter path); **and** (d) run each remaining candidate
with `<absolute-candidate-path> -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"`
— using the candidate's own absolute path, not the ambient `python3` on PATH
(which may be a different version and would validate the wrong executable);
reject Python < 3.11 because `tomllib` (required by `setup.py`, `uninstall.py`,
`rebuild_coordinator.py`, and `launch-backend.py`) is stdlib only from 3.11. Fall back to the first
`python3` on the system PATH that survives all four checks (e.g.
`/usr/bin/python3`, `/usr/local/bin/python3`); if none qualifies, setup must
warn and require the user to pass `--interpreter /path/to/python3` explicitly.
Recording a transient or incompatible interpreter leaves every future Claude
session unable to start the MCP server or run maintenance scripts.
`"args"` is `["-I", "<pack_dir>/scripts/launch-backend.py"]` — a Python script
generated by `setup.py` that calls `os.execvpe` to exec the backend binary with
an explicitly constructed minimal environment (only the vars the backend needs:
`CBM_ALLOWED_ROOT`, `PATH`, and the platform-required subset).
**Serena blocking gate:** `launch-backend.py` must NOT exec the Serena binary
directly until D4 prerequisite (8) — metadata-only proxy for
`find_symbol(include_body=True)` and `search_for_pattern` — is confirmed.
These tools return raw source and are NOT disabled by `read_only: true`; a
prompt-injected or unrelated session can call them and read arbitrary source.
Until a confirmed filtering proxy or tool-allowlist mechanism is in place,
`setup.py` must refuse to register Serena in `~/.claude.json` and exit with
a message directing the user to wait for D4 prerequisite (8) resolution.
Using Python for the wrapper on all platforms avoids Windows `.cmd` / `CreateProcess`
compatibility issues (`.cmd` files are not directly executable by stdio-spawn,
requiring `cmd.exe /d /s /c` indirection). This wrapper is the primary isolation
control: `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`
scrubs only designated Anthropic and cloud credentials and will not cover
arbitrary tokens such as `GITHUB_TOKEN` or `NPM_TOKEN`. `setup.py` must ALSO
check `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` as defense-in-depth before
writing the registration. However, because setup runs as a detached terminal
command outside the Claude Code process (see § Quiescence and session staging),
its `os.environ` reflects the launching shell, which may differ from Claude
Code's own spawn environment — a GUI-launched Claude Code that never sourced a
shell profile may omit the variable even when it is active in practice. For
this reason, the check is a **warning, not a hard refusal**: if the variable is
absent from the terminal environment, setup emits a prominent warning noting
that the scrub variable could not be confirmed and prints the implications, but
continues with installation. The subprocess also receives `CLAUDE_PROJECT_DIR` and
`CLAUDECODE=1` automatically (v2.1.154+).

A **pre-first-use liveness probe** calls a backend-specific read tool
(e.g. `list_projects` over stdio, confirmed as the lowest-cost read tool in
source). If it returns the configured project, the correct binary is on the
path and the index is responsive. If it returns an empty list, the project
has not been indexed yet (first-run path). If it fails (subprocess error,
wrong tool names, tool-not-found, connection error, or unexpected output),
the binary is absent or broken; the skill surfaces an error and falls back to
direct file reads. Note: `initialize` is a protocol message consumed by the
host; its `serverInfo` field is not exposed as a callable tool result at PLAN
time, so the probe relies on a callable backend tool, not the protocol
handshake. The exact probe mechanism depends on verified backend capabilities
(tracked in Open Questions).

On setup rerun with a different `CBM_ALLOWED_ROOT`, `setup.py` regenerates
`launch-backend.py` with the new root baked in, re-registers the MCP entry
(updating `~/.claude.json` with the new wrapper path if it changed), and
re-runs the canary. If `~/.claude.json`
is syntactically corrupt (invalid JSON), `setup.py` refuses and emits
remediation instructions — repairing a corrupt file risks silently overwriting
or dropping unrelated Claude configuration. **Hook-path exception:** `setup.py`
compares the currently resolved `core.hooksPath` (read at setup-rerun time)
against the stored `config.toml [hooks] dir`; if they differ, hooks are
re-chained into the new directory (old sentinel blocks removed, new sentinel
blocks written) even when registration is otherwise valid.

### Daemon lifecycle

`codebase-memory-mcp` manages its own background daemon internally — the user
does not start, stop, or manage it. Spawning the binary (via stdio MCP) is
sufficient to reach the running index. `setup.py` invokes the binary directly
to verify installation and run the canary probe. **All setup-time binary
invocations** (installation verification, canary probe, liveness checks, and
any restart during setup) **must use the same explicit minimal environment**
as `launch-backend.py` does at runtime — constructing it inline before
`launch-backend.py` is written, not inheriting the caller's full environment.
A daemon started by setup before the wrapper is promoted would inherit all
ambient tokens (`GITHUB_TOKEN`, cloud credentials, etc.); the wrapper cannot
retroactively sanitize an already-running daemon.

A naive
probe that queries an excluded path and expects zero results is vacuously true
when the index root has no file matching the excluded pattern — the backend
could be silently ignoring exclusions. The probe must use a **positive-control canary** that proves actual ingestion
and actual exclusion. The probe operates against a **disposable fixture directory outside the index
root** — never against the real checkout without exclusions active. Because all
setup-time invocations use the minimal environment, and `CBM_ALLOWED_ROOT`
enforces a source-path restriction, the canary invocations must set
`CBM_ALLOWED_ROOT` to the fixture directory (not the real index root) — the
backend will reject index requests outside the allowed root. After the canary
phase completes, the real build invocations use `CBM_ALLOWED_ROOT` set to the
real index root. The canary
must match the exact rule it tests; a canary that doesn't match the rule either
passes vacuously (Phase 2 shows it present, making setup fail) or validates the
wrong rule. Two pattern types require different approaches:

- **Path-based exclusions** (directory patterns like `secrets/`, `.credentials/`):
  create a `.py` source file inside a fixture subdirectory whose path matches
  the excluded pattern (e.g. `fixture/secrets/canary.py` for a `secrets/` rule).
  The backend will index a `.py` file; the fixture is separate from the real
  checkout.
- **Basename and variant exclusions** (`.env`, `.env.*`, `*.pem`, `*.key`): the
  canary MUST use the **exact configured pattern**, not a similar one. For `.env`,
  create `fixture/.env` (the dotfile itself — NOT `fixture/canary.env`, which
  does not match the `.env` gitignore rule). For `.env.*`, create
  `fixture/.env.local` (NOT `fixture/canary.env.local` — the leading dot is
  required to match the `.env.*` rule). Do NOT use `*.env` as the canary for a
  `.env` or `.env.*` rule — `*.env` matches `canary.env` but NOT `.env` or
  `.env.local`.
  Before
  using this canary, **first confirm via backend documentation or config** that
  the backend indexes files with this extension at all — if it does not, the
  probe is untestable via search query; instead require direct verification of the
  backend's exclusion config (e.g. dump backend config and assert the pattern
  appears). Only proceed with the canary approach if the backend is documented to
  index that extension.

One canary per **supported exclusion pattern class**, run against a fixture
directory (not the real index root), following this two-phase protocol:

**Phase 1 — Confirm ingestion using fixture (before real checkout is scanned):**
(a) create a temp fixture directory OUTSIDE the index root containing only the
canary files and one positive-control `.py` file; (b) point the daemon at the
fixture directory for this test only; (c) trigger a clean index build of the
fixture WITHOUT any exclusion rules active; (d) query each canary and verify it
appears in results — if any canary is NOT found, abort with an explicit error
(the backend doesn't index that path/extension; canary approach is invalid for
this pattern class). The real index root is NEVER scanned without exclusions.

**Phase 2 — Confirm exclusion using fixture (exclusion rules active):**
(e) add the exclusion rule for the pattern class to the fixture rebuild config;
(f) trigger a clean rebuild of the fixture WITH the exclusion active; (g) query
each canary and the positive-control; (h) verify EACH excluded canary returns
zero results AND the positive-control returns at least one result; (i) if either
assertion fails, abort with an explicit error naming which pattern failed;
(j) query the backend for the fixture project's persistent index path and record
it in the transaction journal (the backend stores the fixture graph under its
data root; deleting the fixture source directory does NOT remove this index);
(k) clean up the fixture source directory; (l) stop the daemon, purge the
fixture backend index using the verified path from step (j) — this purge
requires either a **project-scoped purge API** that removes only the fixture
project's data from the shared store, or an **actual data-store override** for
the fixture run (e.g. a `CBM_DATA_DIR` or equivalent env var that redirects the
SQLite store itself to a temporary path, not a separate `CBM_ALLOWED_ROOT` —
`CBM_ALLOWED_ROOT` is source-path confinement, not store isolation, and does not
prevent writing into the production store); if neither is available, the canary
phase cannot safely complete (see D4 prerequisite "project-scoped purge /
isolated fixture store" in Blocking OQs); then retarget the daemon to the real
index root — this purge happens on BOTH the success and failure paths of the
fixture phase. After both phases pass and the fixture index
is purged, restore the daemon to point at the real index root with all
exclusions active and run the first full real-root build.

**MCP registration is deferred until after the full real-root build passes.** The
correct setup ordering, with write-ahead journaling:

(1) Write the **setup transaction journal** at
`pack_dir("codebase-context")/setup-transaction.json` as the VERY FIRST
artifact, with mode `0600` from creation through every rewrite — the journal may
record a prior MCP registration's token-bearing `"env"` block and must not be
readable by other local users. **On Windows, `mode 0600` does not restrict
Windows ACLs**; after creation, apply and verify an owner-only DACL using
`icacls <path> /reset /inheritance:r /grant:r "<ACCOUNT>:(F)"` where
`<ACCOUNT>` is `os.environ["USERDOMAIN"] + "\\" + os.environ["USERNAME"]`
(or just `os.environ["USERNAME"]` when `USERDOMAIN` is absent) —
`shell=False` does not expand `%USERNAME%` so the literal string must be
resolved from the environment before constructing the `subprocess.run` args.
Alternatively use `win32security` from `pywin32` (optional T2 dep); if neither
works, refuse to create this file and surface a remediation message. The journal lists ALL planned durable targets (fixture directory path,
fixture index path placeholder, real-root index path placeholder,
`~/.claude.json` entry, `config.toml` path, `.cbmignore` path and
created/merged ownership mode; for Serena setups: `project_yml_path`,
`project_yml_ownership` (created/merged), `project_yml_prior_readonly` —
prior scalar value of the `read_only:` key only (not full file content); absent
if the file was newly created), and `serena_dir_ownership` (`"created"` if
setup created the `.serena/` directory, `"pre-existing"` if it already existed) plus a `phase`
field updated atomically at each step. Before creating, merging, or restoring
`.cbmignore`, `.serena/project.yml`, or the `.serena/` directory: use `os.lstat()`
on each target path (and `os.lstat()` on `.serena/` itself) to detect symlinks;
if any is a symlink, **refuse with a remediation message** — writing through a
symlink can escape the index root and modify an unintended target, and rollback
on a symlink would modify the symlink's target rather than the in-root file; do
not follow the symlink. `.cbmignore` is written before the
real-root build (it must exist before indexing begins); the journal records
`cbmignore_path` and `cbmignore_ownership` at the time of creation or merge so
failure cleanup can reverse it. For Serena setups, `<index-root>/.serena/project.yml` is written (or
merged with `read_only: true`) before the promote step; the journal records
`project_yml_path`, `project_yml_ownership`, and `project_yml_prior_readonly` at
write time so failure cleanup and uninstall can reverse the change. A
crash-restart reads this journal to know exactly which artifacts exist and which
phase to resume cleanup from.
**The following steps (2)–(5) apply to `codebase-memory-mcp` only.** For
Serena, the transactional path is: **(0) preflight:** before creating the
transaction journal or modifying any durable artifact, check whether
`<index-root>/.serena/project.local.yml` exists. If it exists: (i) **read the
file bytes exactly once** and compute its SHA-256 from those bytes, retaining
both in memory; (ii) validate the effective `read_only` value via PyYAML by
passing those exact bytes to the subprocess via stdin (not by path — avoids a
TOCTOU race where a concurrent write replaces the file between the parse and
the hash). Because setup.py runs in system Python (which need not have PyYAML),
validation uses an ephemeral `pyyaml` environment. **First check whether
PyYAML is importable in the current Python environment** via
`subprocess.run([sys.executable, '-I', '-c', 'import yaml'], capture_output=True)`.
The `-I` flag (isolated mode) prevents the current working directory from being
added to `sys.path`, which would otherwise allow a repo-controlled `yaml.py` or
`yaml/` package in the checkout to shadow the real PyYAML.
If it is: use `sys.executable -I` directly (no download). If it is NOT: display
a one-line consent prompt — "Validating `.serena/project.local.yml` requires
PyYAML. May we fetch `pyyaml>=6.0,<7` into a temporary uv environment?
[Y/n]" — and abort setup if the user declines. Only when consent is given
does setup invoke `uv run --with` (Tier-2 opt-in). The package is not
`serena-agent` (which would bypass the Serena consent gate); it is `pyyaml`
only, fetched into an ephemeral uv environment, not installed permanently.
The subprocess is dispatched with `--no-project` to prevent project-discovery
side effects; use `python` (not `python3` — absent on Windows):
`subprocess.run([uv_path, 'run', '--no-project', '--with',
'pyyaml>=6.0,<7', 'python', '-I', '-c',
'import sys, yaml; d=yaml.safe_load(sys.stdin.read());'
' sys.exit(1 if isinstance(d, dict) and "read_only" in d'
' and d["read_only"] is not True else 0)'],
input=local_file_bytes, ...)`. Only fail when the parsed mapping explicitly
contains `read_only` with a value that is not boolean `True`; an absent key,
blank file, and unrelated-key mapping are safe; `null`/`~`, `false`, strings,
and numbers all fail. If the subprocess exits
non-zero, or if uv or serena-agent is not yet installed, abort setup with
instructions. If the file is absent, retain nothing. **Do not write anything
to disk during this preflight step**.
(a) check whether `<index-root>/.serena/project.yml`
is tracked by git (`git -C <index_root> ls-files --error-unmatch .serena/project.yml`
exits 0 if tracked); create the transaction journal; record `project_yml_tracked:
true/false` into the journal; if a local-file hash was computed in the preflight,
also record `project_local_yml_hash` in the journal (write only when the file
existed); record both in `config.toml [serena]`; write/merge `read_only: true` into the file and
journal the prior `read_only` key value (not the full content); if tracked and
merged, the post-setup summary must instruct the user to commit the file before
the next pull — otherwise `git pull --rebase` will refuse a dirty tree, which
blocks the only freshness mechanism Serena has;
(b) **stage stable runtime scripts before registration** — this step is
**common to all backends**, not CBM-only, and must complete before the MCP
entry is promoted: generate the configured `launch-backend.py` (with `interpreter_path`, backend
name, and backend-specific confinement value baked in: `CBM_ALLOWED_ROOT` for
`codebase-memory-mcp`; the `--project` path and `read_only` verification gate
for serena) into
`<stable-state-dir>/scripts/`; also copy `normalise_remote.py` and
`uninstall.py` from the projected `scripts/` directory. These are required by
the scope gate (normaliser), staged teardown (uninstall.py), and the MCP
registration (launch-backend.py). The launcher must exist before the MCP entry
is written — promoting registration before the launcher is staged leaves the
MCP server calling a nonexistent command;
(c) **acquire `<stable-state-dir>/config.lock`**; promote MCP registration and
write `config.toml` (no `graph_path`, no `[hooks]`, no `CBM_ALLOWED_ROOT`, no
`cbmignore_*` fields; write `[mcp] ownership` (following the same created/displaced determination and
`prior-mcp-entry.json` sidecar-write protocol as CBM step 5b — if a prior
`mcpServers.codebase-context` entry existed, write it to the `0600`-mode
sidecar and set `[mcp] ownership = "displaced"`; journal `prior_mcp_sidecar:
pending/written`; if no prior entry, set `"created"` and skip the sidecar);
common `[index]` fields, `[scripts]`
fields, and `[serena]` fields: `project_yml_path`, `project_yml_hash` (SHA-256
of the final validated `project.yml` file bytes — compute immediately after
the PyYAML validation and `read_only: true` merge complete; copy from journal
before it is deleted; launch-backend.py compares current file hash against this
value before startup), `project_yml_ownership`,
`project_yml_prior_readonly` — the prior value of the `read_only:` key only (a
scalar, not the full file content), copied from the journal before it is deleted
in step (d); this allows uninstall to restore only the `read_only:` field,
leaving all other user edits intact — `project_yml_tracked`,
`project_local_yml_hash` (copied from the journal; absent if the file did not
exist at setup time — launch-backend.py treats absent hash as
file-must-not-exist), and `serena_dir_ownership` (copied from the journal,
where it was set at step (a)),
so uninstall and crash recovery can still read it after the journal is deleted
at step (d)); release the lock. On the Serena path, no hooks are chained;
(d) **Delete the transaction journal — but not before any old-graph purge
decision completes.** On a switch from `codebase-memory-mcp`, retain the
journal until the old-graph purge offer (reconfiguration flow purge step) has
been accepted or declined: the journal holds the prior CBM `graph_path` and
prior config; deleting it first orphans the old index with no cleanup path.
Once the purge decision completes — or if there is no prior CBM backend — delete
the journal. No canary probe, no build, no `list_projects` step.
Rollback reverses steps (a)–(c) via journal.
(2) Run the two-phase canary probe + fixture index purge (steps above).
(3) Before modifying `.cbmignore` or starting the build, verify the index
root has no uncommitted edits: run `git -C <index_root> diff --name-only HEAD`
(staged + unstaged) and `git -C <index_root> ls-files -o --exclude-standard`
(untracked). Exclude `.cbmignore` from this check — setup will create or merge
it and the journal records that delta; it must not trigger the cleanliness gate.
**Tracked  caveat:** if `.cbmignore` is tracked by git
(`git -C <index_root> ls-files --error-unmatch .cbmignore` exits 0), merging
a sentinel block leaves an uncommitted tracked edit; `git pull --rebase` will
refuse the dirty tree and the index root stops advancing. After setup, the
post-setup summary must instruct the user to commit `.cbmignore` before the
next pull (or the user must commit it manually). Setup records whether `.cbmignore`
is tracked in `cbmignore_tracked: true/false` in the journal so failure cleanup
can unconditionally remove only untracked files it created.
If any other files are returned, fail with a message: the backend indexes the
on-disk checkout including working-tree changes; an uncommitted edit produces a
mixed graph where `indexed_commit` (HEAD) misrepresents the actual indexed
content. The setup prompt already asks the user to choose a checkout not used
for active development — if uncommitted edits are present, require the user to
either commit, stash, or discard them before setup proceeds. Journal `cleanup_index_root = <index_root>` to the journal now — if the
build fails or step (4)'s `list_projects` query returns nothing, failure
cleanup falls back to `purge_by_root(cleanup_index_root)` (see cleanup step (e)).
Before starting the build, query the backend (`list_projects`) to check whether
a project with this index root already exists. Record the result as
`real_root_index_preexisted: true/false` in the journal — failure cleanup step
(e) must only purge the real-root index when this field is `false`; if `true`,
the index predated this transaction and must not be deleted without explicit user
confirmation per AGENTS.md §"Check before acting".
**When `real_root_index_preexisted: true`**, new exclusions are NOT retroactive —
previously indexed credential-bearing symbols remain queryable until the index is
purged and rebuilt. Before proceeding, either (a) offer a project-scoped purge
(with explicit user confirmation naming the consequence: "previously indexed
content will be permanently removed and the index rebuilt from scratch") and
proceed only if the user accepts, or (b) run the same negative check as the
canary — query the backend for content that should be excluded under the current
`.cbmignore` rules; if any excluded content is still present in the index, force
path (a). If the user declines path (a) and the negative check fails, refuse to
continue and print instructions for a manual purge.
If path (a) proceeds: **before invoking the purge**, write
`real_root_index_purge_authorized: true` to the journal. This crash-safe
pre-authorization ensures that if the process dies after the purge succeeds
but before the post-purge journal update, crash recovery can detect that a
purge was in progress and treat the index as transaction-owned regardless of
the `real_root_index_preexisted` field. After the purge succeeds, also
**set `real_root_index_preexisted` to `false`** so that normal (non-crash)
rollback correctly treats any replacement index as transaction-owned and
eligible for purge on failure.
Crash recovery: if `real_root_index_purge_authorized: true` is set and
`real_root_index_preexisted` is still `true` (crash during or just after the
purge), re-check whether the index path still exists; if absent, update the
journal to `real_root_index_preexisted: false` and treat the replacement index
as transaction-owned; if still present, the purge did not complete — retry the
purge or abort with a manual-purge instruction.
Record the index root's
current HEAD (`git -C <index_root> rev-parse HEAD`) as `pre_build_head` in
the journal. Update journal phase to `"real-root-build-started"`; run first
full real-root build with exclusions active. On completion, verify
`git -C <index_root> rev-parse HEAD` still equals `pre_build_head` — if HEAD
has advanced (a concurrent pull landed during the build), abort the build
result, do not record `indexed_commit`, and retry once;
if the retry also sees a concurrent pull, fail with a message asking the user
to retry when no pulls are in progress. Only record `indexed_commit` when
pre-build HEAD equals post-build HEAD. Additionally, **re-run the
tracked/untracked cleanliness check** (`git -C <index_root> diff --name-only HEAD`
and `git -C <index_root> ls-files -o --exclude-standard`, excluding `.cbmignore`)
after the build completes — an editor or generator may have created working-tree
changes during the build without advancing HEAD; if any are found, abort and
require the user to resolve them. Update journal phase to
`"real-root-build-complete"` only on this confirmed-stable, clean result.
(4) **After** the first full real-root build completes and HEAD is confirmed
stable: query the backend for the real-root index path (`list_projects` now
returns the project since the build has completed). Write the backend-confirmed
path to the journal. On fresh setup `list_projects` returns an empty list
BEFORE the build, so step 3 (old ordering) could not obtain a per-project
path — moving this query to after the build ensures the path is backend-verified
and per-project, not guessed or derived from the shared data root.
(4b) **Negative exclusion verification** — before promoting any durable artifact,
for each path returned by the graph, evaluate it against the **complete ordered
`.cbmignore` rule set** using the pack-vendored `gitignore_eval.py` module
located in `setup-codebase-context/scripts/` (a GENERATED copy, byte-identical
to `codebase-context/scripts/gitignore_eval.py`, produced by
`tools/sync-gitignore-eval.py` at `make build-self` time). Setup.py resolves
it as `Path(__file__).parent / 'gitignore_eval.py'` — a path relative to
`setup.py`'s own directory — so setup remains self-contained when only the
`setup-codebase-context` skill is projected (no sibling `codebase-context/`
required). Step 5c then copies
this file to `<stable-state-dir>/scripts/gitignore_eval.py` alongside
`normalise_remote.py` and `uninstall.py`; `rebuild_coordinator.py` imports it
from that stable location at runtime. Uninstall removes `gitignore_eval.py`
from `<stable-state-dir>/scripts/` as part of its script-cleanup step. This
module is a minimal pure-stdlib Python implementation (no third-party
dependency; imports only `re`, `pathlib`, `os`); it accepts the `.cbmignore`
file bytes as the **exclusive rule source** and implements the full semantics
described below (do NOT use `git check-ignore` for this purpose — it loads
git's native ignore sources such as `.gitignore`, `.git/info/exclude`, and
`core.excludesFile`, not `.cbmignore`; it also hides tracked files by default
unless `--no-index` is supplied). A summary of the
semantics that the evaluator must implement: evaluate each path component from
root to leaf in rule order; each ancestor directory's final inclusion state is
determined by whether the last matching rule is a negation (included) or
exclusion (excluded); a file cannot be re-included when its immediate parent
directory is effectively excluded after all rules are applied — but a directory
exclusion can be undone by a subsequent negation targeting that directory
(example: `vendor/`, `!vendor/` — directory re-included; then `vendor/*`,
`!vendor/README.md` — README re-included within it). A path is **effectively
excluded** when either its own last matching rule is a non-negated exclusion,
or its parent directory's effective state is excluded. Query the graph for **all** effectively excluded paths using an **exhaustive
path-enumeration API** — the query must not be ranked, scored, or limited to
a top-N result set; if the backend's API paginates, enumerate all pages until
no results remain; if the backend provides no exhaustive path-enumeration API
(only ranked or limited queries), use an alternative mechanism that proves
absence — for example, query the graph for each excluded path candidate
individually, or compare the set of all indexed paths (obtained from an
exhaustive index listing) against the set of effectively excluded paths. If
any excluded path is found in the graph, the initial build did not fully honor
the exclusion file. Abort, retain cleanup state in the journal, and instruct
the user to delete the index and rerun setup (or, for backends that expose a
purge command, run the purge and rerun). Do not write `cbmignore_content_at_index`
until this verification passes — recording the baseline without confirming
exclusions are absent would allow excluded content to remain queryable while
PLAN checks see a matching hash and never trigger a corrective rebuild.
(5) If and only if step 4b passes, promote durable artifacts in this order —
recording each to the journal BEFORE writing, to enable rollback.
**On a rerun, before any promotion write:** read and capture the current
`mcpServers.codebase-context` entry from `~/.claude.json`. Reconstruct the
**prior installed wrapper template** — the `"command"` and `"args"` values that
setup.py would have written for the interpreter that was recorded at the PRIOR
install (read the top-level `interpreter_path` field from the stored `config.toml`). Compare
the current entry against that prior template, not the new template about to be
written. A difference from the prior template indicates external drift (user or
another installer replaced the entry); a difference only between old interpreter
and new interpreter (pack-managed update) is not external drift and must not
trigger the displacement path. If external drift is detected and the current
entry is **absent** (completely deleted since the prior install): surface a
confirmation prompt noting the entry is gone and ask for explicit consent to
recreate it; on consent, determine ownership by the PREVIOUS installation's
ownership: if the previous `[mcp] ownership` was `"displaced"`, the sidecar
holds the original user-owned entry that must be restored on teardown — retain
`displaced` ownership and keep the sidecar intact (the absent generated entry
does not change the obligation to restore the original); if the previous
ownership was `"created"`, there is no prior user entry to restore — treat the
rerun as `[mcp] ownership = "created"` and remove any stale sidecar. If
external drift is detected and the current entry **is present**
but differs from the prior template: surface a confirmation prompt showing a
**structural summary only** — never render the raw `"command"`, `"args"`, or
`"env"` values, as third-party MCP registrations may carry tokens or
credentials in any of those fields; instead show only structural metadata
such as the number of args and whether an env block is present (e.g.
`command: <redacted>, args: [<N> args], env: {<M> keys}`) so the user can
identify the entry without exposing credentials in terminal output or
captured setup logs; the same redaction applies to the uninstall prompt
that displays the stored sidecar entry; ask for explicit consent to
overwrite; on explicit consent,
write the drifted entry to the sidecar file (replacing the entry stored from
the original install, mode `0600`) and set `[mcp] ownership = "displaced"` in
the pending config state — treat the rerun as if a displaced entry existed. If
the entry has not drifted externally, carry the existing `[mcp] ownership` and
sidecar forward unchanged. Do not proceed to any promotion write without this
pre-check on a rerun.
  (5a) Journal records `mcp_registration: pending`; generate
       `pack_dir/scripts/launch-backend.py` (the minimal-environment wrapper,
       baking in `CBM_ALLOWED_ROOT` and the backend binary path); write
       `~/.claude.json` (add `"command": <interpreter_path>, "args": ["-I",
       "<pack_dir>/scripts/launch-backend.py"]` — no `"env"` block, since
       `CBM_ALLOWED_ROOT` is embedded in the wrapper); journal updates to
       `mcp_registration: written`.
  (5b) Journal records `config_toml: pending`; acquire `<stable-state-dir>/config.lock`
       (consistent with the invariant that all `config.toml` writers hold this
       lock — setup.lock does not exclude a concurrent PLAN-time `rebuild_coordinator.py`
       publication); write `config.toml` (including
       `graph_path`, `indexed_commit`, `cbmignore_ownership`,
       `cbmignore_content_at_index` (SHA-256 of `.cbmignore` content at setup
       time — gives the PLAN untracked-`.cbmignore` check (c) a baseline
       immediately after a fresh install, before any rebuild),
       `[mcp] ownership` (`"created"` if no prior entry existed; `"displaced"`
       if a prior entry was overwritten — this field must be written at setup
       time, not derived later, because uninstall branches on it to decide
       whether to remove or restore the MCP entry);
       common `[index]` fields (`repo_url`, `repo_url_source`, `remote_url_raw`,
       `index_root_origin_at_setup`, `index_root_url_raw`)).
       On a **rerun**, use the `[mcp] ownership` and sidecar state determined
       by the pre-promotion drift check above.
       On a **first install**: if a prior `mcpServers.codebase-context` entry
       existed at setup time, write its full JSON to a separately-permissioned
       sidecar file (`pack_dir("codebase-context")/prior-mcp-entry.json`, mode `0600`; on Windows apply an owner-only DACL
       as described for the setup journal above) —
       not into `config.toml`, which is PLAN-visible and must stay secret-free
       (a prior entry’s `"env"` block may contain tokens); set
       `[mcp] ownership = "displaced"`. If no prior entry existed, set
       `[mcp] ownership = "created"` and skip the sidecar. Journal records `prior_mcp_sidecar: pending` before writing,
       `prior_mcp_sidecar: written` after — failure cleanup must delete the
       sidecar if the journal shows it was written but setup did not complete (to
       prevent credential-bearing stale state and incorrect restoration by a later
       uninstall); PLAN-time code must never read it; this sidecar is deleted by
       uninstall after restoring the entry;
       journal updates to `config_toml: written`.
  (5c) Copy scripts to `pack_dir/scripts/` — includes `normalise_remote.py`,
       `uninstall.py`, `gitignore_eval.py`, and `codebase-context-cleanup.py`
       for stable out-of-session access;
       write the `scripts-version-gitignore-eval` stamp to `pack_dir` reflecting
       the `__scripts_version_gitignore_eval__` value baked into the projected
       `rebuild_coordinator.py`; chain git hook sentinels. (Step 4b reads
       `gitignore_eval.py` from the pack source directory before promotion; step
       5c copies it to the durable stable location used by
       `rebuild_coordinator.py` at runtime.)
  (5d) Mark setup complete. **Delete the transaction journal only after the
       old-graph purge decision completes** (when the index root or backend
       changed): the later old-graph purge step reads the previous `graph_path`
       from the journal; deleting it at this step would permanently lose the
       safe reference to the old, potentially secret-containing index if a
       crash occurs before the purge offer is made. Retain the journal until
       the user accepts or declines the purge offer; then delete the journal.
       **Do NOT delete the tombstone (`graph-purge-pending`) here** — if the
       purge is declined or fails, the tombstone must survive beyond the journal
       deletion so that a future uninstall sees the deferred-purge marker and
       does not lose the reference to the old index. Delete the tombstone only
       when the cleanup flow verifies or acknowledges the purge is complete.
       When neither the index root nor the backend changed, the journal may be
       deleted immediately after promotion.

**Before writing any artifact on a rerun**, the journal must record the
**prior value** of that artifact (e.g., the existing `~/.claude.json`
`codebase-context` entry, the existing `config.toml` content, the
`.cbmignore` state). Failure cleanup uses these prior values to **restore**,
not unconditionally delete: if the artifact was newly absent before this
transaction, delete it; if the artifact previously existed, restore the
recorded prior value. This prevents a rerun crash from destroying a working
previous installation.

**Failure cleanup at any phase** (including after partial promotion in step 5):
Treat `pending` and `written` states identically — a crash may occur after the
artifact is written but before the journal state transitions from `pending` to
`written`; both states must trigger idempotent verification and restoration.
(a) if `mcp_registration` is `pending` or `written` in journal: if
`prior_mcp_registration` in journal is absent, remove the `codebase-context`
entry from `~/.claude.json`; if `prior_mcp_registration` is present, restore
it; (b) if `config_toml` is `pending` or `written` in journal: if
`prior_config_toml` is absent, delete `config.toml`; if present, restore its
recorded content; (c) if `cbmignore_path` is in journal: if
`cbmignore_ownership` is `"created"` (newly created this transaction): compare
current file content against the setup-authored content; if no user additions
are present, delete the file; if user added patterns after the crash, remove only the setup-owned
sentinel-delimited block while preserving the user's patterns — do not defer
to teardown, since the transaction journal is deleted in step (h) and no
durable installation remains to execute teardown; if `"merged"`, remove only
the sentinel-delimited block added this transaction (restoring the file to
its pre-merge state);
(c2) if `project_yml_path` is in journal (Serena setups only): if
`project_yml_ownership` is `"created"`, compare the current file content
against the setup-authored content; if no user additions are present, delete
the file; if the user added keys after the crash, retain those keys and
restore only the `read_only:` key to its prior value (stored in
`project_yml_prior_readonly`, or remove the line if absent) — do not silently
erase user work; if
`"merged"`, restore only the `read_only:` key to the prior value stored in
`project_yml_prior_readonly` (or remove the line if absent) — do not restore
the full file to avoid discarding post-setup user edits;
(c3) if `serena_dir_ownership` in the journal is `"created"` and, after
reversing (c2), the `.serena/` directory is empty: remove it — setup created
it and crash-recovery must clean it up;
(d) purge the fixture index: if journal records a backend fixture index path,
purge it directly; if the journal was written before the canary phase recorded
that path (i.e. `fixture_index_path` is absent but `fixture_source_root` is
present), use a backend `purge_by_root` or `list_projects`-then-delete call to
find and remove any index entry whose source root matches the recorded fixture
directory — this closes the window where a pre-index-path crash leaves an
orphaned project in the shared SQLite store invisible to path-based cleanup; (e) if
the real-root build had started (phase ≥ `"real-root-build-started"`) AND the
journal records `real_root_index_preexisted: false` (queried from the backend
before the build started; if `true`, the index predated this transaction —
do NOT purge automatically; require explicit user confirmation first per
AGENTS.md §"Check before acting"): purge the real-root index. If the journal has a `graph_path`
(step 4 completed), purge from that path after the shared-store safety check
(verify the recorded path is a per-project artifact, not the shared SQLite
database; if it identifies the shared database or cannot be confirmed
per-project, print the path and require manual removal). If the journal has
no `graph_path` (build or `list_projects` failed before step 4), fall back
to `purge_by_root(cleanup_index_root)` — query the backend for any project
whose index root matches `cleanup_index_root` and purge each result; apply
the same shared-store safety check before purging. For same-root reruns (index predates this transaction), skip the purge on
rollback — purging it would leave the restored config/registration pointing at
a missing index. **However**, if the real-root build had started (phase ≥
`"real-root-build-started"`), the rebuild may have modified the pre-existing
index before failing; the prior index is no longer guaranteed to be consistent
with the prior config/registration. After restoring config/registration in
steps (a)/(b), write a stale marker (`pack_dir("codebase-context")/stale`) so
the next PLAN sees an explicit staleness signal and triggers a clean rebuild
rather than querying a potentially modified graph; (f) delete all canary files and the
fixture directory; (g) if scripts were copied or hooks were chained by THIS
TRANSACTION (journal records them), remove only those scripts and sentinel
blocks — do not remove scripts or hooks that predate this transaction (they
may belong to a prior working installation that was being replaced); if
prior scripts/hooks existed, restore them from the journal's prior_value
record; (h) delete the transaction journal only after all prior cleanup steps
complete successfully — retain it if any step fails, so that a subsequent
rerun can resume cleanup from the last successful point. This ensures a failed
setup leaves no globally-callable MCP registration or partial configuration
behind.
**As its very first action** (initial install or rerun), `setup.py` must
**acquire an exclusive maintenance lock** (`<stable-state-dir>/setup.lock`,
e.g. `fcntl.flock(LOCK_EX|LOCK_NB)` on POSIX,
`LockFileEx(LOCKFILE_EXCLUSIVE_LOCK|LOCKFILE_FAIL_IMMEDIATELY)` on a dedicated
lock file on Windows) and hold it through the entire setup sequence (releasing
only after the journal is deleted or after a clean failure exit). This applies
equally to fresh installs and reruns — two concurrent fresh invocations can
both write the journal to the same fixed path, running canary daemon
stop/purge/restart concurrently and clobbering each other (the same race the
lock was introduced to prevent on crash-reruns; `uninstall.py` already acquires
this lock unconditionally). If the lock is already held, `setup.py` must exit
with a clear message that another setup is in progress.
Detect the journal and run the full cleanup before starting fresh. Setup must
not exit success without canary-confirmed exclusion
check: a registration promoted before exclusions are verified leaves an open
question about whether secret paths were indexed before exclusions took
effect.

### MCP registration (user-scope)

`setup.py` reads `~/.claude.json`, merges the new entry atomically
(write-to-tmp + rename). Before the rename, `setup.py` must call
`os.lstat("~/.claude.json")` — if the result is a symlink, renaming the temp
file over it would replace the symlink itself (detaching any
dotfiles-manager-owned target) rather than updating the target's contents.
On a symlink, `setup.py` must refuse with remediation instructions, or
explicitly resolve the symlink and write to the real target after confirming it
is within an expected location. **File mode must be preserved:** if
`~/.claude.json` already exists, read its mode via `os.stat().st_mode` and
apply it to the temp file with `os.chmod()` before `os.replace()` — a normal
`022` umask creates a `0644` temp file that would expose token-bearing entries
for other registered MCP servers to local users. If the file does not yet
exist, create the temp file with mode `0600` explicitly. Then rename atomically.
**Windows caveat:** `os.chmod()` only controls the read-only attribute on
Windows — it does not preserve Windows DACLs. On Windows, use
`subprocess.run(["icacls", str(tmp_path), "/reset", "/inheritance:r",
    "/grant:r", (os.environ["USERDOMAIN"] + "\\" + os.environ["USERNAME"]
    if "USERDOMAIN" in os.environ else os.environ["USERNAME"]) + ":(F)"],
    check=True)` — resolve `USERNAME` from
the environment; `shell=False` does not expand `%USERNAME%` (built-in Windows CLI, no
external dependency) on the temp file before `os.replace()`. If `icacls`
fails or is unavailable and `~/.claude.json` already exists, **fail closed**
— refuse to write and surface a remediation message. Alternatively, use
`win32security.GetFileSecurity`/`SetFileSecurity` from `pywin32` if already
installed (declare as optional T2 dependency, not T1). If `~/.claude.json`
does not yet exist, falling back to parent-directory DACL inheritance is
acceptable (no existing tokens to expose).
(Torn-write-safe; not concurrent-writer-safe — see Open Questions.)

No bearer token is generated. The MCP registration contains only the command,
args, and environment variables. `CBM_ALLOWED_ROOT` is embedded in `launch-backend.py` (not in a `"env"` block
in `~/.claude.json`) — it is a filesystem path, not a secret, but it does
reveal which repository is indexed.

`setup.py` writes a **PLAN-visible config** that contains no secrets — only the
metadata the scope-gate needs:

```toml
# ~/.agentbundle/codebase-context/config.toml  (no secrets)
config_version = "1"                      # bumped whenever this file's schema changes;
                                          # codebase-context and setup.py both check this
                                          # on startup and refuse/force rerun on mismatch
interpreter_path = "/usr/bin/python3"     # absolute path to the validated durable system
                                          # interpreter selected at setup time (NOT sys.executable
                                          # — see interpreter probe rules); used by staged commands
                                          # (update, uninstall) so no PATH lookup is needed

[mcp]
ownership    = "created"                  # "created" if no prior mcpServers.codebase-context
                                          # existed at setup time; "displaced" if a prior entry
                                          # was overwritten. Written at setup, read by uninstall
                                          # to decide whether to remove or restore the entry.

[backend]
name         = "codebase-memory-mcp"      # or "serena"

[index]
root          = "/path/to/main-checkout"
repo_url      = "example.com/org/repo"      # normalised: host/org/repo, no scheme, no .git
repo_url_source = "auto"                     # "auto" = derived from git remote get-url origin via
                                              # normalise_remote.py; "override" = set via setup.py
                                              # --repo-url. Normalizer migration must not re-derive
                                              # from origin when this is "override".
remote_url_raw = "https://example.com/org/repo.git"  # credential-redacted raw remote URL (fragment,
                                              # credential query params, and HTTP/HTTPS userinfo
                                              # stripped); source is git remote get-url origin for
                                              # "auto", or the user-supplied --repo-url for
                                              # "override"; normalizer migration anchor for both
index_root_origin_at_setup = "example.com/org/repo"  # normalised origin of index root at setup time
                                              # (independent of repo_url / --repo-url override);
                                              # used by PLAN scope gate to detect post-setup
                                              # identity change on the index root
index_root_url_raw = "https://example.com/org/repo.git"  # credential-redacted raw remote URL of the
                                              # index root's origin; written at setup time (step 5b/c)
                                              # alongside index_root_origin_at_setup; normalizer-
                                              # migration anchor for re-deriving
                                              # index_root_origin_at_setup on normalizer upgrade
                                              # (mirrors remote_url_raw / repo_url for the index root)
graph_path    = "/verified/path/to/graph-db" # backend-confirmed exact index path; used by
                                              # uninstall without querying a stopped daemon
indexed_commit = "abc123..."                  # HEAD of index root at last successful full
                                              # rebuild; set by rebuild_coordinator.py;
                                              # used by PLAN scope gate to compute stale
                                              # delta vs active worktree HEAD
indexed_commit_gen = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"  # UUID (str(uuid.uuid4())) generated fresh
                                              # for each successful rebuild publication; used as
                                              # a CAS token: the coordinator captures prior_gen
                                              # at claim time and checks for equality before
                                              # publishing, so a concurrent publisher's own_gen
                                              # will differ and the losing session correctly
                                              # yields. Not an integer counter.
last_rebuild_timestamp_ns = 1700000000000000000  # monotonic wall-clock nanoseconds
                                              # (time.time_ns()) recorded by rebuild_coordinator.py
                                              # immediately after a successful full rebuild
                                              # publication — written only by rebuild_coordinator.py,
                                              # never by setup, normalizer migration, or the launcher.
                                              # Used as the project-specific freshness proof in the
                                              # freshness-skip check: replace "config.toml mtime >
                                              # stale_event_ns" with
                                              # "last_rebuild_timestamp_ns > stale_event_ns".
                                              # Absent on first setup (before first rebuild); treated
                                              # as 0 (force rebuild) when missing.

[hooks]
dir          = "/path/to/main-checkout/.git/hooks"  # absolute path where sentinels were written
claim_timeout_seconds = 300                  # how long a stale.claimed.<pid> marker is
                                              # considered live before being treated as an
                                              # orphan; default 5 minutes (300 s)
manual       = []                             # list of hook names (e.g. ["post-checkout"])
                                              # that were not auto-modified by setup and
                                              # require manual removal on uninstall
# hook_<name>_prior_mode = 0o644             # one key per hook modified by setup; <name> is
                                              # the hook filename (e.g. "post-merge"). Written
                                              # when setup applies chmod +x to activate the hook;
                                              # restored by uninstall via os.chmod after sentinel
                                              # removal. Only present when chmod +x was applied.
# hook_<name>_created = true                 # one key per hook that did NOT exist before setup;
                                              # setup creates the file with #!/bin/sh shebang +
                                              # chmod +x. Uninstall: after removing the sentinel
                                              # block, if the file contains ONLY the shebang line
                                              # (i.e. no other content was added post-setup),
                                              # delete the file entirely; if other content was
                                              # added, remove only the sentinel block. Only
                                              # present when the hook file was created by setup.

[exclusions]
cbmignore_path      = "/path/to/main-checkout/.cbmignore"  # absolute path to .cbmignore
cbmignore_ownership = "created"  # "created" = setup.py created the file; "merged" = patterns
                                  # were added to a pre-existing file. Determines uninstall
                                  # behavior: "created" → offer to delete; "merged" →
                                  # remove only the sentinel-delimited block.
cbmignore_content_at_index = "sha256:aabbcc..."  # SHA-256 hex hash of .cbmignore content
                                  # at setup time (written at step 5b) or last successful
                                  # rebuild (updated by rebuild_coordinator.py after each
                                  # successful rebuild + negative check). Used by PLAN as
                                  # any-change detection for untracked .cbmignore files:
                                  # a hash mismatch means the file changed since setup/last
                                  # rebuild → conservative force-rebuild. Cannot identify
                                  # which patterns changed. Present after a successful setup.

# Written at setup time (step 5b); refreshed by codebase-context on each PLAN startup
[scripts]
pack_scripts_dir      = "/path/to/projected/scripts/"  # projected pack scripts dir; used for
                                                        # normalise_remote.py + uninstall.py refresh
                                                        # and launcher version stamp check
install_route         = "agentbundle"  # always "agentbundle"; plugin route is not supported
launcher_version_expected = "1.0.0"   # version from scripts-version-launcher at last setup or PLAN refresh;
                                       # stable launcher compares its __launcher_version__ against this;
                                       # codebase-context skill updates it on each PLAN startup if newer;
                                       # deleted along with config.toml during teardown

# Serena-only: written during Serena setup; absent for codebase-memory-mcp installs
[serena]
project_yml_path      = "/path/to/index-root/.serena/project.yml"  # absolute path to Serena project config
project_yml_hash      = "sha256:aabbcc..."  # SHA-256 hex of the final validated project.yml bytes
                                        # at setup time; written by setup step (c) immediately after
                                        # PyYAML validation and read_only: true merge complete.
                                        # launch-backend.py computes SHA-256 of the current file and
                                        # compares against this hash before os.execvpe; any mismatch
                                        # (including YAML edits, anchor/alias additions, byte-level
                                        # changes) causes a refused startup.
project_yml_ownership = "created"  # "created" = setup.py created the file; "merged" = merged
                                    # read_only: true into a pre-existing file. Uninstall:
                                    # "created" → offer to delete; "merged" → restore prior.
project_yml_prior_readonly = "false"   # prior value of read_only: key before setup merged read_only: true
                                        # (absent if "created" or key was not set); uninstall restores only
                                        # this key — not the full file — so post-setup user edits are kept
project_yml_tracked = "false"          # "true" if .serena/project.yml was git-tracked at setup time;
                                        # post-setup summary instructs user to commit before next pull
# project_local_yml_hash = "..."       # SHA-256 of .serena/project.local.yml at setup time; this key
                                        # is OMITTED when the file did not exist at setup time.
                                        # launch-backend.py: absent key → file must not exist;
                                        # present key → file must exist with matching hash.
serena_dir_ownership = "created"       # "created" = setup.py created the .serena/ directory;
                                        # "pre-existing" = .serena/ already existed. Uninstall removes
                                        # the directory only when "created" and it is empty after
                                        # removing project.yml. Crash recovery (c3) also checks this.
```

`hooks.dir` is the exact resolved path where `setup.py` chained the sentinel
blocks. This is required for uninstall and reconfiguration — when `core.hooksPath`
changes after setup, or when the user switches backends, the old sentinel blocks
must be removed from the **original** hooks directory. Without this stored path,
uninstall would re-derive the hooks directory from the current git configuration
(which may have changed) and miss the old sentinels. `uninstall.py` reads
`hooks.dir` from this config rather than re-resolving it.

`repo_url` is the scope-gate identity key. `setup.py` normalises the URL
returned by `git -C <root> remote get-url origin`:

1. **Strip credential-bearing components carefully — fail closed on
   resource-selecting components:** Userinfo, query strings, and fragments can
   carry credentials, but they can also function as resource selectors (e.g.,
   an SSH username that identifies a tenanted namespace, or a query param that
   routes to a specific org/project). Stripping them blindly collapses distinct
   origins to the same `repo_url`, allowing a session on origin B to pass the
   scope gate and consume origin A's graph. Rules:
   - **SSH userinfo:** the pattern `git@host:path` is safe to normalize
     (`git` is the protocol user, not a tenant). Any other SSH username
     (`alice@host:path`) is a resource selector — **fail closed** with an
     error asking the user to configure a canonical credential-free remote URL.
   - **HTTP/HTTPS userinfo:** strip the password/token portion (`user:PAT@host`
     → `user@host` is still ambiguous; `host` is safe). For any non-empty
     HTTP username, fail closed with the same message.
   - **Query string:** strip only **recognized credential key names**
     (`access_token`, `token`, `api_key`, `private_token`, `oauth_token`).
     If any non-credential query params remain after stripping, **fail closed**
     — they may select a repository or tenant.
   - **Fragment:** strip unconditionally (no safe resource-selector use case).
   This prevents any credential from appearing in PLAN-visible config, while
   refusing to silently alias distinct origins. Tests include:
   `https://user:token@example.com/org/repo` → fail closed;
   `https://example.com/org/repo?access_token=secret` → strip → ok;
   `https://example.com/org/repo?scope=read` → fail closed;
   `git@example.com:org/repo.git` → `example.com/org/repo`.
2. Strip scheme and `.git` suffix, canonicalise `git@host:path` → `host/path`,
   lowercase host, preserve path segment case as-is.

The path-case policy is pinned by the SSH/HTTPS/userinfo/query/fragment test
cases in the pack's unit-test suite — if the origin URLs at setup and at PLAN
time differ only in path case (e.g. `org/Repo` vs `org/repo`), the scope-gate
fails closed.

### Index root: regularly-pulled main checkout

The index root must be kept current via periodic `git pull` — this is the
primary freshness driver for both backends. It should be a checkout not used
for active feature development, but it is not read-only; `git pull` on it is
what triggers the `codebase-memory-mcp` file watcher (Tier 1) to re-index, and
what writes the staleness marker via the git hooks (Tier 2). For `serena`,
freshness equals the on-disk currency of the index root — `git pull` is the
only control.

Note: `git pull --rebase` fires `post-rewrite` and `post-checkout`, not
`post-merge`. The pack chains all three hooks (`post-merge`, `post-rewrite`,
`post-checkout`) so that any pull strategy writes the staleness marker.

`setup.py` lists available worktree paths via `git worktree list --porcelain`
and also accepts a free-form path (validated as a git checkout). The setup
prompt:

> "The index root should be a checkout you regularly `git pull` but do not use
> for active feature development — for example, a dedicated worktree on `main`.
> Keeping it current via `git pull` is what keeps the graph current (Tier 1
> watcher picks up the file changes; Tier 2 hooks write a staleness marker as a
> backup signal). An active feature session editing it may degrade graph
> quality."

### Scope-gate: repo-identity, not path containment

The scope-gate compares repo identity, not path ancestry — a session's active
directory and the index root are typically siblings (different worktrees or
clones), so `$PWD` is never under `index_root`. The `codebase-context` SKILL.md
at PLAN start:

1. Call `normalise_remote.py` from `pack_dir("codebase-context")/scripts/` with the current
   CWD — this is the same script used by `setup.py`, ensuring the normalisation
   logic is shared and tested, not re-implemented in prose.
2. **Also call `normalise_remote.py` with the index root** recorded in
   `config.toml [index] root`; compare the result against
   `config.toml [index] index_root_origin_at_setup` (the index root's
   normalised origin recorded at setup time, independent of any `--repo-url`
   override); if they differ, fail closed — the index root's repository identity
   changed after setup. Do NOT compare against `repo_url` here — when
   `--repo-url` was used to authorize a fork, `repo_url` contains the fork URL,
   not the index root's actual origin, and this check would always fail.
3. Compare the CWD output (step 1) against `repo_url` in `pack_dir("codebase-context")/config.toml`
   (the PLAN-visible config; no token in this file).
4. If they differ, or if `git remote get-url origin` fails (no origin, alternate
   remote name), or if `normalise_remote.py` exits non-zero: fail closed — skip
   all graph tools, use direct file reads. This includes
   fork workflows where `origin` points at a fork and not the canonical repo —
   the gate fails closed silently; SKILL.md notes this and explains the user
   can set `repo_url` to the fork's `origin` URL via `setup.py --repo-url`.
5. **Liveness probe.** If repo_url matched (steps 1–4 pass):
   call a backend-specific known tool to confirm the backend is responding.
   If the call returns a subprocess error or MCP tool error, skip all graph
   tools and fall back to direct file reads. The Tier-3 freshness check
   (§ Three-tier freshness) runs after this step and before step 6.
6. **Validate graph currency against active worktree HEAD.** This step must
   run AFTER the liveness probe and any pending freshness check (§ Three-tier freshness):
   if a stale marker was present and triggered a rebuild via `rebuild_coordinator.py`,
   read `indexed_commit` from `config.toml` only AFTER that rebuild completes and
   `rebuild_coordinator.py` has written the updated commit hash. Do NOT read
   `indexed_commit` before the freshness check — a watcher-driven (Tier 1)
   incremental update by the backend may have advanced the index without going
   through `rebuild_coordinator.py`, leaving `indexed_commit` pointing at a
   commit older than what the index actually represents. To detect this without
   relying on the hook having written a stale marker: after reading
   `indexed_commit`, run `git -C <index_root> rev-parse HEAD` and compare.
   Two branches:

   **Branch A — index root has diverged** (index root HEAD ≠ indexed_commit in
   any direction — ahead, behind, or divergent): treat `indexed_commit` as
   absent (conservative fallback). Synthesize a stale marker if none already
   exists at the stale marker location: write a new `stale` file (or call
   `os.utime(stale_path, None)`) so subsequent PLANs invoke
   `rebuild_coordinator.py` rather than repeating this fallback indefinitely.
   **Fall back globally** — do NOT attempt a file-level differential fallback
   in this branch; the file-changed set relative to `indexed_commit` is
   meaningless when the index root itself has advanced (worktree HEAD may equal
   `indexed_commit` while the index root has advanced, yielding an empty
   changed-file set that wrongly allows graph queries). Annotate ALL graph
   responses in this PLAN with `GRAPH-FALLBACK: index-diverged` until a
   rebuild completes.

   **Branch B — index root is current** (index root HEAD == indexed_commit):
   also compare `git -C <worktree> rev-parse HEAD` against `indexed_commit`.
   If the active worktree HEAD differs — the worktree is on a different branch
   or has committed changes beyond `indexed_commit` — perform a committed-file
   differential fallback **only** (no stale marker synthesis; the index root is
   current and does not need rebuilding): identify changed files using
   `git diff --name-status -z <indexed_commit>..<worktree_HEAD>`; include
   both paths for `R` (rename) entries; force direct reads for all returned
   paths with `GRAPH-FALLBACK: worktree-ahead`. This prevents a clean feature
   worktree from bypassing the graph currency check while its committed changes
   are absent from the graph. If worktree HEAD equals `indexed_commit`, no
   committed-file fallback is needed and graph queries proceed normally for
   unchanged files.
   **Also include locally modified files** from both the active worktree AND
   the index root. Run:
   - `git -C <worktree> diff --name-status -z HEAD` (staged + unstaged, active worktree; parse `R` entries to add both old and new paths)
   - `git -C <worktree> ls-files -z --others --exclude-standard` (untracked, active worktree; parse NUL-delimited — without `-z`, filenames containing non-ASCII characters, tabs, or newlines are quoted and may be misread)
   - `git -C <index_root> diff --name-status -z HEAD` (staged + unstaged, index root; parse `R` entries to add both paths)
   - `git -C <index_root> ls-files -z --others --exclude-standard` (untracked, index root; parse NUL-delimited)
   (`<worktree>` is the resolved repository root, not the current working directory — if
   the skill runs from a subdirectory, unqualified git commands would scope probes to that
   prefix and miss changes elsewhere in the tree.)
   Add all returned paths to the direct-read fallback set with
   `GRAPH-FALLBACK: local-edit`. If any git command fails, fail closed
   (treat the entire graph as stale for this PLAN). **Exception for
   `codebase-memory-mcp` when the index root itself is dirty:** Tier 1
   (file watcher) indexes editor saves live, so the graph may already contain
   uncommitted symbols and edges for the dirty files — `indexed_commit` still
   names HEAD, but the graph is ahead of it for those paths. Direct-reading
   only the dirty files does not restore snapshot consistency because queries
   involving those paths (e.g. callers, call-graph edges) can return a mix of
   committed and uncommitted data from other files. When the index root has any locally modified or untracked files under
   `codebase-memory-mcp`, fall back globally (treat the entire graph as stale
   for this PLAN) rather than direct-reading only the dirty paths. **Exclude
   setup-owned files from both checks:** read `config.toml [exclusions]
   cbmignore_path` (stored as an absolute path) and omit it from **both** the
   untracked-file list (`git ls-files -o`) **and** the tracked-diff output
   (`git diff --name-only HEAD`) — both commands emit repository-relative paths,
   so resolve each output path against `index_root` (e.g.
   `Path(index_root) / git_relative_path`) before comparing to `cbmignore_path`.
   When `.cbmignore` is tracked, setup's merge appears in the tracked-diff, not
   the untracked list; omitting it only from the untracked list would still
   trigger the fallback on every PLAN until the user commits it.
   **Before exempting `.cbmignore`:** re-read its content and verify three things:
   (a) the setup-sentinel-delimited exclusion block is still intact (no required
   patterns have been removed or weakened by a pull or user edit); (b) no
   negation patterns appear after the sentinel that would re-enable a mandatory
   exclusion — `.cbmignore` uses gitignore last-match semantics, so an appended
   `!.env` or `!secrets/` after the sentinel overrides a mandatory exclusion even
   with the block intact; scan all lines after the sentinel and reject any negation
   (`!<pattern>`) that matches a mandatory exclusion path; and (c) no new
   **positive** exclusion patterns (non-comment, non-negation, non-empty lines
   outside the setup sentinel) were added since the last indexed state —
   exclusion changes are not retroactive (previously indexed content remains
   queryable until a rebuild), so any new positive pattern outside the sentinel
   is a signal that the user intended to exclude content that may already be in
   the graph. Detect this by comparing the SHA-256 hash of the current `.cbmignore`
   against `config.toml [exclusions] cbmignore_content_at_index` — a hash
   recorded at setup time or after the last rebuild. Do NOT use
   `git show <indexed_commit>:.cbmignore` for tracked files: setup may have
   merged its sentinel block and permitted deferring the commit; comparing
   against the committed version would force a purge/rebuild on every PLAN
   until the user commits, even when no user-authored pattern changed. Using
   `cbmignore_content_at_index` for both tracked and untracked files ensures
   the comparison reflects what was actually indexed. A mismatch means the
   file changed since the last indexed state (any-change detection — cannot
   identify which patterns changed); if the field is absent, treat `.cbmignore`
   as changed — conservative fallback for pre-existing setups before this
   field was defined.
   If check (a), (b), or (c) fails,
   treat `.cbmignore` as a changed file — do NOT exempt it — and require a
   purge/rebuild with negative verification before allowing graph queries.
   Apply the same normalization to `config.toml [serena] project_yml_path` when
   excluding `.serena/project.yml` from both dirty-file checks. These files
   are created and managed by `setup.py`, not user-authored content, and their
   presence (with intact setup content) must not trigger a fallback.
   For files unchanged since `indexed_commit` and not locally modified, graph
   queries may proceed — but note that incoming call-graph edges for those files
   may be stale: if a *caller* changed since `indexed_commit` but the callee did
   not, the graph will not reflect the new or removed call edge. Treat graph
   results for unchanged files as a blast-radius baseline, not an authoritative
   edge set; manually inspect callers of changed files.
   If `indexed_commit` is absent from config (setup predates this field, was
   interrupted before the first full build, or the backend advanced the index
   without `rebuild_coordinator.py`), treat the entire graph as stale and
   fall back to direct reads for this PLAN.
   **Backend-conditional:** this step applies only when the configured backend
   is `codebase-memory-mcp`. For `serena`, setup installs neither hooks nor
   `rebuild_coordinator.py`, so `indexed_commit` is never written and cannot
   advance. Instead of comparing `indexed_commit`, compare the **index root's
   current HEAD** (`git -C <index_root> rev-parse HEAD`) against the **active
   worktree's HEAD** (`git -C <worktree> rev-parse HEAD`). If they differ,
   identify changed files using `git diff --name-status -z <index_root_HEAD>..<worktree_HEAD>` (parse `R` entries to add both the old and new path)
   and force direct reads for those files with `GRAPH-FALLBACK: index-diverged`,
   exactly as the `codebase-memory-mcp` path does. Serena's LSP view is live for
   the index root checkout, not for committed changes on other branches. Also run
   the local-edit fallback check against **both** the active worktree and the
   index root:
   - `git -C <worktree> diff --name-status -z HEAD` (parse `R` entries for both paths) + `git -C <worktree> ls-files -z --others --exclude-standard` (active worktree; NUL-delimited — without `-z`, non-ASCII/tab/newline filenames are quoted and misparsed)
   - `git -C <index_root> diff --name-status -z HEAD` (parse `R` entries for both paths) + `git -C <index_root> ls-files -z --others --exclude-standard` (index root; NUL-delimited)
   **Exclude setup-owned files from both index-root checks:** read
   `config.toml [serena] project_yml_path` (if present) and omit that exact path
   from the dirty-file check — it is managed by `setup.py` and must not trigger a
   fallback. **`read_only` enforcement must be in `launch-backend.py` before exec**
   — the PLAN skill check is too late (the server is already running; sessions
   that never invoke `codebase-context` can still call editing tools). The wrapper
   must read `project_yml_path` (baked at setup time) and verify `read_only: true`
   before `os.execvpe`. Because YAML's grammar for duplicate keys, anchors,
   aliases, explicit-key blocks, tagged keys, and Unicode-escaped keys cannot
   be fully verified by a scanner without a real YAML parser (and PyYAML is not
   stdlib), **`launch-backend.py` verifies `project.yml` by hash rather than
   by content scanning**: compute the SHA-256 of the current file and compare
   against `project_yml_hash` stored in `config.toml [serena]` at setup time
   (stdlib `hashlib`). If the hash differs or the file is absent, refuse startup
   with instructions to rerun `setup-codebase-context` (which re-validates with
   PyYAML and stores a new hash). Any modification — YAML aliases, anchors,
   explicit keys, Unicode escapes, or any other form — changes the bytes and
   therefore the hash, making this check bypass-resistant for all YAML syntax
   forms without requiring a parser in the wrapper.
   **Also check for a local override file:** Serena loads `project.yml` then
   overlays a sibling `project.local.yml` (same directory as `project_yml_path`);
   if that sibling file exists, compare its SHA-256 hash against the
   `project_local_yml_hash` stored in `config.toml [serena]` at setup time (use
   stdlib `hashlib` — no YAML parsing needed in the wrapper). If the file's hash
   **differs** from the stored hash, **refuse startup** with instructions to rerun
   `setup-codebase-context` (which will parse the changed file with PyYAML and
   either update the stored hash if the new content is safe, or abort if it
   introduces a `read_only` override). If the file is absent but was recorded at
   setup, refuse startup similarly — the local file state has changed since setup.
   If no hash was recorded at setup (file did not exist at setup time) and the
   file is now present, refuse startup and instruct the user to rerun setup. This
   hash-based check is bypass-resistant: any YAML form of an override (unicode-
   escaped keys, quoted keys, aliases) changes the file content and therefore its
   hash.
   **Also before proceeding to graph queries**, re-read `project_yml_path` and verify `read_only: true` as defense-
   in-depth; if drifted, emit a fatal error instructing the user to restore or
   rerun `setup-codebase-context`.
   If either check returns any other paths, fall back globally — use direct file
   reads for all paths and emit `GRAPH-FALLBACK: local-edit`. A partial fallback
   (direct reads only for dirty paths) is insufficient: Serena's live LSP graph
   can incorporate modified call sites into relationship results for
   otherwise-unchanged files, so any uncommitted edit makes the entire graph
   snapshot-inconsistent.

`normalise_remote.py` maps both `git@example.com:org/repo.git` and
`https://example.com/org/repo.git` to `example.com/org/repo`. Its SSH/HTTPS/`.git`
test cases are part of the pack's unit-test suite. **Drift prevention:** a
construction test (`tools/test-normalise-remote-parity.py` or equivalent)
asserts byte-equality between the canonical source in
`setup-codebase-context/scripts/normalise_remote.py` and the generated copy in
`codebase-context/scripts/normalise_remote.py`; CI blocks merge if they diverge.
The canonical is `setup-codebase-context/scripts/normalise_remote.py`; the
`codebase-context/scripts/` copy is generated by `tools/sync-normalise-remote.py`
and must not be hand-edited. **Makefile amendment required:** the current
`build-self` target only calls `agentbundle catalogue self-host`; it has no step
that executes `packs/*/tools` scripts. Implementing this RFC requires amending
the root `Makefile`'s `build-self` target to run pack-local pre-projection scripts
(i.e., `packs/codebase-context/tools/sync-normalise-remote.py`) before invoking
`agentbundle catalogue self-host`. This Makefile change is part of this RFC's
affected surface and must be included in its implementing PR. **Note:** the
`shared-libs/` projection machinery was retired in RFC-0023 and actively guarded
against; this pack uses an explicit pack-local sync step, not shared-libs
projection.

### OS-aware install (setup.py)

| OS | Arch | Default backend | Install method |
|---|---|---|---|
| macOS | arm64 | codebase-memory-mcp | Tier-1 manual prerequisite (see below) |
| macOS | x86_64 | codebase-memory-mcp | Tier-1 manual prerequisite |
| Linux | x86_64 | codebase-memory-mcp | Tier-1 manual prerequisite |
| Linux | arm64 | codebase-memory-mcp | Tier-1 manual prerequisite |
| Windows | amd64/arm64 | codebase-memory-mcp | Tier-1 manual prerequisite (PowerShell installer or Scoop/Winget/Chocolatey) |
| Any | any | serena | `uv tool install -p 3.13 serena-agent==<pinned-version>` (user-selected alternative) |

**Installation contract (Tier-1):** Per the repo's setup-skill dependency policy
(`guides/_shared/how-to/author-a-skill.md`), automated binary download is not
permitted. `setup.py` uses a declare → detect → fail-clean pattern:

- **`codebase-memory-mcp`**: `shutil.which("codebase-memory-mcp")`. If absent:
  emit the exact prerequisite install command and exit. If present: verify the
  **exact pinned version** (`codebase-memory-mcp --version`, compared against
  the version pinned in `pack.toml`) and fail clean if it does not match. A
  version-floor check (`>=`) is insufficient — tool names, HTTP transport
  flags, auth mechanism, and rebuild behavior are version-specific; an
  unverified newer release may break any of these silently. If an exact-match
  requirement is too strict for real-world operations, an explicit compatibility
  range (pinned minor, e.g. `>=1.2.0,<1.3.0`) must be tested and documented
  in `pack.toml` before widening the check. **Version revalidation at launch:**
  the setup-time version check is not sufficient — a package manager upgrade
  after setup can silently replace the binary at the stored path. `launch-backend.py`
  must persist the expected compatibility range (baked in at setup time alongside
  `CBM_ALLOWED_ROOT`) and run `codebase-memory-mcp --version` before `os.execvpe`;
  **the version probe must use the same scrubbed environment** that will be passed
  to `os.execvpe` (the minimal `env` dict, not the inherited process environment)
  — an uninspected binary run with the full inherited environment can read
  inherited tokens and secrets even when its version is subsequently rejected;
  if the version is outside the expected range, refuse startup with a message
  instructing the user to rerun `setup-codebase-context` to repin.
- **`serena` / uvx path**: The pack uses **persistent installation** via
  `uv tool install -p 3.13 serena-agent==<pinned>` rather than ephemeral `uv tool run` /
  `uvx`. Rationale: `uv tool list` reliably reports persistently installed
  tools; it does not report tools that were previously invoked via `uvx`
  (ephemeral `uv tool run`) but not installed. A persistent install also
  ensures a stable executable path across shell sessions.
  After install, `shutil.which("serena")` may still return `None` if uv's
  tool executable directory is not on `PATH` — `uv tool install` does not
  guarantee a PATH entry. The bin directory must be resolved via
  `subprocess.check_output(['uv', 'tool', 'dir', '--bin'], text=True).strip()`
  (the `--bin` flag returns the executable directory, not the tool-env root
  returned by bare `uv tool dir`). The serena executable is then
  `pathlib.Path(bin_dir) / ("serena.exe" if sys.platform == "win32" else "serena")`.
  If the resolved path does not exist as a file, treat this as an install
  failure: the `serena-agent` package may not have been installed correctly.
  Offer to re-run `uv tool install -p 3.13 serena-agent==<pinned>` and
  re-verify, rather than instructing the user to add a directory to PATH
  (adding the directory cannot make a non-existent executable appear).
  Detection flow: (a) check
  `shutil.which("uv")` — **`uv` must be present**, not just
  `uvx`: all subsequent operations (`uv tool list`, `uv tool install`) invoke
  the `uv` binary directly, and a system with `uvx` but no `uv` would fail
  at step (b) with `FileNotFoundError`. If absent: emit the `uv` install
  command and exit. Then (b) run `subprocess.check_output(['uv',
  'tool', 'list'], text=True)` in Python (not a POSIX pipeline) and check
  whether the output contains `serena` at the pinned version. Only if absent
  does setup enter the Tier-2 consent gate (ask the user before running
  `uv tool install -p 3.13 serena-agent==<pinned>`). After installation, re-verify by
  re-resolving the executable via `uv tool dir --bin` + platform-aware suffix
  (not `shutil.which("serena")` — uv tool bin dir is not guaranteed to be on
  PATH, so `which` returns None even after a successful install). The exact
  detection logic must be verified against the installed uv version
  (tracked in Open Questions: "Serena pinned version").
  **Version revalidation at launch:** identical contract as for
  `codebase-memory-mcp` — `launch-backend.py` persists the expected
  compatibility range at setup time and runs `serena --version` before
  `os.execvpe`; **the version probe uses the same scrubbed environment** as
  the `os.execvpe` call (not the inherited process environment);
  if the version is outside the expected range, refuse startup
  with a message instructing the user to rerun `setup-codebase-context` to
  repin. A `uv tool upgrade` after setup can silently replace the Serena
  binary at the stored path, violating the `read_only` contract; the
  pre-exec version check closes this window.

For `serena`, the pinned version is recorded in `SKILL.md` and `pack.toml`; the
exact version must be confirmed against backend docs before shipping (tracked in
Open Questions). The version pin ensures MCP tool names and flags do not drift
independently of the pack.

Windows installs use `codebase-memory-mcp` as the default backend
(`windows-amd64` and `windows-arm64` binaries confirmed in GitHub Releases).
The full three-tier freshness model applies on Windows, identical to macOS and
Linux. `serena` remains an explicit opt-in alternative on all platforms.

### Per-backend tool reference (SKILL.md, not here)

The two backends expose different MCP tool names; no unified API exists across
them. The `codebase-context` SKILL.md includes a per-backend quick-reference
table mapping canonical operations (discover symbols, expand neighbourhood,
estimate blast-radius, check freshness, trigger rebuild) to each backend's
actual verified tool names. Tool names must be pulled from each backend's own
documentation before authoring.

**Retrieval discipline (applies to both backends):**

- **Token-budget-aware requests:** SKILL.md must instruct the agent to
  estimate its remaining context budget before issuing graph queries and
  request only as many nodes as fit. A graph traversal that dumps all
  reachable edges into a full codebase context window is worse than a
  targeted grep — it crowds out the code the agent actually needs to edit.
  Prefer backends that support a `limit` or `top_k` parameter on retrieval
  calls.
- **Structural ranking over keyword ranking:** when ordering results,
  prefer structural centrality (call-graph depth, import depth, fanout) over
  keyword match score. A symbol that appears in many call sites and import
  chains is structurally more relevant to understanding a change's blast radius
  than a symbol that happens to share a name with the query term.
- **Provenance on results:** prefer backends that return source location
  and resolution method alongside each result (e.g., resolved via static
  analysis vs. heuristic match). When a backend does not expose provenance,
  treat its results as lower confidence and explicitly mark any downstream
  assertion as tentative. This prevents heuristic graph results from being
  cited as definitively correct in a PLAN.

**Serena read-only prerequisite [security — add to D4 backend verification]:**
Serena's MCP server exposes its full tool set by default, including
source-editing tools that can modify files. A session that bypasses the skill
scope gate — or is manipulated via prompt injection from graph content — could
use those tools to edit the dedicated main checkout. Setup must either (a)
configure serena with a read-only mode (if supported at the pinned version) or
(b) verify that only the five canonical read-only operations are exposed. If
neither is available at the pinned version, serena cannot be registered without
a filtering proxy; add "serena read-only/tool-allowlist confirmation" to the D4
backend viability verification for serena.

### Three-tier freshness (backend-conditional)

**Tier 1 — Real-time (both backends).**
`codebase-memory-mcp` runs an internal file watcher that fires when files
change in the index root. The primary driver is `git pull` on the index root
(which changes many files, triggering incremental re-indexing). Editor saves
to the index root also trigger it, but the index root is not a development
worktree and this is expected to be infrequent. `serena` reads live LSP servers
directly from whatever is on disk in the index root; its "freshness" is
entirely determined by how current that checkout is.

**Tier 2 — Staleness marker (codebase-memory-mcp only, best-effort).**
The pure-shell sentinel block (hook text is generated inline by `setup.py`;
there is no separate `post-merge.py` helper shipped as an artifact) is
chained into the resolved git hooks directory
for the index root's repo. `setup.py` resolves `git -C <index_root> config --path --get core.hooksPath`
first — the `--path` flag applies Git's own pathname expansion rules (expanding
`~`, `%(prefix)/...`, and other Git pathname syntax) before returning the value.
However, `--path` does **not** resolve relative values to absolute paths — a
value like `.husky/_` is returned as-is. `setup.py` must therefore apply a
second step: if the expanded path is relative, resolve it against the index
root's working-tree directory (`git -C <index_root> rev-parse --show-toplevel`),
not the process CWD. Resolving from CWD would silently target the wrong hook
tree when setup is invoked from a sibling worktree. Using plain `git config`
without `--path` returns the raw value and requires a separate expansion step
that cannot handle all Git pathname forms. If set (e.g. by husky or a managed
toolchain), the fully resolved absolute path is used. Otherwise it falls back to
`os.path.join(<index_root>, git -C <index_root> rev-parse --git-common-dir) + "/hooks"`.
The `--git-common-dir` output is often the relative string `.git`; it **must**
be joined to `<index_root>` (not CWD) before use. `setup.py` uses
`subprocess.check_output(['git', '-C', index_root, 'rev-parse', '--git-common-dir'])`
and resolves with `os.path.join(index_root, output.strip())`.
When using the common-dir fallback, this directory is shared across all linked
worktrees, so the hook fires on merge and rebase operations in any worktree —
not only the index root. When `core.hooksPath` is set, the sharing behavior
depends on whether it points at a worktree-local or shared path. Spurious marker
writes (from unrelated worktrees) cause extra Tier 3 freshness checks; this is
harmless since Tier 3 is idempotent and the rebuild tool is expected to be a
no-op when the index is already current.

Sentinel markers delimit the pack's contribution. `setup.py` and `uninstall.py`
add and remove the sentinel block from all three hook files (`post-merge`,
`post-rewrite`, `post-checkout`). The `post-merge` and `post-rewrite` sentinels
are identical (plain `unset` form). The `post-checkout` sentinel differs: it
captures the preceding exit status and installs an EXIT trap to re-emit it when
the script exits (preserving the hook chain's exit status).
`uninstall.py` removes the full variant (including the `trap` line) from
`post-checkout`.
(Hook sentinel text is generated inline by `setup.py`; there is no shipped
`post-merge.py` artifact.)

```sh
# >>> codebase-context v1 >>>
_cc_gd=$(git rev-parse --git-dir 2>/dev/null)
case "$_cc_gd" in
  /*) ;;                                       # POSIX absolute
  [A-Za-z]:/*) ;;                             # Git-for-Windows drive-letter (C:/...)
  ?*) _cc_gd="$(git rev-parse --show-toplevel 2>/dev/null)/$_cc_gd" ;;
esac
if [ "$_cc_gd" = '/absolute/resolved/git-dir-from-index-root' ]; then
  touch '/absolute/resolved/path/to/.agentbundle/codebase-context/stale' || true
fi
unset _cc_gd
# <<< codebase-context v1 <<<
```

The baked-in guard value (`/absolute/resolved/git-dir-from-index-root`) is the
result of `git -C <index_root> rev-parse --git-dir` resolved to an absolute
path at setup time. **Windows normalization:** on Git for Windows, `git
rev-parse --git-dir` emits forward-slash drive-letter paths (`C:/...`). The
guard value must be baked in the same format — `setup.py` must call `git rev-parse
--git-dir` via subprocess (not `os.path.realpath`) and normalize the baked
value to match what the hook will receive at runtime. If `os.path.realpath` is
used at setup time (Windows backslash style), the guard comparison will never
match. `--git-dir` returns the **per-worktree** git metadata
directory — `.git` (primary checkout) or `.git/worktrees/<name>` (linked
worktree). This is worktree-specific: sibling feature-branch worktrees that
share the same common directory have DIFFERENT `--git-dir` values and do NOT
match the guard. Only hook events that fire in the exact index-root worktree
trigger staleness. All baked paths (guard and `touch` target) are
single-quoted in the generated sentinel to prevent shell expansion of any
`$`, backtick, or other metacharacter that may appear in the path.

`setup.py` resolves the baked guard value:
```python
gd = subprocess.check_output(
    ['git', '-C', index_root, 'rev-parse', '--git-dir'], text=True
).strip()
# git rev-parse already produces the canonical slash-format path (C:/... on
# Git-for-Windows). Only prepend the toplevel for relative paths; use
# git's output directly — do NOT pass through os.path.realpath (which
# produces OS backslashes on Windows and would mismatch the hook's git output).
if not gd.startswith('/') and not (len(gd) >= 2 and gd[1] == ':'):
    top = subprocess.check_output(
        ['git', '-C', index_root, 'rev-parse', '--show-toplevel'], text=True
    ).strip()
    gd = top + '/' + gd
baked_guard = shlex.quote(gd)           # git's canonical slash format; matches hook's rev-parse output
stale_path  = shlex.quote(os.path.realpath(stale_marker_path).replace('\\', '/'))
```

The worktree-specific guard means merges and rebases in sibling worktrees
(feature branches) do NOT mark the index stale — only operations in the index
root itself do. Since the index root is the designated "regularly-pulled main
checkout," this is the intended behavior: only pulls into the index root
invalidate its graph. The PLAN-time staleness check (Tier 3) compensates for
any staleness not captured by the hook.

The repo-identity guard ensures the sentinel only writes the stale marker when
the hook fires inside the index-root worktree — not for sibling worktrees or
unrelated repositories sharing the same `core.hooksPath`. Before writing any hook,
`setup.py` also checks whether `core.hooksPath` is set at local/worktree scope
(`git config --local core.hooksPath`) or inherited from global/system config.
If inherited from global/system config, `setup.py` warns the user that the
sentinel will write to a shared hooks directory and requires explicit
confirmation before proceeding (the repo-identity guard in the sentinel still
provides the runtime guard, but the user should be aware of the scope).

The hook body has no `exit` statement for `post-merge` and `post-rewrite` —
git ignores exit codes for those two hooks, so there is no status to preserve
and omitting `exit` keeps any blocks appended after the sentinel reachable.

`post-checkout` is different: git propagates its exit code as the exit code of
`git checkout` / `git switch`. When an existing `post-checkout` hook ends with
a failing command but no explicit `exit`, appending this sentinel replaces the
effective exit status with the `unset` call's success, masking the original
failure. To preserve the exit code, `setup.py` wraps the `post-checkout`
sentinel in a status-preserving bracket:

```sh
# >>> codebase-context v1 >>>
_cc_prev_exit=$?
trap "_cc_trap_exit=\$?; test \$_cc_trap_exit -eq 0 && exit $_cc_prev_exit || exit \$_cc_trap_exit" 0
_cc_gd=$(git rev-parse --git-dir 2>/dev/null)
case "$_cc_gd" in
  /*) ;;                                       # POSIX absolute
  [A-Za-z]:/*) ;;                             # Git-for-Windows drive-letter (C:/...)
  ?*) _cc_gd="$(git rev-parse --show-toplevel 2>/dev/null)/$_cc_gd" ;;
esac
if [ "$_cc_gd" = '/absolute/resolved/git-dir-from-index-root' ]; then
  touch '/absolute/resolved/path/to/.agentbundle/codebase-context/stale' || true
fi
unset _cc_gd _cc_prev_exit
# <<< codebase-context v1 <<<
```

The EXIT trap fires when the script exits. `_cc_trap_exit=$?` captures the
script's final exit status as the very first action in the trap body, before
any other command can clobber `$?` (notably `test` itself sets `$?` to 1 on
failure, so a non-zero status like 7 would become 1 if read after `test`).
When `$_cc_trap_exit` is zero (all later blocks succeeded), the trap
re-emits the captured pre-sentinel value `$_cc_prev_exit`, preserving
`git checkout`'s exit code. When non-zero (a later block failed), the trap
re-emits that exact failure code so it is not masked or rounded to 1. Unlike a bare `exit` inside the sentinel, the EXIT trap does
not terminate the script immediately — subsequent hook blocks appended by
other managers remain reachable. If a later block sets its own `trap ... EXIT`,
it overrides this one (LIFO semantics); the last setter controls the final
exit status, which is the correct behavior when multiple blocks each want to
preserve some notion of "prior status." `unset _cc_gd _cc_prev_exit` runs
before the trap fires; since the trap embeds `$_cc_prev_exit` literally at
set time, unsetting it does not affect the baked exit code in the trap.

**`set -e` safety.** `touch ... || true` guards both sentinel forms (plain and
EXIT-trap). If an existing hook enables `set -e` (exit-on-error), a failed
`touch` — for example when the state directory has been removed — would
otherwise terminate `post-checkout` with a nonzero exit code. The `|| true`
fallback ensures the stale marker write is best-effort: its failure is
silently swallowed and the hook exits cleanly. `setup.py` should also scan
the existing hook for `set -e` and warn the user if found, so they are aware
that any of their hook blocks may abort on first error.

**Preflight: existing EXIT trap guard.** Before appending the sentinel,
`setup.py` must scan the existing `post-checkout` body for any
`trap ... EXIT` or `trap ... 0` statement — POSIX signal `0` is the
portable equivalent of `EXIT` and must be treated identically. Shell
traps do NOT compose — our trap would silently replace any earlier EXIT
handler registered by a prior hook block. If either form is found,
`setup.py` must refuse automatic modification and print the sentinel
block verbatim. The instructions must
tell the user to merge BOTH trap bodies into a single `trap ... EXIT`
statement — not to position our block after the existing one, because
every `trap ... EXIT` statement replaces the prior handler outright regardless
of ordering; two separate trap statements cannot coexist in the same script.

For `post-merge` and `post-rewrite`, the sentinel retains the plain `unset`
form with no exit-status handling (git ignores those hooks' exit codes). `touch` itself
eliminates interpreter fragility: `sys.executable`
(considered in an earlier iteration) becomes invalid if setup ran under a
virtualenv or pyenv installation that is later deleted, causing `git checkout`
to exit 127. `python3` is absent in some GUI git clients. `touch` requires no
interpreter, works in every POSIX environment, and is the simplest possible
stale-marker writer. `setup.py` writes the stale path (shell-quoted via
`shlex.quote()`) as a literal string into the sentinel block at setup time.
No separate helper script is needed or shipped for this path computation.

Before writing any hook, `setup.py` canonicalizes the hooks directory path via
`os.path.realpath()` before any containment check. This resolves symlinks in
the path and its ancestors — a `core.hooksPath` that points to a symlink
chain ending inside a tracked directory would otherwise pass a lexical
containment test while `os.lstat` on the final hook file reports a regular
file, bypassing the refusal. Canonicalization must happen **before** the
containment check is evaluated. After canonicalization, `setup.py` checks
whether the resolved hooks directory is inside the git **working tree**
(i.e. the canonicalized hooks path is a descendant of
`os.path.realpath(git -C <index_root> rev-parse --show-toplevel)`) **but not
inside the git metadata directory**.
For the metadata directory: run `git -C <index_root> rev-parse --git-common-dir`;
if the output is relative (e.g. `.git`), join it to `<index_root>` before
calling `os.path.realpath()` — passing a bare relative path to `realpath()`
resolves against the process CWD, not the index root, and will misclassify
`<index_root>/.git/hooks` as a tracked hooks directory when setup runs from
a sibling worktree.
Canonicalized form: `os.path.realpath(os.path.join(<index_root>, <git-common-dir>))`
if not already absolute.
The standard `<index_root>/.git/hooks` path is lexically inside `--show-toplevel`
but it is inside `--git-common-dir`, so it passes this check automatically.
Only a hooks path that is both inside `--show-toplevel` AND outside
`--git-common-dir` (i.e. a tracked directory like `.husky/`) triggers the
refusal. **For tracked hooks directories, Tier 2 is skipped entirely** —
`setup.py` must NOT print the sentinel block for manual integration. The
sentinel block contains user-specific absolute paths (the resolved
`pack_dir` path); committing it violates the repository privacy rule against
personal paths in tracked files, and leaving it uncommitted makes the index
root permanently dirty, which blocks `git pull --rebase` (the only freshness
mechanism Serena has). `setup.py` prints a notice that Tier 2 (post-merge git
hook) is unavailable for this repository configuration, and that only Tier 1
(file watcher) and Tier 3 (graph_status at PLAN startup) are active.

If the hooks directory is outside the working tree, or is the standard git
metadata dir (the common case, including the `--git-common-dir/hooks` fallback),
`setup.py` proceeds:

The resolved `pack_dir("codebase-context")` absolute path is shell-quoted via
`shlex.quote()` before interpolation into the sentinel block — paths with
spaces or shell metacharacters are handled safely.

1. If the hook file does not exist: create it with a `#!/bin/sh` shebang and
   `chmod +x`, then append the sentinel block; **record `hook_<name>_created
   = true` in `config.toml [hooks]`** so teardown knows to delete the file
   (not just the sentinel) if no other content was added post-setup.
2. If the hook file exists: use `os.lstat` (not `os.stat`) to check whether
   the file is a symlink. If it is a symlink, **resolve the target with
   `os.path.realpath()`** and apply the same tracked-directory test to the
   resolved target: if the target is inside `--show-toplevel` AND outside
   `--git-common-dir`, **skip Tier 2 entirely** — printing the sentinel for
   a target in a tracked directory would either commit user-specific absolute
   paths (privacy violation) or leave the working tree permanently dirty. Do
   NOT fall through to printing the sentinel or adding to `[hooks].manual` for
   this case. If the symlink target resolves inside `--git-common-dir` (e.g. a target
   at `<checkout>/.git/hooks/something`), refuse automatic modification and
   print the sentinel block for manual integration — this hook layout is
   unusual and its implications are unclear; add to `[hooks].manual` so
   uninstall prints the removal instructions. If the symlink target is
   outside `--show-toplevel` entirely, refuse automatic modification of the
   symlink itself (do not follow it) and print the sentinel block for manual
   integration. Otherwise (not a symlink) read its shebang. If POSIX shell (`#!/bin/sh`, `#!/bin/bash`, `#!/usr/bin/env bash`,
   `#!/usr/bin/env sh`):
   - Check for the executable bit; if missing, apply `chmod +x` (after user
     confirmation that this is intentional) or refuse and print for manual
     integration. **Before applying `chmod +x`, journal the original mode**
     (e.g. `hook_<name>_prior_mode = 0o644`) in the setup transaction journal
     and in `config.toml [hooks]`. On rollback and on uninstall, restore the
     original mode via `os.chmod(hook_path, prior_mode)` after removing the
     sentinel block — the hook was inert before setup activated it, and
     teardown must not leave it active. Add this case to mock-install tests.
   - Scan for unconditional `exit` or `exec` statements before EOF — if found,
     the appended block would be unreachable; refuse and print for manual
     integration.
   - Otherwise: construct the complete new hook content in memory (existing
     content + exactly one blank line as separator + new sentinel block — strip
     any trailing newlines from the existing content, then append `"\n\n"` before
     the sentinel so the result is always one blank line, never zero or two),
     write it to a temp file in the same
     directory, set the same executable permission, then `os.replace(temp,
     hook_path)` to atomically replace the hook (`os.replace` supersedes the
     destination on all platforms including Windows; `os.rename` fails on
     Windows when the destination exists). In-place append or truncate is
     forbidden — a concurrent worktree executing the hook during a partial
     write reads a corrupt or truncated script. Git does not hold a file lock
     on hooks during execution.
3. If the shebang is non-shell: refuse and print for manual integration.

Mock-install tests cover: absent-hook creation, shell-shebang append,
non-shell-shebang refusal, terminal-exit/exec refusal, and tracked-hooks-dir
refusal.

`setup.py` checks for sentinels before appending (idempotent across all three
hook files). **Sentinel upgrade detection:** the generated sentinel text is
versioned via the opening delimiter: `# >>> codebase-context <version> >>>`
(e.g. `# >>> codebase-context v1 >>>`). A `__sentinel_version__` constant in
`setup.py` holds the current version string. Detection: scan the hook file for
a line matching `# >>> codebase-context ` (prefix match); extract the version
token between `codebase-context ` and ` >>>`; if it differs from
`__sentinel_version__`, `setup.py` replaces the entire sentinel block (from
`# >>> codebase-context ` to the matching `# <<< codebase-context`) atomically
(write-to-tmp + rename) with the new sentinel body — no user confirmation
required for a same-root sentinel refresh, since the generated text is
deterministic. The removal contract uses the same prefix match (not an exact
string) so any versioned sentinel is correctly found and removed. This ensures
hook fixes and security improvements (e.g. the `|| true` guard) reach existing
installations.

When overwriting an existing registration that differs in **either
index root or backend**, `setup.py` confirms the overwrite with the user first.
After confirmation, the operation is staged before destructive steps.

**Session quiescence is required for any setup (initial or rerun) that stops, purges, or restarts
the CBM daemon** — not only when the root or backend changes. A same-root,
same-backend rerun that modifies exclusions also triggers the canary phase
(daemon stop → purge → restart). Because the current Claude session holds the
MCP registration and has an active subprocess, running daemon work in-session
creates client/graph-lock races. The quiescence gate must therefore fire
whenever any canary or daemon work is about to begin, regardless of whether
the root or backend changed.
**Serena setup does not require session quiescence on a fresh install** — no
daemon is started or stopped, and no canary phase runs. The `config.toml` write
(step (c)) is protected by `config.lock`. **Exception: a rerun switching from
`codebase-memory-mcp` to serena requires quiescence and external staging** — the
old CBM daemon must be stopped and the old-graph purge offered, which is CBM
daemon work that triggers the § Quiescence and session staging gate above exactly as any
CBM daemon stop does.

1. Write new config and scripts to temporary locations.
2. **Session quiescence — stage as external command.** The canary phase
   stops, purges, and restarts the daemon regardless of whether the backend
   changed. Even for an initial install, the shared CBM daemon may already be
   running for another project; stopping or purging it in-session creates
   client/graph-lock races with existing users.
   `setup-codebase-context` cannot execute the overwrite in-session.
   **For a rerun** (existing `config.toml`): stage
   `<interpreter> <setup-codebase-context-skill-dir>/scripts/setup.py --update`
   (where `<interpreter>` is the recorded `interpreter_path` from `config.toml`).
   **Before emitting this command**, probe `interpreter_path` — verify it exists
   and passes the version check (`>= 3.11`); if stale or removed, apply the same
   durable-interpreter fallback probe used at initial setup and substitute the
   found candidate, printing a warning that the registered interpreter was stale.
   Without this fallback, a removed interpreter causes the staged command to fail
   before `setup.py` can run, and setup cannot repair its own registration.
   **For an initial install** (no `config.toml` yet): stage
   `<probed_interpreter> <setup-codebase-context-skill-dir>/scripts/setup.py --install`
   (where `<probed_interpreter>` is the interpreter found during the
   durable-interpreter probe described in the Python interpreter selection section).
   Then explain that all Claude sessions must be closed before running the staged
   command, and exit. On backend switch, also note that the old backend's daemon may hold
   graph file locks.
3. Remove old sentinel blocks from the previous hooks directory.
3b. **If the index root changed or the backend changed**, reverse old
    backend-owned files before promotion: read the stored `[exclusions]
    cbmignore_path` and `cbmignore_ownership` from the old `config.toml`
    journal snapshot. **Before deleting or stripping:** inspect the file for
    user-added content beyond what setup wrote — for `.cbmignore`, content
    outside the setup-sentinel-delimited block; for `.serena/project.yml`,
    keys other than `read_only:`. If user-added content is present, **surface
    a path-specific confirmation** naming the file, the user-added content, and
    the consequence of proceeding (those additions will be lost) — do not
    silently discard. If the user declines, abort the rerun with a remediation
    message (manually remove or migrate the content, then rerun). Only if no
    user content is found (or the user confirms): **before reversing**, journal
    the pre-reversal state — record `old_cbmignore_content` (**complete file
    contents** if `"created"` — the user may have added patterns after setup, and
    journaling only the sentinel block would lose those patterns on rollback;
    just the sentinel block if `"merged"`, since the user's pre-existing content
    is unmodified) and equivalent `old_project_yml_content` for Serena
    (complete file if `"created"`; just the `read_only:` line if `"merged"`).
    **For `.cbmignore` only, when this reversal is part of a root or backend
    change** (a purge offer follows at step 6): do NOT reverse `.cbmignore`
    immediately — instead, journal the pre-reversal state for rollback but
    defer reversal to AFTER step 6; if step 6's purge succeeds, reverse it
    then; if the purge is declined or fails, write `graph-purge-pending` and
    RETAIN the `.cbmignore` sentinel block. For cosmetic-only reconfiguration
    (neither root nor backend changes): reverse `.cbmignore` immediately (delete if
    `"created"`, remove sentinel block if `"merged"`). Apply the same
    inspection-and-journal-before-reverse to Serena-to-anything or
    anything-to-Serena transitions on `project_yml_path`/`project_yml_ownership`
    (Serena's `project.yml` is safe to reverse immediately — it is not an
    exclusion guard for a live graph).
    **Failure cleanup after step 3b** must restore old files from these journal
    entries — if promotion doesn't complete, the MCP registration may be restored
    to the old one, which depends on the old exclusion/read-only guards being in
    place. This ensures uninstall later finds only the new setup's artifacts, and
    that a former Serena checkout does not remain unintentionally read-only.
4. Atomically rename/promote staged files into their final locations.
5. Chain sentinels into the new hooks directory.
6. **Old graph purge offer (index root or backend change — runs AFTER promotion):**
   read the `config.toml [index] graph_path` recorded in the journal BEFORE
   promotion replaced it. The stored path is a hint only; require daemon
   verification (uninstall Steps 1–3) to obtain the live-confirmed path before
   any scripted deletion — the same exact-path safeguards and user consent prompt
   as the full uninstall flow. The previous graph may contain previously indexed
   secrets; a later uninstall will only know about the new `graph_path`. If the
   user declines, print the old path and a manual-removal reminder; write a
   cleanup tombstone with `reason = "declined"`. If the user accepts but
   verification or deletion fails, print the error, display a manual-removal
   reminder, and write a cleanup tombstone with `reason = "failed"`. **For
   any deferred or failed purge outcome** (decline or failure): write the
   cleanup tombstone at `pack_dir("codebase-context")/graph-purge-pending`
   (mode `0600`, recording the old path and the reason) so that a future
   uninstall treats this as a deferred purge and retains `.cbmignore` exclusions
   until the graph is manually removed; also write `codebase-context-purge-locator`
   to `user_state_path().parent` so the tombstone is discoverable after pack
   removal. **Before deleting the transaction journal** (which holds the old
   `cbmignore_path`, `cbmignore_ownership`, and sentinel markers): extract
   that metadata and write `cbmignore-cleanup.json` (mode `0600`) to
   `pack_dir("codebase-context")` recording `cbmignore_path`,
   `cbmignore_ownership`, exact sentinel start and end markers, the absolute
   path to `cbmignore-cleanup.json` itself, and the absolute path to
   `graph-purge-pending`; also write `codebase-context-cbmignore-pending`
   (mode `0600`) to `user_state_path().parent` containing the absolute path
   to `cbmignore-cleanup.json`. A later manual purge via
   `codebase-context-cleanup.py` requires this durable record to locate the
   old `.cbmignore` and remove its sentinel block. This step is skipped when neither the index
   root nor the backend changes.
   **This step runs after promotion so that a purge failure leaves the new
   installation intact — journal rollback for steps 1–5 never needs to restore
   a graph, because the graph has not yet been touched.**

This ordering ensures that if step 1 fails, the old registration remains intact.
If step 3 or 4 fails, the new state is in temporary locations and can be
cleaned up; the old registration may already be partially removed, which is
surfaced to the user as a "partially updated — re-run setup to complete" error.
A full rollback to pre-confirmation state is not guaranteed for hooks removal
(filesystem renames are not transactional), but at minimum the error condition
is explicit rather than silent. Removing old hooks on a backend switch (same root, different
backend) must still locate the *previous* hooks directory from stored config
rather than deriving it from the new backend — these may resolve to different
paths if the backends use different hook-path strategies. If the user declines,
setup aborts and the old registration (including its hooks) is left intact.
`uninstall.py` removes the sentinel blocks from all three hooks and the
copied scripts. **Manual integration tracking:** when setup refuses to
modify a hook (symlink, non-shell shebang, or existing EXIT trap — NOT
tracked-hooks directory) and instructs the user to integrate the sentinel
manually, setup records the hook name in `config.toml` under
`[hooks] manual = ["post-checkout"]` (or whichever hooks were declined).
On uninstall, hooks listed in `manual` are not automatically modified;
instead, `uninstall.py` prints the sentinel block for the user to remove
manually — mirroring the install-time refusal behavior. Hooks not in
`manual` are cleaned up unconditionally by `uninstall.py`.
**Tracked-hooks directories do not enter `[hooks].manual` and never emit
the sentinel for manual integration.** For those configurations, Tier 2
is skipped entirely (no sentinel, no `manual` record): the sentinel
embeds user-specific absolute paths that must not be committed and cannot
be left uncommitted without dirtying the tree. `uninstall.py` skips hooks
cleanup for hooks-path-inside-working-tree configurations (same detection
logic as setup: inside `--show-toplevel` AND outside `--git-common-dir`).

The hook sentinel writes `pack_dir("codebase-context")/stale` via the POSIX
shell `touch` command. Concurrent fires from multiple worktrees racing on the
same file are safe — any race winner produces a valid marker, and `touch` on an
existing file simply updates its mtime; no atomic write-to-tmp+rename or nonce
is required for a presence-only stale signal. The hook does not call the daemon
— MCP tools are accessed only through spawned subprocess sessions, not from
git hooks directly.

The git hook uses pure shell `touch`; hook text generation is inlined into
`setup.py` and there is no separate `post-merge.py` artifact to ship or copy.

Note: `post-checkout` fires on every branch switch across all linked worktrees,
which is a significantly higher trigger frequency than merge/rebase. Each
spurious trigger causes a Tier 3 freshness check; this is expected harmless
because the `codebase-memory-mcp` rebuild tool is a no-op when the index is
already current (this assumption is tracked in Open Questions).

**Tier 3 — Explicit check at PLAN (both backends, primary gate).**
After the scope-gate, identity check, and liveness probe pass:

- `codebase-memory-mcp`: check for BOTH `stale` AND any `stale.claimed.<pid>`
  files before starting work — **using a glob that matches only PID marker
  names**, not `.ts` sidecar files. The glob pattern is `stale.claimed.[0-9]*`
  with a filter that excludes names containing a dot after the PID (i.e.
  `stale.claimed.<pid>.ts` is skipped; only `stale.claimed.<pid>` is a live
  or orphaned claim). A concurrent session holds the claimed file while
  rebuilding. Decision table:

  **Freshness-aware claim (requires backend atomic index replacement):** The
  claim rename (`stale` → `stale.claimed.<pid>`) is always the FIRST action
  when a `stale` marker is present — never a pre-claim mtime comparison.
  Claiming first prevents the race where a hook writes a fresh `stale` between
  the mtime comparison and the delete, which would silently discard the new
  signal. After claiming, a freshness skip is optionally available: if the
  backend is **confirmed to use atomic index replacement** (write to a temp
  path, then rename to the index path — so the index mtime updates only after
  a successful complete rebuild), compare the **original stale-event time**
  against the index mtime; if the index is newer than the stale event, apply
  **project-specific proof** before deleting the claim: (a) read
  `last_rebuild_timestamp_ns` from `config.toml [index]` and verify it is
  **greater than the stale event time** — in a shared SQLite store, another
  project's rebuild updates the database mtime but does NOT update this
  project's `last_rebuild_timestamp_ns`; `config.toml` mtime alone is
  insufficient because launcher-version refreshes, normalizer migrations, and
  other non-rebuild writes bump `config.toml`'s mtime without rebuilding the
  project index; `last_rebuild_timestamp_ns` is written ONLY by
  `rebuild_coordinator.py` after a successful full rebuild publication, making
  it an unambiguous project-specific rebuild signal; if the field is absent or
  `<= stale_event_ns`, this project has not been rebuilt since the signal and
  the claim must be rebuilt; (b) read `indexed_commit` from `config.toml` and
  verify it matches the current HEAD of the index root
  (`git -C <index_root> rev-parse HEAD`). If both checks pass, the index is
  current for this project — delete the claim and proceed. If either fails,
  the claim must be rebuilt, not skipped. Skipping without this check would
  silently clear the stale marker without confirming the configured project is
  indexed at HEAD. **The stale-event time must be read from the claimed
  inode AFTER renaming but BEFORE applying the lease `os.utime()`** — reading
  before the rename is a race: if a hook fires between a pre-rename stat and
  the rename, the claim captures the newer marker but would embed the old
  timestamp; if the index mtime lies between those events, the freshness skip
  incorrectly deletes the claim and silently loses the new signal. Correct
  sequence:

  1. `os.rename(stale_path, 'stale.claimed.<pid>')` — claim first (atomic)
  2. `stale_event_ns = os.stat('stale.claimed.<pid>').st_mtime_ns` — read
     the claimed inode's actual event time
  3. Write `stale_event_ns` (ASCII decimal) to `stale.claimed.<pid>.ts` via
     atomic write-to-tmp + rename — sidecar persists the event time for
     orphan detection across process restarts
  4. `os.utime('stale.claimed.<pid>', None)` — set lease time to NOW

  The claimed file's mtime (step 4) is used only for **lease expiry**; the
  `.ts` sidecar value is used only for **freshness comparison**. Orphan
  detection reads `stale_event_ns` from the `.ts` sidecar; if the sidecar is
  absent (crash between steps 1 and 3), treat as orphan with
  `stale_event_ns = None` (unknown — disable freshness skip; rebuild
  unconditionally). Using `0` is wrong: with atomic replacement enabled the
  freshness check is `index_mtime > stale_event_ns`, so `0` makes every real
  index appear newer and silently skips the rebuild. On orphan reclaim, copy the orphan's
  `.ts` sidecar to the new claim's sidecar path before applying the new
  lease utime — preserving the original event time. This skip is
  **disabled until atomic replacement is verified** as part of D4 backend
  prerequisites: if the backend writes the index in-place, its mtime advances
  on the first write (not completion), and a PLAN mid-rebuild would discard
  the retry signal and query a partial index. When unconfirmed, claim and
  rebuild unconditionally (no freshness skip).

  | State seen | Meaning | Action |
  |---|---|---|
  | No marker | graph is current | proceed |
  | `stale` only | rebuild needed (index predates marker) | claim it: rename to `stale.claimed.<pid>` |
  | `stale.claimed.*` only | another session is rebuilding OR session crashed | orphan-check (see below); if live, only query if the backend is **confirmed to provide snapshot-isolated reads** (blocking prerequisite: "Snapshot-isolated reads" — see Open Questions); if unconfirmed, fall back to direct file reads for this PLAN; if orphaned, reclaim and rebuild |
  | both `stale` + `stale.claimed.*` | hook fired during active rebuild OR rebuild crashed and hook re-fired | apply lease/orphan check to the claimed file (same logic as row above); if live: fall back to direct file reads (snapshot-isolation unconfirmed); stale marker stays for next PLAN; if orphaned: remove claimed file, keep stale marker, process as "stale only" (claim and rebuild) |

  **Orphan recovery via bounded lease, not PID check**: PID-only orphan
  detection is unreliable because the operating system recycles PIDs — a
  newly started unrelated process may hold a PID that previously belonged to
  a crashed rebuild session, making `os.kill(pid, 0)` return success
  indefinitely. The claimed file therefore embeds a **claim timestamp** using
  `os.utime()` set **at the moment of claiming** (not inherited from the `stale`
  marker's mtime — the stale marker may be arbitrarily old and would cause an
  active claim to appear immediately expired). A claimed file whose mtime is
  older than a configured lease timeout (default: 5 minutes, covering the
  maximum expected rebuild duration from Open Questions) is treated as orphaned
  regardless of whether the PID is still alive. Lease timeout is configurable in
  `config.toml` under `[hooks] claim_timeout_seconds`. On orphan detection,
  acquire the **config lock** (`<stable-state-dir>/config.lock` — the same dedicated lock file used for publication), then use a single atomic `os.replace(orphaned_claim_path,
  own_claim_path)` to take ownership, then release the config lock —
  `own_claim_path` is `stale.claimed.<new_pid>`; before applying the new lease
  `os.utime()`, copy the orphan's `.ts` sidecar
  (`stale.claimed.<old_pid>.ts`) to `stale.claimed.<new_pid>.ts` atomically
  (write-to-tmp + rename), preserving the original stale-event time for the
  freshness comparison; then delete `stale.claimed.<old_pid>.ts`
  (`Path.unlink(missing_ok=True)` — a concurrent uninstall may have removed it).
  If the sidecar is absent, record `stale_event_ns = None`
  (unknown — disable freshness skip; rebuild unconditionally).
  `os.replace` is cross-platform: on Linux/macOS it is atomic and replaces
  the target if it already exists; on Windows it uses `MoveFileExW` with
  `MOVEFILE_REPLACE_EXISTING`, which also replaces atomically but raises
  `PermissionError` if the destination is locked by another process (handle
  this by treating the error as ownership loss — fall back to the
  "live claimed" branch). Do not use `os.rename` for this operation: on
  Windows, `os.rename` raises `FileExistsError` when the destination already
  exists, and a recycled PID can produce exactly that collision here.
  The session that completes the replace owns the rebuild.
  Do **not** first rename the orphan to `stale` then create a new claim in two
  steps: two sessions doing this concurrently both succeed at creating their own
  claim files without ever contending on a shared resource, producing duplicate
  rebuilds. Immediately after a successful rename, set the claim mtime to now
  via `os.utime()`. **Treat `FileNotFoundError` from `os.utime()` as ownership
  loss** — another session renamed the claim away between your rename and your
  utime; fall back to the "live claimed" branch rather than proceeding as owner.
  Sessions that fail the initial rename (`FileNotFoundError` — orphan already
  taken by a concurrent session) also fall back to the "live claimed" branch.

  **Residual race — concurrent rebuild window:** because `rename` preserves the
  original mtime, a second session can read the freshly claimed file as expired
  before the first session's `os.utime()` runs. If the second session then
  renames the claim and the first session's subsequent `utime` succeeds (the
  rename happened after `utime`), both sessions believe they own the rebuild.
  The `FileNotFoundError` guard only detects ownership loss when the competing
  rename happens *before* `utime`. When it happens after, both sessions rebuild
  concurrently. This window cannot be closed with POSIX filesystem operations
  alone without an actual locking primitive (e.g. `fcntl.flock`). **This is
  accepted because `codebase-memory-mcp`'s rebuild is CONFIRMED idempotent**
  — `project_lock.c` serializes concurrent rebuilds on the same project
  (see D1 and the "Backend rebuild concurrency safety" Recommended-defaults
  entry), so two sessions cannot run parallel rebuilds. If a future backend
  version removes this serialization guarantee, the orphan-recovery path would
  need `fcntl.flock` or equivalent instead of the rename protocol. **Regardless:** before
  acquiring the config lock a session may do a **preliminary fast-fail claim
  check** — re-read the claim file and confirm its own PID still matches; if
  absent or bearing a different PID, discard the rebuild result and exit. This
  is an optimization only. The **authoritative claim check must also run inside
  the config lock** (see below) — a gap between a pre-lock check and lock
  acquisition allows another session to transfer ownership in that window,
  enabling the displaced session to publish `indexed_commit` under a revoked
  claim.

  The lease timeout is set conservatively so a
  legitimately slow rebuild is not mistaken for an orphan; the actual
  rebuild-duration OQ should inform the default before shipping.

  Before starting the rebuild, record the current HEAD of the index root
  (`git -C <index_root> rev-parse HEAD`) **and capture a working-tree
  cleanliness snapshot**: run `git -C <index_root> diff --name-status -z HEAD`
  (staged + unstaged) and `git -C <index_root> ls-files -z --others
  --exclude-standard` (untracked). HEAD advancement via `git pull` is the
  impetus for rebuild; uncommitted edits in the index root are unexpected and
  block publication. Record each dirty file’s path, status, and SHA-256
  content hash so post-rebuild comparison can detect both NEW dirt and
  in-place byte-level mutations of pre-existing dirty files.
  After the rebuild completes successfully, re-read HEAD and verify it is
  unchanged; if HEAD has advanced (e.g. a pull landed mid-rebuild), discard
  the completed rebuild, write `indexed_commit` as absent, and schedule a
  fresh rebuild. **Also run the same working-tree cleanliness commands**
  post-rebuild and compare the **complete** dirty-file sets: if the post-rebuild
  set differs from the pre-rebuild set **in any way** (files added, files
  removed, files whose status changed, or any dirty file whose SHA-256
  content hash changed since the pre-rebuild snapshot), the working tree
  changed during the rebuild and the graph may contain a mixed or transient state — do NOT
  publish `indexed_commit` as authoritative; **globally invalidate** by writing
  `indexed_commit` as absent and scheduling a fresh rebuild. A path-only
  check for new additions is insufficient: if a file was already dirty before
  the rebuild and is reverted during it, it disappears from the dirty set —
  subsequent PLANs see a clean root and may trust a graph built from mixed
  state. The post-rebuild dirty-file set must exactly match the pre-rebuild
  set for publication to proceed. Only write `indexed_commit = <confirmed_head>`
  when pre-rebuild HEAD equals post-rebuild HEAD, **the pre-rebuild dirty set
  (excluding setup-managed files) is empty**, and the post-rebuild dirty set
  (also excluding setup-managed files) is also empty. **After acquiring the config lock** (immediately before writing
  `indexed_commit`), recheck HEAD and the dirty set one final time — a pull
  landing during lock-wait could otherwise produce a stale or mixed-commit
  publication.
  Before applying this
  gate, **exempt** `.cbmignore` when `cbmignore_ownership` is managed
  (`"created"` or `"merged"`) and its current SHA-256 matches the hash
  captured at the **start of this rebuild** (before the backend runs); after
  a successful rebuild and negative verification, update
  `cbmignore_content_at_index` in `config.toml` to that start-of-rebuild
  hash — this lets the file change between setup and the next rebuild without
  permanently blocking publication, while still detecting mutations that occur
  mid-rebuild; exempt
  `.serena/project.yml` when `project_yml_ownership` is managed and its
  current SHA-256 matches the hash captured at the start of this rebuild.
  These files are setup-owned untracked files and their separate hash and
  negative verification checks already detect unsafe changes — including them
  in the dirty-set gate would permanently block publication on all repos
  using a setup-managed `.cbmignore`. A nonempty non-exempted pre-rebuild dirty set
  means the graph represents `HEAD` plus uncommitted edits; recording
  `indexed_commit = <HEAD>` would mislead PLAN into trusting a graph that
  does not purely reflect the recorded commit. When the non-exempted
  pre-rebuild dirty set is nonempty, do NOT publish `indexed_commit`; leave
  it absent so PLAN falls back to direct reads for this PLAN.
  The rebuild then runs against the claimed snapshot; the claimed file and
  its `.ts` sidecar are **both** deleted after a **successful** rebuild.
  (The hook body is a pure shell `touch` with no nonce payload, so no nonce
  comparison is possible — the claim is deleted unconditionally on success.)
  **Hold the claim through `indexed_commit` publication.** Do NOT delete the
  claimed file before writing `indexed_commit` to `config.toml`. The claim file
  is the ownership token — deleting it before publication creates a TOCTOU
  window: another session can rename it immediately after an existence check,
  and the original session then publishes `indexed_commit` for an unowned
  rebuild. Instead: at **claim time**, read and save the current `indexed_commit_gen`
  from `config.toml` as `prior_gen` (absent if no session has yet published);
  generate a fresh `own_gen` UUID for this rebuild. Prepare the
  `indexed_commit` and `own_gen` values for publication. Publication is
  protected by a **shared lock** (`fcntl.flock(LOCK_EX)` on a dedicated lock file `<stable-state-dir>/config.lock` on POSIX; `LockFileEx(LOCKFILE_EXCLUSIVE_LOCK)` on a dedicated lock file on Windows — **never flock `config.toml` directly**: its atomic tmp+rename write replaces the inode, so a lock on the old inode provides no mutual exclusion): acquire the lock; **immediately re-read the
  claim file and confirm own PID still matches** — if absent or bearing a
  different PID, release the lock, discard the rebuild result, and exit
  without updating `config.toml` (this is the authoritative check; the
  preliminary fast-fail above does not substitute for it); read the current
  `config.toml` in full; check `indexed_commit_gen` against `prior_gen` —
  if it equals `prior_gen` (nobody published between our claim and now),
  **recheck HEAD and dirty set** (re-read `git rev-parse HEAD` and the
  working-tree dirty set; if HEAD or the non-exempted dirty set has changed
  since the pre-publication checks, a pull landed during lock-wait — release
  the lock and schedule a fresh rebuild); then
  **update `indexed_commit`, `indexed_commit_gen`, `cbmignore_content_at_index`,
  and `last_rebuild_timestamp_ns`** (set to `time.time_ns()` at the moment of
  publication, inside the lock) in the freshly-read config and write the
  merged result atomically (tmp + rename). `cbmignore_content_at_index` must
  be computed as `sha256:` + SHA-256 hex of the `.cbmignore` bytes
  **captured immediately before the rebuild begins** — not at the moment of
  publication. At publication time, re-read `.cbmignore` and verify its
  current hash matches the pre-rebuild hash; if it differs, the file was
  modified during the rebuild (introducing unverified exclusions), so
  discard, release the lock, and retry the full rebuild from scratch with a
  freshly captured snapshot. Additionally, run **negative verification** before advancing the baseline:
  use the pack-vendored `gitignore_eval.py` module specified at step 4b (fed
  the `.cbmignore` bytes as the exclusive rule source; do NOT use
  `git check-ignore`; ancestor-state propagation, directory-exclusion semantics,
  re-inclusion via directory negation).
  Report a failure only when effectively excluded paths are present in the graph.
  (Checking all current patterns with full gitignore semantics, rather than only
  new-relative-to-prior, avoids needing to reconstruct the prior pattern set from
  a stored SHA-256 hash, which is not possible for untracked files; ancestor-state
  evaluation avoids false failures for legitimately re-included paths.) — do NOT
  advance `cbmignore_content_at_index`, release the lock, retain the stale
  marker so the next PLAN retries, and exit without updating `config.toml`.
  Only advance `cbmignore_content_at_index` when the negative verification
  confirms excluded paths are absent from the graph. This prevents recording a new unverified
  `.cbmignore` state as the baseline, which would allow newly excluded
  content to remain queryable while PLAN checks see a matching hash and
  never trigger a rebuild. This keeps the exclusion baseline
  synchronized with the rebuilt commit so PLAN does not keep detecting the
  same exclusion delta on subsequent invocations. Update
  `cbmignore_content_at_index` on each successful rebuild (the initial value was
  written at step 5b; this keeps it current with the newly rebuilt commit);
  release the lock. If it differs from `prior_gen`, discard, release the lock,
  and fall back to direct reads for this PLAN only. Merging only the indexed
  fields under the lock preserves concurrent changes to other fields (e.g.
  a `repo_url` update from a concurrent normalizer migration). Delete the
  claim file only AFTER releasing the lock. This CAS serializes publication:
  any session that claims the same stale marker captures `prior_gen` before any
  concurrent publication can occur, so a later publisher's `own_gen` will differ
  and the original session correctly yields.
  Before proceeding to graph queries, **re-run the full `stale` +
  `stale.claimed.*` state check** (same table as the freshness protocol) —
  the hook may have fired after the session claimed the prior marker but
  before the rebuild completed, and another session may have already claimed
  the new marker (so a `stale`-only check would miss it). Apply the full
  three-row dispatch: if `stale` only, rebuild again if the session time
  budget permits, else fall back to direct reads; if `stale.claimed.*` only
  or both, treat as a live claimed rebuild and fall back to direct reads for
  this PLAN (do NOT query while another session is rebuilding). **When deferring (time budget
  exceeded), immediately call `os.utime(stale_path, None)` to retimestamp the
  deferred marker to now.** The just-completed rebuild's index mtime is newer
  than the hook-fire time at which the marker was originally written; without
  retimestamping, the next PLAN's freshness check sees `index_mtime >
  stale_mtime` and skips the rebuild — silently serving a graph that does not
  include the concurrent pull. Retimestamping ensures the marker is always
  detected as a pending signal by the next PLAN.
  If the rebuild errors or times out: (1) if a `stale` file already exists
  (a hook fired during the rebuild and wrote a newer marker), delete the
  claimed file and its `.ts` sidecar — the existing marker is fresher; (2)
  otherwise, use `os.replace(claimed_path, stale_path)` to atomically replace
  `stale` with the claimed file (use `os.replace`, not `os.rename` — on
  Windows `os.rename` raises `FileExistsError` if `stale` was written by a
  concurrent hook between the check in (1) and this operation; `os.replace`
  handles this by atomically overwriting the destination); immediately call
  `os.utime(stale_path, None)` to set its mtime to now, and delete the `.ts`
  sidecar. If `os.replace` succeeds and a concurrent hook had written `stale`
  in the window, that hook's marker is now replaced — but the next pull will
  write another, so no signal is permanently lost. This prevents the next freshness check from discarding the retry
  signal — which would cause the next PLAN to serve a failed or partial index
  without rebuilding. **The `.ts` sidecar must be deleted on ALL exit paths**
  (success, failure, orphan-reclaim) to prevent a stale sidecar from being
  mistaken for a live or orphaned claim on subsequent PLANs.

- `serena`: confirm LSP servers are live and responsive. No marker or rebuild.
  Freshness depends entirely on the index root's on-disk currency (i.e. how
  recently `git pull` was run there). The SKILL.md states this explicitly.

Rebuild duration and concurrent-rebuild coalescing under `codebase-memory-mcp`
(i.e., whether the rebuild tool itself is re-entrant) are tracked in Open
Questions.

### Trust boundaries

`setup.py` crosses three trust boundaries:

1. **Third-party backend installation** — trust level differs by backend:
   - **`codebase-memory-mcp` (Tier-1 manual prerequisite):** `setup.py` detects
     the binary and emits the install command; the user installs manually.
     Source-availability (MIT) ≠ verified build. Security-sensitive teams
     should build from source or prefer `serena`.
   - **`serena` (Tier-2 consent gate):** On any platform where the user selects serena
     (serena is opt-in on all platforms; `codebase-memory-mcp` is the default), `setup.py` runs
     `uv tool install -p 3.13 serena-agent==<pinned>` *after* an explicit consent gate. This
     is a Tier-2 installation, not Tier-1 — setup itself performs the package
     fetch and install on consent. Tests must cover the consent-gate path
     (user approves and user declines). Supply-chain risk applies to the PyPI
     distribution of `serena-agent==<pinned>` — the consent message must name the
     package and version being installed. An exact version pin does not prevent
     installing a namesake or typosquat; verifying that the `serena-agent` PyPI
     distribution is published by the expected upstream project is a blocking
     spike prerequisite (see Open Questions: "Serena PyPI provenance").

2. **Writes to `~/.claude.json`** with an atomic tmp/rename. The write path
   is shown to the user before execution. No credential value is generated
   or written — the registration contains only the command path and args
   (`"command"` + `"args"` fields); **no `"env"` block** is written.
   `CBM_ALLOWED_ROOT` is baked into `launch-backend.py` at setup time and
   must not appear in the registration’s `"env"` block (which is MCP-visible
   and inherited by the subprocess anyway).

3. **The MCP subprocess reads all source files** in the configured index root,
   including secret-containing files. The security perimeter is `CBM_ALLOWED_ROOT`
   — the subprocess rejects `index_repository` calls for paths outside the
   configured tree. `CBM_ALLOWED_ROOT` enforcement is a **setup prerequisite**:
   `setup.py` must verify that the backend rejects out-of-scope index requests
   before completing setup (see Open Questions: "`CBM_ALLOWED_ROOT` enforcement
   verification"). Since MCP tools are accessed only through spawned stdio
   subprocesses — one per Claude session, running as the same OS user — there
   is no cross-user MCP exposure and no port for a squatter to target.

   **Secret-path exclusions are a setup gate, not a recommendation.** The MCP
   subprocess reads all source files under the index root; backend tools that
   return symbol bodies or snippets can surface credential-bearing content
   directly into model context. OS process isolation (stdio subprocess per
   session, same OS user) and `CBM_ALLOWED_ROOT` restrict which paths can be
   indexed, but any PLAN query can extract a secret that has already been
   indexed. `setup.py` must apply and verify a default exclude list via a
   `.cbmignore` file (gitignore syntax, placed in the index root). Default
   patterns: `.env`, `.env.*` (covers `.env.local`, `.env.production`,
   `.env.development`, `.env.staging`, and other dotfile-variant env files —
   note `.env` and `.env.*` are separate gitignore rules; `.env` alone does not
   expand to variants), `*.pem`, `*.key`, `credentials.json`, `.git/config`, and
   any pattern from the user's `.gitignore` known to contain secrets. The canary
   probe must test the **exact configured patterns** — not a generic glob like
   `*.env` which does not match `.env` or `.env.local`.
   **Ownership and transaction safety:** `setup.py` creates `.cbmignore` if
   absent (new) or merges the required patterns if it already exists (merged);
   the setup transaction journal records the `.cbmignore` path and whether it
   was `created` or `merged` — this is required for rollback and uninstall.
   On rollback (setup failure): if `.cbmignore` was `created`, delete it; if
   `merged`, remove only the sentinel-delimited block that was added. On
   uninstall: same as rollback semantics. If the backend does not support
   `.cbmignore`-style exclusions (and does not enforce equivalent
   secret-path exclusion by a separately verified mechanism), `setup.py`
   must refuse to complete setup and emit a clear error rather than
   proceeding fail-open. **Serena is exempt from this rule:** Serena is
   LSP-based and does not index file content to a persistent store; its
   secret protection is provided by scope-confinement (`--project` flag),
   the metadata-only proxy requirement (D4 prerequisite 8), and PLAN
   scope-gate enforcement — not by `.cbmignore`. The user may
   extend the exclude list; they may not clear it.

   **Index purge on exclusion change.** When setup is rerun against an existing
   persistent index, applying new exclusion patterns does not retroactively
   remove previously indexed content — credential-bearing symbols cached before
   the exclusions were added remain queryable. `setup.py` must require a clean
   rebuild or explicit purge of the index after updating exclusion patterns, and
   perform a negative verification (confirm the excluded paths return no results)
   before marking setup complete. For backends that do not expose a purge
   command, `setup.py` must delete the index database/files and trigger a full
   rebuild — but only after: (a) confirming the target path **exactly matches
   the backend-reported index path for the configured repository** — a
   descendant-of-data-root check alone is insufficient when a backend stores
   multiple project indexes under one shared data root (e.g.
   `~/.cache/<backend>/<project-hash>/`), because a stale or malformed
   stored path could delete a different project's index or the shared data root
   itself; `setup.py` must query the backend for the index path corresponding to
   the currently configured repository root and reject any target that does not
   match (explicit rejection of the data root itself and any sibling project
   directory); `setup.py` also calls `os.path.realpath()` on both the resolved
   backend data root and the target path before any check, so symlinks cannot
   redirect deletion outside the allowed root; (b) obtaining explicit user
   confirmation showing the full path to be deleted; and (c) **stopping the
   daemon and verifying it has stopped** (via port-check or OS process list)
   before deleting any index files. On POSIX, a running daemon holds open file
   descriptors to its index; deleting the path unlinks it but the daemon
   continues serving from the open inode — excluded secrets remain queryable
   until the process stops. On Windows, deletion fails outright on open files.
   **Shared-store safety check before deletion:** `codebase-memory-mcp` stores
   multiple projects in one shared SQLite database. The `graph_path` reported
   by the backend may identify the shared database file, not a per-project
   artifact — deleting it would erase every project's graph. Before any deletion,
   verify that the path points to a **per-project directory**, not the root SQLite
   file. If the path identifies the shared database or cannot be confirmed as
   per-project, refuse automatic deletion and provide the path for manual removal
   with a clear warning. If the backend provides a project-scoped purge API
   (e.g. a `purge_project` MCP tool), prefer it over direct file deletion.
   The unambiguous rebuild sequence is: (1) stop daemon and verify stopped;
   (2) delete the per-project index (confirmed per-project) or invoke the
   backend's project-scoped purge API; (3) run the backend's **offline CLI
   rebuild command** with the daemon stopped — no concurrent access; (4) start
   the daemon; (5) run the liveness probe to confirm the daemon is serving the
   rebuilt index; (6) run negative verification (confirm excluded paths return
   no results). Starting the daemon before the offline rebuild finishes can cause
   concurrent access to a partial index; running the liveness poll before
   starting the daemon has nothing to poll. `setup.py` emits restart instructions
   only when no system supervisor is in place. A stale or malformed stored path
   must never cause deletion outside the known backend data directory.

## Alternatives Considered

The options are evaluated along three axes: **transport model** (no indexing /
per-session stdio / shared HTTP daemon), **graph quality** (grep-level /
AST symbol-only / LSP + tree-sitter def/ref graph), and **coordination /
index-ownership** (none / per-session private / shared coordinated daemon).
The coordination axis is required to distinguish the rejected per-session stdio
option from the recommended option — both use stdio transport and LSP/tree-sitter
graph quality, but they differ in whether multiple sessions share a single
coordinated daemon and index store (recommended) or each session spawns its
own isolated process with its own private store (rejected due to SQLite
contention and per-session rebuild cost). Remote cloud indexing is out of scope
and does not add a further axis. Prior art for each shape: the do-nothing option is the
current state of most AI coding tools; the per-session stdio shape is the MCP
default and the model used by every existing pack in this catalogue; the shared
HTTP daemon shape draws on language-server practice (`rust-analyzer`, `pyright`,
both long-running shared processes across editor instances).

| Option | Transport | Graph quality | Coordination | Status |
|---|---|---|---|---|
| Do-nothing | none | grep | none | Accepted as fallback if OQs resolve "no" |
| Stdio MCP (per-session) | stdio | LSP/tree-sitter | per-session private | Rejected — SQLite contention on N worktrees; per-session rebuild cost |
| Python stdlib indexer | none | AST only | none | Rejected — Python-only, ctags-level |
| Core extension point | any | inherits backend | inherits | Deferred — requires core RFC first |
| GrapeRoot direct | closed HTTP | ? | shared (external) | Rejected — proprietary, opaque telemetry |
| Full-stack Rust semantic backend | HTTP/stdio | tree-sitter + FTS + embeddings | shared coordinated | Deferred — pre-1.0, solo maintainer, no SLSA; upstream contribution path open |
| Stdio subprocess + shared internal daemon — `codebase-memory-mcp` (this RFC) | stdio (per-session client, shared internal daemon) | tree-sitter + FTS | shared coordinated | Recommended — pending OQ resolution |
| Stdio subprocess + per-session LSP — `serena` (this RFC) | stdio (per-session client and server) | LSP | per-session private | Alternative — no shared daemon; retains per-session startup/indexing cost at scale |

### Keep current direct-file and grep workflow (do-nothing)

Continue relying on direct file reads, grep, and agent-issued shell commands
for codebase exploration. No new pack, no daemon, no MCP registration.

**Cost of delay:** the multi-worktree token-waste problem persists. Each
session re-explores context it has already built; the compounding cost scales
with the number of concurrent worktrees and the depth of the codebase. Teams
whose agents operate across eight or more active worktrees report the most
acute waste. The do-nothing option is appropriate when: the repo is small
enough that per-session re-exploration is cheap; the team is not yet on
multi-worktree workflows; or the design-acceptance prerequisites cannot be
confirmed for either backend. If neither backend can satisfy the prerequisites,
this option becomes the default.

### Hook-based per-session priming (stdio transport)

Register the MCP server via `command`+`args` (stdio); each `SessionStart` hook
starts the indexer against the current worktree.

**Rejected because:** stdio transport spawns a subprocess per Claude session —
8 concurrent worktrees produce 8 independent processes. Each process tries to
scan the same root simultaneously (SQLite write contention), and each scans a
diverged in-progress branch state rather than the stable base. There is also no
persistent endpoint for cross-session coordination.

### Embed a Python-stdlib indexer in `tools/`

Build `tools/graph-index.py` using only the Python `ast` module.

**Rejected because:** `ast`-only covers Python files and produces symbol
definition locations only — no call graph, no cross-file import edges. This is
ctags-level quality, and ctags already exists. The open-source backends produce
a qualitatively better graph using tree-sitter (130+ languages, real def/ref
edges) or live LSP. Building an inferior version in-house fails the
"substantive, not duplicative" charter principle.

### Repo-scope pack that extends `core`'s session-start hook

Add an extension-point mechanism to `core`'s `session-start.py`; ship this
pack as repo-scope with a `tools/hooks/context-prime.py` that core discovers.

**Rejected because:** it requires a core RFC and review cycle before this pack
can ship. It also does not resolve the MCP registration — user-scope settings
are needed for cross-worktree sharing regardless. The core extension point is
worth pursuing independently (tracked in Open Questions).

### Wrap GrapeRoot directly

Install GrapeRoot's launcher and use its closed-source graph engine.

**Rejected because:** GrapeRoot's engine is a proprietary compiled binary from
a private repo. It installs machine telemetry (`identity.json`) and an
undocumented leaderboard sync mechanism. An unauditable binary with opaque data
transmission is not acceptable for teams with security review requirements.

### Wrap a full-stack Rust semantic graph backend

An MIT-licensed, Rust-native semantic graph backend exists that ships its own
MCP server with 23 tools (symbol search, neighbourhood traversal, blast-radius,
memory, knowledge ingestion), SQLite or PostgreSQL persistence, FTS + optional
embeddings fused via Reciprocal Rank Fusion, 100+ tree-sitter grammars, and
1,000+ tests. It has a confirmed working MCP server — which would resolve
several D4 blocking OQs immediately — and its retrieval discipline (structural
ranking, provenance metadata on results, token-budgeted context packs) is more
mature than either current backend.

**Deferred, not rejected.** The capability is compelling; the enterprise trust
gap is the blocker. The evaluated implementation has: no SLSA attestation or
Sigstore signing; no disclosed-security process (`SECURITY.md` absent); pre-1.0
API contract (v0.14.x, significant restructuring across minor versions); a
solo individual maintainer with no org governance or named co-maintainers; and
zero external adoption evidence. Every axis enterprise procurement and security
teams evaluate first is either red or unverified.

**Open contribution path.** The gaps that the existing backends leave open
(read-only mode, rebuild idempotency guarantees, provenance metadata) could be
addressed by upstream contributions to this backend rather than by extending
the current backends. If the project matures — SLSA attestation,
post-1.0 stability, org or multi-maintainer governance — it becomes the
strongest available option and this RFC's backend table should be reopened.
The patterns mined from this evaluation (named GRAPH-FALLBACK events, structural
ranking, provenance metadata, blast-radius as a canonical operation) are already
folded into the SKILL.md requirements above; they apply regardless of which
backend is chosen.

**Conditions for revisiting:** (a) SLSA L2+ build provenance, (b) post-1.0
semver stability, (c) org governance or ≥2 active maintainers with demonstrated
review history, (d) ≥6 months of no breaking API changes after 1.0.

## Risks

- **Daemon offline at PLAN time.** Graph tool calls fail. The skill treats this
  as non-fatal: fall back to direct file reads. *Accepted unmitigated* — the
  pack makes no promise the daemon is running.

- **Index root not regularly pulled; graph becomes stale over time.**
  If the user forgets to `git pull` the index root, both backends silently serve
  outdated results. Mitigation: SKILL.md states the pull requirement explicitly
  and recommends a scheduled pull (cron / launchd) on the index root. Accepted
  — automated pull scheduling is out of scope for this pack.

- **User-installed binary from a third party.** Supply-chain compromise in the
  binary distribution would deliver malicious code. Mitigation: Tier-1 manual
  prerequisite pattern — `setup.py` does not download automatically; user installs
  from the project's official release page. Security-sensitive teams directed to
  `serena` or source build.

- **`CBM_ALLOWED_ROOT` not set; any repo on the machine can be indexed.**
  If `CBM_ALLOWED_ROOT` is absent (delivery mechanism unconfirmed — see Open
  Questions) or not honored by the backend version, the user's home directory
  becomes the effective root. A session in any repository could call
  `index_repository` against sensitive directories outside the intended scope.
  Mitigation: `setup.py` must verify `CBM_ALLOWED_ROOT` is enforced before
  completing setup (canary that attempts indexing a path outside the allowed
  root and confirms rejection). Accepted pending OQ resolution on env var
  delivery to stdio subprocess.

- **`~/.claude.json` write is not concurrent-writer-safe.** Two
  simultaneous setup skill runs can produce a lost update. Mitigation:
  documented; resolved if agentbundle exposes a shared write lock (Open
  Questions).

- **Scope-gate is skill-enforced, not daemon-enforced.** The user-scope MCP
  registration is globally callable regardless of which repository Claude has
  open. A session in an attacker-controlled repository can query the indexed
  repo's graph without loading the SKILL.md scope-gate — prompt injection from
  foreign repo files or hooks can retrieve symbol bodies, cross-file import
  edges, or call graphs from the indexed codebase. Framing the scope check as a
  "non-optional precondition" in SKILL.md does not constitute an authorization
  boundary; a prompt-injected session bypasses it entirely. Mitigation: see
  blocking OQ "Repository-scope enforcement" — the daemon must enforce which
  repository may query it, either via project-scoped MCP registration or a
  daemon-side repository check embedded in the request. Accepted pending OQ
  resolution — per-session scoping is unsupported by either current backend
  version.

- **Operational — daemon OOM-kills mid-PLAN.** Agent receives tool errors.
  Mitigation: skill's fallback instruction covers mid-session failure; large-
  codebase users should configure OS memory limits.

## Rollout

New optional pack, zero existing users — rollout is purely additive.

**Install route:** `agentbundle install --pack codebase-context` is the only
supported install route. `claude plugin install` is not supported — see the
agentbundle-only rationale under **Three version checks apply at runtime** (below). The pack
projects skills and scripts into the adopter's agent configuration; it does
not auto-run the setup skill. After projection, the `[pack.first-value]`
section in `pack.toml` surfaces instructions to run the
`setup-codebase-context` skill.

**State root resolution:** `setup.py` resolves the pack state root from the
agentbundle state file via two paths.

**Path A — agentbundle importable:** Wrap the import in a
`try/except (ImportError, AttributeError)`. If it succeeds and both
`agentbundle.safety.user_state_path` and `agentbundle.config.pack_dir`
resolve without error:
1. Load the state path via `agentbundle.safety.user_state_path()`.
2. Call `agentbundle.config.load_state(state_path)` to construct `state`.
3. Require a `codebase-context` adapter row in `state`; if absent, refuse
   with a clear error — a pip-installed agentbundle with no `codebase-context`
   row means the pack was not installed via agentbundle (a plugin install on
   such a machine would otherwise pass the import and fall through).
4. Call `agentbundle.config.pack_dir("codebase-context", state=state)`. The
   bare `pack_dir("codebase-context")` call without a loaded `State` does not
   honor a custom `[catalogue] user-dir`; roots belong to per-adapter rows
   and are resolved only when a loaded `State` is passed. `State` has no
   `user_root` attribute — the root is derived internally by `pack_dir` from
   the state's adapter rows. The exact call signature must be verified against
   `packages/agentbundle/agentbundle/config.py:251-296,439` and
   `agentbundle.safety.user_state_path()` before implementing (tracked in
   Open Questions: "`pack_dir()` API contract").
5. **Bind the running projection to the adapter projection root:** obtain
   the projected skill directory from the `codebase-context` adapter row
   (the directory where agentbundle projected the skill's SKILL.md and
   scripts into the IDE skills path — distinct from `pack_dir`, which is the
   stable state directory). Verify that `Path(__file__).resolve()` is a
   descendant of that projected skill path. If not (e.g. the user invoked a
   copy from a Claude plugin cache while an agentbundle installation also
   exists), refuse with a clear error — the agentbundle row exists but this
   skill is not running from the adapter-managed projection, so the stable-path
   launcher upgrade guarantee does not hold. (The exact agentbundle API for
   obtaining the projection path from the adapter row must be verified against
   `packages/agentbundle/agentbundle/commands/install.py:770-807` — tracked
   in Open Questions: "`pack_dir()` API contract".)

If agentbundle is present but the API is incompatible (older version missing
`user_state_path`, `load_state`, or `pack_dir` with `state=`): surface an explicit
"upgrade agentbundle" error and refuse. If the state file is absent or
unreadable (`ConfigError` or `StateFileLegacy`), refuse and emit remediation
instructions.

**Path B — agentbundle not importable (zipapp route):** A standalone agentbundle
zipapp (`.pyz` on `$PATH`) is not importable as a Python module but maintains the
same state file at the canonical path. Parse the state file directly using
`tomllib.load` (TOML only; `user_state_path()` always writes TOML). Verify the
`"schema-version"` key (hyphenated, as written on disk — `config.py:472` uses
`raw.get("schema-version")`); if absent or mismatched, refuse. Require a
`"codebase-context"` adapter row; if absent, refuse — an unimportable agentbundle
with no codebase-context state row cannot be a valid agentbundle install. Do NOT
fall through to a default `~/.agentbundle` path; that would silently accept a
plugin install on a machine with a zipapp agentbundle that lacks the pack row.
Read the `"user-root"` base from the adapter row (`config.py:552` uses
`body.get("user-root")`). Apply home-confinement and lstat checks to the
resolved base. Then **explicitly construct the pack directory** as
`<resolved-base>/codebase-context` — `user-root` is the catalogue base, not
the pack-specific directory; the canonical resolver's `safety.make_pack_dir()`
(`safety.py:710`) appends the pack slug. Apply the same lstat and
home-confinement checks as the canonical resolver (`safety.py:694-725`) to
the pack directory before proceeding.

The `pack_dir()` API contract Open Question tracks confirming the API signature.

The `agentbundle install` route surfaces `setup-codebase-context`, which interactively configures
the backend, writes the MCP registration into `~/.claude.json`, copies scripts
to the resolved scripts directory, and chains hooks. **A new Claude Code session is required
after setup completes.** Claude Code reads `~/.claude.json` at startup; MCP
tools registered during a running session are not available until the session
is restarted. The setup skill must emit an explicit reminder: "Restart Claude
Code to load the new MCP registration before running `codebase-context`."

On re-run with a different index root: user confirms the overwrite interactively
within the skill; only then are the previous index root's sentinel blocks removed
and new hooks chained.

**Pack upgrade script refresh:** When the pack is upgraded, the skill code in the projection changes but the copy of
`normalise_remote.py` in the stable state directory remains unchanged.
(`post-merge.py` is inlined into `setup.py` and has no stable-state copy to
refresh.) To prevent old normalization code from running against a new
skill/config protocol, a version check runs **on every invocation of either
skill** — both `setup-codebase-context` and `codebase-context`. The check
compares **per-artifact version stamps** in the stable state directory against
version
strings baked into the projected skill files:

- `scripts-version-normalise-remote` — stamped by `codebase-context` and
  `setup-codebase-context`; compared against
  `__scripts_version_normalise_remote__ = "x.y.z"` baked into both SKILL.md
  and `setup.py`.
- `scripts-version-uninstall` — stamped by `setup-codebase-context` at setup
  time; compared against `__scripts_version_uninstall__ = "x.y.z"` baked into
  `setup.py`. On version mismatch detected at setup rerun, atomically refresh
  `uninstall.py` from the skill's own projected `scripts/` directory
  (copy-to-tmp + rename). Bump whenever `uninstall.py` or its cleanup logic
  changes. **Direct-teardown guard:** `uninstall.py` must self-check at
  startup — compare `__scripts_version_uninstall__` baked into itself against
  `scripts-version-uninstall` in `pack_dir`; if they differ, exit non-zero with
  instructions to rerun setup to refresh. **Limitation after pack upgrade:**
  both the copied script and the stamp may retain the same old value after an
  upgrade without setup rerun — they match each other but are behind the
  projected pack's newer version. The `setup-codebase-context` skill's teardown
  flow must also compare `scripts-version-uninstall` against
  `__scripts_version_uninstall__` baked into the projected `setup.py`; if behind,
  print instructions to rerun setup first before teardown. Both checks together
  close the window: copy-vs-stamp drift is caught in `uninstall.py` itself;
  stamp-vs-projected-pack drift is caught in the skill. **Direct invocation of
  `uninstall.py` after a pack upgrade — without first re-running
  `setup-codebase-context` and without going through the skill's teardown
  flow — is not a supported path.** The self-check cannot detect
  stamp-vs-projected-pack drift; only the skill can. Teardown must always be
  invoked through `setup-codebase-context`, which performs both version
  comparisons before proceeding.
**Three version checks apply at runtime:**
- **`__launcher_version__`** baked into `launch-backend.py` at setup time:
  `launch-backend.py` uses a **two-source version check** at process startup,
  before any exec, to close the first-session upgrade gap:
  (1) **Direct projected stamp:** attempt to read `scripts-version-launcher`
  from `pack_scripts_dir` (recorded in `config.toml [scripts]`). For
  `agentbundle install` routes, agentbundle upgrades in place so
  `pack_scripts_dir` is stable and this read reflects the current pack version.
  (2) **`launcher_version_expected`:** read `config.toml [scripts]
  launcher_version_expected`, which is refreshed on each PLAN startup.
  **This pack requires the `agentbundle install` route only.** `claude plugin
  install` is explicitly not supported: plugin upgrades move the skill to a new
  versioned cache path, leaving the old cache directory readable on disk and
  making it impossible for the stable launcher to discover the current version
  without skill activation. Declaring this configuration "unsupported" does not
  fail closed — the old launcher would silently pass indefinitely, including
  after security fixes to environment isolation or proxy gates. Removing
  plugin-route support eliminates this entire class of gap. `pack.toml` must
  restrict `allowed-adapters` accordingly; `setup.py` must detect and refuse
  plugin-route installs with a clear error pointing to `agentbundle install`.
  For the supported `agentbundle` route: agentbundle upgrades in place (stable
  path), so `pack_scripts_dir/scripts-version-launcher` reflects the current
  version immediately after upgrade. `launcher_version_expected` (in
  `config.toml [scripts]`) is additionally refreshed on each `codebase-context`
  PLAN startup — the skill reads `scripts-version-launcher` from its own
  projected scripts directory (resolved via `__file__`) and updates
  `launcher_version_expected` under the **shared config lock** (`<stable-state-dir>/config.lock` — same dedicated lock file as the rebuild publisher; fresh read-and-merge before writing)
  whenever the value advances. The launcher reads `pack_scripts_dir` as the
  primary source; `launcher_version_expected` is a secondary cross-check.
  If either value does **not exactly equal** `__launcher_version__`,
  `launch-backend.py` must exit non-zero with a message instructing the user to
  rerun `setup-codebase-context` to refresh the launcher. This rejects
  mismatches in both directions (upgrade and rollback) and fails closed:
  sessions that call MCP tools directly without loading the skill will see an
  immediate startup failure if the launcher is stale.
  Bump `scripts-version-launcher` whenever `launch-backend.py`'s content
  changes (environment isolation, version revalidation, serena proxy gate).
- `config_version` in `config.toml` (top-level key): a general schema version
  for the entire configuration and runtime state contract. `codebase-context`
  reads and checks this on every PLAN startup; if absent or mismatched, it
  refuses to proceed and instructs the user to rerun `setup-codebase-context`.
  This covers changes to `config.toml` schema, marker names, authentication
  layout, or any other runtime state contract that does not necessarily change
  `normalise_remote.py`. Bump `config_version` whenever any such change ships.
- `scripts-version-normalise-remote` (file in `pack_dir`) — stamped by both
  `codebase-context` and `setup-codebase-context`; compared against
  `__scripts_version_normalise_remote__ = "x.y.z"` baked into both SKILL.md
  and `setup.py`. The projected `pack.toml` is not available at runtime alongside
  the skill — the adapter projection does not include it. Placing the check only
  in `setup-codebase-context` was insufficient because users may run
  `codebase-context` indefinitely without manually re-running setup after an
  upgrade. Bump this constant whenever `normalise_remote.py` or its calling
  protocol changes.
- `scripts-version-gitignore-eval` (file in `pack_dir`) — stamped by
  `codebase-context` at setup time; compared against
  `__scripts_version_gitignore_eval__ = "x.y.z"` baked into the projected
  `rebuild_coordinator.py`. `rebuild_coordinator.py` reads the stamp at the
  start of every runtime invocation; on mismatch, it atomically refreshes
  `gitignore_eval.py` from the `codebase-context` projected `scripts/`
  directory (copy-to-tmp + rename) and then refreshes the stamp. This ensures
  a corrected evaluator is active before the next negative verification without
  requiring a setup rerun. Bump whenever `gitignore_eval.py` semantics change.

On version mismatch in `codebase-context`: atomically refresh `normalise_remote.py`
from `codebase-context`'s own projected `scripts/` directory (copy-to-tmp + rename).
Do **not** advance the version stamp yet — the identity migration below must
complete first (see ordering below). Each skill owns the scripts it needs at runtime.

**Identity migration on normalizer upgrade.** When `normalise_remote.py` is
refreshed, the stored `config.toml [index] repo_url` was produced by the old
normalizer. If the new normalizer changes its output for the same remote URL,
the scope check will fail-closed (correct repo appears to be a different one).
Setup records a **credential-redacted** raw remote URL in `config.toml [index]
remote_url_raw` at setup time — apply the same recognized-credential-key
stripping described in normalization step 1 (strip URL fragment entirely —
everything from `#` to end; strip `access_token`, `token`, `api_key`,
`private_token`, `oauth_token` from the query string; strip userinfo from
HTTP/HTTPS; preserve non-credential URL components (path, port) — query params
cause fail-closed even when non-credential, matching the normalization contract).
This retains uniqueness as a collision-resistant identity anchor while holding
no secrets in the PLAN-visible config. If any credential key stripping is
ambiguous or if the URL has any remaining query params (credential or not), fail
closed and require the user to configure `--repo-url` with a clean URL.
After refreshing `normalise_remote.py`, `codebase-context` must verify the
change is normalizer-driven only. **Apply the same credential-redaction
transform** (strip URL fragment entirely; strip `access_token`, `token`,
`api_key`, `private_token`, `oauth_token` from query string; strip
HTTP/HTTPS userinfo) to the current
raw remote URL (`git -C <index_root> remote get-url origin`) before
comparing against the stored `remote_url_raw`. If `redact(current_remote)`
differs from `remote_url_raw` (the remote URL itself changed), **fail closed**
and require the user to rerun setup — regardless of what
`old_normalizer` returns. Two different origin URLs can map to the same
normalized form, so `old_normalizer(current_remote) == stored_repo_url` is
NOT sufficient to establish the remote is unchanged. If
`redact(current_remote) == remote_url_raw` AND
`new_normalizer(current_remote) != stored_repo_url`, the difference is
normalizer-only — **acquire the shared config.toml lock** (same lock used by
rebuild publication), re-read the current `config.toml` under the lock, update
`repo_url`, write the merged result atomically (tmp + rename), and release the
lock. This prevents the rebuild CAS from overwriting a concurrent migration
or the migration from overwriting a freshly-published `indexed_commit`. Every
writer of `config.toml` — setup's step 5b (CBM path), Serena path step (c),
rebuild CAS, normalizer migration, and PLAN-time launcher-version refresh —
must acquire this same lock before reading and writing. Silently overwriting `repo_url` when the remote has changed
would retrust the scope gate for a different repository while the graph may
still contain data from the original. A mismatched identity that cannot be
resolved is surfaced to the user; they rerun setup to re-record it.
**Fork override exception:** if `config.toml [index] repo_url_source = "override"`,
the migration must not re-derive `repo_url` from `git remote get-url origin` —
the user intentionally set a fork URL and re-deriving from origin would silently
replace it with the upstream identity. Setup records `remote_url_raw` for override
installs too — the credential-redacted form of the user-supplied `--repo-url`
value (same redaction rules as for auto installs; source is the argument, not
`origin`). For override installs, the migration re-normalises from `remote_url_raw`
(the stored raw override value) with the new normalizer — not from the
already-normalized `repo_url`, which has lost the scheme and `.git` suffix the new
normalizer may need. If the result differs from `stored_repo_url`, update `repo_url`
accordingly.
**`index_root_origin_at_setup` re-derivation (both auto and override paths):**
After updating `repo_url` (under the same `config.lock`-protected write), if
`index_root_url_raw` is present, also re-derive `index_root_origin_at_setup`:
apply credential-redaction and the new normalizer to
`git -C <index_root> remote get-url origin`; verify
`redact(index_root_remote) == index_root_url_raw` first (fail closed if not —
the index root's remote changed independently); then write
`new_normalizer(index_root_remote)` as the new `index_root_origin_at_setup`.
This step applies regardless of `repo_url_source` (auto or override): PLAN
scope-gate step 2 always compares the live index-root identity against
`index_root_origin_at_setup`, so a normalizer upgrade would otherwise cause
the gate to fail closed permanently with no diagnostic on all install types.
Only after the identity migration succeeds should `scripts-version-normalise-remote`
be advanced. **There is no shortcut:** do not skip migration because
`new_normalizer(stored_repo_url) == stored_repo_url` — a new normalizer may
handle schemes, SCP syntax, or `.git` suffixes differently while remaining
idempotent on the already-normalized value; the correct comparison is
`new_normalizer(remote_url_raw) == stored_repo_url` (or `remote_url_raw` for
the override case), which is the migration itself. This ordering is crash-safe: a crash before the stamp advancement
leaves the old stamp, so the next invocation retries the migration rather than
skipping it with a stale identity.

**Rollback:** The user runs the uninstall sub-flow of `setup-codebase-context`
(or a dedicated teardown skill). The uninstall sequence is strictly ordered to
ensure the internal daemon is stopped before the graph is purged and the index
path is resolved before config is removed:

**Step 0 — Stage teardown for outside-session execution.** Any Claude session
that loaded this registration has a live stdio subprocess; teardown races with
active clients. **The canonical uninstall path is direct terminal invocation with
no Claude sessions open:** `<interpreter> <pack_dir("codebase-context")>/scripts/uninstall.py`.
**`uninstall.py` must acquire the exclusive maintenance lock**
(`<stable-state-dir>/setup.lock`) as its very first action, before Step 1,
and hold it through final cleanup. Without this lock, a concurrent
`setup.py --update` can promote new hooks or registration while `uninstall.py`
is reading the old state, leaving a registration that points at deleted files
or removing hooks that setup just wrote. If the lock is already held (a
concurrent setup is running), `uninstall.py` must exit with a clear message
that another setup is in progress.
(`<interpreter>` is the absolute path recorded in `interpreter_path` in
`pack_dir("codebase-context")/config.toml`. **Interpreter probe in the skill:**
the `setup-codebase-context` skill must probe this path before printing the
teardown command — if `interpreter_path` is absent or points to a non-executable
file, the skill applies the full durable-interpreter probe (same rules as initial
setup: reject virtualenv/pyenv/uv paths, reject `~/.pyenv/versions/`, run the
candidate with `-c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"`
to confirm Python ≥ 3.11) and uses the first passing candidate as the fallback;
if no candidate passes, print a fatal message requiring the user to supply a
Python ≥ 3.11 interpreter path manually. The probe must happen in the skill, not
in `uninstall.py`, because a missing or incompatible interpreter prevents the
shell from launching the script at all. `uninstall.py` itself may additionally validate at startup for
defense-in-depth, but the skill is the primary resolver.)
The `setup-codebase-context` skill's role is to print this command, explain that
all Claude sessions must be closed before running it, and exit. The skill does
NOT execute teardown from within an active Claude session — the current session
itself has the registration loaded and would be the subject of teardown. An
implementation that attempts teardown from within the skill will immediately
fail its own "no active sessions" gate.

**Step 1 — Verify the index path.** *`codebase-memory-mcp` only;* if the
configured backend is `serena`, skip directly to Step 4 — serena has no
persistent graph, no `graph_path`, and no `list_projects` tool; Steps 2 and 3
are not applicable. For `codebase-memory-mcp`: call
`list_projects` via the binary (spawn a stdio subprocess using the same
explicitly constructed minimal environment as `launch-backend.py` — not the
inherited shell environment, which may contain `GITHUB_TOKEN` or other
credentials; this applies to every uninstall-time backend invocation: liveness
checks, `list_projects`, and daemon-stop commands) to query the backend for the
exact current index path of the configured repository; compare with
`config.toml [index] graph_path`. If they match, retain the backend-verified
path; if the query fails or they do not match, mark the path as unverified.
This live query distinguishes the configured project's index from sibling
project directories under the same data root — containment checks alone cannot
make this distinction if the backend moves its data root.

**Step 2 — Retain the graph index path from config as a hint** (while
`config.toml` is still present). Read `config.toml [index] graph_path` — the
value written at setup time. This is a **reference hint only**, not sufficient
authority for scripted deletion — the backend's project mapping may have changed
since setup, and the path may now identify a sibling or shared-store file. The
authoritative path for scripted purge is the daemon-verified value from Step 1.
If Step 1 succeeded (daemon available, project found, path matched), use the
daemon-verified path. If Step 1 failed or returned no match, the stored hint
can be presented to the user for manual review, but scripted deletion must not
proceed. Once `config.toml` is removed in step 3, this hint is no longer
available, so it must be captured here. If `graph_path` is absent, there is no
hint and the user is prompted for a manual path.

**Step 3 — Graph database purge (decision + execution, before config removal).**
The graph purge offer AND execution MUST happen before `config.toml` is
deleted: if the purge is deferred to after step 4 and step 4 succeeds but
the purge crashes, both `config.toml` (the persisted `graph_path`) and the
uninstall script are already gone — a rerun cannot safely locate or execute the
consented purge, stranding a secret-containing index. Prompt "Remove the graph
index files? (y/N)" now, while config and daemon-verified path are available.
Apply the purge safeguards: (a) use only the **daemon-verified path** from step
1; call `os.path.realpath()` on it and confirm it is contained within the
backend's known data root (e.g. `~/.cache/codebase-memory-mcp/` — verify
actual path at spike; resolved with `realpath`; refuse if the path escapes, equals, or
is a sibling of the data root). Containment alone is insufficient — the daemon
may return the shared SQLite database file itself, which is contained in the data
root and daemon-verified, yet deleting it erases every project's graph. After
confirming containment, additionally verify that the path is a **per-project
artifact** (not the shared database), then **prompt for affirmative consent
once** before any deletion or API purge. Both API-based and filesystem
deletion are guarded by the same consent prompt — do NOT invoke the
project-scoped purge API before the user has confirmed:
(i) if the backend exposes a project-scoped purge API (a confirmed D4
prerequisite) **and the user confirmed**, invoke it and skip direct file
deletion; (ii) if no project-scoped purge API exists and the path identifies
the shared database (e.g. it matches the data root's top-level `*.db` or
equivalent single-store file), refuse automatic purge and require the user to
run the backend's own project-removal command manually; (iii) direct deletion
is only permitted when the path is confirmed to be a per-project subdirectory
or file distinct from the shared store, **and the user confirmed**. If Step 1 could not verify the path (daemon unavailable, mismatch
with stored `graph_path`, or query failed), refuse **all** scripted deletion —
containment and artifact-shape checks alone cannot establish project ownership,
so a confirmation prompt still risks deleting a sibling project's graph.
**Write a purge-pending tombstone** (`pack_dir("codebase-context")/graph-purge-pending`
recording `graph_path` from config and the failure reason) before proceeding —
Step 4 will remove `config.toml` and `uninstall.py`, making the user-instructed
retry impossible if the path is only printed to the terminal. **Before proceeding to step 4 (`agentbundle uninstall`), record the
tombstone's absolute path in a well-known canonical location** — write a
plain text file named `codebase-context-purge-locator` under
`user_state_path().parent` (the canonical `~/.agentbundle/` directory);
this canonical root is fixed and never a custom `[catalogue] user-dir`, so
the locator remains discoverable after `agentbundle uninstall` removes the
adapter row that identifies the custom `pack_dir`. Remove the locator file
once the deferred purge completes successfully. The tombstone itself
persists through pack removal and can be found by the user or a future tool
to perform the deferred purge. Then print the tombstone path and a manual-removal
reminder (e.g. start the daemon and verify the path before deleting), and
proceed to Step 4 to revoke MCP access; do not offer a deletion confirmation here;
**(b) Stop the shared daemon before direct deletion.** For direct filesystem
deletion (case iii above) with backend `codebase-memory-mcp`: stop the
internal daemon by invoking `codebase-memory-mcp daemon stop` and waiting
for process exit (timeout 10 s) **before** deleting the file. Do NOT stop
the daemon when the API purge already completed at step (i) or when the
user declines deletion — stopping the shared daemon unnecessarily interrupts
other projects using the same backend. If the daemon does not exit within
the timeout, **skip the graph purge only** — write a cleanup tombstone
(`pack_dir("codebase-context")/graph-purge-pending` recording the path for
manual removal) and proceed directly to Step 4. Failure to purge a live
database must NOT block access revocation — the MCP registration, hooks, and
pack files must still be removed so no new Claude sessions can reach the
backend. If backend is `serena`: no persistent daemon to stop (the LSP
server exits with the session).
(c) **Conditional deletion** — apply only when a project-scoped purge API
was NOT already used at step (i): if the API was used, the purge already
completed; do NOT also delete the file directly (this would erase any
remaining projects in a shared store). After stopping the daemon if required
by (b), on user consent, delete the daemon-verified path using the
safeguard-confirmed per-project artifact only. If the user declines, print the path and a
manual-removal reminder noting it may contain previously indexed secrets;
**also write a cleanup tombstone** (`pack_dir("codebase-context")/graph-purge-pending`
recording the path and a "declined" reason) and write
`codebase-context-purge-locator` to `user_state_path().parent` recording
the tombstone's absolute path — a declined purge requires the same durable
references as a failed one, including the canonical locator that remains
discoverable after pack removal.
**If the purge API call or direct deletion raises an error** (network
failure, permission error, partial deletion), do NOT block Step 4 — write
a cleanup tombstone (`pack_dir("codebase-context")/graph-purge-pending`
recording the affected path and failure details), print a warning with
manual-removal instructions, and proceed directly to Step 4. Access
revocation (MCP deregistration, hook removal) must not be blocked by a
purge error: leaving the globally-callable MCP registration in place
because the graph store could not be cleaned is the worse outcome.

**Step 4 — Remove pack files:** the `~/.claude.json` MCP entry — action depends
on `config.toml [mcp] ownership` (a field written at setup time: `"created"` if
no prior entry existed; `"displaced"` if a prior entry was overwritten).
**Before acting, read the current `mcpServers.codebase-context` entry and
compare it against the pack-generated wrapper template** (same `"command"` and
`"args"` values as were written at setup time): if the current entry has
drifted (the user or another installer replaced it), do not silently remove or
overwrite it — surface a confirmation prompt naming the current entry and the
intended action (remove or restore); proceed only on explicit confirmation.
if `"created"` and not drifted, remove the key; if `"displaced"` and not
drifted, restore the entry from `prior-mcp-entry.json` sidecar rather than
removing the key (the restored entry must survive through subsequent setup
reruns — new setup must carry the original forward; **delete the sidecar only
after all step-4 teardown succeeds** — on crash-retry, if sidecar is absent
and `ownership = "displaced"`, restoration already completed); this explicit
ownership field is required because a missing sidecar is ambiguous — fresh
installs with no prior entry also have no sidecar, so "missing sidecar" cannot
distinguish "already restored" from "never had prior",
`pack_dir("codebase-context")/scripts/launch-backend.py` (the generated
minimal-environment Python wrapper),
`pack_dir("codebase-context")/scripts/normalise_remote.py`,
`pack_dir("codebase-context")/scripts/gitignore_eval.py`,
`pack_dir("codebase-context")/scripts/codebase-context-cleanup.py` (omit if
`cbmignore-cleanup.json` is present — the cleanup helper must survive until
deferred cleanup completes),
`pack_dir("codebase-context")/scripts/uninstall.py` (itself — the final action
of the teardown script is to delete its own copy),
`pack_dir("codebase-context")/config.toml` and the per-artifact version stamps
(`pack_dir("codebase-context")/scripts-version-normalise-remote`,
`pack_dir("codebase-context")/scripts-version-uninstall`, and
`pack_dir("codebase-context")/scripts-version-gitignore-eval`) — **these must be
deleted LAST, after all fallible cleanup in this step completes** (hooks removal,
backend-owned file reversal, package-manager removal); deleting them earlier
makes crash recovery impossible: a retry cannot resolve hook/config paths and
`uninstall.py` fails its own version check,
the staleness marker (`pack_dir("codebase-context")/stale`),
all claimed markers (`pack_dir("codebase-context")/stale.claimed.*` — glob;
a crashed rebuild may leave these), the sentinel-delimited blocks from
all three git hook files (`post-merge`, `post-rewrite`, `post-checkout`), and
the `.cbmignore` artifact per the stored ownership mode in `config.toml`: if
`cbmignore_ownership = "created"`: if a purge tombstone is present
(`graph-purge-pending` exists), **retain the sentinel-delimited exclusion
block** until the graph is successfully purged or unregistered — removing
exclusions while the graph is still live allows a later `index_repository`
to ingest credential paths that setup required to be excluded; **before
deleting `config.toml`**, write a `cbmignore-cleanup.json` file (mode
`0600`) to `pack_dir("codebase-context")` recording `cbmignore_path`,
`cbmignore_ownership`, the exact sentinel start and end markers, the
absolute path to `cbmignore-cleanup.json` itself, and the absolute path to
`pack_dir("codebase-context")/graph-purge-pending` (the tombstone) — the
tombstone path must be recorded here because `pack_dir` may be under a
custom `[catalogue] user-dir` that becomes undiscoverable after
`agentbundle uninstall` removes the adapter row; **also** write a
discoverable pointer file `codebase-context-cbmignore-pending` (mode
`0600`) to `user_state_path().parent` (the canonical `~/.agentbundle/`
directory) containing only the absolute path to `cbmignore-cleanup.json`
— this pointer survives `agentbundle uninstall` removing the adapter row
and allows any cleanup tool to locate the file without knowing the custom
`pack_dir`; both `cbmignore-cleanup.json` and the canonical pointer are
**not** deleted by teardown's config-cleanup step; only remove
the exclusion block after the graph has been purged — a post-purge cleanup
path is provided by (a) a subsequent `setup-codebase-context` invocation
and (b) a standalone `codebase-context-cleanup.py` script; both paths
**first check `graph-purge-pending`**: (i) if the tombstone is absent, the
purge is complete — proceed directly to reading `cbmignore-cleanup.json`
via the canonical pointer, removing the sentinel-delimited block, then
deleting both `cbmignore-cleanup.json` and the canonical pointer; (ii) if
the tombstone is present, read it to obtain the recorded graph path and
check whether that path still exists: if the path does not exist (the user
has already manually removed it), offer to accept the purge as complete
(`"The graph store at <path> no longer exists. Mark purge complete? [Y/n]"`
); if the user confirms or the path was never a filesystem path (e.g. a
remote registry purge), delete `graph-purge-pending` and proceed to
cleanup; if the path still exists, print the path and manual-removal
instructions, then offer `"I have already removed it manually [Y/n]"` — on
confirmation, delete `graph-purge-pending` and proceed to cleanup; on
decline, exit without modifying `.cbmignore`. Both the setup and the
standalone cleanup script implement this same acknowledgement flow so the
tombstone is always cleared through a verified or user-confirmed step. Otherwise (no tombstone),
**inspect for post-setup user additions** (content outside setup's
sentinel-delimited block) before offering to delete — if user content is
found, surface a confirmation naming the additions and the consequence of
proceeding (those patterns will be lost); only fully delete on explicit
confirmation or when no user content is present; **if the user declines full
deletion**, remove only the setup-owned sentinel-delimited block while
preserving the user-added lines (same as the `"merged"` branch below) —
the pack's mandatory exclusions must not persist after **successful graph purge**.
If `cbmignore_ownership = "merged"`: if a purge tombstone is present
(`graph-purge-pending` exists), **retain the sentinel-delimited exclusion block**
until the graph is successfully purged or unregistered — removing exclusions
while the graph is still live allows a later `index_repository` to ingest
credential paths that setup required to be excluded; **before deleting
`config.toml`**, write `cbmignore-cleanup.json` to `pack_dir("codebase-context")`
and a canonical pointer `codebase-context-cbmignore-pending` to
`user_state_path().parent` (same as the "created" branch above) — both are
**not** deleted by teardown's config-cleanup step; the post-purge cleanup
step applies the same tombstone acknowledgement flow as the "created" branch
above (check tombstone, verify or accept purge completion, delete tombstone,
then proceed); when the tombstone is absent or cleared, remove only the
sentinel-delimited block (preserving user-owned patterns) and then delete
both `cbmignore-cleanup.json` and the canonical pointer. Otherwise, remove only
the sentinel-delimited block added by setup (leaving user-owned patterns intact). For Serena setups: the
`.serena/project.yml` artifact per `config.toml [serena] project_yml_path` and
`project_yml_ownership`: if `"created"`, apply the same post-setup-user-content
inspection before offering to delete (check for keys other than `read_only:`);
if user content is found and the user declines full deletion, **remove the
setup-owned `read_only: true` field** (restore it to its pre-setup value per
`project_yml_prior_readonly`, or remove the line if absent) while preserving
the user-added keys — the checkout must not be left permanently read-only
because the user chose to keep their own additions;
if `"merged"`, restore the `read_only:` key to the value stored in
`project_yml_prior_readonly` (or remove the line if absent) — do not restore
the full file so post-setup user edits are preserved.
If `serena_dir_ownership = "created"` in `config.toml`: after removing or
restoring `project.yml`, if the `.serena/` directory is now empty, remove it
— setup created it and teardown must clean it up.
If `config.toml` has no `[serena]` section, skip this step.
**Before executing package-manager removal, persist the install route and the
current teardown phase** to a teardown journal (`<stable-state-dir>/teardown-
journal.json`, mode `0600`) recording `install_route` (always `"agentbundle"`),
`phase` (`"package-removal"`), and `stable_state_dir` (absolute path to the
stable state directory). **Also write a teardown locator**
(`codebase-context-teardown-locator`, mode `0600`) to `user_state_path().parent`
containing the absolute path to `<stable-state-dir>/teardown-journal.json` —
with a custom catalogue `user-dir`, a crash after `agentbundle uninstall`
succeeds removes both the adapter row (which locates the stable directory) and
the projected setup skill (which provides `uninstall.py`); without this locator
in the canonical `user_state_path().parent`, the teardown journal and
`uninstall.py` become undiscoverable for a retry. Delete the teardown locator
only after the teardown journal is deleted. The package-manager's own state row
is deleted when the command succeeds — if the process crashes after
`agentbundle uninstall` succeeds but before `config.toml` is deleted, the
agentbundle state row is gone and a retry can no longer resolve the route from
the package manager; it must read the persisted journal instead. Update the
journal phase to `"config-cleanup"` only after the package-manager command
succeeds; delete the journal only after `config.toml` and version stamps are
fully removed.

**Remove the projected pack files using agentbundle before deleting
`config.toml`, version stamps, or `uninstall.py`** — the pack requires the
`agentbundle install` route; `claude plugin install` is not supported (see
version-check section). The package-manager removal is fallible; if it fails,
teardown must be retryable, and a retry needs these files intact to resolve
hook/config paths and pass the self-version check:
- `agentbundle uninstall --pack codebase-context`
  **Idempotency on crash-retry:** if the teardown journal records phase
  `"package-removal"` and `agentbundle uninstall` exits nonzero with an
  error indicating the pack row is absent (not a permission error or network
  failure), treat the removal as having already succeeded — advance the
  journal to `"config-cleanup"` and proceed without re-raising. This makes
  the `package-removal` → `config-cleanup` transition idempotent across the
  crash window between them.
Only after the package-manager command succeeds (or is determined to be
already complete per the above), proceed to delete `config.toml`, version
stamps, and finally `uninstall.py` (self-deletion).

The backend binary is left in place. The user is responsible for manually
removing any launchd plist, systemd unit, or Task Scheduler entry they
created outside of `uninstall.py`'s scope.

Rollout owner: the pack author. No shared infrastructure; no deployment window.

**Testing.** `setup.py`'s install-detection, settings-write, hook-chaining,
overwrite-confirmation, wrapper construction (verifies `launch-backend.py` is
generated with `CBM_ALLOWED_ROOT` baked in, `"command"` is the durable
interpreter, `"args"` is `["-I", "<pack_dir>/scripts/launch-backend.py"]`, and
**no `"env"` block** is written), and wrapper isolation (the constructed minimal
environment contains only the required vars) logic is covered by mock-install
unit tests. The `codebase-memory-mcp` path (macOS
arm64) is the primary CI platform; Linux x86_64 via Docker. The `serena` path
has its own mock-install test verifying: `uv tool install` invocation (persistent
install), no hooks installed, no rebuild registered, Tier 3 LSP-liveness check
fires correctly. macOS x86_64 and Linux arm64 are manually verified on first
release.

**Windows first-release acceptance criteria (manual)**: `codebase-memory-mcp`
provides `windows-amd64` and `windows-arm64` binaries via PowerShell installer,
Scoop, Winget, and Chocolatey. Before claiming Windows support at release,
verify manually on a Windows machine: (a) binary installs via PowerShell
installer without admin rights; (b) MCP registration written correctly to
`~/.claude.json` — `"command"` is the durable system interpreter,
`"args"` is `["-I", "<pack_dir>/scripts/launch-backend.py"]`, no `"env"` block;
(c) `CBM_ALLOWED_ROOT` is baked into `launch-backend.py` and honored by the
binary (verify by confirming the binary process receives only the explicitly
constructed minimal environment, not the full inherited environment);
(d) liveness probe (`list_projects`) succeeds; (e) setup rerun idempotency.
A Windows CI job (GitHub Actions `windows-latest`) is the preferred gate;
accepted as manual on first release if CI is unavailable.

## Open Questions

The following questions must be answered before implementation begins. Each has
a recommended default and an owner/date.

**Resolved (CONFIRMED or CONTRADICTED — no longer blocking):**

- **HTTP transport + loopback binding** — CONTRADICTED. MCP is stdio-only
  (verified from source v0.9.1-rc.1). No HTTP MCP endpoint exists.
- **Bearer token enforcement** — CONTRADICTED. No auth in the binary. Security
  model is OS process isolation + `CBM_ALLOWED_ROOT`.
- **Non-argv token loading** — N/A. No token mechanism of any kind.
- **`"type": "http"` registration field** — CONTRADICTED. Registration is
  `{"command": "...", "args": []}` only.
- **Per-backend MCP tool names** — CONFIRMED. All 15 tools verified from
  `src/mcp/mcp.c`. Rebuild = `index_repository`; liveness = `list_projects`.
- **Backend rebuild idempotency** — CONFIRMED (serialized). `project_lock.c`
  implements two-level file-lock hierarchy; concurrent rebuilds on the same
  project are serialized, not corrupted. `fcntl.flock` not required.
- **Metadata-only vs. raw source output** — CONFIRMED. `get_code_snippet` and
  `search_code` return raw source; all other tools return metadata only.
- **Secret-exclusion + clean-index** — CONFIRMED (manual re-index required).
  `.cbmignore` (gitignore syntax) + `.gitignore` honored. Caller must invoke
  `index_repository` explicitly after updating exclusion rules.
- **Windows binary availability** — CONFIRMED. `windows-amd64` + `windows-arm64`
  in releases. Install via PowerShell script (not curl); Scoop/Winget/Chocolatey
  also supported. curl-based Unix install does not work on Windows.
- **Env var delivery to stdio MCP subprocess** — CONFIRMED. Official Claude
  Code MCP docs document `env` as a first-class field in the stdio server entry;
  the subprocess receives the `env` block contents. However, MCP stdio
  subprocesses **inherit the parent process environment by default** — shell
  secrets (`ANTHROPIC_API_KEY`, cloud credentials, arbitrary tokens) are passed
  to the backend. The MCP registration must use a generated minimal-environment
  wrapper as the primary isolation control (see transport section) — not the
  scrubber alone. `setup.py` checks `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` as
  defense-in-depth: because setup runs as a detached terminal command whose
  `os.environ` may differ from Claude Code's spawn environment, the check is a
  **warning** (not a hard refusal) — if absent from the terminal environment,
  setup emits a prominent warning and continues. Note: the scrubber covers
  designated Anthropic and cloud credentials but does not cover arbitrary tokens
  such as `GITHUB_TOKEN`. The `env` key also undergoes `${VAR}` expansion. Bugs #28332
  and #11927 affect `~/.claude/settings.json` — a different config path from
  this RFC's `~/.claude.json` format. Source: Claude Code MCP docs and
  env-vars reference.
- **Serena transport / startup contract** — CONFIRMED. Transport: stdio subprocess
  (default, recommended for per-workspace clients). Startup command:
  `serena start-mcp-server --context claude-code --project <absolute-path>`.
  Project root delivered via `--project` CLI flag (no env var mechanism).
  One process = one active project root (explicitly documented: "only one coding
  project can be active at a time"). MCP registration shape (wrapper-based, per
  transport section): `{"command": "<interpreter_path>", "args":
  ["-I", "<pack_dir>/scripts/launch-backend.py"]}` where the generated Python
  wrapper exec-s `serena start-mcp-server --context claude-code --project <absolute-path>`
  with a minimal environment. **Once D4 prerequisite (8) (serena metadata-only
  output verification) resolves, `launch-backend.py` must exec the sanitizing
  proxy rather than `serena` directly** — the proxy interposes between the
  launcher and `serena` to reject `find_symbol(include_body=True)` and block
  `search_for_pattern` calls; until then the raw-source tools are accessible
  and the serena path is blocked by the unresolved OQ. Install: `uv tool install -p 3.13 serena-agent`
  (PyPI package name is `serena-agent`; CLI executable is `serena`).
  Source: Serena docs (oraios.github.io/serena).
- **Serena PyPI provenance** — CONFIRMED (with package name correction). The
  `serena` name on PyPI is held by an unrelated AMQP library (v0.9.1, LGPL-3).
  The oraios semantic code analysis tool is published as `serena-agent`
  (https://pypi.org/project/serena-agent/; https://github.com/oraios/serena;
  MIT license; v1.6.1 released 2026-07-21). **All install references in this RFC
  must use `uv tool install -p 3.13 serena-agent`; the CLI executable after
  install is `serena`.** Installing `pip install serena` (without the `-agent`
  suffix) delivers the wrong package (an unrelated AMQP library).

**Blocking (must resolve before implementation):**

- **Serena read-only / config path verification [blocking prerequisite — serena
  only].** `read_only: true` in `<index-root>/.serena/project.yml` is the
  mechanism for disabling editing tools. The exact config path
  (`.serena/project.yml`) must be verified against the pinned `serena-agent`
  version: if Serena loads project configuration from a different path, setup
  and the launcher validate a file Serena never reads, leaving editing tools
  enabled. Project-level `excluded_tools` provides finer-grained control; note
  that a bug (oraios/serena#378) caused `excluded_tools` in the global
  `serena_config.yml` to raise a TypeError at startup — verify the project-level
  mechanism is unaffected. Source: Serena `project.template.yml`, Serena docs.
  *Owner:* pack author. *Decide by:* before first implementation PR for serena.

- **`CBM_ALLOWED_ROOT` enforcement verification [blocking prerequisite].**
  Verify, at the pinned backend version, that `CBM_ALLOWED_ROOT` actually
  rejects `index_repository` calls for paths outside the configured tree.
  If enforcement is not reliable, the pack cannot make scope-confinement
  guarantees. *Owner:* pack author. *Decide by:* before first implementation PR.

- **Serena metadata-only output verification [design-acceptance prerequisite —
  serena only].** PARTIALLY RESOLVED. Semantic symbol tools default to
  metadata-only (names, file paths, line numbers, symbol kinds, type signatures).
  Two specific surfaces return raw source and are **not** blocked by
  `read_only: true`:
  - `find_symbol(include_body=True)`: the `include_body` parameter returns the
    full implementation body. It is a per-call parameter, not a mode flag;
    `read_only: true` does not disable it.
  - `search_for_pattern` (regex grep): returns matched lines with surrounding
    context — raw source fragments.
  **Remaining requirement:** Implement a sanitizing proxy that rejects
  `find_symbol` calls with `include_body=True` and blocks `search_for_pattern`
  calls entirely (prompt-only instruction is insufficient for raw-source
  blocking per D4 acceptance criteria). The proxy-or-reject requirement from
  the `codebase-memory-mcp` raw-source tool allowlist applies to exactly these
  two serena surfaces. *Owner:* pack author.
  *Decide by:* before first implementation PR for serena.

- **Snapshot-isolated reads and atomic index replacement [blocking prerequisite
  — gates concurrent-rebuild query path].** Verify two related properties at
  the pinned backend version. (a) *Snapshot-isolated reads:* verify that
  `codebase-memory-mcp` provides snapshot-isolated reads when a rebuild is in
  progress. The two-level file lock (`project_lock.c`) serializes mutations but
  it is unclear whether read calls block or return partial data during an
  exclusive write lock. If reads block, querying during a live rebuild stalls —
  sessions must time-out and fall back. If reads return partial data, sessions
  that see `stale.claimed.*` must fall back to direct file reads.
  (b) *Atomic index replacement:* verify whether the backend writes a new index
  file via an atomic rename (temp-file → final path) or in-place (appending to
  or overwriting the existing file). This gates the freshness-skip optimization
  described in `§ Three-tier freshness`: with atomic replacement the mtime
  advances only on the rename (completion), making `index_mtime > stale_event_ns`
  a reliable freshness signal; with in-place writes the mtime advances on the
  first write (not completion), making the same check unsafe — a PLAN
  mid-rebuild would silently skip a needed rebuild. Until (b) is confirmed,
  the freshness skip is disabled and claims rebuild unconditionally.
  *Owner:* pack author. *Decide by:* before first implementation PR.

- **Cross-repo query scope [blocking prerequisite — gates first implementation].**
  PARTIALLY CONFIRMED: multiple repos index into the same `~/.cache/codebase-memory-mcp/`
  SQLite store, creating `CROSS_*` edges. `get_architecture` spans the full
  store. `trace_path` and `search_graph` are project-scoped but traverse
  `CROSS_*` edges within the store. UNCONFIRMED: whether `trace_path` can
  follow a `CROSS_*` edge in a single call without requiring two separate
  project-scoped queries. The `target_projects` parameter on `index_repository`
  is undocumented (not in README). **This is not gated on multi-repo use:**
  multi-repo support is a non-goal and that gate may never fire; even a
  single configured repository can return sibling-project metadata from
  `get_architecture`. Project-isolated query results are required before any
  implementation PR. *Owner:* pack author.
  *Decide by:* before first implementation PR.

- **Project-scoped purge / isolated fixture store [design-acceptance
  prerequisite — blocks canary setup phase].** The canary probe requires
  purging the fixture index after each run. Multiple projects share one SQLite
  store, so deleting the fixture index path could erase all projects' graphs.
  `CBM_ALLOWED_ROOT` is **source-path confinement** — it restricts which paths
  the backend indexes, but does not redirect where it writes the SQLite store.
  Pointing `CBM_ALLOWED_ROOT` at a temp source directory does NOT isolate the
  fixture from the production store; the backend will still write into the same
  shared data root. Verify: (a) whether `codebase-memory-mcp` provides a
  project-scoped purge command (e.g. a CLI or MCP tool that removes only one
  project's data from the store without touching other projects); (b) if not,
  whether the backend exposes a data-directory override (e.g. `CBM_DATA_DIR` or
  equivalent env var, or a CLI flag) that redirects the SQLite store itself to a
  temporary path — this is the only mechanism that can genuinely isolate the
  fixture from the production store. **If option (b) is the resolution, it must
  also be applied to the production installation** (not just the canary): the
  production store must reside in an isolated per-project path so that failure
  cleanup, exclusion-change rebuilds, and uninstall can safely delete it without
  touching other projects' data. An option-(b)-only resolution that leaves the
  production graph in the shared SQLite database cannot support safe teardown
  (direct database deletion is prohibited; no project-scoped API exists).
  If neither (a) nor (b) can be confirmed for production, the pack cannot
  implement safe teardown and must be deferred. Without (a) or (b), setup
  cannot safely run the canary phase. *Owner:* pack author.
  *Decide by:* before first implementation PR.

- **Repository-scope enforcement [design-acceptance prerequisite — security].**
  The user-scope MCP registration is callable from any Claude session regardless
  of which repository is open. `CBM_ALLOWED_ROOT` limits which root can be
  *indexed*, not which already-indexed project a session may *query*. A session
  in an attacker-controlled repository can call `trace_path` or `search_graph`
  against the indexed repo's graph without loading the skill's scope-gate
  instruction. Verify whether `codebase-memory-mcp` (at the pinned version)
  enforces per-call project scoping — e.g. validates the calling session's
  working directory against the registered project root — or whether
  project-scoped MCP registration (one entry per project, registered only when
  that project is active) is required. If neither is available, this backend
  must be rejected — D4 declares repository-scope enforcement a blocking
  prerequisite, and documenting or deferring the risk does not prevent a
  cross-repository graph disclosure.
  **Serena extension:** Serena's project-root argument limits *what* is served,
  not *who* may call it — a session in an unrelated repository can invoke
  serena's MCP tools against the registered project root. Verify whether
  project-scoped registration (one entry per project, active only when that
  project is open) or a caller-scope-enforcing proxy is available for serena;
  if neither is available, the serena path must be rejected on the same grounds
  as `codebase-memory-mcp` above. *Owner:* pack author.
  *Decide by:* before first implementation PR.

- **`codebase-memory-mcp` raw-source tool allowlist [design-acceptance
  prerequisite — security].** `get_code_snippet` and `search_code` are
  confirmed raw-source tools; all 15 tools are exposed via the MCP
  registration. The skill instructs the agent not to call raw-source tools,
  but this is advisory only — a prompt-injected session bypasses skill
  instructions and can retrieve source text including secrets. Verify whether
  the binary supports a tool-allowlist config option that excludes named tools
  from MCP registration. If no allowlist is supported: a sanitizing proxy
  between the backend and the MCP host is **required** — it must either suppress
  raw-source tools entirely (removing them from the MCP tool registration so
  they are never callable) or irreversibly reduce their output to a fixed
  metadata schema (symbol names, file paths, line ranges only). A proxy that
  only strips or encodes/escapes text is **not** sufficient: a model capable of
  decoding the transformation still receives the original instructions and secret
  bytes. Documentation of accepted risk is not a valid substitute. If neither an
  allowlist nor a compliant sanitizing proxy is feasible, this backend must be
  rejected. *Owner:* pack author. *Decide by:* before first implementation PR.

- **`codebase-memory-mcp` offline CLI rebuild command [design-acceptance
  prerequisite — canary and purge/rebuild sequences].** The canary phase and
  the purge/rebuild recovery sequence require stopping the daemon and running a
  rebuild without it. Verify whether `codebase-memory-mcp` exposes an offline
  CLI rebuild command (i.e. one that can rebuild a project index without the
  daemon running). If only the daemon-backed MCP `index_repository` tool
  supports rebuilding, the daemon-stopped offline rebuild in the canary and
  recovery sequences cannot be implemented; redesign those sequences to work
  around the constraint or require the daemon to be running. *Owner:* pack author.
  *Decide by:* before first implementation PR.

**Conditional (resolve before the relevant feature):**

- **Multi-project / knowledge-space isolation [multi-project use only].**
  Single config.toml
  supports one index root. For users with multiple projects or multi-repo
  projects: (a) define the per-project config profile model (multiple
  config.toml files? `setup --profile <name>`?); (b) define how
  `CBM_ALLOWED_ROOT` is updated per-profile; (c) clarify whether a single
  Claude session can switch profiles mid-conversation. *Owner:* pack author.
  *Decide by:* before first implementation PR for multi-project scenarios.

- **Context re-priming at compaction [design extension].**
  When Claude Code compacts a conversation, earlier graph context is lost.
  A `UserPromptSubmit` hook (or equivalent per adapter) could detect the
  compacted state and call `get_architecture` to re-prime. Verify: (a) which
  Claude Code hook events are available and whether any signals a compaction;
  (b) which other adapters (Kiro, Cursor, Copilot) support equivalent hook
  events; (c) whether adapter hook events are installable from a pack
  (currently hooks.json is user-managed). *Owner:* pack author.
  *Decide by:* before shipping the context re-priming feature.

**Recommended defaults (can be changed by implementer):**

- **Rebuild duration.** Assume ≤2 minutes for a 50k-line repo; use 5-minute
  lease timeout as a conservative default. Measure empirically and adjust.

- **Backend rebuild concurrency safety.** CONFIRMED serialized (not concurrent).
  `project_lock.c` prevents parallel rebuilds on the same project. Assume
  `codebase-memory-mcp` does NOT coalesce — claim and rebuild unconditionally
  until atomic index replacement is confirmed.

- **`codebase-memory-mcp` Windows install.** CONFIRMED. Use PowerShell
  installer (`install.ps1`) or Scoop/Winget/Chocolatey. Do NOT use the Unix
  curl-pipe installer on Windows. `windows-amd64` + `windows-arm64` artifacts
  in GitHub Releases.

- **`post-checkout` as Tier 2 trigger.** Retain; remove only if the file
  watcher is confirmed to cover all pull strategies.

- **Correct MCP settings file.** CONFIRMED: `~/.claude.json` (not
  `~/.claude/settings.json`). This is treated as the authoritative path
  throughout the RFC (§ Transport, env-var delivery OQ). Verify is complete.

- **PLAN-time liveness probe.** CONFIRMED: use `list_projects`. Lowest-cost
  read tool; no dedicated ping tool exists in the backend.

- **Serena pinned version.** Pin to a specific version in `pack.toml` and
  `SKILL.md` before shipping. The exact version determines tool names and flags.

- **`pack_dir()` API contract.** Verify `agentbundle.config.pack_dir` signature
  and `agentbundle.safety.user_state_path()` against the pinned agentbundle
  version before implementing `setup.py`.

- **Agentbundle shared write lock for `~/.claude.json`.** Use the facility if
  it exists; skip if absent. Verify before implementing `setup.py`.

- **Core extension-point RFC.** Follow-on, not a blocker for this RFC.
