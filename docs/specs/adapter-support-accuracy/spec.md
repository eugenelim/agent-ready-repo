# Spec: adapter-support-accuracy

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0022](../../rfc/0022-kiro-adapter-split.md) — the Kiro IDE/CLI split + `kiro-ide-hook` activation the Kiro corrections must stay faithful to
  - [RFC-0024](../../rfc/0024-copilot-subagent-projection.md) — the Copilot full-parity decision the Copilot corrections must stay faithful to
- **Contract:** none — this spec documents, and does not change, the existing adapter contract.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (work-loop). No risk trigger fired. The one conditional trigger —
governance boundary (frozen RFC/ADR erratum) — was checked and did NOT fire:
RFC-0022/ADR-0012 and RFC-0024/ADR-0013 carry none of the now-wrong claims, so no
erratum is needed. Lean fill: Objective + Acceptance Criteria + Boundaries +
Testing Strategy + Assumptions (the last three earn their place via the sibling-PR
ownership boundary and the FIX-6 empirical re-verification). -->

## Objective

A reader of the adapter support matrix
([`docs/guides/_shared/reference/adapter-support.md`](../../guides/_shared/reference/adapter-support.md))
should get an honest, contract-faithful picture of what each agent tool receives —
with no claim that contradicts the adapter contract or a tool's current behaviour.
This spec corrects six documentation-accuracy defects in that page (and the same
claims wherever else they appear), verified against `docs/contracts/adapter.toml`
(byte-identical to `packages/agentbundle/agentbundle/_data/adapter.toml`) and, for
the Copilot repo-hook claim, against the live github/copilot-cli changelog +
issues. Success: every corrected claim is true against its source of truth, and the
matrix, the caveats, and the backlog agree with one another.

## Boundaries

### Always do

- Verify each claim against `docs/contracts/adapter.toml` (the contract wins on any
  disagreement) before changing the prose.
- For the Copilot repo-scope hook claim, treat the live copilot-cli changelog +
  issues as the source of truth — not the doc page (it records an empirical runtime
  finding that may be stale).
- Keep the dated empirical observations in `copilot-full-parity/spec.md` intact;
  correct only forward-looking conclusions drawn from them.

### Ask first

- Changing a tool's **Tier** in the matrix (re-assess and justify in one line, but
  surface the call).

### Never do

- Touch the Copilot matrix **Skill** cell, the Copilot **Subagent** cell, or the
  "Copilot — subagents have no web tool" caveat — a separate PR owns those.
- Rewrite a frozen Accepted RFC/ADR; if a frozen doc carried a now-wrong claim, an
  Approver-signed `§ Errata` would be the vehicle (it does not, here).
- Change the adapter contract, open an RFC, or run build-self — this is repo-owned
  documentation only.

## Testing Strategy

- **Goal-based check** for every acceptance criterion: each corrected claim is
  checked by reading it against the contract / live changelog (a `grep` of
  `adapter.toml` or the cited changelog/issue), and the repo doc lints
  (`tools/pre-pr-catalogue.py`, `lint-spec-status.py`) pass. No production test
  file — there is no compressible invariant to assert; the contract is the oracle.

## Acceptance Criteria

- [x] **AC1.** The Kiro IDE **Hook** matrix cell and its per-tool caveat describe
  the real three-way split: hook *bodies* project (`tools/hooks/`), standalone
  `.kiro.hook` IDE-event files **project** (`kiro-ide-hook` active →
  `.kiro/hooks/<pack>--<name>.kiro.hook`, full IDE event vocabulary), and only
  **agent-embedded** hook-wiring drops (the IDE loader drops the `hooks` key,
  RFC-0022 E2). Verified against `adapter.toml` `[adapter.kiro-ide]` (hook-body
  direct-file; `kiro-ide-hook` active; hook-wiring `dropped`).
- [x] **AC2.** Kiro IDE's Tier stays **Partial**, justified: agent-embedded
  `hook-wiring` still drops, so hook-wiring-bearing packs get less on Kiro IDE than
  on Kiro CLI (which retains `merge-into-agent-json`).
