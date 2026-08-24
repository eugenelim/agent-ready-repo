# Finding-adjudication path protocol

Use this reference for every post-GATES reviewer report. Pre-EXECUTE reviews
use the parallel protocol in `pre-execute-review.md`.

## Artifact identity and validation

`<round>` is the 1-based ordinal of the review pass being conducted, not a count
of completed ones: in full mode it is `review_round_count + 1`. The validator
refuses `--round 0`, and `review_round_count` is `0` until the first
`review record`, so deriving the round from the raw counter fails on every run's
first report.

Full mode uses the engine `run_id`. Light mode — including direct-light, which
has no persisted spec — generates one ephemeral lowercase canonical UUID for its
bounded review, uses round `1` initially, and round `2` only for its permitted
Blocker re-review; it initializes no cohort state. The validator enforces
canonical lowercase form and refuses with a content-free code that will not tell
you case was the cause, so generate it with
`python3 -c 'import uuid; print(uuid.uuid4())'` — `uuidgen` emits uppercase on
macOS and util-linux and must be lowercased.

The orchestrator assigns a canonical reviewer-role slug and derives this pair:

```text
.context/reviews/<run-id>/<round>-post-gates-<reviewer-role>-raw.md
.context/reviews/<run-id>/<round>-post-gates-<reviewer-role>-adjudication.md
```

**Before persisting the first raw report of a run, prove `.context/reviews/` is
ignored:** run `git check-ignore -q .context/reviews`. A non-zero exit means
this repository does not ignore it — seed delivery is skip-on-conflict, so an
adopter whose `.gitignore` already existed never received the rule. Stop and ask
the owner rather than writing reports into a tracked directory; raw
`security-reviewer` output carries exploit detail and quoted source, and
`git add -A` would stage it.

Route reviewer and adjudicator output directly to those ignored session paths
when possible. If output crosses controller context once, persist it immediately
without classifying, summarizing, quoting, or acting on it. Validate each path
from orchestrator-owned metadata, changing only `--kind` for the second file:

```bash
python '<skill-dir>/scripts/review-artifact.py' validate \
  --root <repo> --run-id <run-id> --round <round> \
  --review-stage post-gates --reviewer-role <reviewer-role> --kind raw
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

Dispatch a subagent matching `finding-adjudicator` with the validated raw path,
unchanged target and structural scope, reviewer role, and governing
spec/rubric/checklist paths. Never paste the report body into its brief. A
missing adjudicator is a loud stop.

## Strict classification

After validating `--kind adjudication`, consume only `## Main-loop result`.
Strict mode enforces the exact three-section envelope, exact clean sentinel,
and sustained-entry-only main result. Numbered findings in either audit,
`ADJUDICATION-INDETERMINATE`, or any non-`None.` indeterminate audit is
`invalid` before fingerprinting. The flagless parser remains legacy-only.

Full mode:

```bash
python '<skill-dir>/scripts/loop-cohort.py' review inspect docs/specs/<feature> \
  --report <adjudication-report-path> --adjudication --json
```

Light mode — including direct-light — has no cohort state and must classify
before every clean, apply, defer, or escalation decision:

```bash
python '<skill-dir>/scripts/loop-cohort.py' review classify \
  --report <adjudication-report-path> --json
```

Never substitute stateful inspect in light mode, omit `--adjudication` in
full mode, or pass `--report <raw-report-path>`.

## Route and record

| Result | Route |
| --- | --- |
| `invalid` | Surface and stop without state change or mutation. |
| `clean` | Exact `Clean — ready to commit.`; run remaining warranted reviewers. |
| `findings` | Use only sustained entries and returned fingerprints. |
| `matches_previous_round=true` | Surface stasis; do not start another round. |

For sustained findings, transition before recording so the retry guard sees the
pre-increment count. **Do not record if the transition exits non-zero.** The
transition carries the review-retry cap guard; `review record --fingerprint`
carries none and increments unconditionally. Issue them ungated and a refused
transition still records, leaving the engine parked in `CODE-REVIEW` with the
cohort a round ahead — a desync only a forbidden `state.json` hand-edit
reconciles. Chain them where the shell supports it; otherwise read the
transition's exit status before recording:

```bash
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> findings-remain \
  && python '<skill-dir>/scripts/loop-cohort.py' review record docs/specs/<feature> \
       --fingerprint <fp1> --fingerprint <fp2> ... --expect-run-id <run-id>
```

Then FIX, fire `wave-complete`, rerun GATES, and re-enter REVIEW. Do not record
an adversarial clean before specialist reviewers finish; a later specialist
finding would advance the round prematurely. On final clean, use the paired
adjudication path with `review record --adjudication`; fingerprints increment
the retry count, while clean recording does not.

Keep each raw/adjudication pair until handoff but never commit it or store its
paths in cohort state. After recording, evict both bodies from controller
context. Re-read only the adjudication artifact when FIX needs a sustained
finding's detail; DECIDE determines which sustained findings remain open.
