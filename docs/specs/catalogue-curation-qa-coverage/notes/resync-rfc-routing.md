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
source repo (`llm-wiki-kit`) has a small documentation-only update to one
candidate: the candidate's description field has a typo corrected (the behavior
is unchanged; only the description prose differs). A re-sync runs.

**How the algorithm classifies it:** The re-sync reads `last-synced.toml` and
computes the content hash for the candidate. The description typo-fix changes
the hash → the candidate is classified `changed` (not `unchanged`). The skill
then checks the prior RFC: RFC-0001 is Frozen. Because the content change is a
documentation correction (no behavioral change, no verdict reversal, no new
candidate), the skill classifies it as a **genuine correction** and routes to
the Erratum path. The skill asks the operator to confirm the classification
before writing.

**Expected skill behavior:**

1. The skill runs re-sync, classifies the candidate as `changed`, and detects
   that RFC-0001 is Frozen.
2. The skill presents the delta to the operator: what changed (the description
   typo-fix), the prior verdict, and asks: "Is this a correction to the prior
   verdict or a new decision? (correction / new-decision)"
3. Operator answers "correction."
4. The skill records an **Erratum** entry, appended additively to RFC-0001
   under an `## Errata` section.
5. The Erratum names: the date, what changed (the description field), the
   corrected value, and the reason it is a correction rather than a new decision.
6. The skill does **not** author a new RFC.
7. The skill does **not** append new decisions to the Frozen RFC body.

**Expected output signals:**
- "RFC-0001 is Frozen — recording operator-confirmed correction as an Erratum."
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
     │    └─ Yes → Erratum (additive, no new file; operator confirms classification)
     │
     └─ New candidates or reversed verdicts?
          └─ Yes → New RFC + Erratum entry on prior RFC naming superseder
```
