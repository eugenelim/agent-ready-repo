# Spike report — the coordinator contract (RFC-0048 Decision 7)

**What this is.** The empirical prototype RFC-0048 Decision 7 asked for: *"a prototype of
the sidecar + `discovery-loop` on `omnigent` against the worked example — not a paper
design,"* whose job is to **confirm the paper resolutions in [`0048-notes/09`](../0048-notes/09-gap-resolutions.md)
hold in practice** and to **confirm the no-engine framing empirically**. The prototype
artifacts are in [`spike/`](spike/); this report distils them.

## Hypothesis

> The upstream convergence loop (`discovery-loop`), the typed state it needs (the
> sidecar), the consent-gate rejection/recovery transitions, and the outer cap can all be
> executed by a **single reasoning context** maintaining **plain typed files** on an
> **existing harness** — with **no new runtime engine** — and the typed state makes
> "everything holds together" **mechanically checkable**, not merely asserted.

Falsifier: if any transition required a coordinator process (a scheduler, a message bus, a
convergence solver) that is not itself just-an-agent-following-doctrine, the no-engine
framing fails and Decision 7's hypothesis is refuted.

## Method

1. Took the `example-assistant` worked example verbatim from [`0048-notes/02`](../0048-notes/02-worked-example-flow-trace.md)
   (a secure single-owner planning agent with approved learning).
2. Instantiated the four sidecar slots as plain files —
   [`blackboard.json`](spike/blackboard.json), [`open-questions.md`](spike/open-questions.md),
   [`traceability.json`](spike/traceability.json), [`decision-log.md`](spike/decision-log.md)
   — each typed to the RFC-0048 D7 schema.
3. Walked the loop G0→G2 as one reasoning context, editing the files by hand at every hop
   ([`loop-trace.md`](spike/loop-trace.md)), deliberately injecting the **two** failure
   modes RFC-0048 names (over-scope; an unbacked security-sensitive screen) to exercise
   the rejection/recovery and ripple transitions rather than a clean straight-line run.
4. Wrote a ~60-line lint ([`check_sidecar.py`](spike/check_sidecar.py)) — the same shape
   as child-4's traceability lint — and ran it against a pre-recovery snapshot and the
   converged snapshot to test whether the typed state is checkable.

