# pre-execute-review — spec-stage review depth (full doctrine)

> **Loaded when:** a pre-EXECUTE review trigger fires during PLAN — a **spec
> amendment** or a **structural change** (adversarial), or the
> **security-boundary** trigger (secure-design). `SKILL.md` keeps the triggers
> and the one-line dispatch; the depth — how the reviewer measures, the re-plan
> re-fire, the gate mechanism, the Profile-A opt-out, and the infra-mandatory
> secure-design pass — lives here.
> **Why progressive disclosure:** the *triggers* are evaluated every full-mode
> PLAN, but this depth only matters once a trigger actually fires on a given
> loop, so it loads on demand rather than sitting inline.

## Finding-adjudication gateway

Persist every completed pre-EXECUTE reviewer report, then run `review
raw-classify --report <path> --json`. `clean` requires the sentinel line
exactly once, zero parsed findings, and nothing else but blank lines; do not
dispatch `finding-adjudicator`. A report carrying a `## Not checked` footer is
never fast-pathed however clean it looks — the footer is prose, and prose is what
the adjudicator reads — so it dispatches. `findings` dispatches it. `invalid` is
a loud stop. Byte equality is direct clean and remains the distinct
recording form for a report whose bytes equal the sentinel exactly. For
that form the comparison is exact: Trimmed whitespace, a trailing newline,
case folding, Unicode normalization, unwrapped Markdown, and the sentinel
as a substring, prefix, or suffix all fail it. Structural clean is the
separate, classifier-decided path that admits surrounding blank lines.

Persistence is unconditional and comes first, so this rule holds identically
whether the harness routes reviewer output straight to the file or the
controller delivers it once: exactness is decided by reading the artifact, never
by classifying output before anyone has written it down.

Route every `findings` report through the same independent gateway before
classifying or acting on it, revising the spec or plan, or firing a review
transition. This applies to adversarial, security, design-intent, and frontend
pre-flight reports whenever those reviewers are warranted. Malformed or mixed
output is not clean. A missing adjudicator on this path is a loud stop; it is
never a named clean skip.

This also includes the architect pack's `design-reviewer` whenever an
architecture integration activates it inside the work-loop. Supply the named
architecture artifact plus its accepted concept/constraints and governing
rubric paths. The adjudicator can verify the reviewer's artifact-relative
`Where:` findings with its existing `Read`/`Grep` surface. This gateway adds no
`design-reviewer` trigger.

`<round>` here is a per-run, per-stage ordinal the orchestrator keeps: 1 for the
first pre-EXECUTE pass, incremented on each `spec-ready` re-entry and each
evidence replacement attempt. Do not derive it from the cohort's
`review_round_count`: ordinary pre-EXECUTE results do not call `review record`,
while the bounded evidence path deliberately does, so that shared counter is
not this artifact namespace.

The orchestrator assigns the canonical reviewer-role slug and persists the raw
report under the ignored session root as:

```text
.context/reviews/<run-id>/<round>-pre-execute-<reviewer-role>-raw.md
```

**Before persisting the first raw report of a run, prove `.context/reviews/` is
ignored:** run `git check-ignore -q .context/reviews`. A non-zero exit means
this repository does not ignore it — seed delivery is skip-on-conflict, so an
adopter whose `.gitignore` already existed never received the rule. Stop and ask
the owner rather than writing reports into a tracked directory.

Artifact-capable runtimes route reviewer output directly to that file. When a
runtime must deliver output through the controller once, persist it immediately
without classifying, summarizing, quoting, or acting on it. Either way the
routing rule is content-independent — it does not need to know whether the
report is clean, because exactness is decided afterward by reading the file. The
raw report is opaque from that point onward. Validate the orchestrator-derived
path before dispatch; never accept a reviewer-selected path:

```bash
python '<skill-dir>/scripts/review-artifact.py' validate \
  --root <repo> --run-id <run-id> --round <round> \
  --review-stage pre-execute --reviewer-role <reviewer-role> --kind raw
```

Before dispatch on Codex or Cursor, inspect the active session's managed
permission profile and exposed tool surface; the projected agent file is
necessary but not sufficient. Admit Codex only when its command tool is inside
the projected read-only sandbox and bounded file-read/search instructions.
Admit Cursor only when its inherited surface is read-only. In both cases the
active profile must withhold mutation, web, MCP, skill, recursive dispatch, and
project-code execution outside that Codex exception. If the profile is not
observable or exposes any additional capability, stop before dispatch and ask
the owner; local configuration never overrides managed policy.

