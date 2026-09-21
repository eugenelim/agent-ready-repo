# Verification ledger — intent placement

**This record outlived its spec.** It documents the shaping of
`intent-placement-and-admission`, re-cut into two slices on 2026-09-20 and then
retired on the same day when the defect it was built on turned out not to be
one. It lives here because `frame-intent-escape-verdicts` is the only
surviving slice of that work, not because it is that slice's own evidence —
this slice's observations are in the last section.

A cold reader wanting the short version should read `## The founding defect was
not a defect` first, then `## Three mechanisms, one error`.

## Shaping spec review — six rounds, 2026-09-19

Reviewer: `codex exec` (codex-cli 0.155.0), `gpt-5.6-sol`, reasoning effort
high, `--sandbox read-only`, a fresh session per round, never the author. The
`shaping-reviewer` `spec`-mode rubric was inlined verbatim in each prompt
because `codex exec` cannot dispatch a projected agent. Each round's packet also
carried the bundled `assets/spec.md` criterion-shape rules, the prior round's
report, and the text that report was raised against, so the reviewer could
attribute each finding's origin.

| Round | Result | Findings | Origin split |
| --- | --- | --- | --- |
| 1 | Findings | 5 Major | 5 from the drafted spec |
| 2 | Findings | 1 Blocker, 5 Concerns | 2 from the round-1 repair, 4 pre-existing |
| 3 | Findings | 1 Blocker, 5 Concerns | 4 from the round-2 repair, 2 pre-existing |
| 4 | Findings | 1 Blocker, 4 Concerns | 1 from the round-3 repair, 4 pre-existing |
| 5 | Findings | 2 Blockers | 1 from the round-4 repair, 1 pre-existing |
| 6 | **Clean** | none | — |

Two findings rested on claims the draft had wrong rather than under-specified,
both checked against the tree before repair: `terse-capture` appears nowhere in
the repository or in `intake-intent`, and `intent_renderer.py` *minimizes* a
reducible source locator rather than refusing it. The first term was dropped,
the second inverted.

### The round-3/round-4 oscillation, and the subtraction that ended it

Round 3 held that the spec's enumerated admission-refusal *domains* were not
mechanizable and asked for exact inputs. Round 4 held that the resulting
exact-input list narrowed established controls. Both were true of their own
text, which is the signature of a wrong premise rather than a defect to patch
again: this slice changes only the destination admission is offered, so
restating admission's refusal contract as criteria here can only be too tight or
too loose. Eight criteria were replaced by one that re-runs the owning suite
unamended, plus criteria for the cases the new derivation actually creates.

Round 5 judged that subtraction on its merits, accepted the single-homing, and
found the replacement criterion still over-claimed: the unamended suite does not
reach `chat-only`, `personal` or `vault` transfer modes, an email-bearing
locator, or the human destination confirmation. Those became four separate
criteria, and the unsafe-destination criterion was rebound to the
repository-relative candidate rather than to path syntax — being absolute is not
itself a defect, since an in-tree repo-root value and a personal-scope value are
both legitimately absolute.

Reports and packets: `shaping-r1` … `shaping-r6` in the session scratchpad, not
committed.

## Plan-stage probe — what executes placement, 2026-09-19

One read-only probe before the plan's first task, against the mechanism the
whole slice rests on. Nothing was committed; the finding is recorded here rather
than in the plan, which states only the decision it produced.

Fifteen of the spec's criteria are behavioural, and both skills declare
themselves prompt-only, so the probe asked whether any code already resolves
`[product] output_dir`. It does, in two places neither shipped reference names:

| Surface | What it already does |
| --- | --- |
| `packages/agentbundle/agentbundle/workspace_mcp.py:1576` `_read_layout_bases` | Reads both layout files; `product` and `design` are **repo-first**, `research` is user-first; anchors a relative value by the layout file's own location; warns and ignores a relative user-scope value; swallows every read error via `contextlib.suppress(Exception)` |
| `packages/agentbundle/agentbundle/commands/install.py:3216` `_append_layout_section` | Byte-preserving append-if-missing, never-overwrite; refuses a symlinked or malformed file; preserves file mode |

Three consequences, each carried into the plan rather than the spec:

1. The spec's repo-first precedence (AC3) matches the shipped resolver. The
   comment at `workspace_mcp.py:1548` reading "user-scope > repo-scope" is
   stale for `product`; the code four lines of logic below it is repo-first.
