# RFC-0025: `work-loop` light mode + risk-based escalation

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-05
- **Date closed:** 2026-06-05
- **Related:** RFC-0015 (wave-scheduled supervisor mode — cost-rejection precedent); RFC-0019 (LLD-aware spec/plan); `work-loop` skill; `new-spec` skill; `docs/CONVENTIONS.md` § "How we do non-trivial work"; `AGENTS.md` § "Excuses we don't accept" + § "Check before acting"

## The ask

- **Recommendation (BLUF):** Give `work-loop` two modes — a **light mode** (lean inline spec + a single adversarial-reviewer pass + no `loop-cohort` state machine) that becomes the **default** for ordinary low-risk work, and the current **full mode** reached when work trips a **risk trigger**. Replace the file-count escalation rule (">1 file → `new-spec`") with the risk-trigger set, and retire the "Small enough to not bother" excuse (`AGENTS.md:161`) that discourages a lean path.

- **Why now (SCQA):** *Situation* — the repo standardised on a spec→plan→loop methodology and it produces reliably good output. *Complication* — there is one heavy gear, and the rule into it is file-count: `SKILL.md:55-56` forces *every* no-spec change above one file into `new-spec`, and from there full `work-loop` runs `adversarial-reviewer` to `Clean` (`SKILL.md:358`) plus a `quality-engineer` pass required by the end-of-session checklist (`SKILL.md:449`), across up to `max_iterations: 5` (`assets/state.json`), behind a `loop-cohort` state machine. A user reported ~$60 of budget for a ~2-hour `new-spec`/`work-loop` session (a single anecdote — see Risks). *Question* — should a two-file, familiar, single-task change pay compliance-grade cost, or should rigor scale with risk?

- **Decisions requested:**
  1. **Reframe the defect** as a *file-count escalation rule that ignores risk*, leaving (a) the existing single-file light path discouraged and (b) small multi-file work with no light path at all — not "no light tier exists anywhere." · recommended: yes · decide-by: on accept · default: yes.
  2. **Replace the file-count rule with a risk-trigger set.** · recommended: yes · decide-by: on accept · default: yes.
  3. **Define `work-loop` light mode** = lean inline spec (Objective + Acceptance Criteria + a short task list) + a single adversarial pass (a fixed Blocker earns one bounded re-review; no unbounded iterate-to-clean; no default `quality-engineer`) + no state machine; **scoped to a single logical task** (may touch a few files; no inter-task dependencies). · recommended: yes · decide-by: on accept · default: yes.
  4. **Express it as a `work-loop` mode** — a SKILL.md branch plus making `new-spec` template sections optional; **no new executable code, no new skill, no new artifact type.** · recommended: yes · decide-by: on accept · default: yes.

## Problem & goals

**Diagnosis.** The cost the user hit is not SKILL.md size (read once, cached). It is the *full path's machinery*: `adversarial-reviewer` iterated to `Clean` (`SKILL.md:358`), a `quality-engineer` pass that is discretionary at selection (`SKILL.md:379-380`) but a floor at the end-of-session checklist (`SKILL.md:449`), up to `max_iterations: 5` (`assets/state.json`), behind `loop-cohort` init/approve/record/check. That gear is appropriate for governance-grade work. The defect is the **rule that routes work into it**: `SKILL.md:55-56` + `AGENTS.md:162` escalate on **file count** (">1 file"), a proxy that ignores risk.

This produces a two-part gap. (a) The repo *does* have a single-file light path — spec-less `work-loop`: trio + gates + a self-review checklist with no subagent and no state machine (`SKILL.md:404-410`) — but `AGENTS.md:161` actively discourages reaching for it ("Small enough to not bother loading the work-loop." → "Load work-loop … The discipline is the point"). (b) For work *above* one file there is **no light path at all** — `SKILL.md:56` sends it straight to `new-spec` + full mode, regardless of whether it is a familiar, single-task, two-file change. A risk-based rule fixes both: it legitimises the existing single-file light path and extends a lean path to small multi-file work that today has none.

**Goals.**
- Make the *default* path for ordinary low-risk work materially cheaper in tokens and wall-clock, without losing a review floor.
- Scale rigor to **risk**, not file count — matching field norms.
- Keep full mode intact and reachable whenever risk warrants it.
- Add the lean path with **no new executable code, skill, or artifact format**.

