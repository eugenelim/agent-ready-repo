# Round 1 adversarial review — credential-broker-contract spec + plan

**Reviewer:** adversarial-reviewer (subagent)
**Date:** 2026-05-26
**Verdict:** Not clean — 8 Blockers, 8 Concerns, 4 Nits.

## Blockers

**1. AC3 names the wrong file for skill frontmatter validation.** `docs/specs/credential-broker-contract/spec.md:110`. `pack.schema.json` validates `pack.toml` manifests, not skill SKILL.md frontmatter. Fix: rewrite AC3 to extend the skill-frontmatter validator in `tools/lint-agent-artifacts.py`; delete pack.schema.json from T1.

**2. AC2 enumerates codex with wrong provenance.** `docs/specs/credential-broker-contract/spec.md:109`. The `.agentbundle/` prefix in codex came via RFC-0011, not via RFC-0004 v0.3's `.agent-ready/` rename. Fix: split AC2 / Assumptions text into two clauses — claude-code + kiro via RFC-0004 + f585e67; codex via RFC-0011.

**3. AC6 "modulo one import-path delta" is contradicted by T3.** `docs/specs/credential-broker-contract/spec.md:119`, `plan.md:121`. T3 requires inlining exceptions.py (69 lines), rewriting the `from .exceptions import (...)` block, rewriting the `_keychain_macos` / `_credman_windows` imports. That's three structural deltas plus a public-surface dropout (PermissiveAclError, SchemaError). Fix: enumerate exact permitted deltas in AC6; rewrite T3's golden-file test to normalize against the enumerated allow-list.

**4. AC7 stdlib-only `sys.modules` assertion is not implementable.** `docs/specs/credential-broker-contract/spec.md:120`. `sys.modules` is global; pytest itself populates it. Fix: rewrite AC7 to assert the *delta* in sys.modules (before/after), or run in a subprocess via `python -c`.

**5. T5 hidden Tier-2 helpers cycle.** `docs/specs/credential-broker-contract/plan.md:151`. T5 Depends on T2 but uses T3's Tier-2 backends. Fix: change to `Depends on: T2, T3`; or land separate `_sso_keychain.py` siblings with their own byte-equivalence AC.

**6. T3/T5/T9/T10 parallelism claim is false.** `docs/specs/credential-broker-contract/plan.md:20,394`. Plan claims four-way parallelism but T5 depends on T2, T7 on T3, etc. Fix: rewrite parallelism paragraph to honour declared Depends on graph (T9, T10 in parallel after T1; T3 after T2; T5 after T2+T3; T7 after T3; T4 after T3; T6 after T5; T8 after T4+T6).

**7. T12/T13/T14 cannot run in parallel — make build-self race.** `docs/specs/credential-broker-contract/plan.md:20,394`. Each runs `make build-self`; parallel branches against shared projection targets will silently merge-revert per `feedback_build_self_undoes_projection_only_edits`. Fix: declare T12, T13, T14 sequential; or carve `make build-self` into supervisor's post-merge step.

**8. AC25 `auth: env` substring-trap.** `docs/specs/credential-broker-contract/spec.md:155`. AC25 doesn't pin matching shape; `FOO_BAR_BAZ` could substring-satisfy declared key `BAR`. Fix: extend AC25's `auth: env` line to pin exact-string equality on `Constant.value`; add a lint-self-test for distinguishing `FOO_BAR` vs `FOO_BAR_BAZ`.

## Concerns

**9. AC34 has no separation-enforcement test.** `spec.md:178`, `plan.md:336`. T14 could be absorbed into T15 without breaking grep tests. Fix: add a goal-based check (distinct commit message) or pin separation in PR-description language.

**10. AC44/AC45 not specific enough to execute.** `spec.md:194-195`. Footer wording and conformance-suite addition not pinned. Fix: inline the exact text or move to a notes file with line range.

**11. AC38 version-substitution unpinned.** `spec.md:185`, `plan.md:367`. No source for the prior-minor patch number. Fix: pin the source (`git describe --tags --match 'agentbundle-v0.1.*' --abbrev=0`) and assert the CHANGELOG body against the resolved value.

**12. AC5 marker-rail undefined.** `spec.md:115`. No reference for what `<adapt:NAME>` markers are. Fix: add inline regex definition `<adapt:[A-Z_]+>` per RFC-0007.

**13. AC12 2 KB threshold undefended.** `spec.md:128`. No source for the constant. Fix: name `CRED_MAX_CREDENTIAL_BLOB_SIZE` Win32 lower-bound; pin to named symbol.

**14. Boundaries cites non-existent wording table.** `spec.md:38`. RFC-0013 § 6 has check rules, not literal stderr strings. Fix: change to "wording inherited from AC26(a/b/c), extended per-broker per RFC § 5"; add broker-specific stderr strings to a pinned location.

**15. T8 lint-of-self test incomplete.** `plan.md:225`. Only covers dotfile check, not the four broker-specific checks. Fix: extend lint-of-self test to cover all four broker-specific AST checks.

**16. AC42 ROADMAP has no closure rule.** `spec.md:192`. Fix: name when the entry leaves ROADMAP (e.g. "AC36-AC39 land + at least one manual-QA transcript per row").

## Nits

**17. Verify `docs/contracts/adapter.toml` is hand-edited.** `spec.md:6`. May be projection target.

**18. Rollout overstates reversibility of Phase 1.** `plan.md:377`. Contract bump is effectively forward-only once `credential-brokers` ships.

**19. T9 template-file count drift from RFC § 5.** `plan.md:247`, `spec.md:165-167`. RFC says "labelled sections under existing `assets/credentialed-skill-SKILL.md`"; spec says four files. Fix: choose one shape; if four files, add a Changelog note explaining the divergence.

**20. Changelog count drift.** `spec.md:219`. 12 surfaces, not 9.
