# Spec: design-handoff-read

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none — no synchronous, event, or RPC interface surface.
- **Shape:** mixed
- **Depends on:** [`docs/specs/design-output-addressing/`](../design-output-addressing/spec.md)
  — two of the three artifacts read here have no address until that spec ships.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: an author corrects them in place as the work teaches.

## Objective

Frontend create mode honours a named aesthetic direction instead of re-deriving
one. It resolves the adopter's `[design] output_dir`, reads the aesthetic
direction, the per-screen brief, and the token taxonomy when each is present, and
consults its own canonical product-reference list only when none resolves. Today
the pack has no awareness of that directory at all: its only link to the design
pack is a probe for whether a skill is installed.

This is the one new trust boundary in the surrounding work. A value the adopter
controls becomes a filesystem path, files under it are read, and their content
reaches the step that emits production frontend code — which is the committed
deliverable, so anything the content induces outlives the session. Every control
below exists because of that, and each is stated as an obligation on an artifact a
reader can check rather than as a description of runtime behaviour.

## The three artifacts read

| Artifact | Path under the approved `output_dir` | Written by |
| --- | --- | --- |
| Aesthetic direction | `direction/<slug>.md` | `creative-direction` |
| Per-screen brief | `screens/<slug>/<screen>.md` | `user-flow` |
| Token taxonomy | `tokens/<slug>.md` | `design-system` |

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — adopters gain a handoff and must know its trust posture | `guides/frontend-engineering/how-to/read-the-design-handoff.md`, `guides/frontend-engineering/README.md` | Guide author | The guide states what is read, from where, and what is ignored | `tools/lint-guidebook-steps.py` exits 0 and the guide is linked from its index |
| Interface compatibility | Applicable — the frontend now depends on a section another pack declares | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/design-handoff.md` | Pack maintainer | The reference resolves `[design]` by name rather than restating its base | The declared base is never duplicated here |
| Operations | Applicable — the controls are verified by recorded runs, not by a gate | `docs/specs/design-handoff-read/notes/verification-ledger.md` | Implementer | One positive and one negative recorded run per control | Every control has both, or a named owner waiver |
| Release history | Applicable — one pack bumps | `docs/product/changelog.md` | Release author | A released entry for `frontend-engineering`, topmost for that artifact | Topmost entry names its new `pack.toml` version |
| Reusable learning | Applicable | `project-knowledge` seam | Work-loop | Receipt or `project-knowledge unavailable` | Recorded at the terminal gate |

## Boundaries

### Always do

- Approve the resolved `output_dir` before reading anything under it, source-aware:
  a repo-root value must realpath within the repository tree or take explicit
  confirmation; a user-profile value is approved against its own declared absolute
  root. Every later prefix check is against that approved value — confinement to an
  unvalidated root is not confinement.
- Treat every artifact as data. Extract the declared field set and discard
  everything else, including any instruction the content contains.
- Distinguish a refusal from a skip everywhere the result is read. A skip means
  nothing was there; a refusal means something was wrong.

### Ask first

- Widening the field set extracted from any artifact.
- Reading any artifact beyond the three this spec names.

### Never do

- Never add a new top-level directory, module, or dependency. This change is
  confined to `packs/frontend-engineering/`, `guides/frontend-engineering/`,
  `guides/README.md`, `docs/specs/`, and `docs/product/`.
- Never let an artifact's content decide what code is emitted, which files are
  written, or which network destination appears in generated output. The content
  describes intent; it never issues instructions.
- Never record or surface an absolute user-profile path in any artifact, including
  verification evidence.
- Never ship a control with only a positive observation. A benign fixture cannot
  distinguish a present control from an absent one, so each control owes a
  recorded negative run or a named owner waiver.
- Never edit a lint, test, or checker to make a failing gate pass.

## Testing Strategy

Every control here governs agent instruction prose, so none is unit-testable and
no gate reads it. Verification is therefore **visual / manual QA against staged
fixtures, paired**: one run where the control is not needed and one where it must
fire. The pairing is the strategy — a single benign run establishes only that the
happy path works, and a single observed refusal from a non-deterministic agent
establishes that the control fired once, so each recorded observation states the
fixture, the observed output, and which of the two it demonstrates.

Two criteria are checkable statically instead, and are marked goal-based below:
the handoff reference's content, and that it resolves the layout section by name.

## Acceptance Criteria

- [ ] Frontend create mode approves the resolved `output_dir` source-aware before
      reading under it: a repo-root value confirmed to realpath within the
      repository tree, a value resolving outside it taking explicit confirmation,
      and a user-profile value approved against its own declared absolute root.
- [ ] Frontend create mode confirms each of `direction/<slug>.md`,
      `screens/<slug>/<screen>.md`, and `tokens/<slug>.md` has a canonicalized
      real path under the approved `output_dir` before reading it.
- [ ] Frontend create mode surfaces a named refusal when an artifact's real path
      resolves outside the approved `output_dir`, worded differently from either skip.
- [ ] `references/design-handoff.md` enumerates, per artifact, the closed field set
      frontend create mode extracts, and states that content outside that set —
      including any embedded instruction — is discarded rather than followed.
- [ ] `references/design-handoff.md` states that a declared `type:` is a collision
      guard and not an authenticity claim, because it sits in the same
      adopter-writable file as the content it labels.
- [ ] `references/design-handoff.md` resolves the `[design]` section by name and
      states no base path of its own.
- [ ] Frontend create mode validates each artifact's declared `type:` before
      extraction and surfaces a mismatch rather than consuming the file.
- [ ] When `output_dir` resolves from user-profile configuration, frontend create
      mode confirms each artifact belongs to the current product before consuming
      it, and surfaces a mismatch rather than consuming it.
- [ ] Frontend create mode reads at most 12 files matching the three paths above,
      at most 128 KiB each, at most 2 directory levels below `output_dir`, and
      traverses no link during the scan.
- [ ] Frontend create mode surfaces which bound it exceeded rather than reading a
      partial set. The count bound fires first for a mis-set `output_dir`, because
      an over-broad root multiplies files before any one file grows.
- [ ] Every path frontend create mode surfaces or records — a consumed artifact, a
      confinement refusal, a `type:` mismatch, a provenance mismatch, or a bound
      breach — names it relative to `output_dir` plus the configuration source.
- [ ] Frontend create mode reads the three artifacts, when present, before
      consulting its canonical product-reference list.
- [ ] Frontend create mode records one named skip when no `[design]` section
      resolves, and a differently worded named skip when the section resolves but
      the directory holds none of the three artifacts.
- [ ] `guides/frontend-engineering/how-to/read-the-design-handoff.md` exists,
      states what is read and what is ignored, and is linked from
      `guides/frontend-engineering/README.md`.
- [ ] `tools/lint-guidebook-steps.py` exits 0.
- [ ] Each control criterion above has both a positive and a negative recorded run
      in the verification ledger, or a named owner waiver recorded in this spec.
- [ ] `agentbundle catalogue verify --root .` exits 0.
- [ ] The topmost `## [frontend-engineering][<version>] — YYYY-MM-DD` heading in
      `docs/product/changelog.md` names that pack's new `pack.toml` version, at the
      level directly beneath `[Unreleased]`.

