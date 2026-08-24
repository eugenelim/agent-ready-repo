# Review finding adjudication implementation notes

## Architecture-review scope clarification

On 2026-08-24 the owner clarified that an architect pack `design-reviewer`
report must use the same adjudication gateway whenever that reviewer is
activated inside the work-loop. The existing adjudicator capability is
sufficient: the orchestrator supplies the named architecture artifact and
rubric paths, while the existing `Where:` specialist grammar supports the
reviewer's artifact-relative findings. No new reviewer trigger is added, and
the change only governs reports activated inside the work-loop.

## Manual falsification QA — 2026-08-24

The three `finding-adjudication-*` eval routes were exercised with the projected
Codex `finding-adjudicator` against synthetic files beneath
`/private/tmp/finding-adjudication-manual-qa/`. The numeric limit in the first
fixture is a fictional import contract, not a cap on reviewer findings; the
adjudicator must enumerate and decide every source finding in a report.

| Eval case | Raw artifact | Adjudication artifact | Bounded main-loop result | Direct-light classification |
| --- | --- | --- | --- | --- |
| `finding-adjudication-sustained` | `/private/tmp/finding-adjudication-manual-qa/sustained/raw.md` | `/private/tmp/finding-adjudication-manual-qa/sustained/adjudication.md` | One numbered finding; smallest fix changes the existing bound to five and rejects the proposed parser replacement | `findings`, one fingerprint |
| `finding-adjudication-refuted` | `/private/tmp/finding-adjudication-manual-qa/refuted/raw.md` | `/private/tmp/finding-adjudication-manual-qa/refuted/adjudication.md` | Exact `Clean — ready to commit.` sentinel; contrary UTF-8 evidence remains only in the refuted audit | `clean`, no fingerprints |
| `finding-adjudication-indeterminate` | `/private/tmp/finding-adjudication-manual-qa/indeterminate/raw.md` | `/private/tmp/finding-adjudication-manual-qa/indeterminate/adjudication.md` | Only `ADJUDICATION-INDETERMINATE`; the audit names the missing directory, manifest, or claimed-path evidence | `invalid`, no fingerprints |

Each classification was produced by:

```text
python3 packs/core/.apm/skills/work-loop/scripts/loop-cohort.py \
  review classify --report <adjudication-artifact> --json
```

The sustained main-loop slice contains neither the raw review prose nor its
over-broad replacement proposal. The refuted slice contains no contrary
reasoning. The indeterminate slice contains no clean sentinel and stops before
fingerprinting or mutation.

## Codex adapter runtime check — 2026-08-24

The owner approved correcting the Codex adapter projection in this in-flight
round after the first adjudicators proved unable to read supplied files. That
runtime evidence supersedes the implementation plan's earlier assumption that
Codex could disable shell while retaining named `Read`/`Grep` access. The
durable spec and acceptance criteria were amended accordingly. The approved
plan body remains unchanged because the active work-loop schedule is
content-hash pinned; editing it mid-run would invalidate the engine's approved
schedule rather than document the implementation deviation.

A fresh Codex-only projection of `packs/core` produced
`sandbox_mode = "read-only"`, `web_search = "disabled"`, and
`features.shell_tool = true` for `finding-adjudicator`. The self-hosted TOML was
byte-identical to that focused projection. A newly dispatched adjudicator then
read the supplied raw report, current diff, and authorities and returned one
sustained and one indeterminate disposition, proving local file read/search was
available without write or web authority.

A second focused projection covered every previously affected shipped agent:
`design-reviewer`, `evidence-retriever`, `source-extractor`,
`experience-reviewer`, `frontend-reviewer`,
`discovery-reliability-reviewer`, and `discovery-threat-reviewer`. All seven
emitted `sandbox_mode = "read-only"` and `features.shell_tool = true`. Web stayed
disabled for the five local-only reviewers and live for the two desk-research
agents whose portable source explicitly declares web tools.

The repository-wide `make build-self` command could not complete in this
managed session because its wholesale replacement step attempted to delete an
existing `.claude/skills` directory, which enterprise policy forbids. The four
tracked files removed before that denial were restored byte-for-byte from their
unchanged `.agents` projections. The owner then ran `make build-self` in an
approved environment: it exited `0`, reported `catalogue self-host --write: ok`,
and introduced no projection changes beyond the existing worktree.

## Review retry cap raised by owner decision — 2026-08-24