- [x] **AC3.** The slash-command caveat no longer says "Kiro has no slash-command
  surface"; it says Kiro ships **no standalone command-file primitive the catalogue
  projects**, and notes Kiro IDE still surfaces slash commands via manual-trigger
  hooks and `inclusion: manual` steering. Verified against `adapter.toml`
  (`command` = `dropped` for every kiro adapter).
- [x] **AC4.** The page states that both Kiro targets read the universal `AGENTS.md`
  layer via Kiro steering.
- [x] **AC5.** The Codex slash-command clause states the replacement for deprecated
  custom prompts is **skills**, which the catalogue projects to Codex at
  `.agents/skills/`. Verified against `adapter.toml` codex `skill` →
  `direct-directory` → `.agents/skills/`.
- [x] **AC6.** The Copilot slash-command clause frames the drop as **won't-fix-by-
  design** (copilot-cli#618/#1113; prompt files superseded by skills), not "doesn't
  yet", and notes Copilot skills project as instruction files
  (`.github/instructions/`). Verified against `adapter.toml` copilot `command` =
  `dropped` and `skill` → `instruction-file` → `.github/instructions/`.
- [x] **AC7.** The Copilot repo-scope hook caveat and the Copilot **Hook** matrix
  cell reframe "regressed" as **trust/prompt-mode-gated loading** (copilot-cli
  changelog 1.0.8 / 1.0.41 / 1.0.51), cite the open conditional bug
  [copilot-cli#1503](https://github.com/github/copilot-cli/issues/1503) (repo hooks
  skipped on `--resume`), re-stamp to CLI 1.0.61 (2026-06-09), and keep "user-scope
  fires". The caveat does **not** assert repo hooks definitely fire on 1.0.61 (not
  reproducible here); it hedges the 1.0.60 non-execution as the likely trust gate.
- [x] **AC8.** Blast radius corrected without falsifying history: the
  `copilot-full-parity/spec.md` T4 conclusion is reframed (its dated 1.0.60
  acceptance observation preserved verbatim), and the `docs/backlog.md`
  copilot-full-parity follow-on records the 1.0.61 re-verification (trust-gate, not
  regression) and #1503.
- [x] **AC9.** No frozen-governance edit: RFC-0022/ADR-0012 and RFC-0024/ADR-0013
  were checked and carry none of the corrected claims, so no `§ Errata` was added.
- [x] **AC10.** The ownership boundary held: the Copilot Skill cell, Copilot
  Subagent cell, and no-web-tool caveat are unchanged.
- [x] **AC11.** Gates green: `tools/pre-pr-catalogue.py` and
  `.claude/skills/work-loop/scripts/lint-spec-status.py` both exit 0; no new
  intra-repo reference introduced by the change dangles.
- [x] **AC12.** Bundled ride-along (same file/concern, surfaced by AC1's caveat):
  the Kiro CLI **Hook** matrix cell reads `body + wiring`, correcting the prior
  `body` understatement — kiro-cli retains `hook-wiring` via `merge-into-agent-json`
  (`adapter.toml` `[adapter.kiro-cli.projections.hook-wiring]`).

## Assumptions

- Technical: `docs/contracts/adapter.toml` is byte-identical to
  `packages/agentbundle/agentbundle/_data/adapter.toml` (source: `diff -q`, 2026-06-11).
- Technical: latest copilot-cli is 1.0.61 (2026-06-09); repo `.github/hooks/`
  loading is gated on folder-trust + prompt-mode opt-in, with no scope-wide
  regression entry; #1503 open, #2540 open (plugin-scope), #2076 closed (source:
  github/copilot-cli changelog + issues, web re-verification 2026-06-11).
- Process: frozen RFC-0022/ADR-0012 + RFC-0024/ADR-0013 do not carry the corrected
  claims (source: grep, 2026-06-11), so the governance-erratum path is not invoked.
