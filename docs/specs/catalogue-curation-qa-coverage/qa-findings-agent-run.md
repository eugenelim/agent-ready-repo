# QA findings — catalogue-curation skills (AC4–AC7), agent-run report

**Run:** source = `skilldrop` (an external skill catalogue), target catalogue =
this repo (`agent-ready-repo`, HEAD `5b6deec4`).
**Method:** each AC was exercised by acting as the assimilating agent — following the
skill's `SKILL.md` + references against the AC's input (fixture, and real skilldrop
primitives where the AC ingests external source), then comparing the produced behaviour
to the AC's `notes/` expected-behaviour oracle and to this repo's actual CHARTER/tooling.

> **What this is / isn't.** This is an **agent-run findings pass** to help improve the four
> skill paths — *not* the human-gated AC4–AC7 closure. It **does not** flip the parent-spec
> checkboxes, touch `workspace.toml`, or modify any skill source (per the qa-coverage spec's
> Never-do). The AC4–AC7 items still require a human operator's live sign-off. Findings below
> are real observations from tracing the skills; none are invented outcomes.

Severity: 🟥 blocker · 🟧 major · 🟨 minor · ⚪ advisory/positive.

---

## Summary

| AC | Skill / path | Verdict | Headline finding |
|---|---|---|---|
| AC4 | `assimilate-repo` re-sync routing | **PASS (logic) / PARTIAL (runnability)** | Routing tree is correct, but the path has no self-contained fixture and the Approver-sign-off gate lives only in the oracle, not the skill. |
| AC5 | `assimilate-primitive` anti-pattern steering | **PASS** | All three fixtures detected + steered correctly; no false positives on real skilldrop skills/scripts. |
| AC6 | `propose-catalogue-pack` | **PARTIAL** | Reject-on-duplication works, but the skill never encodes the CHARTER's **accelerator-pack** routing (exemption + 3 gates) it's expected to apply. |
| AC7 | `assimilate-primitive` hook-confirm | **PARTIAL** | Detection + confirm gate are correct; the **landing** path (git-hook mechanics, version/inventory bumps) and the **SAST tool list** exist only in the oracle, not the skill. |

**Cross-cutting theme:** the `notes/` oracles are excellent and well-grounded (their cross-refs —
`new-rfc/SKILL.md:392-396`, `AGENTS.md:238-241`, `packs/AGENTS.md:127-134`, `CHARTER.md:60-62` —
all resolve correctly). But they repeatedly carry *procedure the skills themselves should carry*.
A live (non-QA) operator running a skill alone would be under-served on AC4, AC6, and AC7. Highest-
leverage improvement: **promote oracle knowledge into skill `references/`.**

---

## AC4 — `resync-rfc-routing`

**Ran:** the three routing forms against a skilldrop-as-source scenario — "a prior `assimilate-repo`
of skilldrop produced RFC-0001 in this catalogue; skilldrop has since grown, re-sync." Traced against
`assimilate-repo/SKILL.md` step 6 + `references/re-sync.md` + `notes/resync-rfc-routing.md`.

**Outcome:** the decision tree is **correct** and matches RFC-0055's forms — Open → in-place Amendment;
Frozen + operator-flagged typo → additive Erratum (Approver-signed); Frozen + new/reversed → new RFC +
Erratum-naming-superseder. Hash-based `unchanged/changed/new` classification and "the commit log *is*
the sync record" are sound.

