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

**Last updated:** 2026-05-24 (closed `skill-secrets` — all T1–T13c shipped; status flipped Draft → Shipped; only AC34/AC35 inheritance invariants and the post-implementation "Credential storage" ADR remain as cross-spec items)

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

## `self-hosting` — shipped (Phase 1 + Phase 2 closed)

Spec: [`specs/self-hosting/spec.md`](specs/self-hosting/spec.md).
Phase 1 cutover landed via PR #18; AC3 closed by PR #20; AC1b artifact
recorded via PR #21. AC8 (`AGENTS.md` composition) closed by the
2026-05-23 Codex multi-pack aggregation pass. Phase 2's comparison-rule
strengthening — CRLF→LF normalisation for text-like files, file-mode
permission-bit comparison for regular files, and symlink-target
comparison via `lstat` (never following) — closed by PR #34. No open
items.

## `distribution-adapters` — shipped (v0.2 contract bump landed)

Spec: [`specs/distribution-adapters/spec.md`](specs/distribution-adapters/spec.md).
Shipped via the build-pipeline PRs that introduced
`packages/agentbundle/agentbundle/build/` and the four reference
adapters. The [RFC-0004](rfc/0004-install-scope-per-pack.md) v0.2
amendment (install-scope dimension; `[scope]` table on the adapter
contract; `[pack.install]` table on `pack.toml`; user-scope refusal
rails A/B/C; state-file v0.2 + `init-state --migrate`; four shipped
packs declare `[pack.adapter-contract] version = "0.2"`) landed in
the same PR; ACs #14–#18 are satisfied. The AC21 carve-out (code-side
Rail-C grep widening to the canonical lowercase-hyphen form) closed
by PR #33: `_MARKER_REGEX` in `agentbundle.build.scope_rails` now
accepts both legacy UPPER_SNAKE and canonical lowercase-hyphen
grammars via alternation. No open items.

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

## `adapt-to-project` — shipped (AC4b transcripts deferred)

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

- **APM / Claude-plugins install-route nudge parity.** Adopters
  installing via APM or Claude-plugins routes (rather than
  `agentbundle install`) never hit the install marker write, never
  see the session-start nudge, and never get the chained
  `adapt.run`. The spec is explicit (CLI-only contract), but the
  RFC-0004 parity work would close this gap. **Unblocks when:**
  APM/Claude-plugins adapter parity lands.
