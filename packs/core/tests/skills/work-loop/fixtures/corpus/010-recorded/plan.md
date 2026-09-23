# Plan: binder-publishing-gate-propagation

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

Every task is **goal-based check** — see the spec's Testing Strategy for why.
No task carries a red stub: `no stub (goal-based)` throughout.

## Constraints

- **One file owns one concern.** The tree exists because the previous draft
  repeated the same fact in several files and patching one broke another. Each
  claim below lands in exactly one authoritative place; every other mention
  becomes a pointer.
- **Evidence and decision are separate rows.** A measurement goes in
  `verified-findings.md`; a design change that follows from it goes in
  `decisions.md`. Z6 produces both.
- **Superseded reasoning is named, not deleted.** The tree's convention.

## Task list

### T1 — Record Z5 in `verified-findings.md`

**Depends on:** none
**Tests:** `no stub (goal-based)`
**Approach:** Add a `### Z5 — telemetry: does the build reach the network?`
finding table in the Z1–Z4 shape (`Z5a`…), covering: the three-layer method and
its controls; the result (no attempt, from any code path); the compiled
`zensical.abi3.so` and its libSystem `_socket`/`_getaddrinfo`/`_recv` references
explained by the `serve` verb; the `zensical.extensions.macros` `git` subprocess
and why the closed allowlist makes it inert; the dependency-set match. Update the
run header so it does not read as if the whole file was run on one date. Add the
Z5 status row.
**Done when:** `grep -n "Z5" verified-findings.md` shows a finding table and a
status row reading `PASSED`, and no `NOT RUN` remains on the Z5 row.

### T2 — Settle the two Z5-contingent claims

**Depends on:** T1
**Tests:** `no stub (goal-based)`
**Approach:** `security-profile.md` § *The subprocess* — replace the
"Z5, unverified" bullet with the measured result, keeping the honest note that we
constrain the input rather than the process, since that remains true of the
*shipped* posture even though the measurement came back clean.
`editorial-model.md` — rewrite the `network_fetch` paragraph's first half: Z5 is
closed and **confirms** the drop, so the declaration is now evidence-backed rather
than contingent. Leave the read-time half (Z4) alone.
**Done when:** `grep -rn "is \*\*Z5, unverified\*\*\|\*\*Z5 is\nopen\*\*" docs/architecture/binder-publishing/` returns nothing. **Scoped to the tree
and to the asserting form on purpose** — run from the repo root against the bare
phrase it also matches this plan, the spec's ACs, and the tree's own quoted
supersession notes, which the convention *requires* to survive.

### T3 — Record Z6 in `verified-findings.md`

**Depends on:** none
**Tests:** `no stub (goal-based)`
**Approach:** Add a `### Z6 — vendored Mermaid in a real browser` finding table:
the three-run design and why the positive control came first; rendering passed
with zero remote requests; the guard suppression explained by the bundle's own
final `globalThis["mermaid"] = …` line; **the accessible-name failure and its
mechanism** — `e.replaceWith(A("div",{class:"mermaid"}))` discards every attribute
on the `<pre>`, and the SVG lands in a `mode:"closed"` shadow root; the
name-present-only-when-broken inversion the degraded run exposed; the two verified
replacement routes; the confirmed-benign degradation; the 3.5 MB asset note. Add
the Z6 status row as **PASSED with a falsification**.
**Done when:** `grep -n "Z6" verified-findings.md` shows the finding table and a
status row that records both halves, and the row does not read `NOT RUN`.

### T4 — Correct the accessible-name claim where it is specified and where it is checked

**Depends on:** T3
**Tests:** `no stub (goal-based)`
**Approach:** Two files, coupled, which is why they are one task.
`zensical-adapter.md` § *Vendoring Mermaid* — confirm the vendoring mechanism, then
specify the accessible-name emission as **allowlisted `attr_list` attributes on the
fence's opening delimiter, lifted into the Mermaid source by the theme as
`accTitle:`/`accDescr:`** (D46), and add the fence-annotation step to the per-file
transformation table. `rollout.md` § *Accessibility smoke checks* — the static check
asserts the attributes against `renderer-plan.json`, and the Z6 bullet becomes a
result. Name what each replaced.

> **This task was re-planned mid-loop, and the reason belongs on the record.** The
> first draft specified a `<figure role="group" aria-label>` wrapper. The
> adversarial pass caught that a wrapper **inserts lines around every diagram**,
> which breaks the single-integer `line-offset` that four files depend on — and that
> it names a container rather than the graphic. Both objections were correct. The
> replanned mechanism was then verified in a browser before being written down
> (Z6f, Z6i), which is the same discipline the gates themselves exist to enforce.
**Done when:** no file in `docs/architecture/binder-publishing/` asserts the name
survives via the `<pre>`'s `attr_list` attributes, and
`grep -rn "Z6, not yet run" docs/architecture/binder-publishing/` returns nothing.
Same scoping caveat as T2.

### T5 — Record the accessible-name decision and the Z-gate correction