2. Neither function can be imported by a skill. A pack ships independently of
   the `agentbundle` CLI and `intent_renderer.py` is stdlib-only, so both are
   reused by semantics and stay separate aligned copies — the plan's second
   risk, and the ADR prerequisite rail records which is authoritative.
3. `[product] output_dir` therefore has three consumers, not two. AC26's
   "same consumer set" is satisfied only by naming the MCP resolver and the
   install append alongside the skills.

The probe also settled the mechanism fork the criteria depend on: a stdlib-only
resolver script shipped beside `intent_renderer.py`, decided 2026-09-19 by
eugenelim. Against prose the behavioural criteria would have reduced to
source-text assertions, which this repository has already recorded as
satisfiable by a comment.

## Spec-stage secure-design review, 2026-09-19

Reviewer: `codex exec`, `gpt-5.6-sol`, reasoning effort high, `--sandbox
read-only`, fresh session. The `security-reviewer` rubric was inlined verbatim
with boundary-scoped depth from four `security-checklists` references —
`path-and-file`, `config-misconfig`, `agentic-skills`, `llm-agent`. The gate
fired on four crossed boundaries: untrusted adopter-configuration parsing,
filesystem confinement and symlink decisions, writes at repository and
user-profile scope, and a widened agent tool surface.

Result: two Blockers, two Concerns, and a `## Not checked` footer naming what a
pre-implementation pass cannot reach (no SAST/SCA without a diff, no taint-flow
or race verification without code). Disposition:

| Finding | Disposition |
| --- | --- |
| `Bash` grants arbitrary execution with no containment contract | **Partly sustained, partly accepted.** The enforceable half became AC-0037, which derives the adapter set from `contracts/adapter.toml` and fails on an empty derivation or an unclassified member. The remainder is the accepted residual in the spec's `## Assumptions`, owner-decided 2026-09-19; making the feature fail closed on unenforcing adapters was declined |
| Untrusted path values can cross into agent instructions or shell syntax | **Sustained.** AC-0028 states the observable, AC-0029 refuses control characters, line breaks and invalid UTF-8, and AC-0030 fixes one serialized form |
| The optional integration fallback has no fail-closed security contract | **Sustained.** AC-0034 requires the core-absent fallback to satisfy AC-0029 through AC-0033 or write nothing |
| Confinement is not bound to a trusted root and the actual write | **Sustained.** AC-0031 binds validation to the write at both the layout path and the intent target, AC-0032 names both trusted roots, and AC-0041 traps file operations outside the permitted sets |

The reviewer also judged the portability exception explicitly: a stdlib-only
reimplementation of confinement is acceptable because a portable pack cannot
import `agentbundle.catalogue_tooling.file_safety`, but only as a named
exception with equivalent outcomes. That is why AC-0038 through AC-0041 exist.

## Spec-stage adversarial review, 2026-09-19

Reviewer: `codex exec`, `gpt-5.6-sol`, high, read-only, fresh session per round,
with the `adversarial-reviewer` rubric inlined in spec/plan mode. The gate fired
on structural surface: a new script module, a new cross-pack integration, a
widened tool surface, and an ADR.

| Round | Findings | Origin split |
| --- | --- | --- |
| 1 | 5 Blockers, 2 Concerns, 1 Nit | all from the first drafted plan |
| 2 | 6 Blockers, 1 Concern, 2 Nits | all from round-1 text or its repairs |
| 3 | 3 Blockers, 1 Concern | all from round-2 text or its repairs |
| 4 | 2 Blockers | both from earlier text, not the round-3 repairs |
| 5 | 1 Blocker, 1 Concern | the Blocker from the new T0 wording |
| 6 | 1 Blocker, 1 Concern, 2 Nits | T0 scope, plus stale references |
| 7 | 3 Blockers, 1 Concern, 1 Nit | T0 scope, writer bypass, AC-0041 ordering |
| 8 | **`Clean — ready to commit.`** | — |

Every finding in both rounds was verified against the tree before adoption, and
three rested on facts the plan had wrong:

- `install.py:_append_layout_section` **never creates an absent layout file**
  (`install.py:3334-3336`) and **returns early when the section already exists**
  (`install.py:3462-3467`), so it can neither create a file nor insert a missing
  key. Treating it as a complete model for persistence would have shipped a
  writer that could not satisfy AC-0008 or AC-0009.