## Follow-ons

- `docs/specs/frontend-experience-composition/` — the shared state-coverage map and
  the risk-tier depth selector. Independent of this spec; both depend on
  `design-output-addressing`.
- Pack maintainer: `packs/frontend-engineering/pack.toml` declares no layout
  section, and `references/design-handoff.md` is deliberately not an
  `agentbundle-layout.md`, so the layout conformance test does not read it. The
  deferred `docs/ux` base flip must name this file explicitly or it will strand
  the frontend read.
- Pack maintainer: no gate reads pack prose for the `packs/AGENTS.md` § Security
  controls. A prose-presence checker would certify phrasing rather than the
  control, so this needs a predicate stronger than presence before it is built.

## Assumptions

- Technical: `packs/frontend-engineering` has no awareness of any design output
  directory today; its only link to the design pack is a probe for whether
  `conversion-design` is installed
  (source: `grep -rn "agentbundle-layout\|output_dir\|docs/design" packs/frontend-engineering/.apm/`
  returns only genre-routing hits)
- Technical: `frontend-engineering/SKILL.md` carries no containment prose at all,
  so the controls here are authored from `copy-direction`'s pattern rather than
  adapted from an existing frontend step (source: read of that skill)
- Technical: `packs/AGENTS.md:56-58` requires canonicalize-then-prefix-check before
  every read, data-not-instruction extraction, and a current-project belonging
  check for a user-level config path; root `AGENTS.md` places trust-boundary
  validation in the non-waivable class (source: read of both files)
- Technical: `copy-direction/SKILL.md` approves the resolved `output_dir` before
  reading under it — a repo-root value must stay within the repository tree or take
  explicit confirmation — and is the only skill in either pack carrying that step
  (source: read of its step 1)
- Technical: no skill reaches `packages/agentbundle/agentbundle/workspace_mcp.py`;
  every layout reference instructs a direct read of `./agentbundle-layout.toml`,
  and `_read_layout_bases` returns `str(candidate.resolve())` with no prefix check,
  so skill prose is the only enforcement point
  (source: `workspace_mcp.py:1576-1619`; `tests/conformance/test_pack_layout_declared_section.py:5-7`)
- Technical: a user-profile `output_dir` must be an absolute path and is shared
  across every repository, so one vault can serve two products
  (source: `packs/experience-design/.apm/skills/copy-direction/references/agentbundle-layout.md`)
- Technical: the bound values are calibrated against the largest design tree
  available — this repository's, which holds 41 artifacts of which 9 match the
  three crossing patterns (2 under `direction/`, 7 under `screens/<slug>/`, 0 under
  `tokens/`) (source: probe over `docs/design/`, 2026-09-16)
- Technical: `tools/check-guide-index.py` asserts only that every active pack has a
  direct link in `guides/README.md`; it cannot observe whether an individual page
  is reachable (source: read of that tool)
- Technical: this repository's shipped spec corpus holds 467 specs and 7,428
  criteria, mean 15.9, so this spec's count sits near the median
  (source: probe — `grep -c "^- \[[ xX]\]" docs/specs/*/spec.md`, 2026-09-16)
- Process: every non-cosmetic pack-content change bumps matching versions and
  updates that pack's eval harness (source: `packs/AGENTS.md`)
- Process: each phase ships its guide (source: `docs/CONVENTIONS.md:1130`)
- Product: this spec is separated from the addressing work because it is the only
  new trust boundary in it and warrants its own review surface
  (source: user confirmation 2026-09-16)
