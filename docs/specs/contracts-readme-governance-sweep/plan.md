# Plan: contracts-readme-governance-sweep

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `contracts/README.md` — AC1–AC4.
- `profiles/AGENTS.md` — AC5.
- `workspace.toml` — AC6, AC7.

**What demonstrates done**
- Goal-based: the AC1 grep matches nothing outside a URL; every link target
  resolves on disk; `wc -l profiles/AGENTS.md` under 150; `make ci`.

**What I am NOT changing**
- No contract, schema, or `_data/` twin.
- No `packs/AGENTS.md` or `packs/README.md` — recorded as its own entry.
- No rule meanings; only how they are worded and linked.

## Declined patterns

- **Tempted:** keep the "Governing spec or RFC" table column and just swap its
  links to absolute URLs. **Declined:** it made a wide table wider, and the
  mapping is naturally three groups rather than eleven rows. Moved to prose,
  which also let the agentskills.io link stay relative where it correctly is.
- **Tempted:** strip the agentskills.io link too, for consistency. **Declined:**
  `guides/_shared/` ships in the same archive, so that relative link resolves for
  an adopter. Absolutising it would be cargo-culting the rule past its reason.
- **Tempted:** also add the pointer to `packs/AGENTS.md` and `packs/README.md`
  while establishing the pattern. **Declined:** the backlog entry scopes to
  `profiles/`, and the discovery that `packs/` never got it is a finding to
  record, not a licence to widen the diff.
- **Tempted:** treat `contracts/README.md` as insider context and leave it, the
  way the packages sweep retained `AGENTS*.md`. **Declined:** measured — the
  packager always includes `contracts/`, so it is genuinely exported. The
  retention rule for `AGENTS*.md` turned on not being exported.

## Tasks

### T1 — AC1–AC4: sweep and repoint `contracts/README.md`
- **Mode:** goal-based. `Done when:` the AC1 grep is clean and every link target
  resolves.

### T2 — AC5: `profiles/AGENTS.md` pointer
- **Mode:** goal-based. `Done when:` the pointer is present and the file is under
  the 150-line cap.

### T3 — AC6/AC7: backlog dispositions
- **Mode:** goal-based.

## Anchor-test sweep

Searched for tests pinning either file's content: none pin `contracts/README.md`
prose or `profiles/AGENTS.md` body text. The `AGENTS.md` line-cap check is a
count, not a content hash, and the file stays well under it (75 of 150).

## Verification log

- **AC1** `grep -nE '\b(RFC|ADR)-0[0-9]{3}\b' contracts/README.md` -> matches only
  inside link-definition URLs; no prose ordinal survives.
- **AC2/AC4** all five link targets resolve on disk: distribution-adapters spec,
  RFC-0003, RFC-0076, RFC-0001, agentskills-io-standard.md, plus
  contracts/profile.schema.json for AC5.
- **AC3** the eleven-row "Governing spec or RFC" column became three prose groups;
  the origin fact (authored at docs/specs/adapter-contract/, renamed here) kept with
  its link.
- **AC5** pointer added; `wc -l profiles/AGENTS.md` -> 75, well under the 150 cap.
- **AC6** premise corrected against the code, not inherited: neither packs/AGENTS.md
  nor packs/README.md carries the pointer the entry claimed wave 1 added.
- **AC7** two entries removed, one added (`packs-agents-normative-pointer`); 134 -> 133.
- **REVIEW** `adversarial-reviewer` = named skip (session instruction prohibits
  subagent dispatch). Self-reviewed against the spec-less checklist.