- Both consuming skills declare `allowed-tools: Read Write Edit Agent`, and
  `intake-intent:210` declares "No network, shell … is permitted", while every
  script-shipping core skill — `close-work`, `work-intake`, `workspace-status`,
  `new-spec` — declares `Bash`. The script `intake-intent` already instructs the
  agent to use is therefore not executable under its own declared surface. That
  contradiction predates this slice; owner decision 2026-09-19 folded it in. The ADR that records these construction decisions is a prerequisite rail under the plan's `## Constraints`, not a task: it implements no acceptance criterion.
- `test_intake_intent.py:173-183` already admits a `personal-vault` source after
  both gates and asserts the minimized locator, so AC-0024 needed no new case.

Round 2's sharpest finding was a contradiction introduced by round 1's own
repair: AC-0038 permitted only the invoking skill's own scripts, while the single
resolver lives in `core` and `frame-intent` ships in `product-engineering`. The
criterion now derives the permitted set from the invoking skill's directory plus
the scripts of a provider pack named by one of its declared `pack.integrations`
entries, which is the narrowest widening that makes the settled design
satisfiable.

Reports and packets: `shaping-r1` … `shaping-r9`, `adversarial-r1`,
`adversarial-r2`, `security-r1` in the session scratchpad, not committed.

## Gate status at the close of shaping, 2026-09-19

| Gate | Rounds | Final result |
| --- | --- | --- |
| Shaping spec review (`shaping-reviewer` rubric) | 16 | **`Clean`** |
| Spec-stage adversarial review (`adversarial-reviewer` rubric) | 8 | **`Clean — ready to commit.`** |
| Spec-stage secure-design review (`security-reviewer` rubric) | 6 | **Concerns** — three, each self-labelled `Pre-existing`, routed to the owner as scope decisions rather than absorbed |
| `lint-contract-item-alignment.py` | — | zero failing findings for this spec directory |
| `lint-traceability.py` | — | exit 0 |

The shaping lane reached `Clean` twice and reopened both times, which is the
record worth keeping rather than the final count. Round 6 was `Clean`; the
security gate then forced an amendment that added nine criteria, so that result
stopped binding. Round 11 was `Clean` again; a second security round added three
more criteria and the same thing happened. A `Clean` contract review is a
statement about the text in front of the reviewer, not a property the artifact
keeps while another gate is still running.

### Open scope decisions carried out of shaping

The security lane's last three findings are hardening asks against gaps that
predate this slice, and one design question the adversarial lane raised twice.
They are recorded here rather than converted into criteria, because absorbing a
reviewer's every remedy is how a review loop grows scope without an owner ever
choosing it.

1. **No-clobber on filesystem-equivalent aliases.** An untrusted slug could
   select a path that aliases an existing intent on a case- or
   Unicode-insensitive filesystem. AC-0044 confines the target and AC-0031
   refuses a non-regular file; neither refuses an alias of a *regular* file.
2. **Layout-file permission preservation.** AC-0009 preserves bytes, which
   detects no metadata change, so a staging replacement could widen or narrow
   the layout file's mode.
3. **A resource bound on consulted configuration.** An oversized layout file or
   `output_dir` forces unbounded reading and path handling before any refusal.
4. **The cross-pack installed-script locator.** `pack.integrations` is used for
   handoff and review metadata elsewhere in this repository, never to resolve an
   installed script path. T7 proves one adapter by invocation and AC-0037
   classifies the rest, but no repository mechanism maps a provider skill to its
   installed script directory across adapters.

## The cross-pack execution channel, and why it was deleted — 2026-09-20

The slice reached 54 criteria and three unresolvable security Blockers before
anyone asked the question that settled it: *what is being reached for outside
the boundary?*

Walking the intent lifecycle answered it. Every boundary the lifecycle actually
crosses was already closed:

| Stage | Crossing | Status |
| --- | --- | --- |
| Resolve | Repo config read by a user-scope skill | Handled as data — validate, bound, refuse |
| Resolve | Repo config aiming a write at the user's tree | Foreclosed by AC-0013 |
| Persist | Repo-influenced value landing in user-scope config | Gated by human confirmation of the resolved path |
| Admit | Personal config redirecting repository admission | Foreclosed by AC-0016 |
| Admit | Repo-scope skill running repo-scope code | Not a crossing; the existing posture of every core skill |