The owner explicitly authorised one review round beyond the configured cap after
round 6 sustained eight findings, none of them Blockers. `max_review_retries`
was raised from `5` to `7` in `state.json` by hand. That is normally forbidden —
the skill says never to edit `state.json` directly — so it is recorded here as
an owner decision rather than left as a silent mutation.

The alternative the tooling names is `loop-cohort reset` followed by
`loop-engine reset`, which would have destroyed six rounds of retry and
fingerprint history and orphaned all twenty paired `.context/reviews/`
artifacts (forty files) by changing the run id. The audit trail was judged worth more than cap purity here,
given the remaining findings were two Concerns and six Nits.

Raised again from `7` to `9` on the same authority when the owner asked for the
evidence-on-request doctrine to be folded in, which is a new change and so earns
its own review. Raised before dispatching the round rather than on hitting the
refusal, which is the failure this same round fixed in the shipped protocol.

One operator error contributed to the stop. `findings-remain` and
`review record` were issued as two sequential commands without gating the second
on the first's exit status. The engine refused the transition on the cap guard
while the cohort recorded anyway, leaving `review_retry_count` at 6 with the
engine still parked in `CODE-REVIEW`. Raising the cap and re-firing the
transition reconciled the pair. The transition-then-record ordering exists so
the retry guard observes the pre-increment count; it only holds if the caller
reads the transition's exit code first.

## Evidence-on-request doctrine written and reverted — 2026-08-24

Round 7 produced an `indeterminate` the adjudicator could not settle because the
finding rested on a lint the reviewer had run and the agent, holding only `Read`
and `Grep`, could not. The orchestrator improvised: produced the lint output to a
file, re-dispatched with the path, and got a sustained verdict. The owner then
asked for that improvisation to become doctrine, and it was written into
`references/finding-adjudication.md` as a section titled "Indeterminate on
machine-checkable evidence".

Round 8 rejected it, and the reasons are worth keeping because the same shape
will be tempting again:

- **Confused deputy.** "The orchestrator runs it" left the command's provenance
  unbound. The referent was a command named in free-form adjudicator prose,
  written after that adjudicator read an untrusted reviewer report — so report
  text could reach the one agent in the loop holding `Bash`. The surrounding
  document is otherwise absolute that the controller must not act on artifact
  prose; this inverted that discipline into execution.
- **No agent contract.** The protocol went into the skill reference, which the
  subagent never reads. The agent's supplied-path list is closed at four classes
  and says "Do not discover additional paths", so a conforming adjudicator would
  refuse the evidence file and a non-conforming one would treat machine output as
  its highest-trust input.
- **Unvalidated input.** `ARTIFACT_KINDS` is closed to `{raw, adjudication}`, so
  an `evidence/` file is structurally unvalidatable — no size ceiling, no UTF-8
  refusal, no link checks.
- **Unbounded and outside retry accounting.** The path never reaches
  `review record --fingerprint`, so `max_review_retries` never fires.
- **Undefined composition.** Partial re-dispatch left unstated who merges the
  carried-forward verdicts. The orchestrator did it by hand this round, which put
  the controller in the business of authoring sustained lines and the clean
  sentinel into an artifact whose entire premise is independent authorship.

The section was reverted whole. Both it and a second request — a predicate
testing whether a finding's proposed *mechanism* is correct, as distinct from
merely over-broad — are registered as `adjudicator-evidence-and-remedy-predicate`
in `[backlog].open`.

The generalisable lesson: this control reviews other agents' claims, and nothing
reviews the orchestrator's own design decisions. A contract change agreed in
conversation reaches the shipped artifact with no acceptance criterion, no test
pin, and no reviewer until the next round reads the result. Both requests here
were sound; the mechanism for landing them was not.

## Owner waiver of the adjudicated-clean finish requirement — 2026-08-24

The Finish checklist requires every warranted reviewer to produce an adjudicated
`Clean — ready to commit.` result. That bar is met for `security-reviewer` in
round 8 and waived by the owner for the other two.

Round 8 sustained three findings across `adversarial-reviewer` and
`quality-engineer`, deduplicating to two defects: the pre-EXECUTE `<round>`
ordinal was underivable, and an `os.geteuid` call was unguarded off POSIX. Both
were fixed, and the full gate chain re-run green afterwards — but no round 9 was
run, so the final tree carries two fixes no reviewer has seen.