**Findings:**
- 🟧 **No self-contained fixture — AC4 isn't runnable standalone.** AC5/AC7 ship fixtures; AC4 ships
  only a `notes/` oracle that references an *external prior artifact* ("agent-commander RFC-0001 from
  the 2026-07-22 session" + its `last-synced.toml`). Those don't exist in a fresh checkout. **Fix:**
  add a fixture prior-RFC (`fixtures/resync/RFC-0001.md`) + a `last-synced.toml` baseline so AC4 is
  exercisable in isolation like the other three.
- 🟧 **Approver-sign-off gate is in the oracle, not the skill.** `notes/resync-rfc-routing.md`
  (Cases 2 & 3) requires pausing for Approver sign-off before writing an Erratum (citing
  `new-rfc/SKILL.md:394-396` "corrections are appended here, Approver-signed" — verified). But
  `assimilate-repo/SKILL.md` step 6 and `re-sync.md` say only "an Erratum entry, additive." An agent
  following the skill alone would write the Erratum unsigned. **Fix:** add the sign-off requirement to
  `re-sync.md`.
- 🟨 **Erratum is operator-initiated, but the skill reads as skill-detected.** `re-sync.md` skips
  `unchanged` candidates by hash, so a verdict typo is *never auto-detected* — the operator flags it.
  SKILL.md step 6 "an Erratum if Frozen + a genuine correction" doesn't convey that. **Fix:** say
  "an operator-flagged correction."
- 🟨 **Wording contradiction on whole-RFC supersession.** `notes/…` Case 3 calls the superseder-Erratum
  "RFC-0055's documented whole-RFC supersession form," while `re-sync.md` and the parent spec
  (`../catalogue-curation/spec.md:81`) say RFC-0055 *does not* define whole-RFC supersession. Reconcile
  the wording ("a catalogue convention, not an RFC-0055 form").

---

## AC5 — `antipattern-steering`

**Ran:** `assimilate-primitive` detection (Phase 2 step 7) against all three fixtures, **plus** a
false-positive check against real skilldrop primitives (a terse skilldrop skill and
`skills/deck-builder/scripts/build_deck.py`).

**Outcome — detection correct on all three, matching the oracle:**
- `script-triggers-skill.sh` → §1 (script triggers skill); mixed primitive → **Steer** (drop the
  `example-agent-cli` line, keep `find|sort`). ✓
- `agent-reviews-own-output.md` (`import-lister`) → §2 (self-review); step 4 only → **Steer** (remove
  step 4, fold stdlib filter into step 3, keep as subagent). ✓
- `flooding-prompt.md` (`generate-release-notes`) → §3 (flooding) → **Steer** (progressive disclosure,
  drop IMPORTANT/REMINDER walls). ✓
- **No false positives** on skilldrop: terse `name`+`description` skills and the deterministic
  `build_deck.py` (data-in/data-out, no agent CLI) pass clean. Good calibration signal.

**Findings:**
- 🟨 **"Exactly one detection" / steer-vs-reject threshold is oracle-only.** `anti-patterns.md` §1 has
  the sole-purpose reject rule, but nothing steers the agent away from **over-detecting** (also flagging
  the tool grant, the bash dash-normalization, etc.). **Fix:** a "one violation → one steer; don't
  compound advisories" note in `anti-patterns.md`.
- 🟨 **No positive counter-example for a legit mechanical subagent.** The oracle works to explain why
  `import-lister` does *not* trip skill-vs-agent confusion or the reviewer ceiling (`CHARTER.md:60-62`);
  a cold agent could mis-route it. **Fix:** add a "this is fine" read-only-subagent example to
  `anti-patterns.md` §2.
- ⚪ **Positive:** strongest of the four — `anti-patterns.md` gives clear tells + rules, and detection
  reproduced the oracle exactly.

---

## AC6 — `propose-catalogue-pack`

**Ran:** a real skilldrop-derived proposal — "add a `knowledge-work-deliverables` pack (ADRs, PRDs,
runbooks, decks, threat models, journey maps from skilldrop)" — through `propose-catalogue-pack/SKILL.md`
step 1 against the actual CHARTER and the 23 existing packs. Also traced the oracle's `database-tooling`
sample.

