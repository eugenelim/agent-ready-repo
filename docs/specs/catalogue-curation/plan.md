# Plan: catalogue-curation pack

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn.

## Approach

Build the pack skeleton first (registration + wiring), then the two shared contracts every skill leans on (the transform manifest and the ledger schema), then the D6 guard, then the four skills, then docs + bookkeeping, closing with a full-gate + build-self pass. The riskiest parts are the **fail-closed export verify** (a leak is the worst outcome) and the **D6 path-gate** (must protect engine behavior without false-positiving on the self-host recipe edit) — both get TDD with explicit red cases. The four skills are prose (`SKILL.md`) plus small stdlib helper scripts for the mechanical bits (ledger read/write, manifest-driven substitute+verify, the guard lint); no engine changes, no new dependency.

## Constraints

- **RFC-0059** (design), **ADR-0048** (ledger schema/path/salt/retention), **RFC-0055** (re-sync erratum/amendment routing), **RFC-0002** (self-host projection + no drift).
- Never touch `packages/agentbundle/**` behavioral code or `packs/credential-brokers/**` (D6). `build/recipes/self-host.toml` include edit is the one permitted engine-tree touch.
- No Copybara dependency; patterns only. Stdlib-only helper scripts (Windows-portable `.py`).

## Construction tests

**Integration tests:**
- End-to-end `assimilate-primitive` dry run: ingest a fixture skill → lands under a pack's `.apm/skills/` → `build-self --dry-run` clean.
- `export-catalogue --mode white-label` against a fixture target: passes on a clean tree, **fails** on a seeded upstream-URL/email/slug/owner leak (the fail-closed red case).
- Two-hop dependency: install `catalogue-curation` resolves with `governance-extras` present, fails without it.

**Manual verification:** one real `assimilate-repo` run against a small local repo, confirming ledger resume after an interrupt.

## Design (LLD)

### Design decisions
- **Skills = prose + thin stdlib helpers**, not an engine. Mechanical steps (ledger I/O, manifest-driven substitute/verify, guard lint) are small `.py` scripts under each skill's `scripts/`; judgment (destination diagnosis, verdicts, pack-fit) stays in `SKILL.md`. Traces to: all skill ACs.
- **Transform manifest is declarative data** (a reference `.md`/`.toml` under `export-catalogue/references/`), not code — auditable, drift-fixable at the rule. Traces to: export ACs.
- **Guard = presence-lint + path-gate**, not prose-intent detection (rejected as undecidable). Traces to: D6 ACs.
- **Reuse the engine's blessed helper, don't roll our own path handling** — all `assimilate-*`/`export` writes route through `agentbundle.safety.write_jailed`/`assert_under` (resolve-then-verify-prefix, symlink-foiling). Read-only consumption of the engine's public safety helper is sanctioned reuse, not a D6 engine change. Traces to: write-confinement AC.
- **Ingest routes through the repo's own gates** — `assimilate-*` invokes the existing lint suite + SAST/SCA on the candidate before it lands (proactive, not deferred to the work-loop reviewer). No new scanner dependency. Traces to: ingest-gates AC.

### Data & schema
- **Per-run ledger** `~/.agentbundle/catalogue-curation/<run-id>/ledger.toml`: append-only array of `{path, name, content-hash, verdict, status, destination}`; salted `<run-id>`; purged on completion. **Per-source marker** `sources/<source-hash>/last-synced.toml`: `{content-hashes[], synced[]dated}`; append-only; purge-exempt. Per ADR-0048. Traces to: assimilate-repo ledger/re-sync ACs.

### Interfaces & contracts
- Four `SKILL.md` activation surfaces (disjoint descriptions); the transform manifest; the ledger schema; the guard lint CLI (`--check`, exit non-zero on violation). Traces to: skill + guard ACs.

### Component / module decomposition
- New: `packs/catalogue-curation/` (pack.toml, plugin.json, README, `.apm/skills/{assimilate-primitive,assimilate-repo,propose-catalogue-pack,export-catalogue}/`), a guard lint under `tools/`, per-skill helper scripts. Reused: `new-rfc`/`new-adr`/`new-guide` (by reference), `.adapt-discovery.toml` markers, `pre-pr`/`build-check` wiring. Traces to: scaffolding ACs.

### Failure, edge cases & resilience
- Export is **fail-closed**: verify hard-fails on any surviving anchor (mode-aware), dangling symlink, non-blank source. Ledger is idempotent + resumable + worktree-concurrent-safe (append-only, stable-identity keys). Guard path-gate fails safe (blocks protected-tree writes absent the exemption carrier). Traces to: export + ledger + guard ACs.

### Dependencies & integration
- Depends on `core` + `governance-extras` (first pack-on-non-core dep). Integrates with the self-host recipe (one include entry) and the `pre-pr`/`build-check` gate. No external/runtime deps. Traces to: scaffolding + guard ACs.

## Tasks