Then select a subagent matching `finding-adjudicator`. Pass only the validated
raw-artifact path, unchanged target and structural scope, reviewer role, and
governing spec/rubric/checklist paths—not the report body. Persist its complete
output at the paired path:

```text
.context/reviews/<run-id>/<round>-pre-execute-<reviewer-role>-adjudication.md
```

Validate that artifact with the same command using `--kind adjudication`, then
classify its envelope before any pre-EXECUTE decision:

```bash
python '<skill-dir>/scripts/loop-cohort.py' review inspect <spec-dir> \
  --report <pre-execute-adjudication-path> --adjudication --json
```

An `invalid` classification is a fail-closed stop except for the exact bounded
machine-checkable evidence route below. Otherwise do not revise the spec or plan
and do not call `review record`. Evict the raw report prose and consume only the
strict classifier's `## Main-loop result`. Only sustained findings may drive a
spec/plan revision or the iterate-to-clean branch. A refuted-only result is the
existing exact `Clean — ready to commit.` result and does not consume a repair
round. An indeterminate stop for owner choice, conflicting authority, or a
non-machine-checkable claim remains terminal and is never recorded as clean.
Keep all artifacts for the final audit without adding cohort state.

### Pre-EXECUTE evidence variant

Use the closed catalog, no-artifact-to-command rule, one-gate limit, containment
requirements, fixed evidence envelope, exclusive creation, digest rebinding,
and complete-replacement authorship defined in
`finding-adjudication.md` § *Bounded evidence retry*. The adjudicator source
contract already includes the optional fifth supplied path; never rely on this
reference alone to widen its paths or tools.

This exception applies only when strict classification returns reason
`indeterminate-present`, the adjudication audit identifies one missing
machine-checkable fact, and a catalog entry fixed before the raw report declares
that exact measured fact. Artifact prose may select the fact category only; no
artifact-derived gate ID, command, argument, path, environment value, or
substitution reaches execution. Allocate the next unused pre-EXECUTE ordinal
and derive fresh paths:

```text
.context/reviews/<run-id>/<attempt>-pre-execute-<reviewer-role>-evidence.md
.context/reviews/<run-id>/<attempt>-pre-execute-<reviewer-role>-adjudication.md
```

After the shared non-executing eligibility, artifact-excluding read-allowlist,
fresh-path, containment, capture-cap, and exclusive-create preflight succeeds,
run the retry-cap transition, confirm it succeeded, and record the validated
first-adjudication digest; a refused transition records and executes nothing:

```bash
# The transition prints `(seq=N)`. Record only if it succeeded, and pass that
# N: a resuming session reads the same value from `loop-engine status`, so the
# operation id it recomputes matches and the round is not written twice.
python '<skill-dir>/scripts/loop-engine.py' transition <spec-dir> findings-remain
python '<skill-dir>/scripts/loop-cohort.py' review record <spec-dir> \
    --fingerprint <validated-adjudication-sha256> --expect-run-id <run-id> \
    --operation-id <run-id>:<seq>
```

After the record succeeds, run the literal catalog entry under its declared
controls, exclusively persist and validate `--kind evidence`, and immediately
revalidate it with `--expected-sha256 <first-validator-digest>`. Fire
`spec-ready` to re-enter `SPEC-PLAN-REVIEW`; do not revise the unchanged target
or let the controller compose prior verdicts. Dispatch the adjudicator with the
unchanged raw path and source-finding set plus the evidence path and expected
provenance. Persist, validate, and strictly classify one complete replacement
adjudication. A further evidence attempt repeats this entire guarded path; an
exhausted cap or missing control stops before execution.

## Adversarial spec/plan review — how the reviewer measures

Both triggers route to the same reviewer mode and the same spec-stage checklist;
what differs is the standard the reviewer measures against.

`Clean` measures planning-level viability, not implementation completeness. A
plan is sufficient when its observable contract, owner, boundaries, ordering,
discovery predicates, required outcomes, and verification modes make safe start
possible. Sustain a mechanism or test-shape finding only when its absence makes
the plan unable to start or verify the contract. Helper names, symbols,
fixture-internal detail, and a finished edge-case matrix remain build-time
guidance and cannot prevent `Clean`.