The crossing that generated the blockers appears nowhere in that list. It came
from a mechanism choice: sharing one resolver binary between two packs whose
install scopes do not meet — `packs/product-engineering/pack.toml:21` is user
scope, `packs/core/pack.toml:34` is repo-scope only. That meant a user-scope
skill executing code out of a repository tree, in a skill that follows the
adopter into every repository they open.

**No locator could have fixed it**, and two measured facts say why:
`contracts/adapter.toml` is read via `_read_bundled` from inside the agentbundle
wheel and is never projected into an adopter tree, and `.agentbundle-state.toml`
is not gitignored, so it is committed repository-controlled content. Every
candidate anchor was authored by the party being trusted. Validating
repo-supplied code with repo-supplied metadata is circular, which is why the
same security Blocker survived three successive locator refinements.

Owner decision 2026-09-20: each pack ships its own resolver; no skill executes
another pack's code. AC-0034 and AC-0048 through AC-0053 retired. The authority
the spec requires is the layout file that decides placement, not one copy of the
code that reads it; AC-0055 holds the two copies to one rule by running every
resolution, persistence, disclosure, confinement and file-operation criterion
against each.

A correction worth recording: an earlier recommendation in this session proposed
deriving the locator from `.agentbundle-state.toml` **mapped through**
`contracts/adapter.toml`. The first file's presence was verified; the second's
was not, and it is not there. The recommendation was acted on before that check
was made.

## Secure-design review of the per-pack design, 2026-09-20

The earlier secure-design record assessed the deleted cross-pack design and
could not establish the current prerequisite. Re-run against the per-pack
contract, same reviewer configuration, two rounds:

| Round | Findings | Disposition |
| --- | --- | --- |
| 9 | 1 Blocker, 2 Concerns | Blocker: the second copy lacked the write-boundary controls assigned only to core — **sustained**, AC-0055 widened from target-and-code equality to every resolution, persistence, disclosure, confinement and file-operation criterion, run against each copy. Concerns: pre-deletion provider wording — **sustained**, swept from AC-0037, T0 and Rollout; personal intent and staging access policy — **sustained**, AC-0054 extended and AC-0056 added |
| 10 | 0 Blockers, 2 Concerns | `Write`/`Edit` bypassing the bound writer — **partly sustained**: AC-0058 states the rule in each skill's body, and the residual is named in `## Assumptions` because a script-level trap cannot see a model's tool write and the request-file transport needs `Write`. Staging identity — **sustained**, AC-0057 requires exclusive creation of a new regular file bound through the replacement, refusing hostile pre-placement |

The transport question the contract lane raised in the same round is recorded
with them, because it changed the security surface: an agent holding `Bash`
builds a command line, so a heredoc, a pipe, a `printf` or an argument would all
put an untrusted value back into command text or the process table. The only
transport the declared surface supports is a **request file** written with
`Write` and named by a fixed path token, so it is part of the contract and
AC-0039, AC-0040 and AC-0057 govern it.

## Three mechanisms, one error — 2026-09-20

Recorded because the pattern cost more than any single finding in it. Three
successive mechanisms were introduced to satisfy criteria, and each generated
its own review cycle before being removed:

| Mechanism | Introduced to | Removed because |
| --- | --- | --- |
| A cross-pack installed-script locator | let both skills share one resolver | every candidate trust anchor was authored by the party being trusted |
| A stdin channel for untrusted values | keep values out of `argv` | an agent holding `Bash` builds a command line, so no in-line stdin transport exists |
| A request file written with `Write` | carry values out of band | `Write` has no documented atomic create-only, no-follow, or owner-only-before-content contract |

The common error was answering "how do I move this safely?" without first asking
**what actually has to move, and who controls it.** For placement the answer is
nothing: the resolver takes the repository root and a validated slug, and reads
`output_dir` from disk itself — so the one repository-controlled value in the
flow never travels, and no transport is needed at all.

The transport problem was never placement's. It entered through AC-0027 when the
pre-existing `intake-intent` contradiction was folded into scope on 2026-09-19:
the *renderer* takes intake content, a title and a possibly-external source
locator, and those do have to move. Owner decision 2026-09-20 reversed that fold
and moved the renderer's executability to `## Follow-ons` with its evidence.
AC-0027 now covers the resolver alone.