`omnigent` itself is taken as the harness per [its repo](https://github.com/omnigent-ai/omnigent)
(confirmed present; runner/server, policy gates outside the prompt, git-worktree
blackboard, YAML agent defs, cost policies, human-in-the-loop pauses — and — its docs being
**silent on any state-sidecar / general-blackboard capability beyond worktrees** (absence of
evidence, matching RFC-0048's "documented alpha gaps") — precisely the gap this prototype
fills). We did not stand up an omnigent server; we prototyped the part omnigent lacks (the
typed sidecar + the loop contract) in the form omnigent would store (worktree files),
which is the honest scope of the spike.

## Results — each paper resolution, confirmed or qualified

| Gap (note 09) | Paper resolution | Spike result |
| --- | --- | --- |
| **O2/O3/O7** typed state | blackboard + OQ queue + traceability + backlog as files | **Confirmed.** All four slots are expressible as plain JSON/markdown a single context maintains; see `spike/`. |
| **O4** connectedness check | a lint over the edge set | **Confirmed, empirically.** `check_sidecar.py` flagged 2 dangling service leaves pre-recovery and reported CONVERGED after — connectedness is checkable in ~60 lines, no engine. |
| **O11** rejection/recovery | reject → cascade-invalidate downstream slots via traceability edges → re-run affected lenses | **Confirmed.** The fulfillment rejection walked out-edges, marked the subtree `stale`, dropped its edges, and re-ran only the UX lens — the edge set scoped the blast radius. A markdown+JSON edit, not a framework call. |
| **O5** live lenses | `security-reviewer` + `quality-engineer` design-artifact mode mid-loop | **Confirmed in shape.** The security lens firing inside the ripple is exactly this; it ran as a controller-invoked lens over a non-code artifact. |
| **O6** saturation | no new OQ + traceability closed + a full clean pass | **Confirmed.** Encoded as the checker's exit code + the human's full-pass eye; the "no invalidating edit" clause stays a judgment, honestly. |
| **O12** outer cap | round cap + cost budget; on cap → stall surfaces to human | **Confirmed as a field + transition; not hit live.** Converged at round 4/12, $6.40/$25. The stall path is defined and modelled (`loop-trace.md` §"the cap path") but the happy run did not exercise it — an honest gap (see Threats). |
| **A1** checkpoint/resume | write decision-brief, status=awaiting-human → option-card → verdict → decision-log → resume | **Confirmed in shape.** Each consent gate is a decision-log row with `ratified-by=human`; the resume is the next round reading the log. omnigent's human-in-the-loop pause is the store. |
| **A2** decision/option-card schema | gate · summary · decisions · recommended · reversibility-class · artifacts | **Confirmed.** The decision-log schema carries exactly these fields; it is a decision *record* that becomes a real audit trail only with the integrity properties named in RFC-0053 § Security & integrity contract (append-only · attested ratifier · tamper-evidence). |
| **the ripple** (note 02) | lenses answer each other through the blackboard, never chat | **Confirmed.** OQ-3 settled across security→product→tech→ux→design as queue-status + blackboard edits; zero agent-to-agent negotiation (the MAST guardrail held by topology). |

## The no-engine verdict

**The hypothesis survived.** Every transition was performed by one reasoning context
editing four plain files, with a single ~60-line *checker* (a lint, not a coordinator) as
the only executable. Nothing in the loop required a scheduler, a message bus, or a
convergence solver. The harness supplied runner + worktree + policy gates + consent UI;
it did not supply, and did not need, a convergence engine. This matches the repo precedent
the framing rests on: RFC-0041 shipped an end-to-end infra loop as doctrine + a reference
library + reuse, "no engine"; `work-loop`'s own supervisor mode is doctrine + the
`loop-cohort` *script* (a scheduler-as-lint, not a service). The coordinator is the same
kind of thing one altitude up.

So the catalogue ships: a `discovery-lead` **agent definition** + a `discovery-loop`
**skill** (content, like `implementer`) + the sidecar **schema** (core doctrine). The
*store* and the *gate enforcement* are the harness's. No runtime crosses the charter's
Principle 3.

## Threats to validity (honest)

- **Single example, single operator.** One worked example, walked once, by the same agent
  that designed the loop — anchoring is possible. Mitigation: the example was taken
  verbatim from note 02 (authored before this spike), and the two failure modes were
  injected deliberately rather than discovered, so the transitions were tested, not
  narrated past.
- **The cap was not hit live.** O12's stall-surfaces-to-human transition is modelled, not
  exercised, because the happy path converged at round 4/12. The transition is simple (a
  counter compare + a surface) and grounded in `work-loop`'s existing cap, but "modelled"
  is weaker than "ran". Flagged as the one resolution the spike confirms by construction
  rather than by execution.
- **The checker is a presence lint, not a reachability lint.** It flags a dangling subtree
  at its *tip* (the orphan leaf), not every node above it. Child-4's real lint may want a
  root→leaf reachability pass; recorded as a refinement, not a blocker.
- **omnigent not stood up.** We prototyped the sidecar in the file form omnigent stores but
  did not run an omnigent server. The claim is "the part omnigent lacks is small, typed,
  and engine-free", not "we ran it end-to-end on omnigent". A full on-harness run is a
  reasonable follow-on before the implementing spec closes.

## What this licenses the RFC to claim

1. The no-engine framing for the coordinator is **demonstrated**, not hypothesized —
   closing the one assumption RFC-0048's own spike section left open for D7.
2. The four sidecar slots + the gate state machine (rejection/recovery + cap) + the
   consent checkpoint/resume are **specifiable as a contract** an adopter (or a bespoke
   harness) implements, harness-neutrally.
3. The connectedness verifier is **real and cheap** — the typed state plus a lint, not a
   runtime.