When the **structural-change** trigger fires, the reviewer checks the plan
against the spec's **Boundaries** section (defined by the `new-spec` skill's
bundled `spec.md` template) — primarily `Never do` for hard structural rules and
`Ask first` for the ones that require sign-off; `Always do` for positive defaults
the plan must honour. If `Boundaries` is empty, that's the finding to surface
first — an empty Boundaries section is a spec-stage gap, **not** a fallback cue.
Only when the spec has no Boundaries section at all (an unmigrated template, say)
fall back, in order, to: the PLAN step's **declined-pattern register**, and the
effective repository guidance's approval and action rules (when installed
elsewhere, follow the adopter's own headings and mapped sources).

Apply a focused repository-idiom delta only when the plan introduces a
load-bearing structural mechanism: a module or component boundary, framework
extension/composition mechanism, persistence or messaging pattern,
construction/registration path, or cross-cutting abstraction. Use this finding
shape exactly: **This proposal introduces X. A mapped repository source or
canonical production example uses Y for the same responsibility. Confirm or
justify the deviation.**

Do not derive Y from one incidental neighboring file, demand cosmetic
uniformity, turn repetition into an invariant, expand product scope, or require
the core pack's file layout. Tentative or contradictory evidence is an
assurance gap, not a repository rule. The check asks for confirmation or a
reasoned deviation; it does not silently redesign the proposal.

## Mid-EXECUTE re-plan — Phase-1 note

In Phase 1 approved plans are **immutable in substance**: `loop-cohort schedule
check-current` guards every `CODE-*` transition against the scheduled
`plan_hash`. Lifecycle **bookkeeping** is exempt — the preamble status token and
progress checkboxes are normalized out of the hash, because this skill mandates
writing them. Any *substantive* edit to `plan.md` after `approve-plan` — task
text, a `Depends on:` edge, a re-ordering — still causes a refusal.

If EXECUTE discovers a plan
error, surface to the human and stop — do not edit `plan.md` in-flight. The
full mid-EXECUTE re-plan path (structural-change re-fire, reviewer re-run, new
approval) is a Phase-2 feature; this section will be updated when it ships.

## Why early, and the gate mechanism

Cheap-to-fix-early applies harder to specs and structural decisions than to code
— catching a vague behavior, a missing `Depends on:`, a mismatched verification
mode, or a misplaced module boundary here costs a sentence; catching it
post-EXECUTE costs a re-do. Gate mechanism in Phase 1: the plan approver writes `Status: Approved` in
`plan.md` and the agent fires `plan-approved` (PLAN-HUMAN-GATE →
SPEC-PLAN-APPROVED). The `loop-cohort approve-plan` verb then writes
`approved_plan_hash` to `state.json`; `loop-cohort plan check-current`
(with `--require-schedule` for `code` mode) verifies the hash; `plan-locked`
fires to transition to CODE-IMPLEMENTATION. No new state fields. **Both
triggers respect the Profile-A opt-out:** skip if the project doesn't use the
reviewer at all.

## Secure-design review — net-new wiring and the infra-mandatory pass

The spec-stage `security-reviewer` dispatch is **net-new wiring** — distinct from
the adversarial-only firing above and from the separate light→full escalation use
of the same security-boundary trigger; it is not a re-use of either. The
boundary-matching `security-checklists` modules are inlined into its brief in
their **proactive-control framing**, per the
[`security-checklists` Module index](../../security-checklists/SKILL.md#module-index)
— the boundary→module routing authority.

**For infra-flavored work this spec-stage pass is mandatory, not discretionary.**
"Infra-flavored" is a **defined signal, not an ad-hoc judgement**: work that the
**destructive/irreversible risk trigger** routes to full mode *and* whose spec
matches the Module index's IaC / deploy-config entry — the same classifier that
already drives security-module loading (the spec-stage half keys this match on
the spec; the diff-stage half on the diff — same Module-index entry). When that
signal is present the `security-reviewer` runs at spec stage **regardless of** the
discretionary security-boundary trigger, and the orchestrator **force-loads** the
infra-relevant `security-checklists` modules (the candidate set the REVIEW
`security-reviewer` bullet names), loaded 1–N as the spec warrants per that Module
index. The matching diff-stage pass, the reviewer-plus-scanner pairing, and the
Profile-A / missing-subagent interaction all live in that REVIEW bullet — this is
the spec-stage half of the same non-skippable, both-stages pass. (Full
infra-mandatory detail: [`infra-verification.md`](infra-verification.md) §
*REVIEW — mandatory, multi-module security on infra-flavored work*.)

Unrelated but adjacent: `loop-cohort.py`'s `_resolve_spec_dir` is a lexical
`..` check, not path confinement — don't cite it as the pattern for a new
path-taking verb.
