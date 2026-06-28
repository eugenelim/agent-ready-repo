# Spec: RFC correction convention (Errata / Amendments)

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0055
- **Brief:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An author recording a post-publication correction to an RFC has one
unambiguous, portable convention to follow. The `new-rfc` skill is its sole
home: `SKILL.md` documents which section to use keyed to the RFC's lifecycle
class — **Errata** for a Frozen RFC (Accepted/Rejected), **Amendments** for an
in-flight Open RFC — together with an optional, threshold-gated two-layer
structure (an authoritative *Current state* layer over a dated *History / audit
trail*, where the current-state layer wins on disagreement) and the append-only
supersession rules. The skill's `assets/rfc.md` template carries the same shape
as a clearly-conditional commented scaffold, so the structure travels into every
RFC an adopter drafts without being cargo-culted into empty sections. The result:
a reader of any RFC that uses the convention finds the present authoritative
rules without walking the whole audit trail, and the convention ships wherever
`governance-extras` is installed — with no coupling to a `core`-seeded doc.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- House the convention's substance in the `new-rfc` skill only — `SKILL.md`
  (the procedure) and `assets/rfc.md` (the optional scaffold).
- Ship the asset scaffold as a **commented, clearly-conditional** block with a
  delete-unless-accumulating-corrections instruction — never a live empty section.
- Key the Errata/Amendments split to the existing Document-lifecycle classes
  (`CONVENTIONS.md` § Document lifecycle): Frozen → Errata, in-flight Open → Amendments.
- Project pack-source edits with `make build-self` and keep the drift gate clean.
- Record the user-visible skill-behavior change under `docs/product/changelog.md` `[Unreleased]`.

### Ask first

- Migrating, retrofitting, or reusing any existing RFC's correction section
  (RFC-0055 D5 is forward-only; this would exceed scope).
- Adding a mechanical lint that enforces the correction structure (RFC-0055 Open
  question recommends *no* for now — judgment-based and threshold-gated).
- Bumping the `governance-extras` pack version (the change rides the unreleased
  0.4.0; a bump is a separate release decision).

### Never do

- Edit `docs/CONVENTIONS.md` to carry the convention (RFC-0055 D4 — keeps a
  `governance-extras` feature out of a `core`-seeded doc; structural boundary).
- Edit any existing RFC's body or correction section (forward-only D5; Frozen
  bodies are immutable).
- Add a new dependency, module boundary, or top-level directory (structural).

## Testing Strategy

All behaviors here are documentation-and-convention shaped — no executable
logic — so verification is **goal-based** except the end-to-end dogfood walk,
which is **manual QA**:

- **Convention documented in `SKILL.md` (D1/D2/D3):** goal-based — `grep` confirms
  the Errata/Amendments lifecycle split, the threshold-gated two-layer structure
  and "current-state wins", and the append-only / supersession rules are present.
- **Asset scaffold present and conditional (D4):** goal-based — `grep` confirms a
  commented correction-section block with a delete-unless instruction, whose shape
  matches `SKILL.md`.
- **How-to note (dogfood):** goal-based — `grep` confirms the repo-only guide
  points at the convention without restating it.
- **Changelog entry:** goal-based — `grep` confirms the `[Unreleased]` entry names
  RFC-0055.
- **Projection + lints:** goal-based — `make build-self` projects to
  `.claude/skills/new-rfc/` with a clean drift gate; `lint-packs` and
  `tools/lint-agent-artifacts.py` (the two lint surfaces) pass.
- **Dogfood walk — the convention reproduces its own precedent:** manual QA —
  applying the documented convention to the RFC-0048 / PR #430 case yields the
  same two-layer shape that case already carries.

## Acceptance Criteria

- [ ] `new-rfc` `SKILL.md` documents recording RFC corrections under two
  lifecycle-keyed sections — **Errata** for a Frozen RFC (Accepted/Rejected),
  **Amendments** for an in-flight Open RFC — selected by the RFC's
  Document-lifecycle class (RFC-0055 D1).
- [ ] `SKILL.md` documents the optional, threshold-gated two-layer structure — an
  authoritative *Current state* layer over a *History / audit trail* (these layer
  names are illustrative; the contract is the two-layer split, not the exact
  heading text) — names the threshold (more than one entry, **or** any entry
  supersedes another), and states that the current-state layer wins on
  disagreement (RFC-0055 D2).
- [ ] `SKILL.md` documents the append-only rule with no per-entry ritual, the
  optional in-place reword (tagged `*(Superseded: …)*`) **for in-flight Amendments
  only**, and that whole-RFC replacement is out of scope — recorded as an Errata
  entry naming the superseding RFC (RFC-0055 D3).
- [ ] `assets/rfc.md` carries an optional, clearly-conditional **commented**
  scaffold for the correction section, headed by a delete-unless-accumulating
  instruction, whose two-layer shape matches `SKILL.md` — heading wording is the
  author's call; the structure is the contract (RFC-0055 D2 shape, in the D4
  template home).
- [ ] No `docs/CONVENTIONS.md` change is made (RFC-0055 D4) and no file under
  `docs/rfc/*.md` is modified (RFC-0055 D5, forward-only) — verifiable from the diff.
- [ ] The repo-only guide `docs/guides/governance-extras/how-to/new-rfc.md` gains
  a short note pointing at the convention; it does not restate the convention and
  does not ship with the pack.
- [ ] `docs/product/changelog.md` `[Unreleased]` records the skill-behavior change,
  naming RFC-0055 and the current unreleased `governance-extras` version (0.4.0 today).
- [ ] `make build-self` projects the source edits to `.claude/skills/new-rfc/` with
  a clean drift gate; `lint-packs` and `tools/lint-agent-artifacts.py` pass.
- [ ] Dogfood walk (manual QA): applying the documented convention to RFC-0048 /
  PR #430 reproduces the same two-layer *structure* it already carries — a
  current-state layer (authoritative, wins on disagreement) over a dated
  append-only audit trail — even though RFC-0048 predates the convention and uses
  its own heading wording (forward-only, D5, so it is read not retrofitted). The
  walk and its observed result are recorded in the PR description.

## Assumptions

- Technical: the convention's substance lands in pack source
  (`packs/governance-extras/.apm/skills/new-rfc/{SKILL.md,assets/rfc.md}`) and
  projects via `make build-self`; the projected `.claude/skills/new-rfc/` mirrors
  confirm `governance-extras` is in this repo's working-tree projection (source:
  file listing + `Makefile build-self`).
- Technical: no executable behavior is added; verification is goal-based grep plus
  the self-host drift gate and the two lint surfaces `lint-packs` /
  `tools/lint-agent-artifacts.py` (source: `tools/lint-agent-artifacts.py` present).
- Process: the work is constrained by RFC-0055 (Accepted 2026-06-28), forward-only,
  no retrofit of the existing correction sections (source:
  `docs/rfc/0055-rfc-amendment-and-errata-convention.md`).
- Process: a user-visible skill-behavior change needs a
  `docs/product/changelog.md` `[Unreleased]` entry (source: changelog maintenance
  header).
- Process: `governance-extras` is at 0.4.0 and unreleased; the change rides it with
  a changelog entry and no version bump — packs are usable unreleased (source: no
  git tag + `0.4.0` still under `[Unreleased]`; user confirmation 2026-06-28).
- Product: the repo-only how-to guide gains a short dogfood note (RFC-0055 D4 "may";
  user confirmation 2026-06-28).
