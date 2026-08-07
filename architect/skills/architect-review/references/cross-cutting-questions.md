# Cross-cutting question bank — the ARB-grade questions, ceremony stripped

These are architecture-quality questions that are *not* in the cloud pillar
spine but catch the most expensive errors — strategic misfit, duplicated
capability, lock-in, an unsupportable system in two years. Mined from
enterprise architecture-review practice with the governance ceremony left
behind: the questions come across, the board does not. Make the WA pass
*actively ask* them, not just have them on a shelf.

> Note: this reference is intentionally duplicated from `architect-design`'s
> `references/cross-cutting-questions.md`. Skill autonomy beats DRY at this
> scale — each skill stands alone. See the pack README.

## The questions

- **Strategic / business alignment** — does this design serve the stated goal?
  The cheapest 100× error to catch is building the wrong thing well; ask it
  first.
- **Build-vs-buy / reuse** — does this duplicate an existing capability or
  service? What does building it cost over buying or reusing?
- **Lock-in / exit** — can we leave this provider/service, and what's the
  switching cost? (Sharp across the provider set: a primitives provider lowers
  lock-in; a deep managed-service bet raises it — credit or charge it honestly.)
- **Supportability in 2 years** — who runs this, with what skills, and what's
  the deprecation path? A design no one can operate is a liability dressed as an
  asset.
- **Data ownership & integration contract** — who owns the data; sync vs. async
  boundaries; the API contract and its versioning story.
- **Third-party security attestation / restricted-scope-data assessability** —
  if the workload handles restricted-scope user data (e.g. Google-user data
  under OAuth scopes) or integrates a third party that must attest its security,
  is the system **assessable** against the relevant gate? Name **CASA** (Google's
  Cloud Application Security Assessment, built on **OWASP ASVS**, tiered T1
  self-scan → T3 lab-verified, triggered by restricted-scope OAuth access) as a
  **downstream verification gate** the design must be *ready for* — minimize
  OAuth scopes, keep trust boundaries assessable, design for least data.

## CASA / ASVS is referenced, never reproduced

This question stays at **design altitude**: it asks whether the design is shaped
to *pass* a downstream security assessment, not whether each control is met.
**Do not reproduce ASVS or CASA control checklists in this pack.** Route
control-level verification to the repo's `security-reviewer` and
`security-checklists` — that is where the controls live. Naming the gate and
designing to be assessable is the architect's job; running the gate is not.

## Several already live in the NFR checklist

Supportability, data-handling, and compatibility overlap `nfr-checklist.md`. The
move here is not to restate them but to make the WA pass *actively ask* the
alignment + build-vs-buy + lock-in questions the NFR list doesn't, and to add the
assessability pointer above.

## Use, don't recite

Ask the questions that bite for *this* design. A design that answers all six
generically, with no teeth, has turned a thinking prompt into a section template.
