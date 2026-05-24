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

**Last updated:** 2026-05-23 (adapt-to-project AC4b automation pins land)

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
recorded via PR #21. AC8 (`AGENTS.md` composition) is closed: Codex
now aggregates skills across packs before splicing the managed block,
and self-host composes root `AGENTS.md` from the core body seed, the
Codex-managed block, and the core footer fragment.

- **Comparison-rule strengthening.** Today's `diff_against_working_tree`
  uses `read_bytes()` equality. Phase 2 strengthens this to byte-for-byte
  after CRLF→LF normalisation, with file-mode bits compared for regular
  files and symlink targets compared via `lstat` (never follow symlinks).

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
- **Rail C grep widening to canonical syntax — paired with AC21 of
  adapt-to-project.** The spec text (line ~342 and the contract-load-
  bearing AC near line ~759) widens to also match the canonical
  lowercase-hyphen form per `adapt-to-project/spec.md` AC21. The
  code-side widening of the Rail-C validate-time grep is deferred per
  AC21's carve-out; until then, a user-scope pack carrying lowercase-
  hyphen markers passes `validate` in code even though the contract
  refuses it. Unblocks when `distribution-adapters`'s next
  implementation pass picks up the widened AC.

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

## `adapt-to-project` — drafted

Spec: [`specs/adapt-to-project/spec.md`](specs/adapt-to-project/spec.md).
Drafted per RFC-0001 § *Post-install adaptation* and RFC-0004 § *Drawbacks
→ `adapt-to-project` discovery doubles its artifact surface*. Cross-
references: `self-hosting`, `agent-spec-cli`, **and RFC-0004**.

The v1 implementation lands the typed `AdaptDiscovery` schema, the
`adapt`/self-host consumers' migration from legacy `[accepted]` /
`[adapt]` tables to canonical `[markers]`, install-gate enforcement
of `[pack.dependencies.required]`, the install→adapt marker-write +
chained in-process `adapt.run`, the session-start hook's dual-scope
marker walk, and the SKILL.md body authoring (class-1 shell-out;
classes 2–4 LLM-judgment writes under the per-scope path-jail).

- **Security: TOML-injection via unescaped pack metadata
  (pre-existing).** `dump_state` and `_append_install_marker`
  interpolate `pack.name` / `version` / projection relpaths into
  TOML output via plain f-strings. A malicious pack manifesting a
  `version` string containing TOML metacharacters can land phantom
  TOML structure in `<repo>/.agent-ready-state.toml` and
  `.adapt-install-marker.toml`. Pre-existing in `config.dump_state`;
  amplified by the install-marker addition. **Unblocks when:** the
  catalogue trust model formalises (today's CLI assumes trusted
  catalogues); fix shape is a tested `_emit_basic_string`
  serialiser + a runtime regex assertion on every pack-sourced
  field that lands in a TOML basic-string position.
- **APM / Claude-plugins install-route nudge parity.** Adopters
  installing via APM or Claude-plugins routes (rather than
  `agentbundle install`) never hit the install marker write, never
  see the session-start nudge, and never get the chained
  `adapt.run`. The spec is explicit (CLI-only contract), but the
  RFC-0004 parity work would close this gap. **Unblocks when:**
  APM/Claude-plugins adapter parity lands.
- **Install-marker `new-companions` tally.** `commands/install.py`'s
  install loop classifies Tier-2 collisions on the fly and doesn't
  keep a tally; `_append_install_marker` writes `new-companions = []`
  unconditionally. The spec's install-marker schema example names
  this field as load-bearing, but the session-start nudge doesn't
  surface companion paths in v1. **Unblocks when:** the first Tier-2
  collision needs to surface through the install→adapt nudge — at
  that point, capture the relpaths during the step-9 write loop and
  pass them through.
- **AC4b — deferred manual-QA rows (three trigger classes).**
  v1 ships the AC4a automation/grep rows; AC4b enumerates 21 rows
  deferred under three trigger classes (see
  `notes/manual-qa-matrix.md` for the canonical per-row table):
  - **Repo-scope class-2 transcripts (rows 8–11).** Brownfield
    fixture seeds the `AGENTS.upstream.md` surface; only the inline
    transcripts are deferred. *Trigger:* follow-up captures an
    adopter session against `brownfield-adapt/AGENTS.upstream.md`
    and attaches transcript + tree fragment inline.
  - **Repo-scope class-3 transcripts (rows 12–14).** *Trigger:*
    brownfield fixture seeds a class-3 surface (e.g., overlapping
    `DESIGN.md` + `docs/CHARTER.md`) and an adopter session is
    captured.
  - **Repo-scope class-4 transcripts (rows 15–16).** *Trigger:*
    brownfield fixture seeds a class-4 surface (overlapping
    `docs/howto/` + `docs/guides/how-to/`) and an adopter session
    is captured.
  - **Cross-cutting end-to-end transcripts (rows 17–18).**
    *Trigger:* follow-up captures interactive adopter sessions for
    dirty-state-repo and Tier-2 detection-repo.
  - **User-scope LLM-judgment rows (rows 19–28).** *Trigger:* first
    pack declaring `allowed-scopes = ["user"]` lands (RFC-0004 §
    *Drawbacks* + *Unresolved questions*).

---

## Cross-spec / outside-the-spec-tree

These are open items called out by accepted RFCs or by multiple specs,
but don't have a spec of their own yet.

- **F-conformance fixtures (RFC-0003).** The per-adapter conformance
  suite that `agentbundle validate --strict` would consume. RFC-0003
  scoped this out of v1; needs its own spec when prioritised.