The owner waived that deliberately, on the reasoning that eight rounds had
reached diminishing returns: 79 findings raised across rounds 4-8, roughly half
adjudicated refuted, and rounds 5-8 sustained nothing above Concern except
defects introduced between rounds by the fixes themselves. The residual risk is
named rather than hidden: the two round-8 fixes are prose and a test guard, both
verified by the focused suites and `make build-check`, neither touching the
classifier, the validator, or the agent contract.

## Portable no-skill opt-out and the Kiro pass-through — 2026-08-24

The owner approved correcting the agent-frontmatter portability boundary in this
in-flight round after `catalogue verify` reported `CAT-V-011` on
`.claude/agents/finding-adjudicator.md` for an `unknown frontmatter key:
resources`. The approved plan body remains hash-pinned and unchanged for the
same reason recorded in the Codex adapter section above.

Three facts drove the correction, each established from current vendor
documentation and a seven-adapter projection probe rather than from the
in-repo assumption:

1. `resources` is **not** Claude Code agent frontmatter. Its documented optional
   fields are `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`,
   `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`,
   `isolation`, `color`, and `initialPrompt`. `resources` is Kiro-native. The
   `claude-code` agent projection is `direct-file` — a byte copy — so a
   Kiro-native key in the portable source lands verbatim in `.claude/agents/`.
2. Claude Code's `skills` field carries the intent the envelope needs. Kiro
   grants skill access through `resources` entries using the `skill://` scheme,
   so an explicit empty `skills` list is the portable "reaches no skills"
   signal. It replaces `resources: []` in the source agent and is admitted to
   `ALLOWED_AGENT_KEYS`; Kiro's `resources` deliberately is not.
3. Both Kiro agent projectors iterate the source frontmatter and pass unmapped
   keys through, while codex, copilot, cursor, and gemini iterate the contract
   mapping and drop what it does not name. A probe declaring all twelve
   non-baseline Claude Code fields confirmed every one reached both Kiro agents
   verbatim, while the other four dropped all of them. That pass-through is why
   `resources` worked as an author override at all, and it also meant a source
   agent declaring `hooks` would reach kiro-cli JSON — the exact condition
   `test_cli_no_ide_hook_field` warns about, which could not fail because its
   fixture declares only `name` and `tools`.

`_CLI_AGENT_FIELDS` / `_IDE_AGENT_FIELDS` now bound each Kiro agent's emitted
shape and log every drop. A non-empty `skills` list raises at build time rather
than emitting an unresolvable `skill://` entry, because templating a bare skill
name into a URI is beyond the mapping grammar's rename/normalize/values rules.
Reverting the two `_restrict_agent_fields` call sites was confirmed to fail the
two new drop tests, and restoring them returned all 23 Kiro adapter tests to
green.

Deliberately **not** done here, and recorded as the reason: refreshing
`ALLOWED_AGENT_KEYS` to Claude Code's full current schema and mapping all
fourteen fields across six adapters. Three of the twelve new fields are pure
renames or scalar value maps the contract grammar already expresses
(`maxTurns`, `background`, `effort` — and `effort` collides with the
`model` rule's existing `related-values` write to `model_reasoning_effort`).
Six need vocabulary the grammar does not have: set subtraction
(`disallowedTools`), enum bucketing across different cardinality and type
(`permissionMode` → codex `approval_policy` → cursor `readonly`), URI
templating (`skills`), object-schema translation (`mcpServers`), event-vocabulary
translation (`hooks`), and body composition (`initialPrompt`). That is an
adapter-contract expressiveness change, not a mapping-table edit.

An earlier note in this file recorded that `make build-check` "stopped on" 65
pre-existing CAT-S003/CAT-S004 warnings. That was wrong, and the correction
matters because a durable `[backlog].open` entry was written on the strength of
it. Those findings are emitted as WARN, and `catalogue lint` computes its exit
status from ERROR severity alone, so the skill-spec lint passes with all 65
present: on 2026-08-24 `catalogue lint --root . --deep` exited 0 reporting
`ok: 65 finding(s)`, `tools/catalogue/pre_pr_catalogue.py` printed
`pre-pr: ✓ skill-spec lint`, and `SKIP_SAST=1 make build-check` completed. The
register entry has been restated as a warning-baseline observation with no
gate-failure claim.

A queued, overlapping check earlier in the run observed CAT-V-014 drift after
the work-loop entrypoint was compressed and its new reference was added. That
result reflected a moving generated tree and was not final gate evidence;
regeneration and the final build check ran sequentially after source freeze, and
`catalogue verify --root .` now reports `ok`.
