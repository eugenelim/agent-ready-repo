# How to author product docs

**Use this when:** you need to create, revise, retrofit, audit, or verify
product documentation — pack READMEs, journeys, tutorials, how-to guides,
reference pages, or explanations.
**Prerequisites:** `product-documentation` pack installed.
**Result:** a documentation artifact matched to the reader's job, inspected
against canonical source behavior, with a stated mode and artifact decision.

## Five modes

The `author-product-docs` skill operates in five modes. You do not need to name
the mode — it infers from your request.

| Request type | Mode | What happens |
|---|---|---|
| "Write", "create", "add docs for" | **Create** | Smallest useful new artifact |
| "Revise", "improve", "update", "rewrite" | **Revise** | Improves one artifact while preserving its role |
| "Retrofit", "connect", "unify", "restructure" | **Retrofit** | Restructures a connected documentation experience |
| "Audit", "check", "review for" | **Audit** | Produces findings without editing |
| "Verify", "confirm docs match", "check against" | **Verify** | Confirms documentation matches current shipped behavior |

## First request

Ask your agent:

> Write a how-to guide explaining how to [your most common user task].

The skill reads the relevant pack sources, proposes a documentation contract,
and drafts a task-first guide. You confirm before any files change.

Other entry points:

> Revise the pack README for [pack name] to lead with what the user can
> accomplish.

> Audit the onboarding guides for inventory-first writing.

> Verify this reference page still matches what the skill actually does.

## What the skill inspects

Before drafting, `author-product-docs` reads:

- `pack.toml` — what the pack declares it does, its scope, dependencies
- Skill and command sources — actual behavior, not the README's description
- Existing guides, README, and journey for the pack

It does not invent capabilities. If a claim in the existing documentation does
not appear in the canonical sources, it flags it as unverified rather than
preserving it.

## The artifact model

One artifact is the default. The skill does not create empty category
directories or produce one page of every Diátaxis kind without need.

| Artifact | Lives at |
|---|---|
| Pack README | `packs/<pack>/README.md` |
| Journey | `packs/<pack>/JOURNEY.md` |
| Tutorial | `guides/<pack>/tutorials/<slug>.md` |
| How-to | `guides/<pack>/how-to/<slug>.md` |
| Reference | `guides/<pack>/reference/<slug>.md` |
| Explanation | `guides/<pack>/explanation/<slug>.md` |

For adopter repositories, the skill inspects the host layout rather than
imposing these paths.

## Audience routing

The skill distinguishes two documentation audiences:

- **External catalogue or product users** → `guides/<pack>/`
- **Internal maintainers or contributors** → `docs/guides/`

It does not route internal guidance into the public guide tree, and it does not
route product documentation into the maintainer tree.

## What remains your decision

- Whether the proposed page kind is right for the reader you have in mind.
- Whether the artifact set is the minimum useful set.
- Whether the draft accurately reflects the product as users will experience it.
- Whether a generated or rendered artifact needs source changes before the
  documentation can be accurate.

## See also

- [Write a guide](write-a-guide.md) — step-by-step for creating one guide page.
- [About the Diátaxis framework](../explanation/the-diataxis-framework.md) — the
  four page kinds and the link-out discipline.