**The review lanes were right every round and could not have caught this.** Each
finding was true of the mechanism in front of it. A correctness reviewer
measuring a mechanism has no way to say "this mechanism should not exist" — that
question is only reachable by walking the lifecycle and asking what crosses a
boundary, which is what produced both this deletion and the cross-pack one.

## The re-cut — 2026-09-20

Twenty-three shaping rounds, ten adversarial and thirteen secure-design rounds
produced a contract of 54 criteria that could not close three security findings.
Re-slicing closed them by deletion. What the record establishes, for anyone
resuming cold:

**The problem was never large.** Three things the adopter experiences: asked
where output goes on every run; two tools writing to different places once
`output_dir` is configured; and configuration one tool ignores. Worst outcome, a
shaping document in an unexpected folder.

**Three mechanisms were introduced and removed**, each generating its own review
cycle: a cross-pack installed-script locator, a stdin channel, and a request
file. Each answered "how do I move this safely" without first asking what has to
move and who controls it. For placement, nothing does: the resolver reads
`output_dir` from disk itself.

**The `Bash` grant was the root of the surface**, not of the problem. Granting
shell to a skill that reads repository content carries three findings no
criterion can close — no integrity binding on repo-resident script bytes, a
working directory the model can change, and uncontained shell on adapters that
cannot express a per-command permission. All three vanish with the grant, and
the grant was only ever needed to make prose criteria mechanically checkable.

**Mechanization belongs where the consequences are.** `intake-intent` touches
admission, confinement and registration, and is already code with a suite, so it
gets code-level evidence. `frame-intent`'s failure is a document in the wrong
folder after the adopter saw the path, so it gets prose evidence and its own
slice, where that weakness is visible rather than hidden inside a code slice.

**What left the family entirely.** The elicitation friction is drift from
RFC-0040's accepted resolution tail, which puts a pack default *before*
elicitation; no consumer implements that step and five packs are affected.
Registered against ADR-0030. Two corrections worth keeping: an earlier
recommendation in this session proposed deriving a locator through
`contracts/adapter.toml`, which is bundled inside the agentbundle wheel and
never reaches an adopter tree — the file's presence was never checked before the
recommendation was acted on. And a later recommendation to make `install` create
the layout file was framed as cheaper than persistence; RFC-0040:202-211 already
routes creation through skill-consent when the adopter *declines* the default,
and ADR-0030 D9 keeps the installer at never-create, so that framing was wrong
on the records too.

**The review lanes were right every round and could not have caught the shape.**
Every finding was true of the mechanism in front of it. A correctness reviewer
measuring a mechanism cannot say "this mechanism should not exist"; that question
is only reachable by walking the lifecycle and asking what crosses a boundary.

## The founding defect was not a defect — 2026-09-20

The brief's `## Current-state evidence` recorded this as live: "An adopter who
points `output_dir` at a personal vault therefore gets `frame-intent` writing to
the vault and `intake-intent` writing to the repository. This is the
deterministic-placement defect already live, not a hypothetical."

It is not a defect. `intake-intent` admits personal and vault sources by design:
`SKILL.md:81-85` requires "a human-confirmed repository-relative destination",
"minimized provenance", and "explicit authority transfer from the external
source into the repository" before such a write, and the renderer carries
`_TRANSFER_MODES = {"chat-only", "personal", "personal-vault", "vault"}`
(`intent_renderer.py:63`). So authoring in a vault and admitting into the
repository are **two stages of one flow**, gated by authority transfer — not two
skills disagreeing about one path.

`intake-intent`'s hardcoded `docs/product/intents/{slug}.md` is also correct
rather than a hardcode to fix: a path that hands off to core is pinned, not
configured, which `frame-intent`'s own layout reference already states for the
sibling case — "`decompose-intent`'s `docs/product/briefs/<slug>.md` output is
**not** governed by this table. That path is the hand-off to core's
`author-delivery-brief continue` skill and stays pinned (a deliberate non-goal of
this layout config)" (`references/agentbundle-layout.md:69-72`).

**Why this is the most expensive entry in this file.** Every mechanism recorded
above — the cross-pack resolver, the installed-script locator, the stdin
channel, the request file, the `Bash` grant and its three irreducible findings —
was built to repair something that already worked. The brief's framing was taken
as given and never tested against the admission contract it described. The
correction came from the owner asking whether `intake-intent` already had a
default, which it did, at `intent_renderer.py:69`, all along.

## This slice's own observations

Empty until `frame-intent-escape-verdicts` T2 runs.
