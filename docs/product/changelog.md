# Changelog

All notable user-visible changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Maintenance: this file is updated in the same PR that introduces the
> change. CI will warn (configurable: block) when a PR touches code that
> changes user-visible behavior but does not touch this file.
>
> Entries can be drafted from conventional commits: `git log --oneline`
> filtered to `feat:` and `fix:` since the last tag is a starting point,
> not a finished product. Rewrite for users, not contributors. See the
> [Common Changelog guidance](https://common-changelog.org/) — the audience
> is humans who use the software, not humans who wrote it.

## [Unreleased]

### Added

- **The repo now has a SAST/SCA gate** — `make sast` runs **Bandit** (Python pattern SAST),
  **pip-audit** (dependency/SCA), **Semgrep** (cross-cutting SAST, including custom `mode: taint`
  rules under `tools/semgrep/`), and a **CodeQL** code-scanning workflow (deep interprocedural
  taint — the open-source analogue of Snyk Code). The first three are chained into
  `make build-check` so every PR is scanned by the repo's own single native gate (locally and in
  `build-check.yml` CI); CodeQL runs as its own workflow. Bandit fails on medium-or-higher findings
  (tuning in `bandit.yaml`). The genuine findings surfaced were fixed in the same change: weak SHA-1
  digests marked `usedforsecurity=False`; the arXiv retriever upgraded to HTTPS; the `session-start`
  hook's env-var path overrides sanitized against directory traversal (a fix every adopter inherits);
  and the SSO broker's `test` verb now rejects non-`http(s)` URL schemes. A committed `.snyk` policy
  file is the Snyk-native suppression vehicle for the organisational scan. All four scanners are
  CI-only dev tools (`tools/requirements-sast.txt`) and are **never** added to a shipped package's
  runtime dependencies. See ADR-0017.

- **Gemini CLI is now a full-parity adapter** — `agentbundle install --adapter gemini` (repo or
  user scope) projects every catalogue primitive to Gemini CLI's native `.gemini/*` layout:
  skills → `.gemini/skills/`, subagents → `.gemini/agents/<name>.md` (the `tools:` allowlist is
  **kept** and name-mapped to Gemini's tool ids — `Read`→`read_file`, `Bash`→`run_shell_command`,
  … — and `model` maps tier-preserving to the Gemini 2.5 line), commands →
  `.gemini/commands/<name>.toml`, and hook bodies → `.gemini/hooks/` with the wiring + a managed
  `context.fileName = ["AGENTS.md", "GEMINI.md"]` bridge merged into `.gemini/settings.json` so the
  canonical `AGENTS.md` is read. Every pack admits `gemini` at both scopes. Previously Gemini CLI
  got nothing (it doesn't read `AGENTS.md` by default). Contract v0.12 → v0.13 (RFC-0027 /
  ADR-0016). Distribution-only.
- **Cursor can now install the `research` and `architect` packs** — both packs added `cursor`
  to their `allowed-adapters`, so `agentbundle install --pack research --adapter cursor` (and
  `--pack architect`) now projects their skills to `.cursor/skills/` — and, for `research`, the
  two retrieval subagents to `.cursor/agents/` with `readonly: true` — instead of refusing the
  install up front. The Cursor adapter shipped in the previous release, but no pack had opted
  in. (The credentialed packs are covered by the next entry.)
- **Credentialed packs can now install via Cursor and Copilot** — `atlassian`, `contracts`,
  `converters`, `figma`, and `credential-brokers` added `copilot` + `cursor` to their
  `allowed-adapters`, so a Cursor- or Copilot-based adopter can install them (and the SSO/token
  broker lands at `~/.agentbundle/bin/` as before — the broker delivery is adapter-independent).
  Previously these packs admitted only `claude-code`, `kiro-ide`, and `codex`. Recorded as an
  RFC-0013 § Errata decision; no contract change (both adapters already declare the
  `.agentbundle/` install prefix the broker needs).