### T1: Pack skeleton registers and projects
**Depends on:** none
**Touches:** packs/catalogue-curation/**, packages/agentbundle/agentbundle/build/recipes/self-host.toml
**Tests:**
- `lint-packs` + `validate` pass; `self --dry-run` succeeds; `build-self` no drift.
**Approach:**
- Author `pack.toml` (deps on core + governance-extras), `plugin.json`, `README.md`, empty `.apm/skills/` dirs; add to `self-host.toml` include; confirm absent from profiles.
**Done when:** pack registers, projects, and `make build-self` is drift-clean.

### T2: Transform manifest + ledger schema helpers
**Depends on:** T1
**Touches:** packs/catalogue-curation/.apm/skills/export-catalogue/references/**, packs/catalogue-curation/.apm/skills/*/scripts/**
**Tests:**
- Ledger helper: append-only round-trip; purge leaves the per-source marker; salted run-id stable per source.
- Manifest parse: four anchors with source+scope; strip globs; include-set.
**Approach:**
- Write the declarative transform manifest (distilled from `0059-notes/`); write stdlib ledger I/O + manifest loader helpers.
**Done when:** helper unit tests green; schema matches ADR-0048.

### T3: D6 guard — presence lint + path-gate
**Depends on:** T1
**Touches:** tools/**, packs/catalogue-curation/.apm/skills/*/SKILL.md, (pre-pr/build-check wiring)
**Tests:**
- Path-gate: red on a `packages/agentbundle/<module>.py` change without carrier; green with carrier; green (excluded) on `build/recipes/self-host.toml`; red on `packs/credential-brokers/**`.
- Presence lint: red when a skill lacks the scoped refusal clause.
**Approach:**
- Implement the lint (`git diff --name-only` path check + carrier read from the `Engine-Change-RFC:` commit trailer); wire into `build-check.yml` (the repo's own-lint home — `pre-pr.py` deliberately runs no repo linters, so the gate lives in CI, not the projected hook); add refusal clauses.
**Done when:** all guard tests green and the gate is wired.

### T4: `assimilate-primitive`
**Depends on:** T1, T2, T3
**Touches:** packs/catalogue-curation/.apm/skills/assimilate-primitive/**
**Tests:**
- Integration: fixture skill ingested → lands under a pack → build-self dry-run clean; refuses a `packages/agentbundle/**` destination.
- Security: URL fetch rejects `file:`/`ftp:` and private/link-local/metadata IPs (https/git only); write routed through `agentbundle.safety.write_jailed` rejects a traversing/absolute path + an in-source symlink; a fixture whose body is malicious prose is **shown raw for review** before write and an ingested **hook** requires an explicit confirm; the repo's lints + SAST/SCA run over the migrated candidate and a seeded lint failure blocks the landing.
- Craft: a goal-based check that the produced `description` is collision-checked against all existing skill descriptions (a seeded near-duplicate is flagged, naming the collision); manual-QA that the landed target-state is terse + progressive-disclosure (detail in `references/`, mechanical steps in `scripts/`) + cold-reader-glossed + guided (offered choices, not a dump).
- Anti-pattern steering: a fixture whose script invokes a skill/agent (or a self-reviewing agent, or an over-broad tool grant) is flagged with the named anti-pattern and either reshaped to convention or rejected — never landed as-is.
**Approach:**
- Author `SKILL.md` in two phases: **(1) security** — fetch via git/https-guarded → SSRF-checked → show raw body for inspection → confirm on code/hooks → run repo lints+scanners; **(2) craft-shape** — diagnose destination via local CHARTER → reshape to craft (rewrite description + collision-check, apply progressive disclosure, gloss) → present shaped target for approval → write via `safety.write_jailed` → prompt build-self. Reject cleanly at either phase. Elicitation points prepare context (found / options / recommendation), never bare questions.
**Done when:** the end-to-end ingest integration test + the security tests + the collision goal-based check pass.

### T5: `assimilate-repo` (+ ledger + re-sync + RFC emission)
**Depends on:** T2, T3, T4
**Touches:** packs/catalogue-curation/.apm/skills/assimilate-repo/**
**Tests:**
- Ledger resume after interrupt (deterministic run-id); concurrent-worktree append no-clobber; incremental re-sync classifies unchanged/changed/new; re-sync RFC routing (Open→Amendment, Frozen-correction→Erratum, Frozen+new→new RFC recorded as an Erratum entry naming it on the prior).
- Recorded QA: a survey run produces an RFC file and *prompts* the `propose-catalogue-pack` hand-off — no auto-created pack shell (offer-not-invoke).
**Approach:**
- Author `SKILL.md` (iterative verdicts, ledger-backed, RFC emission, offer-not-invoke hand-off) using T2 helpers + RFC-0055 routing.
**Done when:** resume + re-sync + routing tests pass.

### T6: `propose-catalogue-pack`
**Depends on:** T1, T3
**Touches:** packs/catalogue-curation/.apm/skills/propose-catalogue-pack/**
**Tests:**
- Given a fixture area, scaffolds a pack shell + emits an RFC; rejects a non-additive area; fit-test reads the local CHARTER.
**Approach:**
- Author `SKILL.md` (additivity + four-principles + local-CHARTER coverage test → scaffold + RFC, or reject).
**Done when:** scaffold + reject paths verified.

### T7: `export-catalogue` (+ modes + persisted defaults + fail-closed verify)
**Depends on:** T2, T3
**Touches:** packs/catalogue-curation/.apm/skills/export-catalogue/**
**Tests:**
- Verify hard-fails on seeded four-anchor leak (each anchor); passes on clean; attributed mode allows anchors only in the notice surface; re-home transforms land on the target copy only (DEFAULT_ADAPTER, self-host targets/include, blank source).
- Verify is case-insensitive + text-files-only (a binary artifact is out of scope, declared) + literals-only after normalization; export writes route through `safety.write_jailed`; the operator-supplied target path is validated (rejects empty / repo-overlapping).
**Approach:**
- Author `SKILL.md` + verify/substitute helper driven by the T2 manifest; both modes; target-only re-home transform.
**Done when:** the fail-closed integration test (clean-pass / leak-fail) is green.

### T8: Two-hop dependency regression test
**Depends on:** T1
**Touches:** packages/agentbundle/**/tests/**
**Tests:**
- Install resolves with `governance-extras` present; fails the dependency gate without it.
**Approach:**
- Add the regression test alongside existing dependency-gate tests.
**Done when:** both cases assert correctly.

### T9: Per-pack guide
**Depends on:** T4, T5, T6, T7
**Touches:** docs/guides/catalogue-curation/**
**Tests:**
- Goal-based: guide home exists, all four quadrants present, links resolve (`lint-agent-artifacts` link check / doc-link grep).
**Approach:**
- Author via `new-guide`: tutorial (first assimilation) + how-tos (survey/propose/export/resume/re-sync) + reference (manifest/ledger/guard) + explanation (why-a-pack, single-authoritative-source, fail-closed).
**Done when:** guide set complete and linked from `pack.toml`/`README`.

### T10: CHANGELOG + backlog anchors
**Depends on:** T1
**Touches:** docs/product/changelog.md, docs/backlog.md
**Tests:**
- Goal-based: `[Unreleased]` entry present; backlog anchors greppable.
**Approach:**
- Add changelog entry + backlog anchors for `retire-primitive`, `audit-catalogue`, ledger stale-run sweep.
**Done when:** entries present and greppable.

### T11: Full gate + build-self green ✓
**Depends on:** T1-T10
**Touches:** (verification only)
**Tests:**
- `lint-packs`, `validate`, `lint-skill-spec`, `lint-agent-artifacts`, `self --dry-run`, guard lint, `pytest` (pack + engine test roots) all green; `make build-self` drift-clean.
**Approach:**
- Run the full pre-pr gate; fix drift; confirm.
**Done when:** the complete gate is green on a clean tree.
**Result (2026-07-22):** 49 unit tests pass; build-check exit 0 (all lint, SAST/SCA, semgrep clean); projection drift-free after clearing stray `__pycache__` dirs from scripts/ and re-running `build-self --force`.

## Rollout

- **Delivery:** additive — a new opt-in pack, off by default, in no profile. Reversible (remove the pack dir + the one include entry). Nothing irreversible; the ledger is user-local scratch.
- **Infrastructure:** none (no service, no runtime).
- **External-system integration:** none.
- **Deployment sequencing:** pack skeleton (T1) before skills; guard (T3) before/with skills so no skill lands without the refusal-clause + gate; the `.apm` packs release via the marketplace/APM aggregate (version bump), not PyPI.

## Risks

- The fail-closed verify over-omits a safe file (accepted — leaking is worse; documented allowlist edit).
- The path-gate false-positives on a legitimate engine change unrelated to this pack (mitigated by the exemption carrier + `build/recipes/**` exclusion).
- Skill activation collision with `init-project`/`adapt-to-project` or the discovery skills (mitigated by the disjointness boundary in RFC-0059; validated by pack activation evals if added).

## Changelog

- 2026-07-02: initial plan (from RFC-0059 + ADR-0048).
- 2026-07-02: folded spec-stage security review — untrusted-code review + hook-confirm, URL SSRF allowlist, `safety.write_jailed` write-confinement, honest verify bounds, ledger free-text ceiling; and the operator direction to run the repo's own lints + SAST/SCA on ingested code proactively (T4/T5/T7 tests extended; no new dependency).
- 2026-07-22: T11 complete — build-check green (49 unit tests, lint, SAST/SCA, semgrep); projection drift-free. Remaining: 3 manual-QA sessions for agent-behavior ACs (assimilate-primitive, export-catalogue, assimilate-repo).
