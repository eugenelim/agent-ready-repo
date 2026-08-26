---
title: "`catalogue-curation` — guides"
summary: Choose the operator workflow for authoring, compiling knowledge, surveying, assimilating, governing, or redistributing catalogue primitives.
pack: catalogue-curation
kind: explanation
---

# `catalogue-curation` — guides

The operator's toolkit for **growing and maintaining** an agent-skill catalogue:
write new skills to standard, bring good work in from outside (shaped to our craft),
compile pack-owned knowledge, survey a whole repo, and derive an owned catalogue
for another org or domain.
Domain-agnostic — the same toolkit serves a non-SDLC catalogue.

---

## Step 1 — Standards (read this first)

[**Skill standards**](explanation/skill-standards.md) — one page. The three standards every skill is measured against, whether you write it or bring it in. Gives you the reading order for what follows.

---

## Step 2 — Choose your path

### Main journey: writing a new skill

Building a skill from scratch — frontmatter to PR.

1. [Skill standards](explanation/skill-standards.md) — what you'll be measured against *(Step 1 above)*
2. [Your first skill](tutorials/your-first-skill.md) — the end-to-end tutorial: workspace design, standards inline at each step, definition of done
3. [How to author a skill](../_shared/how-to/author-a-skill.md) — the deep reference once you've done the tutorial

### Side journey: assimilating an existing skill or repo

Bringing external work into the catalogue — safely, and shaped to convention.

1. [Skill standards](explanation/skill-standards.md) — know what you're measuring incoming material against *(Step 1 above)*
2. Choose the entry point for your material:
   - [Your first assimilation](tutorials/first-assimilation.md) — one skill from a URL
   - [Your first subagent](tutorials/your-first-subagent.md) — one subagent definition; where the OWASP AST review shifts focus
   - [Survey a repo](how-to/survey-a-repo.md) — a whole source at once, resumably
3. [The convergence model](explanation/the-convergence-model.md) — why assimilation shapes rather than pastes; the three convergence layers in full

### Side journey: shipping pack-owned knowledge

Turn a maintained reference corpus into a portable, discoverable router Skill.

1. [Author and compile an OKF bundle](how-to/author-an-okf-bundle.md) — declare a reference-only OKF 0.2 bundle, compile its managed output, check drift, and inspect catalogue discovery
2. [Catalogue format](../_shared/reference/catalogue-format.md) — the surrounding manifest, schema, ownership, and validation contract

---

## Step 3 — Go deeper (when you're ready)

- [The convergence model](explanation/the-convergence-model.md) — three layers, two primitive types, the no-merge-back principle, and the pack arc
- [Catalogue operator journey](explanation/catalogue-operator-journey.md) — how org-stack engineers, catalogue maintainers, and catalogue authors use the pack at their altitude
- [Why curation is its own pack](explanation/why-catalogue-curation.md) — the single-authoritative-source model and the fail-closed posture

---

## Full reference

### Tutorials

- [Your first skill](tutorials/your-first-skill.md) — write a new skill from scratch; workspace design, standards inline, definition of done
- [Your first assimilation](tutorials/first-assimilation.md) — bring one external skill in, safely and to convention
- [Your first subagent](tutorials/your-first-subagent.md) — bring in an external subagent definition; where the OWASP AST review shifts focus

### How-to

- [Author and compile an OKF bundle](how-to/author-an-okf-bundle.md) — project pack-local OKF knowledge into a portable router Skill and verify it is current
- [Survey a repo for what to adopt](how-to/survey-a-repo.md) — inventory a whole source into a reviewable RFC, resumably
- [Create a self-hosted catalogue](../_shared/how-to/create-a-self-hosted-catalogue.md) — derive, brand, validate, and package an owned catalogue for another org or domain

### Reference

- [The ledger and the engine guard](reference/ledger-and-guard.md) — where assimilation state lives, and what the guard blocks
- [Catalogue CI contract](../_shared/reference/catalogue-ci-contract.md) — publication ordering, exit codes, and responsibility boundaries for CI-driven catalogue releases

### Explanation

- [Skill standards](explanation/skill-standards.md) — the three standards, the definition of done for both paths, and the reading order
- [The convergence model](explanation/the-convergence-model.md) — the three convergence layers (agentskills.io, catalogue craft, OWASP AST), two primitive types, and the no-merge-back principle
- [Catalogue operator journey](explanation/catalogue-operator-journey.md) — how org-stack engineers, catalogue maintainers, and catalogue authors use the pack at their altitude
- [Why curation is its own pack](explanation/why-catalogue-curation.md) — the single-authoritative-source model and the fail-closed posture

---

Installing and upgrading live in [`../_shared/`](../_shared/).
