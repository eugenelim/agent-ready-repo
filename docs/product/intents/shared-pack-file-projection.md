# One shared source projects a file into every skill location that needs it

- **Slug:** `shared-pack-file-projection`
- **Status:** Withdrawn
- **Level:** feature
- **Owner:** eugenelim

## Disposition — withdrawn 2026-11-05, drift is already pinned and a past projection was retired

Checked on 2026-11-05: all eight `file_safety.py` copies under `packs/**` hash identically (one md5), and roster tests pin byte identity for several copies against the `close-work` source (for example `tests/roster/test_navigate_decisions_file_safety_mirror.py` and `test_architect_assess_file_safety_mirror.py`). The repository also built and then retired this exact mechanism: `packages/agentbundle/agentbundle/build/shared_libs.py` records that a byte-copy projection of shared helpers into every skill was removed in favour of an in-process import. Extending `DUP_GROUPS` is not a cheap alternative either, because `check_dup_sync` in `tools/lint-catalogue-curation-guard.py` is fixed to `packs/catalogue-curation/.apm/skills`. Reopen only if a shared helper spreads to many more skills with no byte pin.

## Outcome

A maintainer puts a shared helper in one place and declares where it lands, and
`make build-self` writes every copy. A fix to the shared source reaches every
skill that carries it by regeneration, instead of waiting for someone to
remember which skills hold a copy.

## Boundary

- Admits: a declared source-to-destination projection whose destination is
  under `packs/**`, covering a skill's `scripts/`, `assets/`, and
  `references/` subfolders and seed files.
- Admits: one source fanning out to several destinations, since the case that
  raises this is a helper shared by more than one skill.
- Admits: deciding what happens to the copies that exist today — eight
  byte-identical `file_safety.py` files under `packs/**` (in `work-loop`,
  `work-intake`, `close-work`, `repository-grounding`, `architect-design`,
  `architect-assess`, `navigate-decisions` and `new-rfc`). Only the
  `close-work` copy is a declared pair, mirrored into `catalogue_tooling` by
  `_library_mirrors`; the other seven are hand-maintained, as
  `docs/specs/architect-design-document-gates/spec.md` AC-0079 records for the
  architect gate copy.
- Excludes: the existing `packs/… → packages/…` pairs. Those work, and
  `_runtime_projections` and `_library_mirrors` in
  `packages/agentbundle/agentbundle/build/self_host.py` already declare them.
- Excludes: changing what any shared helper does. This is about where copies
  come from, not about their behaviour.

## Owner

AgentBundle distribution maintainers. The mechanism lives in
`packages/agentbundle/agentbundle/build/self_host.py`, so a change to it is an
agentbundle engine change: `packs/AGENTS.local.md` requires an
`Engine-Change-RFC:` trailer naming a real RFC and matching version bumps in
`pyproject.toml` and `agentbundle/version.py`.

## Unresolved questions

- Is a projection the right answer at all, or is a pack-aware `DUP_GROUPS`
  enough? The second is a `tools/` change; the first is an agentbundle engine
  change needing an `Engine-Change-RFC:` trailer and matching version bumps.
- If a projection: does a `packs/**` destination belong in `_library_mirrors`,
  in a new declaration function, or in a generalised one? Every pair declared
  today runs `packs/… → packages/…`, so a destination inside `packs/` is a
  shape the mechanism has never written.
- What gates a declared destination that is added but never regenerated? The
  existing pairs are covered because `make build-self` writes them and
  `build-check` compares them; a new destination class needs the same closure
  or it repeats the defect it is meant to remove.
- Does an asset or reference projection need the sibling-closure derivation
  that `_runtime_projections` applies, or is that specific to the flat `_data/`
  layout the current mirrors target?
- Is a seed file the same case? Seeds already have their own flow, so this may
  be two mechanisms rather than one.

## Projection

None yet. This intent is recorded for shaping and is not queued work.

## Prior position this intent must beat

the `DUP_GROUPS` comment in `tools/lint-catalogue-curation-guard.py` records the repository's
existing answer, attributed to RFC-0059's D-scripts decision, option (a) "with
pack lint": "the pack model has no cross-skill shared-code location, so
security-critical helpers are duplicated per skill and MUST stay
byte-identical." Its `DUP_GROUPS` map is the mechanism — a helper filename
plus the skill directories whose `scripts/` carry a copy — and it already pins
`ssrf_check.py` and `write_jail.py` that way.

So duplication is a decision, not an oversight, and this intent argues against
it. It has to answer why a projection is worth more than a parity lint now,
when it was not then. Two things changed that are worth weighing: the copies
have spread beyond the pack that decision was written for, and `DUP_GROUPS` is
hardcoded to `packs/catalogue-curation/.apm/skills`, so a copy in any other
pack — architect's included — is pinned by a bespoke test or by nothing.

The cheaper move, if the decision stands, is to give `DUP_GROUPS` a pack
dimension rather than build a projection. That is a change to `tools/`, needs
no `Engine-Change-RFC:` trailer, and would cover every duplicated helper the
repository already carries.

**Provenance caveat:** the decision's text is not in
`docs/rfc/0059-catalogue-curation-pack.md`. The lint's comment is the
surviving statement of it, so confirm where it was actually recorded before
treating the RFC as its home.

## Opportunity

`test_packaged_runtime_closure.py` states the rule this is about: a copy
that "sat outside the declared pairs and so was maintained by hand: two tests
compared it after the fact, but nothing wrote it" was a defect worth removing,
and "asserting the pair is declared — not merely that the bytes match today —
is what keeps it on the `make build-self` path."

The mechanism that rule depends on cannot express a `packs/**` destination, so
a pack script that needs a shared helper has only two options today: import
`agentbundle`, which an adopter install cannot resolve, or hand-copy and pin
the bytes with an after-the-fact comparison. The seven undeclared `packs/**` copies
of `file_safety.py` took the second, and each therefore carries the shape the
rule calls a defect.

The cost is a security one. `file_safety.py` is the blessed filesystem-confinement
helper, so a hardening fix to the canonical body reaches the declared
`packages/` destinations by regeneration and reaches the `packs/` copies only
when a person notices.

## Source

- Mode: repo-origin
- Locator: `packages/agentbundle/agentbundle/build/self_host.py`
- Revision: 121664d72
- Authority: repository maintainers
