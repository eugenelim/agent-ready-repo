---
title: "The Digital Experience Contract"
summary: "Understand how one shared contract connects product strategy, experience design, engineering, and delivery evidence."
pack: core
kind: explanation
---

# The Digital Experience Contract

The Digital Experience Contract is a shared markdown template that connects four discipline packs across a single product's lifecycle. It is the answer to one failure mode: artifacts that each pass their own rubric but produce a product experience that is locally polished and globally broken — a strategy with no adoption hypothesis, a design with no implementation evidence, a build that declares done at lint pass.

## The contract

The contract is a blank form. Adopters create one per product in their project's `docs/` directory and fill each section as the relevant discipline does its work. The form is not a ceremony: at explore tier, only the fields the contract annotates `Required: explore+` are required. At production tier, the full set is required. The tier is declared in the frontmatter and can be raised as the product matures.

The form travels across the four packs because each pack carries an identical copy of the blank template in its skill references. The four copies must stay identical — `tools/repo/check_contract_drift.py` enforces this. If they drift, the tool names which copy diverged and why.

The contract ships with `schema-version: "1.0"` in its frontmatter. When a breaking field change is needed in a future release, the schema version bumps, the drift check detects mismatched versions, and the change is forced to be deliberate.

## The three tiers

Each field in the contract carries a `Required: <tier>+` annotation. The tier reflects when the field matters — not when you should fill it in. Those annotations are the authority on what each tier owes; read the template itself rather than a list here.

| Tier | When | What's required |
|---|---|---|
| **Explore** | Early discovery; prototypes | The fields the contract annotates `Required: explore+` |
| **Pilot** | Pre-release; limited users | Everything in Explore, plus the fields the contract annotates `Required: pilot+` |
| **Production** | Public; all users | Everything in Pilot, plus the fields the contract annotates `Required: production+` |

Explore-mode work is intentionally lightweight. An early prototype that fills only its explore-tier fields and moves fast is the right use of the contract at that stage. Do not treat the full field set as a checklist for exploratory work.

## The ownership map

Each section of the contract belongs to one discipline. Skills in that pack fill the section. Skills from other packs may read all sections, but must not silently rewrite a section owned by another discipline.

| Section | Owner |
|---|---|
| Strategy | `product-strategy` |
| Product Engineering | `product-engineering` |
| Experience Design | `experience-design` |
| Frontend Engineering | `frontend-engineering` (frontend-engineering skill) |

The ownership rule enforces continuity without ceremony. A product-strategy skill that reads the "First-Success Operationalization" field and notices it is absent does not fill it in; it labels its output `[provisional — product-engineering not installed]` and states what PE work remains. The same rule applies in the other direction.

## Graceful capability detection

Any skill that attempts to hand off to a skill in an unavailable pack must:

1. Perform the smallest safe fallback — produce what the skill can without the missing input.
2. Label the output `[provisional — <owner-pack> not installed]`.
3. State what specialist work remains.

No phantom handoff may ship. Every handoff either resolves to an installed skill or degrades explicitly. "I populated the Experience Design section based on the product brief" is not a graceful degradation if experience-design pack is not installed; "I sketched the primary journey from the PE brief — provisional, experience-design review pending" is.

This rule is what makes the contract safe across partial installations. An adopter without the `frontend-engineering` pack installed can still populate the contract's other sections; the Frontend Engineering section is left blank or marked `[provisional — frontend-engineering not installed]` until the pack is added.

---

*The four pack copies of the template must be byte-identical; use `tools/repo/check_contract_drift.py --root .` to verify. Relevant pack journey pages: [product-strategy](../../product-strategy/), [experience-design](../../experience-design/), [core](../).*
