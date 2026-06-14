# Spec: apm-internal-ref-sweep

Mode: light (no risk trigger fired — mechanical prose/comment cleanup, single logical task, familiar territory; owner directed light mode).

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** inline (light mode)
- **Constrained by:** none

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it.

## Objective

Shipped pack content (`packs/*/.apm/**`) must carry no catalogue-internal
governance references, because adopters receive the artifact but none of the
governance it was written under. The earlier `house-voice-writing-craft` PR
fixed the flagged sites and deferred the systemic remainder to this sweep
(`docs/backlog.md § apm-leak-lint-rfc`). This sweep removes the remaining
`make build-*` build-target references, the `RFC-NNNN` citation, the "this
catalogue" identity asides, and one same-class `RFC-0023` comment in `figma` —
without changing any behavior. `credential-brokers` (frozen by RFC-0013) is
left for a separate pass.

## Acceptance Criteria

- [x] `core/.apm/hook-wiring/session-start.toml` no longer names `make build-self`.
- [x] `core/.apm/hooks/pre-pr.py` drops the "this catalogue's own" identity framing (reworded adopter-neutral; the meaning — it runs none of the source project's own linters — is kept).
- [x] `core/.apm/skills/work-loop/SKILL.md` drops the `RFC-0025` citation (line ~272) and the `make build-check` / "the catalogue" reference (line ~459); the byte-identical risk-trigger block (lines 57–77) is untouched.
- [x] `core/.apm/skills/work-loop/scripts/lint-spec-status.py` and `test-lint-spec-status.py` docstrings drop `make build-check` and `tools/hooks/pre-pr.py`; the script self-test still passes.
- [x] `core/.apm/skills/receive-brief/scripts/lint-brief-coverage.py` and `test-lint-brief-coverage.py` drop `make build-check`; the script self-test still passes.
- [x] `core/.apm/skills/adapt-to-project/assets/reference.md` replaces "this catalogue" with a project-neutral term.
- [x] `figma/.apm/skills/figma/scripts/test_exit_codes.py` drops the `RFC-0023:` comment prefix.
- [x] `core` bumped 0.4.3 → 0.4.4; `figma` bumped 0.1.2 → 0.1.3; `marketplace.json` re-aggregated.
- [x] `make build-self` zero drift; `make build-check`, `lint-skill-spec`, `lint-packs`, the touched script self-tests all pass.
- [x] No behavior change: every edit is comment/docstring/prose only (code paths untouched).
- [x] All real carve-outs left intact: spec-driven workflow vocabulary (`docs/specs/<feature>/…`, `docs/rfc/`, `docs/adr/`), real IETF RFCs (`RFC-9457`, `RFC-1918`), template placeholders, and `test-lint-spec-status.py` fixture data.
- [ ] `credential-brokers` `.apm/**` RFC citations (setup.py, user-libs/credbroker) are **not** swept here (deferred: credbroker-frozen-pack-ref-sweep).

## Tasks

- T1: Reword the core leak sites (session-start, pre-pr.py, work-loop SKILL + scripts, receive-brief scripts, adapt reference); bump core.
- T2: Reword the figma RFC-0023 comment; bump figma.
- T3: build-self; run gates + touched script self-tests; single adversarial pass; changelog.
