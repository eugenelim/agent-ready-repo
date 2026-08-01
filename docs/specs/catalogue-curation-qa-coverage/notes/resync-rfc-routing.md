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

## Case 2: Source RFC is Frozen + verdict typo → Erratum (operator-initiated)

**Setup:** RFC-0001 in `agent-commander` has been Accepted (Frozen). It
recorded a `query-planner` skill with a typo in the verdict field:
`"Assimulate"` instead of `"Assimilate"`. This was a transcription error when
RFC-0001 was authored; the decision itself (assimilate `query-planner`) is
correct. The source candidate is unchanged (content hash matches
`last-synced.toml`). A re-sync runs, triggered by a new candidate in the source.

**How the algorithm classifies it:** The re-sync reads `last-synced.toml` and
computes the content hash for `query-planner`. Hash matches → the candidate is
classified `unchanged` and skipped (re-sync.md:12-16 — unchanged candidates are
not re-surfaced). The skill does **not** auto-detect the typo. After the re-sync
summary is presented, the operator notices the `"Assimulate"` typo in the prior
RFC's verdict and flags it as a correction request.

**Expected skill behavior:**

1. The skill classifies `query-planner` as `unchanged` and skips it during the
   re-sync pass — the typo is not auto-detected.
2. After the re-sync summary, the operator flags: "`query-planner` verdict in
   RFC-0001 has a typo — `Assimulate` should be `Assimilate`."
3. The skill recognizes this as an operator-reported genuine correction
   (verdict typo, per re-sync.md:29). Since RFC-0001 is Frozen, the skill
   routes to the Erratum path.
4. The skill requests **Approver sign-off** before recording the Erratum
   (per `new-rfc/SKILL.md:394-396`: "corrections are appended here,
   Approver-signed"). It does not write until sign-off is confirmed.
5. The skill records an **Erratum** entry, appended additively to RFC-0001
   under an `## Errata` section.
6. The Erratum names: date, Approver sign-off, candidate (`query-planner`),
   prior verdict text (`"Assimulate"`), corrected verdict text
   (`"Assimilate"`), and reason (typographical error — not a reversed
   decision).
7. The skill does **not** author a new RFC.
8. The skill does **not** append any new decisions to the Frozen RFC body.

**Expected output signals:**
- "RFC-0001 is Frozen — recording operator-confirmed correction as an Erratum."
- The skill pauses and requests Approver sign-off before writing the Erratum.
- The erratum entry (with Approver name) is appended to RFC-0001's Errata section.
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
4. The skill requests **Approver sign-off** before appending the supersession
   Erratum to RFC-0001 (per `new-rfc/SKILL.md:394-396`: Frozen-RFC Errata
   are Approver-signed). It does not write the Erratum until sign-off is
   confirmed.
5. The skill records an **Erratum entry on RFC-0001** naming the superseding
   RFC (RFC-0002). This is RFC-0055's documented whole-RFC supersession form.
6. The skill does **not** append new decisions directly to RFC-0001's body.

**Expected output signals:**
- "RFC-0001 is Frozen — new decisions require a new RFC."
- A new RFC file (RFC-0002 or next available number) is authored.
- The skill pauses and requests Approver sign-off before writing the Erratum on RFC-0001.
- An Erratum entry (with Approver name) is appended to RFC-0001: "Superseded by RFC-0002 (date)."
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
     ├─ Genuine correction (verdict typo, moved destination)?
     │    └─ Yes → Erratum (additive, no new file; always operator-confirmed —
     │              re-sync never auto-classifies a correction; the operator
     │              flags the correction and the skill routes to Erratum)
     │
     └─ New candidates or reversed verdicts?
          └─ Yes → New RFC + Erratum entry on prior RFC naming superseder
```
