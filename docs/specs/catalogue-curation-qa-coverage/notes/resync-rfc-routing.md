# Expected behavior: resync RFC routing

Documents the three routing cases for AC4. The live QA session (AC4) exercises
these cases against the `agent-commander` RFC-0001 produced in the 2026-07-22
`assimilate-repo` session.

Source authority: `packs/catalogue-curation/.apm/skills/assimilate-repo/references/re-sync.md`
and `docs/rfc/0055-*.md` (RFC-0055 governs Errata and Amendments).

---

## Case 1: Source RFC is Open → record as Amendment

**Setup:** The prior sync produced RFC-0001 in the `agent-commander` repo, and
RFC-0001 is still in `Status: Open` (i.e., not yet Accepted or Rejected).

A re-sync of the same source (e.g. `llm-wiki-kit`) finds changed or new
candidates.

**Expected skill behavior:**

1. The skill reads the `last-synced.toml` baseline and classifies each
   candidate as `unchanged`, `changed`, or `new`.
2. For `changed` and `new` candidates the skill surfaces verdicts as it would
   in a first-time survey.
3. Because the prior RFC is Open, the skill records the delta **in-place as
   an Amendment** to RFC-0001 — not as a new RFC.
4. The Amendment entry is appended to RFC-0001 under an `## Amendments` section
   (RFC-0055 form), with a date and a summary of the changed verdicts.
5. The skill does **not** author a new RFC file.

**Expected output signals:**
- "RFC-0001 is Open — recording delta as an Amendment."
- The amendment section is added to the existing RFC-0001 file in
  `agent-commander`.
- No new RFC file is created.

---

## Case 2: Source RFC is Frozen + genuine correction → Erratum

**Setup:** RFC-0001 in `agent-commander` has been Accepted (Frozen). The
operator — not a re-sync — notices that a verdict recorded in RFC-0001
contains a typo in the destination pack name (e.g., the skill was recorded
as going to `core` but the correct destination was `governance-extras`).

**Why operator-initiated:** A verdict typo does not change the source
candidate's content. The re-sync algorithm classifies by content hash; if the
source content is unchanged, the candidate is marked `unchanged` and skipped.
The correction must be initiated by the operator, who identifies the error
directly (e.g., during RFC review, code review, or reading the output later)
and tells the skill to record a correction.

This is a **genuine correction** — a verdict typo, not a new decision.

**Expected skill behavior:**

1. The operator supplies: the RFC number, the incorrect field, and the
   corrected value — this is the input, not the re-sync algorithm's output.
2. Because the prior RFC is Frozen and this is a genuine correction (not a new
   decision or reversal), the skill records an **Erratum** entry, appended
   additively to RFC-0001 under an `## Errata` section.
3. The Erratum names: the date, the incorrect field, the corrected value, and
   the reason it is a correction rather than a new decision.
4. The skill does **not** author a new RFC.
5. The skill does **not** append new decisions to the Frozen RFC body.

**Expected output signals:**
- "RFC-0001 is Frozen — recording operator-supplied correction as an Erratum."
- The erratum entry is appended to RFC-0001's Errata section.
- No new RFC file is created.

---

## Case 3: Source RFC is Frozen + new candidates or reversed verdicts → new RFC

**Setup:** RFC-0001 in `agent-commander` has been Accepted (Frozen). The
re-sync reveals new source candidates (files added to `llm-wiki-kit` since
the prior sync) and one reversed verdict (a skill that was previously rejected
should now be assimilated given new context).

These are **new decisions and reversed verdicts**, not corrections.

**Expected skill behavior:**

1. The skill classifies the delta: new candidates present; at least one prior
   verdict reversed.
2. Because the prior RFC is Frozen and these are new decisions (not
   corrections), the skill authors a **new RFC** — e.g., RFC-0002 in
   `agent-commander`.
3. The new RFC follows the standard RFC format with: the new candidates +
   verdicts, the reversed verdict with justification, and a reference to
   RFC-0001 as the prior sync.
4. The skill records an **Erratum entry on RFC-0001** naming the superseding
   RFC (RFC-0002). This is RFC-0055's documented whole-RFC supersession form.
5. The skill does **not** append new decisions directly to RFC-0001's body.

**Expected output signals:**
- "RFC-0001 is Frozen — new decisions require a new RFC."
- A new RFC file (RFC-0002 or next available number) is authored.
- An Erratum entry is appended to RFC-0001: "Superseded by RFC-0002 (date)."
- The skill explicitly states: "New decisions are not appended to a Frozen RFC."

---

## Routing decision tree

```
Re-sync delta found
│
├─ Prior RFC Open?
│    └─ Yes → Amendment (in-place on prior RFC)
│
└─ Prior RFC Frozen?
     ├─ Genuine correction (typo, moved destination)?
     │    └─ Yes → Erratum (additive, no new file)
     │         Note: correction is operator-initiated, not algorithm-detected
     │
     └─ New candidates or reversed verdicts?
          └─ Yes → New RFC + Erratum entry on prior RFC naming superseder
```