- **AC4b — deferred manual-QA rows (real-adopter captures + user-scope-pack).**
  v1 ships the AC4a automation/grep rows. AC4b's remaining open
  shape (see `notes/manual-qa-matrix.md` for the canonical per-row
  table):
  - **Repo-scope class-2 transcripts (rows 8–11).** Brownfield
    fixture seeds the `AGENTS.upstream.md` surface; **Claude-
    simulated captures recorded inline** as preparatory evidence
    against the four documented outcomes (accept / edit / skip /
    decline). *Trigger to close:* real-adopter session against
    `brownfield-adapt/AGENTS.upstream.md` (or an installed core
    pack in an adopter's own repo); replaces the simulated
    captures with the real transcript + tree fragment inline.
  - **Repo-scope class-3 transcripts (rows 12–14).** Brownfield
    fixture extended in this PR with the class-3 surface
    (`DESIGN.md` overlapping canonical `docs/CHARTER.md`); **Claude-
    simulated captures recorded inline** for accept / edit /
    decline. *Trigger to close:* real-adopter session; same shape
    as rows 8–11.
  - **Repo-scope class-4 transcripts (rows 15–16).** Brownfield
    fixture extended in this PR with the class-4 surface
    (`docs/howto/` + `docs/guides/how-to/`); **Claude-simulated
    captures recorded inline** for accept / decline. *Trigger to
    close:* real-adopter session; same shape as above.
  - **Cross-cutting end-to-end primitives (rows 17–18).** ~~Deferred
    end-to-end transcripts.~~ **Promoted to AC4a method (a)
    automation** via `tests/integration/test_adapt_preflight_detection.py`,
    which exercises the deterministic detection primitives
    (`git status --porcelain`, content-hash divergence against
    `state.toml`) the skill body's Pre-flight invokes. Closed
    against AC4a *(a)*; no AC4b transcript needed for these rows.
    The skill-body narration of the Pre-flight remains pinned by
    AC4a *(b)* rows 2 and 3.
  - **User-scope LLM-judgment rows (rows 19–28).** *Trigger:* first
    pack declaring `allowed-scopes = ["user"]` lands (RFC-0004 §
    *Drawbacks* + *Unresolved questions*).

  AC4b stays open: simulated captures for rows 8–16 are
  preparatory evidence, not closing per AC4a's *(c)* contract
  ("captured against a real adopter session").

## `user-scope-hooks` — drafted

Spec: [`specs/user-scope-hooks/spec.md`](specs/user-scope-hooks/spec.md).
Drafted from [RFC-0005](rfc/0005-user-scope-hook-support.md) (which
merged at Draft in #35 and was amended in #36 to extend Kiro support
at both scopes). The spec is the implementation contract for both
forks the RFC designs:

- **Claude Code at user scope:** `user-merge-json` mode merging
  `hook-wiring` into `~/.claude/settings.json`; `hook-body` reroots
  to `~/.claude/hooks/<pack>/<name>.{sh,py}`.
- **Kiro at both scopes:** `merge-into-agent-json` mode merging
  `hook-wiring` into pack-owned `<scope-root>/.kiro/agents/<attach-to-agent>.json`;
  closes RFC-0001 Open Q1 (Kiro `hook-wiring` `degraded-info-log`).

The plan breaks the work into thirteen tasks (T1 schema accept →
T11 agent-spec-cli amendment, with T8 split into T8a/T8b/T8c —
state schema, install/uninstall, upgrade reconciliation). Tasks
T1–T9 land code; T10 and T11 amend the two sibling specs
RFC-0005's follow-on artifacts name.

- **All 31 ACs open** (AC1–AC29 plus AC17b for Claude Code event
  pass-through and AC19b for `attach-to-agent`-rename upgrade).
  Coverage unblocks incrementally as tasks land:
  - **AC1, AC2, AC3, AC4, AC5, AC7** close with T1 (schema +
    contract version bump).
  - **AC6** closes with T2 (validate rails) and T3 (fixture-on-disk
    coverage).
  - **AC8–AC14** close with T5 (`user-merge-json` mode).
  - **AC15–AC19, AC17b** close with T6 (`merge-into-agent-json`
    mode).
  - **AC16** also touches T7 (phase-order invariant).
  - **AC20–AC22** close with T8a (state schema + migration).
  - **AC23–AC25, AC12, AC11, AC19** close with T8b
    (install/uninstall threading + `--force-merge`).
  - **AC19b** closes with T8c (upgrade reconciliation).
  - **AC26** closes with T9 (`reconcile` reporter).
  - **AC27** stays green throughout (every PR runs
    `make build-check`).
  - **AC28, AC29** close with T3 (fixtures) and inheritance
    through every test PR after.
- **ADR is post-acceptance.** RFC-0005 named the ADR
  ("CLI may write to hand-edited shared user-settings files under
  an ID-tagged array-append merge contract, and to pack-owned
  agent files under a per-agent variant of the same contract").
  Lands after T1–T9 are done; not gating the spec.
- **First user-scope hook-bearing consumer pack — deferred.** Per
  RFC-0005 § First consumer (and § Unresolved Q4). The spec
  measures contract correctness via fixture packs, not via a
  shipped consumer.

## `skill-secrets` — shipped

Spec: [`specs/skill-secrets/spec.md`](specs/skill-secrets/spec.md).
Shipped from [RFC-0006](rfc/0006-skill-secrets-storage.md) (Accepted
2026-05-24). Delivered the two-layer architecture (skills don't hold
credentials; credentialed primitives do), the three storage tiers
(env → OS keyring → dotfile floor at `~/.agent-ready/credentials.env`),
the stdlib-only loader + `agentbundle creds` verb
(`setup`/`check`/`where`/`rm` only; no `get`), the argv ban +
`SKILL.md` "Don't" block, the `conventions-check` extensions, the
worked example, and the ADR-0002 amendment freezing the narrow
"hook-shaped" definition.

Per-task closure (15 tasks; T13 split into T13a/T13b/T13c):

- [x] **T1** — ADR-0002 amendment (closed AC1; landed in spec PR).
- [x] **T2** — stdlib `.env` parser (closed AC2).
- [x] **T3** — loader API + Tier-1 + platform dispatch + wheel-installability
      (closed AC3, AC4, AC4b, AC4c, AC5).
- [x] **T4** — macOS Keychain Tier-2 (closed AC6, AC7, AC8).
- [x] **T5** — Windows Credential Manager Tier-2 (closed AC9, AC10,
      AC11, AC12).
- [x] **T6** — Tier-3 dotfile incl. shared-parent behavior (closed
      AC13, AC14, AC15).
- [x] **T7** — `creds-schema.toml` parser + canonical-path resolution
      (closed AC24, AC24b).
- [x] **T8** — `agentbundle creds` CLI verb; tombstone args; per-platform
      exit-code matrices (closed AC16–AC23).
- [x] **T9** — SKILL.md frontmatter + lint allow-list (closed AC25).
- [x] **T10** — `conventions-check` AST-walker extensions (closed
      AC26, AC27).
- [x] **T11** — `add-credentialed-skill` author skill + template variants
      (closed AC28).
- [x] **T12** — `example-credentialed-skill` worked example (closed AC29).
- [x] **T13a** — seed-side CONVENTIONS.md edit (closed AC30).
- [x] **T13b** — Diátaxis how-to (closed AC31).
- [x] **T13c** — this entry's per-task closure (closed AC32).
- [x] **AC33** — `make build-check` clean across every PR.
- [ ] **AC34, AC35** — inheritance invariants (orphan-fixture guard;
      no live writes to developer keychain / dotfile). Enforced by
      every future test PR that adds fixtures under
      `packages/agentbundle/tests/fixtures/creds/`.

Open follow-ons (not gating shipped status):

- **New ADR ("Credential storage for credentialed skills") is
  post-implementation.** RFC-0006 § Follow-on artifacts names it; with
  T1–T13c shipped, this is the next item (precedent:
  `user-scope-hooks`'s ADR).
- **Linux `libsecret` tier deferred.** v2 RFC scoped alongside an
  adopter-profile audit per RFC-0006 § Unresolved Q1; not gating
  v1 (Linux lands on Tier 3 floor). The `v2-libsecret` stub stays
  open under cross-spec items below.

---

## Cross-spec / outside-the-spec-tree

These are open items called out by accepted RFCs or by multiple specs,
but don't have a spec of their own yet.

- **F-conformance fixtures (RFC-0003).** The per-adapter conformance
  suite that `agentbundle validate --strict` would consume. RFC-0003
  scoped this out of v1; needs its own spec when prioritised.
- **v2 RFC: Linux `libsecret` tier (RFC-0006).** RFC-0006 § Unresolved
  Q1 defers the Linux keyring tier to a v2 RFC alongside an
  adopter-profile audit (headless / SSH dev boxes, WSL2, Docker dev
  containers, corporate fleet defaults). Three integration paths are
  on the table (`secret-tool` CLI, `gi.repository.Secret` Python
  bindings, `ctypes.CDLL("libsecret-1.so.0")` direct); choosing
  among them is part of the audit. Until then, Linux adopters land
  on Tier 3 (dotfile).