- **`--dry-run` previews an install or upgrade without writing anything** —
  `agentbundle install --dry-run` and `agentbundle upgrade --dry-run` run the
  full read-only pre-flight, print a per-file plan to stdout (one
  `<action> <tier> <target>` line each — `create` / `overwrite` /
  `companion`, with Tier-2 lines naming the `.upstream.<ext>` companion the
  real run would drop), and exit 0 without touching the tree, state, or
  install marker. A present Tier-2 collision does not change the exit code;
  the preview is informational. `install --dry-run --force` is refused
  (`--force`'s destructive cleanup is incompatible with a read-only preview).
  The install preview covers the rendered adapter projection; it does not yet
  enumerate the governance seeds (`AGENTS.md`, `docs/CHARTER.md`,
  `docs/CONVENTIONS.md`) a real install also delivers. See the
  [preview how-to](../guides/how-to/preview-install-or-upgrade.md).

### Changed

- **`agentbundle upgrade` tells you when it keeps your edits** — when a
  projected file you edited since install collides with the new version
  (Tier-2), the upgrade preserves your file and drops the upstream version
  as a `<path>.upstream.<ext>` companion, exactly as before. It now also
  prints, on stderr after the upgrade commits, how many files were kept
  and the companion path of each — so you can find them and run
  `adapt-to-project` to merge. Parity with what `install` already reports;
  no change to the file-safety contract (the CLI still never clobbers or
  prompts). Per
  [RFC-0001 § Errata (2026-06-11)](../rfc/0001-bundle-distribution-by-adapter-spec.md#errata),
  which reconciles the original draft's unbuilt in-CLI Tier-2 prompt with
  this deterministic companion-drop design.

- **Leaner work-loop context use, same rigor** — the review reviewers
  (`adversarial-reviewer`, `security-reviewer`, `quality-engineer`) now return
  only their distilled findings block (or `Clean — ready to commit.`), with no
  pre-findings methodology recap or process narration. The `work-loop` skill
  drops the full reviewer report from resident context once findings are
  recorded — the on-disk report plus `state.json` fingerprints are the durable
  record — and gains a `## Context hygiene` section with three context-saving
  levers (reference-read reduction, task-boundary compaction, narrowest-gate
  during FIX), each with a portable no-subagent floor, plus a "reduce, never
  lossily transform" guardrail. No verification surface changes: gates, the
  iterate-to-Clean loop, fingerprint stasis detection, the quality-engineer
  floor, and the iteration cap all behave exactly as before. See
  [`docs/specs/work-loop-context-hygiene/`](../specs/work-loop-context-hygiene/spec.md).

- **Codex receives full skill bodies** — the `skill` projection for the
  Codex adapter flips from `managed-block-inline` (one-line teasers
  in `AGENTS.md` between `<!-- agent-skills:start -->` /
  `<!-- agent-skills:end -->`) to `direct-directory`. Codex users now
  read `.agents/skills/<name>/SKILL.md` byte-equal to source — the
  same surface Claude Code and Kiro have always had. Per
  [RFC-0009 § Adapter contract change](../rfc/0009-codex-native-skills.md#adapter-contract-change).
  On the first install after upgrade, the adapter strips the
  legacy `<!-- agent-skills:start --> … <!-- agent-skills:end -->`
  region from any pre-existing `AGENTS.md` in place; outside-block
  content is preserved. The strip is destructive by design: hand-
  edited content *between* the delimiters is not migrated
  (RFC-0009 § Failure modes). The strip mechanism
  (`_strip_legacy_skill_block` + the retained `_splice_managed_block`
  helper) is kept for one minor release as the migration window
  (released N) and then removed in the release after (N+1).
  **Self-host mirrors Codex repo projection.** The self-host allow-list
  includes both `claude-code` and `codex`, so this repo now carries
  Codex's repo-scope projection alongside Claude Code: `.agents/skills/`
  for full skill bodies, `.codex/agents/` for subagent TOML, and
  `.codex/hooks.json` for hook wiring. `make build-check` enforces those
  paths the same way it enforces `.claude/`.

- **Uniform multi-pack entry point across `direct-directory` adapters**
  — `codex`, `claude-code`, and `kiro` all expose
  `project_packs(pack_paths, contract, output_root)` as the
  canonical orchestrator-facing surface. Single-pack `project()`
  is retained as a wrapper. Same-name skill collisions across
  packs resolve deterministic-last-wins by source-order.

- **Orphan-skill cleanup across `direct-directory` adapters** — after
  every multi-pack `project_packs(...)` call, the projected skill
  directory is swept: child directories whose names are not in the
  union of source skill names across the call's pack list are
  removed. Bound to the `skill` primitive only; symlinks are
  removed via `Path.unlink()` (never followed).

### Deprecated

- (nothing yet)

### Removed

- (nothing yet)

### Fixed

- (nothing yet)

### Security

- (nothing yet)

<!--
## [1.0.0] — YYYY-MM-DD

### Added
- Initial public release.

[Unreleased]: https://github.com/<org>/<repo>/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/<org>/<repo>/releases/tag/v1.0.0
-->
