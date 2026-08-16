# Spec: contracts-readme-governance-sweep

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none. Documentation text only; no schema, code, or behaviour changes.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (no risk trigger fired). Checked the governance-surface trigger
explicitly: it does NOT fire. This edits prose *about* contracts, not any
contract, schema, or authority rule — every rule the file states survives with
the same meaning. -->

## Objective

`contracts/` ships inside a packaged catalogue archive; `docs/` does not. So
every repo-relative link out of `contracts/README.md` — and every internal
governance ordinal in its prose — is dangling for the adopter who receives it.
The same page tells them `contracts/` is authoritative and then points at three
documents they do not have.

Success: an adopter reading the shipped `contracts/README.md` can follow every
link it offers, and learns the same rules without being asked to resolve an
internal ordinal.

## Acceptance Criteria

- [x] **AC1 — no internal governance ordinal survives in prose.**
  `grep -nE '\b(RFC|ADR)-0[0-9]{3}\b' contracts/README.md` matches nothing
  outside a URL. The rule each ordinal carried is stated instead: the authority
  paragraph says `contracts/` wins and that every listed contract is bundled
  byte-identically, without citing the decision numbers that established it.

- [x] **AC2 — the shipped page has no dangling link.** Repo-relative links into
  `docs/` are replaced with absolute project URLs, matching the precedent
  `packages/credbroker/README.md` already sets (working GitHub URLs, ordinal-free
  link text). The one remaining relative link —
  `../guides/_shared/reference/agentskills-io-standard.md` — is kept relative
  deliberately: `guides/_shared/` travels in the same archive, so it resolves.

- [x] **AC3 — no knowledge is dropped.** The per-file → governing-design mapping
  that the old "Governing spec or RFC" table column carried is preserved as a
  prose section. The origin fact (the contract was first authored at
  `docs/specs/adapter-contract/` and renamed here) survives, with its link.

- [x] **AC4 — every link target exists.** Each URL's path resolves to a file in
  this repository, and the relative link resolves on disk.

- [x] **AC5 — `profiles/AGENTS.md` names the machine source of truth.** It
  describes the profile schema in a table with no pointer to
  `contracts/profile.schema.json`, so a reader cannot tell which one wins. The
  pointer is added to § *Current schema fields*, and the file stays under the
  150-line subdirectory `AGENTS.md` cap.

- [x] **AC6 — the `profiles-agents-normative-pointer` premise is corrected, not
  inherited.** That entry says it "mirrors" a pointer wave 1 added to
  `packs/AGENTS.md` and `packs/README.md`. No such pointer exists in either file
  — `docs/product/research/catalogue-audience-discovery.md:276` records the same
  finding independently ("packs/AGENTS.md does NOT say 'the machine source of
  truth is `contracts/pack.schema.json`'"). This spec therefore establishes the
  pattern rather than mirroring it, does `profiles/` only as the entry asks, and
  records the `packs/` gap as its own entry rather than silently widening scope.

- [x] **AC7 — the backlog entries are dispositioned.**
  `contracts-readme-governance-markers` and `profiles-agents-normative-pointer`
  are removed; the `packs/` gap AC6 surfaces is recorded as a new entry.

## Boundaries

### Never do

- Never change a rule while restating it. The authority model, the
  byte-identical-bundling requirement, and the per-file mapping keep their
  meaning exactly.
- Never touch a contract file, schema, or `agentbundle/_data/` twin. Prose only.
- Never add the pointer to `packs/` in this PR. AC6 records it instead — it is a
  second file pair and a second decision.

## Assumptions

- `contracts/` ships and `docs/` does not. Verified in the catalogue packager:
  `contracts` is in its always-included directory set, alongside `packs`,
  `profiles`, and `.claude-plugin`; `docs` appears in no include list.
