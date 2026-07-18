# ADR-0051: workspace.toml: TOML format and main-branch direct spec targeting

- **Status:** Accepted
- **Date:** 2026-07-18
- **Decision-makers:** eugenelim
- **Supersedes:** none (supersedes the umbrella-branch coordination pattern adopted in the 2026-07-18 workspace.toml design session — that session settled the artifact's existence and three-queue schema; this ADR records the format and branching decisions resolved in the same RFC)
- **Related:** [RFC-0064](../rfc/0064-ini-001-ai-native-ecosystem.md) — governing RFC; decisions D2 and D4

## Decision summary

- **Decision:** `workspace.toml` is a TOML file committed on `main`; spec branches target `main` directly; each spec PR updates `workspace.toml` in the same diff; no umbrella branch.
- **Because:** TOML's named sections, typed lists, and inline comments are purpose-fit for a programmatically-read multi-initiative queue; the fast-merge model eliminates the only problem an umbrella branch solves (long-lived in-flight coordination), making the umbrella purely overhead.
- **Applies to:** the `workspace.toml` in-repo coordination artifact introduced by RFC-0064 (INI-002 scope and any future initiative using the same pattern).
- **Tradeoff accepted:** TOML is a second format alongside the Markdown-everywhere convention; skills and adopters must understand both. Main-branch workspace.toml means concurrent spec PRs must each carry a compatible `workspace.toml` edit — rebase conflicts on this file, though trivially resolved (each spec touches a different TOML entry), become routine.
- **Revisit if:** a TOML parser incompatibility surfaces in a supported harness or agent environment, making Markdown+frontmatter the only portable option; or if concurrent spec PRs routinely produce `workspace.toml` conflicts that are *not* trivially resolved (evidence that the parallel-spec model has outgrown the single-file assumption).

## Context

RFC-0064 (INI-001 AI-Native Ecosystem — Platform Core) establishes `workspace.toml` as the in-repo declared-intent coordination artifact: a file that holds three queues (shaping, brief, and work) per initiative and is read by skills (`check-workspace`, `work-loop`, `receive-brief`, `author-brief`) at session start and on ship.

Two decisions gated implementation:

**D2 — Format.** Skills read `workspace.toml` programmatically. The file's structure is inherently nested (per-initiative named sections, per-section typed lists, inline comments explaining entry semantics) and grows to hold multi-initiative parallel state. Markdown+frontmatter — used by every other artifact in `docs/product/` — keeps YAML frontmatter flat; arbitrary nesting requires a custom parser the existing `receive-brief` / `work-loop` skills do not have. TOML is structurally equivalent to the use case: named tables (`["ini-002".work]`), typed arrays, and inline comments are first-class language features, not bolted-on conventions.

**D4 (revised) — Git coordination pattern.** An earlier design session (2026-07-18) considered keeping spec branches targeting a long-lived initiative umbrella branch, merging to `main` in batches when a milestone ships. The umbrella pattern is established in large OSS projects (Linux kernel topic branches, Shopify release cycles) precisely because it solves multi-contributor, long-lived in-flight coordination. That problem does not exist here: specs in this repo are short-lived (days to weeks), each touching a *different* TOML entry in `workspace.toml`. The coordination benefit of an umbrella branch is zero; its cost — branch management overhead, merge ceremonies, delayed feedback — is real. The revised D4 drops the umbrella entirely.

## Decision

**D2 — Format: `workspace.toml` uses TOML.**

`workspace.toml` is a TOML file. Its schema uses TOML named tables for per-initiative sections (`["ini-002"]`, `["ini-002".work]`, etc.), TOML arrays for queue entries, and TOML inline tables for dependency-bearing entries (`{path = "spec/m1-workspace-core", needs = "..."}`). The full schema is defined in RFC-0064 § Proposed design.

Markdown+frontmatter is **not** used for this artifact, despite being the convention for every other artifact in `docs/product/`. The exception is justified by the programmatic-read requirement: TOML's native nested-table and typed-array support removes the custom-parser burden from every skill that reads the file.

**D4 (revised) — Git coordination pattern: `workspace.toml` on `main`, spec branches direct-to-main.**

`workspace.toml` lives on `main` as a repo-level artifact. Spec branches target `main` directly (no umbrella branch). Each spec PR includes a `workspace.toml` edit in its diff, moving the corresponding queue entry from `queue` to `active` (when starting) and from `active` to `shipped` (on merge). Because concurrent specs touch different TOML entries, rebase conflicts on this file are mechanically resolvable without human judgment.

The umbrella-branch pattern considered in the 2026-07-18 design session is rejected for this use case (see Alternatives considered).

## Decision drivers

- **Programmatic readability.** Skills read `workspace.toml` at every session start; the format must be parseable by Python's standard `tomllib` / `tomli` without a custom parser.
- **Native nested-section support.** The three-queue, multi-initiative schema requires per-initiative named sections — a first-class TOML feature that has no Markdown+frontmatter equivalent.
- **Fast-merge model.** Short-lived spec branches (days to weeks) mean long-lived umbrella branches solve a coordination problem that doesn't exist here.
- **Trivial conflict resolution.** Each spec PR touches a different TOML key; concurrent-spec rebase conflicts are structurally guaranteed to be non-overlapping and resolvable with `--ours` or simple inspection.
- **No execution state in git.** `workspace.toml` records declared intent only; actual execution state lives in the harness platform (Devin, Manus, GitHub Copilot all confirm this pattern). This keeps the file stable enough to be a committed main-branch artifact.

## Consequences

**Positive:**
- Skills parse `workspace.toml` with `tomllib` (stdlib in Python 3.11+; `tomli` backport for earlier versions) — no custom parser authored or maintained.
- TOML inline comments (`# Batch 3 — after workspace-core`) let the file be self-documenting without polluting the data structure.
- `workspace.toml` on `main` is always present after Batch 2 ships; `check-workspace` and related skills need no branch detection or `git show` — they read the local file.
- Spec PRs carry their own queue-state update; the workspace state is always synchronized with the committed tree.
- No umbrella branch means no merge ceremony, no batch-ship coordination, no stale umbrella branch to clean up.

**Negative:**
- TOML is a second format in the repo; contributors and skills must understand both TOML (for `workspace.toml`) and Markdown+frontmatter (for every other `docs/product/` artifact).
- Python 3.10 and earlier require `tomli` as a dependency (`pip install tomli`); skills that need to support those versions must declare the backport.
- Concurrent spec PRs each carry a `workspace.toml` edit; while conflicts are trivially resolved, they are routine when multiple specs are in flight simultaneously.
- `workspace.toml` as a single file is a coordination bottleneck at scale (50+ active specs across many initiatives). The RFC-0064 Known Unknowns section flags `portfolio.toml` as a follow-on artifact for that scale; this decision is not load-bearing past that threshold.

**Revisit if:** a TOML parser incompatibility surfaces in a required harness environment; or concurrent `workspace.toml` conflicts are routinely non-trivial (evidence the parallel-spec volume has outgrown the single-file assumption, triggering a `portfolio.toml` or per-initiative-file follow-on RFC).

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** every skill that reads `workspace.toml` uses `tomllib.loads()` (Python 3.11+) or `tomli.loads()` (backport); no skill parses the file as Markdown or YAML. Spec PRs that update queue state include a `workspace.toml` diff. No umbrella branches appear in the repository for initiative coordination.
- **Owner:** eugenelim

## Alternatives considered

**Markdown+frontmatter (`workspace.md`).** Every other `docs/product/` artifact uses Markdown+frontmatter. Rejected: YAML frontmatter is designed for flat key-value; the three-section, multi-initiative nested structure requires a custom parser. TOML handles this natively and without additional tooling.

**State branch for `workspace.toml`.** A dedicated `state/<slug>` branch holding execution state. Rejected: no established git precedent; breaks rebase and PR workflows; contradicts the platform-owns-execution-state finding (Devin, Manus, GitHub Copilot all store live execution state in the platform, not git).

**Initiative umbrella branch.** Keep spec branches targeting a long-lived `initiative/<slug>` umbrella branch; batch-merge to `main` on milestone ship. Considered and rejected: the umbrella solves multi-contributor, long-lived in-flight coordination — a problem that does not arise when specs are short-lived and each touches a different TOML key. The cost (branch management, merge ceremonies, delayed feedback on `main`) is real; the benefit is zero at this repo's scale and spec cadence. Consistent with the no-long-lived-branches principle.

**Per-initiative file (`workspace-ini-002.toml`).** Separate TOML file per initiative. Rejected for now: `check-workspace` resolves cross-initiative dependencies (`ini-002:work:...`); a single file makes the DAG resolution trivial. The `portfolio.toml` follow-on RFC (RFC-0064 Known Unknowns) covers the scale threshold where per-initiative files earn their cost.

## References

- [RFC-0064 § Decisions](../rfc/0064-ini-001-ai-native-ecosystem.md) — D2, D4, and the full alternatives analysis.
- [RFC-0064 § Proposed design — `workspace.toml` schema](../rfc/0064-ini-001-ai-native-ecosystem.md) — schema details including named-section format and `needs` prefix notation.
- [RFC-0064 § Known unknowns — portfolio coordination](../rfc/0064-ini-001-ai-native-ecosystem.md) — the `portfolio.toml` follow-on for 50+ initiative scale.