**Depends on:** T4
**Tests:** `no stub (goal-based)`
**Approach:** `decisions.md` — add the next `D`-row (D46) for the accessible-name
mechanism: decision, rationale, both rejected routes and what each costs, and the
allowlist rule Z6h forces. Add a Z6 row to *What the Z-gates changed after D40*.
**Done when:** D46 is the line immediately after D45 with **no blank line between
them** — a blank line silently terminates the table and renders the row as literal
pipe text, which the first attempt did and `grep -n "^| D46"` happily passed — and
the correction table carries a Z6 row.

### T6 — Answer V6 and simplify the defensive specification

**Depends on:** none
**Tests:** `no stub (goal-based)`
**Approach:** `verified-findings.md` — update the V6 row in place: answered **no**,
with the two measured adapters, the five unmeasured ones and why, and the
consequence. `overview.md` § *What "repository scope" means outside Git* — the
"Rules 2–4 apply only when …" paragraph states the measurement and drops
"`--root` is effectively **required**"; rule 4 does the work; the self-realpath
guard is retained as a cheap net for the unmeasured adapters. `invocation.md` §
*Entry-point resolution* — the same, in its own voice, and `--root` becomes
recommended-for-determinism rather than required.
**Done when:** `grep -n "is effectively \*\*required\*\*" docs/architecture/binder-publishing/overview.md docs/architecture/binder-publishing/invocation.md`
returns nothing — the two files that asserted it — and the V6 row does not read
`NOT RUN`. **A tree-wide grep is the wrong check**: `overview.md`, `verified-findings.md` and `history.md` all quote the
superseded wording deliberately, and D47 quotes it in its own
*Supersedes* column, so a tree-wide grep reports failure on a *correct* tree — the
mirror image of the D46 table-row grep that passed on a broken one.

### T7 — Bring the tree's bookkeeping current

**Depends on:** T1, T3, T6
**Tests:** `no stub (goal-based)`
**Approach:** `rollout.md` — Phase 1's gate list, the decisions-required list, and
U7's status. `history.md` — a round entry in the established voice, recording that
the gate run falsified one specified control and relaxed one. `README.md` — the
status line, and the `verified-findings.md` row of *Read in this order* if it
scopes the live gates to Z1–Z4.
**Done when:** `grep -rn "Z5, Z6" rollout.md` returns nothing that reads as
pending, and `grep -n "Z5\|Z6\|V6" README.md history.md` shows them as run.

### T8 — Capture the two out-of-tree defects as deferrals

**Depends on:** T6
**Tests:** `no stub (goal-based)`
**Approach:** `workspace.toml [backlog].open` — two entries with
cold-start-sufficient comments: the `converters` bare-relative script-path defect
(`mermaid-renderer`, `markdown-to-html`), and the exit-code-2 collision between
"script not found" and a skill's "dependency missing" reading.
**Done when:** both slugs are present in `[backlog].open` and parse under
`tomllib`.

### T9 — Gates, review, finish

**Depends on:** T1–T8
**Tests:** `no stub (goal-based)`
**Approach:** `python3 tools/lint-ruff.py`; `SKIP_SAST=1 make build-check` (legitimate
here — the diff touches no `SAST_DIRS` path and no SAST config);
`python3 .claude/skills/work-loop/scripts/lint-spec-status.py --root .`. Then the
single bounded `adversarial-reviewer` pass, and the cold `design-reviewer` pass over
`docs/architecture/binder-publishing/` scoped to gate propagation. Every finding is
dispositioned, and both passes' findings plus their dispositions are recorded in
`notes/review-2026-08-07.md` so the ACs have a durable artifact rather than a
transcript.
**Done when:** all three gates exit 0, both reviewers' findings are dispositioned,
and `git status` is clean but for this change.

### T10 — Commit the harness and the review record

**Depends on:** T9
**Tests:** `no stub (goal-based)`
**Approach:** The gate harness lives in `/tmp`, which does not survive, while
`verified-findings.md` commits Phase 1 to rebuilding Z1–Z6 as CI assertions *with
negative controls*. Copy the fixture generator, the socket tracer, the browser
probes, the sandbox profiles, the a11y shim, and the per-run JSON into
`notes/harness/`, and the transcribed results into `notes/gate-results-2026-08-07.md`.
Record both review passes and their dispositions in `notes/review-2026-08-07.md`.
**Done when:** `notes/` holds the harness and both records, and no AC cites an
artifact that exists only in a transcript.

## Risks

- **Propagation misses a mention.** This is the defect class the tree split exists
  to prevent and the one `history.md` says recurs. Mitigated by making every
  `Done when:` a `grep` over the whole tree rather than over the file just edited —
  and by re-running the greps unfiltered at T9 rather than trusting the per-task run.
- **The Z6 correction reads as a renderer problem.** It is not: the vendoring
  mechanism works. The rows must keep "rendering passed" and "the name assertion
  failed" visibly separate, or a reader will conclude ADR-0073 is in question.
- **Over-claiming V6.** Five adapters are unmeasured. The relaxation is safe
  because the guard stays, but the prose must not imply seven were tested.

## Changelog

- 2026-08-07 — plan drafted from the executed gate results.