**Outcome:** the **reject-on-duplication path works.** The proposal duplicates several existing packs —
`product-strategy` (skilldrop's `prfaq`/`okr-cascade`/`strategy-analysis`), `experience-design`
(`user-journey-map`), `architect` (design docs/ADRs), `product-engineering` (PRDs). Correct disposition:
**Reject on Principle 2 (Substantive, not duplicative)**, naming the overlapping packs — which step 1
("duplicates an existing pack … is a reject with the failing principle named") gets the agent to. Step 5
elicitation also correctly surfaces the genuinely-additive slice (skilldrop's `runbook-generator` /
`postmortem-generator` / `incident-comms`, not covered by `release-engineering`).

**Findings:**
- 🟧 **The skill never encodes accelerator-pack routing** (`grep -c accelerator` = 0 in both `SKILL.md`
  and `pack-shell.md`). The CHARTER (`docs/CHARTER.md:49-56`, `:87-90`) defines a whole class:
  tech-stack accelerator packs are **exempt from Principle 1 (Universal)** and must instead clear three
  extra gates (**named maintainer, maturity scope, archiving/deprecation path**). The oracle
  (`notes/propose-pack.md`) expects the skill to apply this routing (its `database-tooling` walkthrough
  hinges on it), but SKILL.md step 1 lists only the four principles. An agent following the skill alone
  would **wrongly fail a tech-stack pack on Principle 1** and **never collect the three gates.** Biggest
  AC6 gap. **Fix:** add the accelerator branch to step 1 (or a `references/accelerator-packs.md`).
- 🟧 **`pack-shell.md:15-16` states a constraint the tooling doesn't enforce.** It claims "`.apm/skills/`
  … at least one primitive, or the pack won't validate," but the oracle confirms `agentbundle catalogue
  lint --deep` passes on an **empty `.apm/`** scaffold — and the skill scaffolds empty by design (step 3
  "empty `.apm/`"). **Fix:** reword to "the scaffold is empty; primitives are added in a later
  assimilation pass," and drop the false validation claim.
- 🟨 **RFC step doesn't cite the canonical template.** SKILL.md step 4 "Emit an RFC …" doesn't point at
  `packs/governance-extras/.apm/skills/new-rfc/assets/rfc.md`; the oracle had to specify the whole
  metadata-bullet block + section order. **Fix:** cite the template path + the added
  `## Candidate primitive inventory` section.
- 🟨 **Privacy-rule violation in the RFC template (oracle-flagged).** `new-rfc/assets/rfc.md` uses
  `<github-handle>`, which violates the repo privacy rule (`AGENTS.md:217-221`, generic
  `<account-handle>` required). One-line fix in `governance-extras`.
- 🟨 **CHARTER internal inconsistency (surfaced here).** `CHARTER.md:52-53` says an accelerator pack
  "clears the **four** principles below, plus …," while `:87-90` says accelerator packs "clear the
  **remaining three** … instead of this one [Universal]." Reconcile.

---

## AC7 — `hook-confirm`

**Ran:** `assimilate-primitive` against `fixtures/hook-confirm/sample-hook.py`, **plus** a detection
check against a real skilldrop script (`build_deck.py`) to test whether the code-confirm class keys on
*hooks* or *executable code* generally.

**Outcome — Phase 1 detection + confirm gate are correct and match the oracle precisely:**
- Shebang `#!/usr/bin/env python3` → higher-scrutiny executable code (SKILL.md step 3). ✓
- Raw body shown **before** the prompt (step 2). ✓
- Requires the exact phrase **`yes, land this code`** — not bare `yes` (SKILL.md:35-37). ✓
- AST01–AST10 correctly scoped to **SKILL.md/behaviour-definition files, not raw scripts** (step 5),
  matching the oracle. ✓
- Real skilldrop `build_deck.py` also trips the code-confirm class → the gate keys on *executable code*,
  not the word "hook." ✓ (broader than the fixture — good.)

**Findings (all on the LANDING path):**
- 🟧 **SAST tool list is stale/incomplete.** step 4 + `ingest-safety.md` name the SAST/SCA as `.snyk` /
  dependency-scan / CodeQL. But this repo's *actual* Python SAST is **bandit + semgrep** — confirmed
  present (`bandit.yaml`, `tools/semgrep/`, and `Makefile:129` `SAST_CONFIG := bandit.yaml .snyk …
  codeql.yml`), and the oracle's step-4 procedure is entirely bandit/semgrep. The skill never names
  either. **Fix:** cite `bandit -c bandit.yaml …` and `semgrep --config … tools/semgrep/` (with the
  repo's `SEMGREP_EXCLUDE`) in step 4 / `ingest-safety.md`.
- 🟧 **The git-hook landing procedure exists only in the oracle.** `notes/hook-confirm.md` documents,
  in detail, things in **no** skill file: the **git-hook vs agent-hook** distinction (git hooks land
  **flat** in `.apm/hooks/`, **no** `.apm/hook-wiring/`); the **version bump + four inventory-string
  updates** (`pack.toml` + `plugin.json` descriptions, `docs/index.md` hook count, `tools/hooks/README.md`);
  and the **run-order** (`lint --deep` before `build-self`, `verify` **after**, or verify step 15
  self-host-drift fails). `packs/core/.apm/hooks/` currently holds 3 hooks — the "bump to 4 + sync every
  inventory string" is real and easy to miss. SKILL.md Phase 2 (steps 6–10) is far too terse for it.
  **Fix:** extract a `references/hook-landing.md` in `assimilate-primitive`. Biggest AC7 gap.
- 🟨 **Phase 2 is under-specified for any pack-mutating land, not just hooks** — "present shaped target →
  write → prompt `make build-self`" omits the version bump, inventory sync, and changelog entry a real
  `packs/` change requires.
- ⚪ **Positive:** the security-critical half (raw-body-first, exact-phrase confirm, AST-scoping) is
  correct and matches the oracle to the line.

---

## Recommended priority

1. 🟧 **AC6** — add accelerator-pack routing to `propose-catalogue-pack` step 1 (entirely absent today).
2. 🟧 **AC7** — reconcile the SAST list (bandit/semgrep) and extract `references/hook-landing.md`.
3. 🟧 **AC4** — ship a self-contained resync fixture + surface the Approver-sign-off gate in `re-sync.md`.
4. 🟨 Reconcile the two doc/tooling contradictions: `pack-shell.md:15-16` (empty-`.apm/` validation) and
   `CHARTER.md:52 vs :90` (accelerator principle count).
5. ⚪ **AC5** is in good shape — optional craft polish only.

**Net:** the four skills are *functionally correct on their security-critical and judgment cores*
(detection, confirm gate, routing tree, reject-on-duplication all reproduced the oracle). The gap is
**documentation completeness** — the `notes/` oracles encode correct procedure the skills should own,
so a live operator (not reading the QA notes) is under-served on the accelerator path, the hook-landing
path, the SAST tooling, and the Approver-sign-off gate.
