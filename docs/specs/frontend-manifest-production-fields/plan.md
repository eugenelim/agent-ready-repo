# Plan: frontend-manifest-production-fields

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`
- `packs/frontend-engineering/JOURNEY.md`, `pack.toml`, `.claude-plugin/plugin.json`
- `docs/specs/frontend-engineering-doctrine-update/spec.md`, `workspace.toml`

**What demonstrates done**
- `catalogue lint` clean for the pack; `make build-self FORCE=1`; `make ci`.

**What I am NOT changing**
- The frontend reviewer's lens, or any reviewer's scope.
- The other eleven manifest fields.
- The Digital Experience Contract — this makes FE meet it, not redefine it.

## Declined patterns

- **Tempted:** make FE actually assess security and reliability, since it is
  already looking at the surface. **Declined:** that is what the two backlog
  entries explicitly ruled out, and it would put an unqualified verdict in front
  of a ship decision. Recording the handoff is the useful half.
- **Tempted:** require both fields at every tier. **Declined:** the contract
  annotates them `production+`, and requiring production ceremony on an explore
  surface is the thing the tiering exists to prevent.
- **Tempted:** leave them blank when unknown. **Declined:** a blank field cannot
  be distinguished from an unasked question. AC3 makes the "not at this tier"
  answer explicit.
- **Tempted:** skip the pack version bump — it is only prose. **Declined:** two
  new required fields change what an adopter's completion check demands.

## Anchor-test sweep

- `JOURNEY.md:161` enumerates the eleven fields in prose — updated (AC5).
- `pack.toml` ↔ `.claude-plugin/plugin.json` version parity is now enforced by
  CAT-L009, which I turned on in #953. It fired on the bump, exactly as intended,
  and the manifest was synced.
- `evals/eval_queries.json` references the manifest by name only, so no eval
  pins the field list.
- `dist/` is gitignored; projection is regenerated, not committed.

## Verification log

- **AC1–AC5** applied to SKILL.md (manifest table + verify mode) and JOURNEY.md.
- **AC6** pack 0.1.4 -> 0.2.0; plugin.json synced; `make build-self FORCE=1` ok.
- **Lint** `lint_catalogue(pack='frontend-engineering')` -> CAT-L007/8/9 clean.
- **AC8** two entries removed (125 -> 123).
- **REVIEW** `adversarial-reviewer` = named skip (session instruction prohibits
  subagent dispatch). Self-reviewed against the spec-less checklist.
