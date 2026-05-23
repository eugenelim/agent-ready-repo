# Roadmap — open items by spec

Single index of open work across every spec in `docs/specs/`. Each open
item names the spec, the Acceptance Criterion (where one applies),
what's blocking it, and how it gets unblocked.

This file is governance about *this repo's* evolution, not adopter
scaffolding. The adopter-facing product roadmap template lives at
[`product/roadmap.md`](product/roadmap.md) (a *Projected* path
sourced from `packs/core/seeds/`). This file is per-instance: it lives
on disk here, has no pack-side source, and surfaces as an `[info]`
line under `make build-check` per AC6 of the self-hosting spec.

For shipped work, see [`product/changelog.md`](product/changelog.md)
and each spec's own Changelog section.

**Last updated:** 2026-05-23

## How this file is maintained

- Every spec records its own `Status:` field and `Acceptance Criteria`
  checkboxes. This file aggregates the open items so they're visible in
  one place — it is not the source of truth.
- When a spec ships or an AC closes, update the spec first, then update
  the relevant entry here in the same PR.
- When a new spec lands, add a section for it here even if every AC is
  open (so the file stays a complete index).
- If an item here is no longer accurate against the underlying spec,
  trust the spec and fix this file.

---

## `self-hosting` — Phase 1 shipped; Phase 2 pending

Spec: [`specs/self-hosting/spec.md`](specs/self-hosting/spec.md).
Phase 1 cutover landed via PR #18; AC3 closed by PR #20; AC1b artifact
recorded via PR #21. The remaining work is Phase 2.

- **AC8 — `AGENTS.md` composition.** Project root `AGENTS.md` as
  `packs/core/seeds/AGENTS.md` (body) + `packs/core/seeds/_agents-footer.md`
  (footer) via the `composite-agents-md` recipe.
  **Blocked on:** Codex adapter's last-pack-wins managed-block splice —
  multi-pack aggregation overwrites instead of composes.
  **Unblocks by:** fixing the Codex multi-pack splice in the build
  pipeline, then wiring the `composite-agents-md` runtime.
- **Composite recipe runtimes.** `per-pack-overlay`, `composite-agents-md`,
  and `composite-marketplace` currently ship as metadata-only TOML stubs.
  Phase 2 lands the runtime that drives seed-projection composition,
  AGENTS.md body+footer composition, and root-marketplace aggregation
  from per-pack manifests.
- **Comparison-rule strengthening.** Today's `diff_against_working_tree`
  uses `read_bytes()` equality. Phase 2 strengthens this to byte-for-byte
  after CRLF→LF normalisation, with file-mode bits compared for regular
  files and symlink targets compared via `lstat` (never follow symlinks).
- **Self-host adapter allow-list.** Phase 1 restricts `make build-self`
  to the `claude-code` adapter. Phase 2 re-adds `codex` to
  `SELF_HOST_ADAPTERS` once the multi-pack aggregation fix lands so
  AGENTS.md's managed block can project correctly.

## `distribution-adapters` — shipped (v0.2 contract bump landed)

Spec: [`specs/distribution-adapters/spec.md`](specs/distribution-adapters/spec.md).
Shipped via the build-pipeline PRs that introduced
`packages/agentbundle/agentbundle/build/` and the four reference
adapters. The [RFC-0004](rfc/0004-install-scope-per-pack.md) v0.2
amendment (install-scope dimension; `[scope]` table on the adapter
contract; `[pack.install]` table on `pack.toml`; user-scope refusal
rails A/B/C; state-file v0.2 + `init-state --migrate`; four shipped
packs declare `[pack.adapter-contract] version = "0.2"`) landed in
the same PR; ACs #14–#18 are satisfied.

- *No open items of substance.* The pre-amendment ACs (#1–#13) carry
  the same bookkeeping drift documented above — checkboxes are still
  literally `- [ ]` against shipped code. Same as `agent-spec-cli`:
  reconciliation work, not new scope.

## `agent-spec-cli` — shipped (v0.2 CLI surface landed)

Spec: [`specs/agent-spec-cli/spec.md`](specs/agent-spec-cli/spec.md).
Shipped via PR #23 (commit `cd4f3e5`) — 11 subcommands, library-first
CLI importing `agentbundle.build`. The
[RFC-0004](rfc/0004-install-scope-per-pack.md) v0.2 amendment
(argparse `--scope` on six subcommands + `--force` on `install`;
scope-resolution helper; path-jail per scope; `~`-expansion refusal;
v0.1 state-file refuse-and-explain at write; dual-scope install
conflict + `installed: <pack> @ <scope>` rail; `recommends`
cross-scope warning text split; `adapt` dual-state-file walk) landed
in the same PR; the ten `(RFC-0004)`-tagged ACs are satisfied.

- *No open items of substance for v1.* Same AC-checkbox bookkeeping
  drift as `distribution-adapters`: a follow-up PR should reconcile.
- **Deferred to a follow-up RFC** (called out in RFC-0004 itself, not
  net-new scope): user-scope hook-wiring merge story (Rail B keeps
  hook-bearing packs user-scope-refused until that lands); `global`
  (system-wide) scope (not reserved, not refused — absent); new
  user-scope packs (the dimension lands without a consumer).
- **Deferred to v1.1** (carried over from the prior roadmap entry):
  SSH git URL support in `install` (`git+ssh://...` currently exits
  non-zero with a "deferred to v1.1" message); the full `--strict`
  `validate` behaviour against the v0.1 conformance fixtures (which
  themselves are owned by RFC-0003's deferred F-conformance task).

---

## Cross-spec / outside-the-spec-tree

These are open items called out by accepted RFCs or by multiple specs,
but don't have a spec of their own yet.

- **`adapt-to-project` skill.** Deferred per RFC-0001 Open Q3 and
  referenced by both `self-hosting` and `agent-spec-cli`. Owns
  `<adapt:NAME>` marker resolution for plugin-installed packs and
  materialises `.adapt-discovery.toml` from a repo's concrete values.
  Skill stub exists at `.claude/skills/adapt-to-project/SKILL.md` (per
  the skills index); the resolver itself is not implemented.
- **F-conformance fixtures (RFC-0003).** The per-adapter conformance
  suite that `agentbundle validate --strict` would consume. RFC-0003
  scoped this out of v1; needs its own spec when prioritised.