**Non-goals** (could-have-been goals, deliberately dropped):
- *Not* removing or weakening full mode — it stays intact for risk-triggered work.
- *Not* adding iteration or token accounting to light mode — a tempting knob, explicitly declined; light mode is single-task by definition (Decision 3), so there is no unbounded iterate-to-clean and no `max_iterations` counter to maintain.
- *Not* a Copilot-style **no-spec** mode — we keep a lean spec, because a persisted contract is cheap and the spec-less checklist path already covers true throwaways.
- *Not* changing `new-spec`'s heavy procedure — it remains the full-mode entry point; light mode writes its lean spec inline.
- *Not* touching `loop-cohort.py` or `lint-spec-status.py` — light mode is defined by *not invoking* them.

## Proposal

**Decision 1 — reframe.** The single-file light path (`SKILL.md:404-410`) proves a lean shape is workable; the work is (a) re-setting the escalation rule from file-count to risk and (b) giving small multi-file work the same lean shape — not building a parallel system.

**Decision 2 — risk-based escalation.** Replace ">1 file → full" with: **escalate to full mode when any of these holds.** The set is anchored to the gates the repo already maintains, not invented — each trigger maps to an existing review or safety gate, which is the exhaustiveness argument:

| Trigger | Anchored to |
|---|---|
| Unfamiliar territory (you can't predict the design) | the reason `new-spec` exists — "surface what you don't know you don't know" (`AGENTS.md:162`) |
| More than one person will build or review it | spec-as-shared-contract |
| Decomposes a multi-feature brief / has inter-task dependencies | `receive-brief`; supervisor-mode DAG (RFC-0015) |
| Touches a compliance/governance surface (charter, conventions, security boundary) | charter/RFC gating; `security-reviewer` trigger set (`SKILL.md:385`: auth, secrets, user input, deserialization, file/network I/O, LLM/agent code) |
| Changes structure (module boundaries) or a public/published interface | pre-EXECUTE structural review; contract specs |
| **Destructive or irreversible operation** (data deletion, force-push, schema drop) | `AGENTS.md` § "Check before acting" |
| **Adds a dependency** | `AGENTS.md` "Dependencies are forever / record before adding" |

This mapping is gates→triggers with one deliberate exception: the `quality-engineer` lens is *not* promoted to a trigger but forgone in light mode (see Drawbacks), so the set covers every existing gate except the one this RFC consciously drops. Absent all of these, light mode is the default. The agent self-selects from these properties; the user can force either mode explicitly (Open question 1).

**Decision 3 — light mode contents.**
- *Spec/plan (3A):* one lean artifact — **Objective + Acceptance Criteria + a short task list**. Other `new-spec` sections (Boundaries, Testing Strategy, Assumptions, LLD, Constraints, Risks, Changelog) become **optional** and are omitted in light mode. Same template, fewer required sections — the Kiro "skip the requirements phase for small/well-understood specs" pattern, not a new format.
- *Review (3B):* **one** `adversarial-reviewer` pass — **not** iterated to `Clean`. A **Blocker** earns exactly **one bounded re-review** of the fix (not unbounded iterate-to-clean); if it survives that, **escalate to full mode** rather than spinning. Concerns/Nits route to `docs/backlog.md` as today. No default `quality-engineer` pass — see Risks for the lens this knowingly forgoes.
- *State (3C):* **none.** Light mode is **single-task** (it may touch a few files but carries no inter-task dependencies); with a single task and a bounded pass there is no unbounded iterate-to-clean and no fingerprint-stasis to detect, so `loop-cohort` is not invoked. Work that decomposes into dependent tasks trips Decision 2 and escalates.

**Decision 4 — vehicle.** A `work-loop` **mode** selected per run. Because light mode is defined by *omission*, it is a SKILL.md branch ("if light mode: write the lean spec inline; execute; gates; one bounded adversarial pass; ship") plus marking the named `new-spec` template sections optional. No `loop-cohort.py`/`lint-spec-status.py` changes; the state machine simply isn't called.

**Migration.** Edit in lockstep: `work-loop/SKILL.md` (add the mode branch + the risk-trigger selector, replacing the `:55-56` file-count rule), `AGENTS.md` (rewrite the `:161` "Small enough" excuse row and the `:162` ">1 file" row to the risk triggers), `CONVENTIONS.md` § "How we do non-trivial work" (state the two modes and the triggers), and the `new-spec` template (annotate the named sections "optional in light mode"). No data to convert (state files are per-session scratch).

## Options considered

Axis: **what is added to relocate the escalation boundary** — from nothing, through parameter tuning, to docs-only, to a separate new tier, to a lean mode inside the existing skill. This exhausts the space: you change nothing, tune the existing path, move the boundary by docs *without* providing anywhere lean to land, build a separate tier, or add a lean landing-mode inside `work-loop`.

| # | Option | What it adds | Trade-off vs goals |
|---|--------|-----------------|--------------------|
| A | **Do-nothing** | — | Zero effort; the cost problem and the field-norm gap persist. Cost of delay: continued over-spend on low-risk work + the credibility hit the feedback named. |
| B | **Tune the full path** (e.g. `max_iterations` 5→3, lints to CI) | tuned parameters | Shaves the full path but leaves it the *only* gear; addresses neither the file-count rule nor the missing lean landing for multi-file work. The band-aid pattern. |
| C | **Raise the rule by docs only — no lean mode** | revised trigger text | Relocates the boundary, but once triggered the *only* machinery is still full mode; newly-"light" multi-file work has nowhere lean to land, so the cost win is small and the spec-less checklist (single-file) stays the only lean option. |
| D | **Separate lightweight skill / Copilot-style no-spec mode** | a new tier alongside | Matches Copilot, but builds a parallel system duplicating `new-spec`/`work-loop` and drops the persisted contract entirely — more surface, not less. |
| E ⭐ | **`work-loop` light mode: lean spec + bounded single review + no state machine, risk-gated** | a lean landing-mode inside the existing skill | Keeps a review floor and a lean contract; risk-gated so full mode is still reached when it matters; adds no executable code/skill/format. Cost: a second mode is cognitive surface and the risk classifier is a judgment call. |

C and E are genuinely exclusive: C provides **no** lean landing for the work it relocates (full machinery once triggered); E provides one. Prior art: **A** is the standing convention; **B** is the optimisation list from the cost audit; **C** is "lighter spec / less review overhead" applied as docs only ([Augment Code](https://www.augmentcode.com/tools/best-spec-driven-development-tools)); **D** is GitHub Copilot plan mode — conversational plan, no persistent artifacts/state/reviewers ([Copilot CLI plan mode](https://github.blog/changelog/2026-01-21-github-copilot-cli-plan-before-you-build-steer-as-you-go/)); **E** is AWS Kiro's graduated model — "Quick Plan … without approval gates" + a skippable requirements phase for small/well-understood specs, full rigor reserved for unfamiliar/compliance work ([Kiro best practices](https://kiro.dev/docs/specs/best-practices/)).

## Risks & what would make this wrong

**Pre-mortem.**
- *Risky work under-escalates → quality regression.* Mitigation: the trigger set is anchored to existing gates (Decision 2 table), and the single adversarial pass is a floor — a surviving Blocker forces escalation. Residual risk: a class of risk not covered by an existing gate would also be missed by this list.
- *A **fixed** light-mode Blocker ships unverified.* This is the sharp one: dropping iterate-to-clean means a fix is not normally re-reviewed — precisely the "declare victory when it feels done" failure the loop guards against (`CONVENTIONS.md:603-607`). Mitigation: Decision 3B gives a fixed Blocker exactly one bounded re-review, and escalates on survival.
- *Agents game the classifier to stay light and save tokens.* Mitigation: triggers are objective properties of the work, not effort estimates; misclassification surfaces in the adversarial pass.
- *The mode boundary becomes the new litigation site.* Mitigation: default is light; the burden is naming a fired trigger, which is concrete.

**Key assumptions (falsifiable).**
- *Most ordinary tasks trip no risk trigger* — if false, light mode rarely applies and the win is small.
- *A single bounded adversarial pass catches the Blockers that matter* — if false, quality drops and a second reviewer must return to light mode.
- *The trigger set is complete because it mirrors existing gates* — if a real risk class exists that no current gate catches, both this list and the status quo miss it.

**Drawbacks (not "none").**
- **Light mode drops the `quality-engineer` lens entirely** — testability, observability, reliability, and maintainability concerns that the end-of-session checklist (`SKILL.md:449`) makes a floor today — though the lens is already discretionary at selection (`SKILL.md:379-380`) — have *no floor* in light mode. For a methodology repo this checklist-floor loss is the most material; accepted deliberately as the price of an affordable default, on the bet that low-risk single-task work rarely carries those concerns. A surviving Blocker (which can be a maintainability Blocker) still escalates into the full lens.
- A second mode is real cognitive surface and a new place to be wrong; the risk classifier is a judgment call with no mechanical check.
- We give up the uniform "every change passes the full gate" guarantee.
- "Adds no executable code" is true, but net-new *prose/skill* surface (the mode branch + trigger selector + optional-section annotations) is real — this is additive in surface, subtractive in cost for the default path.

## Evidence & prior art

**Spike / de-risk result.** Riskiest assumption tested: *"there is no lean shape anywhere, so we must build one from scratch."* **Found PARTLY FALSE, with a real gap underneath.** A lean path *does* exist for single-file spec-less changes (`SKILL.md:404-410`: trio + gates + self-review checklist, no subagent, no state machine) — so the lean *shape* is proven workable. But it is gated to single-file work by `SKILL.md:55-56`, which forces everything above one file into `new-spec` + full mode. So the genuine gap is narrower than "no light tier" but real: small multi-file work has **no** lean path, and the single-file lean path is discouraged (`AGENTS.md:161`). This is what scoped the proposal to "re-set the rule + extend the existing lean shape," not "invent a tier."

**Repo precedent.**
- `AGENTS.md:161-162` — the excuse and the file-count rule this RFC amends; `AGENTS.md` § "Check before acting" and § "Dependencies" — anchors for two added triggers.
- `CONVENTIONS.md:598` — "For anything beyond a one-line edit, follow the loop"; `:603-607` — the "declare victory when it feels done" failure the bounded-re-review mitigation addresses.
- `work-loop/SKILL.md:55-56, 358, 385, 404-410, 449` and `assets/state.json` (`max_iterations: 5`) — the routing rule, the cost machinery, the security-reviewer trigger set, and the existing single-file lean path.
- RFC-0015 — the repo already rejects heavier orchestration on cost ("~15× tokens"); cost-consciousness is an accepted value this RFC extends to the default path. No conflict: RFC-0015 governs supervisor-mode *scheduling*; this governs *per-task rigor*. (No errata needed.)

**External prior art.**
- **GitHub Copilot plan mode** — clarifying questions via `ask_user`, a plan panel, then implement; no persistent files, state machine, or reviewer subagents. The comparator the original feedback cited. ([Copilot CLI plan mode](https://github.blog/changelog/2026-01-21-github-copilot-cli-plan-before-you-build-steer-as-you-go/))
- **AWS Kiro** — "Quick Plan" generates artifacts *without approval gates*; the Analyze-Requirements phase is *optional* ("For small or well-understood specs, you can skip it"); full rigor reserved for "unfamiliar territory … compliance-sensitive" work. The graduated-by-risk model this RFC adopts. ([Kiro best practices](https://kiro.dev/docs/specs/best-practices/))
- **OpenSpec vs Spec Kit** — "Compared to Spec Kit's heavier output (around 800 lines), OpenSpec produced lighter specifications (around 250 lines), thereby considerably reducing review overhead." Spec weight is a recognised tunable axis. ([Augment Code](https://www.augmentcode.com/tools/best-spec-driven-development-tools); leanness corroborated qualitatively — "Spec Kit … a bit heavyweight," OpenSpec "nice and lightweight" — at [Dan Clarke](https://www.danclarke.com/openspec/))
- **"From vibe coding to SDD" (TDS)** — full specs are "probably overkill" for small improvements; SDD is the default "when you're working on a larger project, especially with other people." Direct support for risk/scale-based escalation. ([Towards Data Science](https://towardsdatascience.com/from-vibe-coding-to-spec-driven-development/))

## Open questions

1. **Mode selection — auto-classify vs explicit flag?** Recommended default: the agent self-selects from the documented risk triggers; the user may force `light`/`full` explicitly. · owner: eugenelim · decide-by: implementation spec.
2. **Does `new-spec` also gain a lean-fill option, or stay full-only?** Recommended default: stay full-only; light mode writes its lean spec inline in `work-loop` (Decision 4), so `new-spec` is unchanged. · owner: eugenelim · decide-by: implementation spec.

## Follow-on artifacts

- ADR-NNNN: "Rigor scales with risk — `work-loop` light/full modes and risk-based escalation" (records the file-count→risk-trigger reversal and the accepted `quality-engineer`-lens loss in light mode).
- Spec: `docs/specs/work-loop-light-mode/`.
- Convention changes: `docs/CONVENTIONS.md` § "How we do non-trivial work"; `AGENTS.md` § "Excuses we don't accept" + the escalation text; `work-loop/SKILL.md` (mode branch + risk-trigger selector, replacing `:55-56`); `new-spec` template (sections annotated optional-in-light-mode).
