# One shared source projects a file into every skill location that needs it

- **Status:** Draft
- **Level:** feature

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
- Admits: deciding what happens to the two copies that exist today —
  `packs/core/.apm/skills/work-loop/scripts/file_safety.py`, which is
  undeclared and hand-maintained, and the architect gate copy that
  `docs/specs/architect-design-document-gates/spec.md` AC-0079 records as
  hand-maintained under the same practice.
- Excludes: the existing `packs/… → packages/…` pairs. Those work, and
  `packages/agentbundle/agentbundle/build/self_host.py:118-150` already
  declares them.
- Excludes: changing what any shared helper does. This is about where copies
  come from, not about their behaviour.

## Owner

AgentBundle distribution maintainers. The mechanism lives in
`packages/agentbundle/agentbundle/build/self_host.py`, so a change to it is an
agentbundle engine change: `packs/AGENTS.local.md:20-22` requires an
`Engine-Change-RFC:` trailer naming a real RFC and matching version bumps in
`pyproject.toml` and `agentbundle/version.py`.

## Unresolved questions

- Does a `packs/**` destination belong in `_library_mirrors`, in a new
  declaration function, or in a generalised one? Every pair declared today
  runs `packs/… → packages/…`, so a destination inside `packs/` is a shape the
  mechanism has never written.
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

## Opportunity

`test_packaged_runtime_closure.py:99-106` states the rule this is about: a copy
that "sat outside the declared pairs and so was maintained by hand: two tests
compared it after the fact, but nothing wrote it" was a defect worth removing,
and "asserting the pair is declared — not merely that the bytes match today —
is what keeps it on the `make build-self` path."

The mechanism that rule depends on cannot express a `packs/**` destination, so
a pack script that needs a shared helper has only two options today: import
`agentbundle`, which an adopter install cannot resolve, or hand-copy and pin
the bytes with an after-the-fact comparison. Both existing `packs/**` copies
of `file_safety.py` took the second, and both therefore carry the shape the
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
