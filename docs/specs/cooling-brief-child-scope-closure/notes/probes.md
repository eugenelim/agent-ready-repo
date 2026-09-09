# Probes: what was constructed rather than read

Every load-bearing claim in `spec.md` was produced by running code and printing
the result. Wave 7a-ii lost three review rounds to a criterion that asserted
what `dataclasses.asdict` emits for a `Dependency` — three keys, from reading;
six, from running — so nothing here is asserted from a function body.

All probes ran on 2026-09-03 at HEAD `807fc8ef1`, from the repository root, with
the engine loaded from source rather than an installed projection:

```python
EP = "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
spec = importlib.util.spec_from_file_location("eng", EP)
E = importlib.util.module_from_spec(spec); sys.modules["eng"] = E
spec.loader.exec_module(E)
```

Loading from source matters: an editable install can point at a deleted
worktree, and `agentbundle`'s packaged `_data/` copy is a projection, not the
source of truth.

## Probe 1 — three raw values are representable, so no schema change is needed

Ran `E.parse_workspace_entry` over three TOML entry literals differing only in
`source.parent`, and printed the raw and normalized values.

```
  parent = "none"                          raw='none'  normalized=None  findings=[]
  parent = "docs/product/briefs/b.md"      raw='docs/product/briefs/b.md'  normalized='docs/product/briefs/b.md'  findings=[]
  (absent)                                 raw=None  normalized=None  findings=[]
```

The parsed entry keeps the raw string. `_normalized_optional_artifact_value`
collapses `'none'` and `None` to the same value, but only at its call sites, so
the distinction between "declared empty" and "undeclared" is available to the
engine and is not currently used. Neither form raises a parse finding.

## Probe 2 — the published schema already admits `parent = "none"`

Validated two instances against
`contracts/jsonschema/workspace-entry.schema.json` with `jsonschema.validate`.

```
  schema accepts parent='none': YES
  schema accepts parent='docs/product/briefs/b.md': YES
```

`none` satisfies the `repositoryRelativePath` pattern, so the closure adds no
schema field and needs no contract version bump.

## Probe 3 — the corpus, measured with production's own parsers

Ran `E._extract_canonical_memberships` over the real `workspace.toml`, then
`E._metadata_from_root` over every `kind = "spec"` membership, and classified
each by whether its entry and its body declare a parent.

```
canonical memberships: 215  legacy: 1
spec memberships: 115

A. no parent anywhere:        99
B. BODY-ONLY parent:          0
C. entry declares source.parent: 16
```

All 16 in class C agree exactly between entry and body. Class B — a body-declared
parent the entry omits — is the gap's population, and it is **empty**.

Grouped by collection, the 115 spec memberships are 114 `work.shipped` and 1
`work.active`; 99 declare no `source.parent` and 16 do.

The brief side, and the blast radius of a fail-closed floor:

```
briefs: 15
briefs with 0 attributed children: 11
live kind="brief" needs across all entries: 5
cooled specs today (docs/lifecycle records): 0
```

All 5 brief dependencies are brief→brief edges inside `brief_queue.draft`,
pointing at 4 distinct briefs. With no lifecycle records present, the
fail-closed path is unreachable on this checkout, so it costs zero refusals
today.

## Probe 4 — `provenance_mismatch` is the control, and cooling suppresses it

Built a fixture with one spec in `work.shipped` and varied its entry's
`source.parent` against its body's `- **Brief:**` value.

```
== provenance_mismatch: does the entry/body parent divergence get named? ==
  entry=none  body=b.md  (THE GAP CASE)      [('provenance_mismatch', 'docs/specs/child/spec.md')]
  entry=b.md  body=b.md  (agreeing)          []
  entry=b.md  body=none  (reverse)           [('provenance_mismatch', 'docs/specs/child/spec.md')]
  entry=none  body=none  (parentless)        []
```

The control is symmetric: it fires whichever side declares the parent alone.
This is what makes a declared `parent = "none"` trustworthy — an entry claiming
no parent while its body names a brief is a live finding on every uncooled run.

Probe 5's rows show the other half: once the artifact cools,
`provenance_mismatch` disappears, because `_structural_findings` returns at
`:3138` before reaching the comparison at `:3172`.

## Probe 5 — the gap, constructed with Wave 6's own fixture helpers

Imported `tests/roster/test_status_projection_and_context_exclusion` and reused
its `_brief_body`, `_child_spec`, `_brief_workspace`, `_cool_child`, and
`_reconcile_canonical` helpers, so the fixture semantics are the shipped ones
rather than a re-derivation. `_child_spec`'s own docstring calls its `brief`
parameter "the shape the residual turns on".

```
brief path: docs/product/briefs/brief-1.md

=== brief_queue.shipped ===
  1 attributed  (entry=brief)  uncooled
      cooled=0 ready=['docs/specs/dependant/spec.md']
      findings=[('missing_plan', ...child...), ('provenance_mismatch', ...child...)]
  2 attributed  (entry=brief)  COOLED
      cooled=1 ready=[]
      findings=[('unsatisfied_dependency', 'docs/product/briefs/brief-1.md')]
  3 body-only   (entry=None)   uncooled
      cooled=0 ready=['docs/specs/dependant/spec.md']
      findings=[('missing_plan', ...child...), ('provenance_mismatch', ...child...)]
  4 body-only   (entry=None)   COOLED
      cooled=1 ready=['docs/specs/dependant/spec.md']
      findings=[]

=== brief_queue.executing ===
  5 body-only   (entry=None)   uncooled
      cooled=0 ready=['docs/specs/dependant/spec.md']
      findings=[('missing_plan', ...), ('provenance_mismatch', ...), ('impossible_transition', brief), ('unsatisfied_dependency', brief)]
  6 body-only   (entry=None)   COOLED
      cooled=1 ready=[]
      findings=[('impossible_transition', brief), ('unsatisfied_dependency', brief)]
  7 attributed  (entry=brief)  COOLED
      cooled=1 ready=[]
      findings=[('unsatisfied_dependency', brief)]
```

**Row 4 is the defect.** A cooled child whose brief link is body-only, under
`brief_queue.shipped`, leaves the dependant in `canonical.ready` with an
**empty findings list** — no signal of any kind. Row 2 is the attributed
control on the same mechanism: the dependant is blocked and the refusal is
named. The two rows differ only in whether the entry declared the parent.

**Row 6 is the other half.** The same body-only cooled child under
`brief_queue.executing` leaves `impossible_transition` on the brief, which row 7
shows is suppressed when the child is attributed. That is a finding planted on
live work by the act of cooling a different artifact.

`missing_plan` in rows 1, 3, and 5 is fixture noise — `_child_spec` writes no
sibling plan — and is absent from every cooled row because the cooled arm stops
before the plan predicates. It does not bear on the observable.

## Probe 6 — the brief's own `## Spec map` is not a usable read-free index

A brief is not cooled, so reading *its* body would be a legitimate read-free
route to its children, inverting the attribution problem. Measured whether the
section is machine-readable: parsed `## Spec map` from all 15 briefs and counted
rows matching a backticked-slug table cell.

```
agent-authoring-input-quality.md          specmap=Y rows= 0  entry-linked-children=0
agent-skill-engineering.md                specmap=Y rows= 4  entry-linked-children=4
catalogue-discovery-and-release-integrity.md specmap=N rows= 0  entry-linked-children=0
digital-experience-doctrine-completion.md specmap=N rows= 0  entry-linked-children=0
distribution-routes-programme.md          specmap=Y rows= 2  entry-linked-children=2
tech-site-completion.md                   specmap=Y rows= 9  entry-linked-children=9
universal-implementer-dispatch.md         specmap=Y rows= 0  entry-linked-children=1
work-loop-next-action.md                  specmap=Y rows= 0  entry-linked-children=0
(7 further briefs: specmap=Y rows=0 entry-linked-children=0)
```

Two of 15 briefs have no `## Spec map` at all. Of the 13 that do, 3 carry
parseable rows. The formats disagree: `tech-site-completion.md` backticks its
slugs, `universal-implementer-dispatch.md` does not, `work-loop-next-action.md`
writes the prose "None.", and `agent-authoring-input-quality.md` carries an
empty table row. `universal-implementer-dispatch.md` has one attributed child
that its section does not name in a parseable form.

The section's own prose claims its Status column is "derived from each linked
spec by the `receive-brief` coverage lint".

**Corrected 2026-09-08, after review refuted the original claim.** This probe
first recorded that "no such lint exists" and that "no Python under `tools/`,
`packs/`, or `tests/` reads a `Spec map`". The second half is false. Re-run,
`grep -rln 'Spec map' --include='*.py' tools/ packs/ tests/` returns seven
files, including `packs/core/.apm/skills/author-delivery-brief/scripts/lint-brief-coverage.py`,
which parses the section and enforces that a Shipped brief's mapped children are
non-empty and all shipped, as an exit-1 finding wired into the gate chain.

What was true is narrower: `receive-brief` ships no such lint, and the prose
attributes it to the wrong skill. The lint lives in `author-delivery-brief`.

**The rejection stands on the other two measured facts, which this correction
does not touch.** 2 of 15 briefs carry no `## Spec map` at all, and of the 13
that do, only 3 have parseable rows — the formats disagree across backticked
slugs, bare slugs, the prose "None.", and an empty table row. Parsing this
section *here* would still fail silently into under-attribution. What changed is
the reason: not that nothing checks the section, but that what checks it reads
the brief's own prose while this projection reads workspace entries, and the two
inputs disagree.

**Why the error mattered.** This probe was cited as the basis for an engine
comment and for an ADR clause, both of which then asserted that nothing reads
the section. A search that is narrower than its conclusion propagates as a fact.

## Probe 7 — a declared parent that names no brief membership escapes the floor

Ran the same fixture as probe 5 with the child cooled and its entry's
`source.parent` varied against a registered brief membership of
`docs/product/briefs/brief-1.md`.

```
  parent='docs/product/briefs/brief-1.md'        ready=[]           findings=[('unsatisfied_dependency', brief-1)]  -> PROTECTED
  parent='docs/product/briefs/Brief-1.md'        ready=[dependant]  findings=[]  -> ESCAPES
  parent='docs/product/briefs/does-not-exist.md' ready=[dependant]  findings=[]  -> ESCAPES
  parent='none'                                  ready=[dependant]  findings=[]  -> intended
```

A one-character case change and a dangling path both reproduce probe 5 row 4
exactly: the dependant dispatches and nothing is reported. `_provenance_path_is_invalid`
checks shape and confinement but never existence, and the single-segment pattern
admits uppercase, so neither value raises `invalid_artifact_path`.

This is why the predicate is *scope established* — declared-empty, or declared
**and resolving to a brief membership** — rather than *scope declared*. The last
row is the intended fail-open answer and is not a defect: it is an assertion
someone wrote, where the two middle rows are typos that read as assertions.

## Probe 8 — a finding emitted from `_structural_findings` refuses non-brief dependants

Built a cooled child in `work.shipped` with a queued spec declaring a
`kind = "spec"` dependency on it, and varied whether the cooled entry carried a
structural finding (an out-of-root `source.parent`, which `:3131-3136` raises
ahead of the cooled return).

```
  clean cooled child         ready=['docs/specs/dependant/spec.md']  findings=[]
  cooled child + BAD parent  ready=[]  findings=[('invalid_artifact_path', '../escape/brief.md'),
                                                 ('unsatisfied_dependency', 'docs/specs/child/spec.md')]
```

Any finding raised on a cooled membership puts its path into
`structurally_blocked_paths` (`:3425-3426`), and `:2670` refuses every dependency
on a blocked path before any kind test. So emitting `cooled_child_scope_unknown`
there would refuse `kind = "spec"` and `kind = "defect"` dependants too, past the
`kind = "brief"` boundary the spec states — and would contradict Wave 6 AC14,
which the first row shows holding today.

The emission site is therefore `run_canonical_reconciliation`, which appends to
the findings list without touching `structurally_blocked_paths`.

## Probe 9 — a repository-wide `scope_unevaluable` erases real violations in two arms

Called `_brief_child_scope_is_valid` directly across seven arm/state pairs.

```
arm                        child_states      unevaluable=False  unevaluable=True
  brief_queue.executing    ['Queued']        False              True   <== ERASES A REAL VIOLATION
  brief_queue.executing    []                False              True
  brief_queue.executing    ['Implementing']  True               True
  brief_queue.shipped      ['Queued']        False              False
  brief_queue.shipped      []                True               True
  brief_queue.draft        ['Shipped']       False              False
  brief_queue.cancelled    ['Queued']        False              True   <== ERASES A REAL VIOLATION
```

The docstring's asymmetry is about which *arms* are suppressed, not which
*brief* is affected, so a repository-wide flag clears the violation for a brief
whose live readable children are all `Queued` — in `cancelled` as well as
`executing`.

The bound under test, setting suppression only when the observed set is empty:

```
  brief_queue.executing    ['Queued']        baseline=False  narrowed=False  preserved
  brief_queue.executing    []                baseline=False  narrowed=True   CHANGED (empty-set only)
  brief_queue.executing    ['Implementing']  baseline=True   narrowed=True   preserved
  brief_queue.shipped      ['Queued']        baseline=False  narrowed=False  preserved
  brief_queue.shipped      []                baseline=True   narrowed=True   preserved
  brief_queue.draft        ['Shipped']       baseline=False  narrowed=False  preserved
  brief_queue.cancelled    ['Queued']        baseline=False  narrowed=False  preserved
```

Exactly one cell changes, and it is the genuinely ambiguous one. No live
readable child's violation is erased. The last `shipped` row also shows why the
`brief_queue.shipped` residual is real and not closed by this delivery:
suppression never reaches that arm in either direction.

## Probe 10 — a finding's `detail` never reaches a consumer

Built a cooled attributed child, reconciled, and printed the finding's dataclass
fields beside the projected JSON payload.

```
dataclass fields : ['code', 'detail', 'dispatchable', 'next_action', 'path']
detail value     : 'brief child scope is unknown'
JSON payload keys: ['code', 'dispatchable', 'next_action', 'path']
detail in JSON   : False
snapshot keys    : ['code', 'dispatchable', 'next_action', 'path']
```

`RoutingFinding` carries `detail`, but `_canonical_finding_payload` (`:1493`)
projects four keys and `detail` is not among them, so it reaches neither
`canonical_result_snapshot` nor any CLI or MCP consumer.

This rules out distinguishing the two unknown-scope causes — no parent declared,
versus a declared parent that resolves to no brief membership — by `detail`. The
distinction would exist only inside the process. `next_action` is keyed one per
code in `_FINDING_NEXT_ACTIONS`, so it cannot vary by cause either. One code with
one next action naming both remedies is therefore the honest shape, and the
finding's `path` lets a maintainer read the declared value for themselves.

## Probe 11 — the tightened frozen-spec control kills every over-broad edit

*The frozen body is otherwise unchanged* must permit exactly one changed line. Stated line-wise, a
set-wise implementation would admit a deletion. Stated as *restore the Status
line, then compare the whole file against the pre-edit digest*, it does not.

The pre-edit digest is not invented here: it is the value
`tests/roster/test_cooling_scope_closure.py` already pins for this file,
`2cac21ca5f84e0f4e477a6bab432429a55034f6851dc152cfcd93611e9e3523d`.

```
  unchanged file                   -> True   expect True   OK
  Status line only (legitimate)    -> True   expect True   OK
  Status + body line DELETED       -> False  expect False  OK
  Status + body token CHANGED      -> False  expect False  OK
  Status + body line APPENDED      -> False  expect False  OK
  Status + two lines REORDERED     -> False  expect False  OK
```

Equal line count, per-index equality, and exactly one substituted line are all
required, and no `git` call is needed.


### Probe 11 addendum — the control survives a second Status pointer

A concurrent session flagged that a later delivery might add its own supersession
pointer to the same Status line. Measured, because the control would be worthless if it
broke on that.

```
  one pointer  -> control PASSES
  two pointers -> control PASSES
```

The substitution replaces the whole `- **Status:**` line whatever it contains, so
the comparison is against the pre-edit body rather than against any particular
pointer text. It therefore constrains *how much of the file changed* without
constraining *how many pointers the Status line carries* — which is the right
split, since `docs/CONVENTIONS.md` rule 1 governs pointer content and this
criterion governs body integrity.

## Probe 12 — suppression buys no dispatch change, only the loss of a finding

Measured on an `brief_queue.executing` brief whose only child is cooled, comparing the
attributed case (where Wave 6's shipped suppression is active) against the
unestablished case (where it is not).

```
suppression ACTIVE  (attributed cooled child):
   ready   = []
   findings= [('unsatisfied_dependency', 'docs/product/briefs/brief-1.md')]
suppression ABSENT  (undeclared cooled child):
   ready   = []
   findings= [('impossible_transition', 'docs/product/briefs/brief-1.md'),
              ('unsatisfied_dependency', 'docs/product/briefs/brief-1.md')]

DISPATCH outcome identical: True
delta in findings        : [('impossible_transition', 'docs/product/briefs/brief-1.md')]
```

The ready sets are identical. The whole effect of suppression is that one
finding disappears — it changes no dispatch decision, because the dependency
floor already refuses that brief's dependants for its own reason.

So the choice was between a possibly-false finding that is visible and blocks
nothing further, and silently erasing a real one on the 11 of 15 briefs that
have zero attributed children. `workspace-routing-invariants`'s Objective —
inconsistent state fails closed — settles it: keep the finding, drop the rail.


## Probe 13 — a vacuous dispatch comparison and a false control

**AC9's dispatch-equality clause was vacuous.** Its four arms:

```
   parent=omitted  dependant=True  -> ready=[]
   parent=declared dependant=True  -> ready=[]
   parent=omitted  dependant=False -> ready=[]
   parent=declared dependant=False -> ready=[]
```

`canonical.ready` is empty in every arm, because a `kind = "brief"` dependency on
a `brief_queue.executing` brief is never terminal-satisfied and the cooled child
is not dispatchable. So "identical to the same fixture with…" compared two empty
sets and would hold against a completely broken engine. The clause is deleted,
and AC9 now asserts findings only.

**AC10's control was false for the fixture AC10 specified.**

```
   child body Status=Shipped       cooled=0  control(no record)=0
   child body Status=Implementing  cooled=0  control(no record)=0
   child body Status=Approved      cooled=0  control(no record)=1
```

AC10 asserted that removing the `Cooling` record yields exactly one
`impossible_transition`. That is true only when the child's body status is a
non-execution token. `execution_evidence` (`:3885`) is satisfied by `Shipped` or
`Implementing`, and the Wave 6 helper defaults to `Shipped` — so the control
would have reported none, and the criterion would have failed for a reason
unrelated to the behaviour under test. AC10 now pins `Approved`.

## Probe 14 — the derivation matrix every criterion is transcribed from

Seven axes decide every observable below: the brief's collection and body
status, and per spec its collection, body status, body brief link, raw
`source.parent` and sibling-plan presence, plus which locators carry a `Cooling`
record and any dependency's kind. This matrix pins all seven at once and prints
the unfiltered result, and the criteria state those literals rather than citing
this file.

The construction is recorded here, not just its output, because a reader
re-running from the Wave 6 helpers diverges: `_child_spec` writes no sibling
plan, so it emits `missing_plan` noise this builder does not. Run it from the
repository root.

```python
"""Derivation matrix: every axis explicit, every finding printed unfiltered."""
import importlib.util, sys, pathlib, tempfile, json
ROOT = pathlib.Path(__file__).resolve().parents[0]   # run from the repository root
EP = ROOT/"packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
_s = importlib.util.spec_from_file_location("eng", EP); E = importlib.util.module_from_spec(_s)
sys.modules["eng"] = E; _s.loader.exec_module(E)
BRIEF = "docs/product/briefs/brief-1.md"
OMIT = object()   # entry omits the `parent` key entirely

def _record(did, locator):
    return {"schema":"delivery-lifecycle-record.v1","delivery_id":did,"locator":locator,
      "aliases":[],"fingerprint":"sha256:"+"0"*64,"disposition":"cool-30-days",
      "post_closeout_result":"Cooling","completion_event":"merge",
      "completion_evidence_ref":"commit:"+"1"*40,"completed_on":"2026-01-01",
      "timezone":"Asia/Singapore","review_on":"2026-01-31",
      "authority":{n:{"status":"confirmed"} for n in ("source","write","delete")},
      "confirmation_proof":"sha256:"+"2"*64}

def _spec(root, slug, status, body_brief, plan):
    d = root/"docs/specs"/slug; d.mkdir(parents=True, exist_ok=True)
    (d/"spec.md").write_text(f"# Spec: {slug}\n\n- **Status:** {status}\n- **Brief:** {body_brief}\n")
    if plan: (d/"plan.md").write_text("# Plan\n\n- **Status:** Done\n")

def _entry(path, parent, needs="[]"):
    pc = "" if parent is OMIT else f', parent = "{parent}"'
    return ('{path = "'+path+'", kind = "spec", source = {mode = "repo-origin"'+pc+'}, '
            'summary = "f", needs = '+needs+'}')

def run(root, *, brief_status, brief_collection, specs, cooled_locators):
    """specs: list of dicts with slug/status/body_brief/parent/collection/plan/needs."""
    root.mkdir(parents=True, exist_ok=True)
    b = root/"docs/product/briefs"; b.mkdir(parents=True, exist_ok=True)
    (b/"brief-1.md").write_text(f"# Brief\n\n- **Status:** {brief_status}\n")
    work = {"queue": [], "active": [], "shipped": []}
    for s in specs:
        _spec(root, s["slug"], s["status"], s["body_brief"], s["plan"])
        work[s["collection"]].append(_entry(f"docs/specs/{s['slug']}/spec.md",
                                            s["parent"], s.get("needs","[]")))
    if cooled_locators:
        lc = root/"docs/lifecycle"; lc.mkdir(parents=True, exist_ok=True)
        for i, loc in enumerate(cooled_locators):
            (lc/f"r{i}.json").write_text(json.dumps(_record(f"r{i}", loc)))
    bq = {k: "[]" for k in ("draft","ready","executing","shipped","cancelled","withdrawn")}
    be = ('{path = "'+BRIEF+'", kind = "brief", source = {mode = "repo-origin"}, '
          'summary = "b", needs = []}')
    bq[brief_collection] = f"[{be}]"
    (root/"workspace.toml").write_text(
      '["ini-002"]\nname="F"\nstatus="active"\nmilestone="M1"\n\n["ini-002".work]\n'
      + "".join(f'{k} = [{",".join(v)}]\n' for k, v in work.items())
      + '\n["ini-002".brief_queue]\n' + "".join(f"{k} = {v}\n" for k, v in bq.items())
      + '\n["ini-002".shaping_queue]\nactive = []\nbacklog = []\n')
    ws = E.parse_workspace(root/"workspace.toml")
    cool, _ = E._resolve_cooled_state(root)
    r = E.run_canonical_reconciliation(ws, root, cool)
    return (sorted(e.entry.path for e in r.evaluations if e.dispatchable),
            sorted((f.code, f.path) for f in r.findings))

def child(status="Shipped", body_brief="none", parent=OMIT, collection="shipped", plan=True, slug="child", needs="[]"):
    return dict(slug=slug, status=status, body_brief=body_brief, parent=parent,
                collection=collection, plan=plan, needs=needs)

DEP = child(slug="dependant", status="Approved", body_brief="none", parent=OMIT,
            collection="queue", plan=True,
            needs='[{type = "local", kind = "brief", path = "'+BRIEF+'"}]')
CHILD = "docs/specs/child/spec.md"

CASES = {
 "AC1  cooled, entry+body=brief, brief Shipped, brief-dep":
   dict(brief_status="Shipped", brief_collection="shipped",
        specs=[child(status="Shipped", body_brief=BRIEF, parent=BRIEF), DEP], cooled_locators=[CHILD]),
 "AC1  CONTROL no record":
   dict(brief_status="Shipped", brief_collection="shipped",
        specs=[child(status="Shipped", body_brief=BRIEF, parent=BRIEF), DEP], cooled_locators=[]),
 "AC2  cooled, entry='none' body='none', brief Shipped":
   dict(brief_status="Shipped", brief_collection="shipped",
        specs=[child(status="Shipped", parent="none"), DEP], cooled_locators=[CHILD]),
 "AC3/4 cooled, entry OMITTED body='none', brief Shipped":
   dict(brief_status="Shipped", brief_collection="shipped",
        specs=[child(status="Shipped", parent=OMIT), DEP], cooled_locators=[CHILD]),
 "AC5  cooled, entry OMITTED body=brief, NO dependant":
   dict(brief_status="Shipped", brief_collection="shipped",
        specs=[child(status="Shipped", body_brief=BRIEF, parent=OMIT)], cooled_locators=[CHILD]),
 "AC6  cooled, entry=Brief-1.md (case variant), brief Shipped":
   dict(brief_status="Shipped", brief_collection="shipped",
        specs=[child(status="Shipped", parent="docs/product/briefs/Brief-1.md"), DEP], cooled_locators=[CHILD]),
 "AC7  two cooled: child entry='none', other entry OMITTED":
   dict(brief_status="Shipped", brief_collection="shipped",
        specs=[child(status="Shipped", parent="none"),
               child(slug="other", status="Shipped", parent=OMIT)],
        cooled_locators=[CHILD, "docs/specs/other/spec.md"]),
 "AC8  cooled child OMITTED + second Approved queued spec w/ kind=spec dep":
   dict(brief_status="Shipped", brief_collection="shipped",
        specs=[child(status="Shipped", parent=OMIT),
               child(slug="second", status="Approved", parent=OMIT, collection="queue", plan=True,
                     needs='[{type = "local", kind = "spec", path = "'+CHILD+'"}]')],
        cooled_locators=[CHILD]),
 "AC9  brief EXECUTING body=Executing, child Approved entry OMITTED":
   dict(brief_status="Executing", brief_collection="executing",
        specs=[child(status="Approved", parent=OMIT), DEP], cooled_locators=[CHILD]),
 "AC9  CONTROL same, entry+body=brief":
   dict(brief_status="Executing", brief_collection="executing",
        specs=[child(status="Approved", body_brief=BRIEF, parent=BRIEF), DEP], cooled_locators=[CHILD]),
 "AC10 brief EXECUTING body=Executing, attributed cooled Approved child + queued Approved second":
   dict(brief_status="Executing", brief_collection="executing",
        specs=[child(status="Approved", body_brief=BRIEF, parent=BRIEF),
               child(slug="second", status="Approved", body_brief=BRIEF, parent=BRIEF, collection="queue")],
        cooled_locators=[CHILD]),
 "AC10 CONTROL no record":
   dict(brief_status="Executing", brief_collection="executing",
        specs=[child(status="Approved", body_brief=BRIEF, parent=BRIEF),
               child(slug="second", status="Approved", body_brief=BRIEF, parent=BRIEF, collection="queue")],
        cooled_locators=[]),
 "AC11 cooled child OMITTED + cooled BRIEF, brief-dep":
   dict(brief_status="Shipped", brief_collection="shipped",
        specs=[child(status="Shipped", parent=OMIT), DEP], cooled_locators=[CHILD, BRIEF]),
 "AC12 UNCOOLED, body=brief, entry OMITTED":
   dict(brief_status="Shipped", brief_collection="shipped",
        specs=[child(status="Shipped", body_brief=BRIEF, parent=OMIT)], cooled_locators=[]),
 "AC12 UNCOOLED, body=brief, entry='none'":
   dict(brief_status="Shipped", brief_collection="shipped",
        specs=[child(status="Shipped", body_brief=BRIEF, parent="none")], cooled_locators=[]),
 "AC13 UNCOOLED, body='none', entry='none'":
   dict(brief_status="Shipped", brief_collection="shipped",
        specs=[child(status="Shipped", body_brief="none", parent="none")], cooled_locators=[]),
}
with tempfile.TemporaryDirectory() as t:
    for i, (label, kw) in enumerate(CASES.items()):
        ready, finds = run(pathlib.Path(t)/f"c{i}", **kw)
        print(label)
        print(f"     ready    = {ready}")
        print(f"     findings = {finds}")
```

Run on the current engine, so `findings` is the **pre-change** state. Where a
criterion asserts new behaviour, its row records what must change.

```
AC1  cooled, entry+body=brief, brief Shipped, brief-dep
     ready    = []
     findings = [('unsatisfied_dependency', brief)]
AC1  CONTROL no record
     ready    = ['docs/specs/dependant/spec.md']
     findings = []
AC2  cooled, entry='none' body='none', brief Shipped
     ready    = ['docs/specs/dependant/spec.md']
     findings = []
AC3/4 cooled, entry OMITTED body='none', brief Shipped
     ready    = ['docs/specs/dependant/spec.md']
     findings = []
AC5  cooled, entry OMITTED body=brief, NO dependant
     ready    = []
     findings = []
AC6  cooled, entry=Brief-1.md (case variant), brief Shipped
     ready    = ['docs/specs/dependant/spec.md']
     findings = []
AC7  two cooled: child entry='none', other entry OMITTED
     ready    = []
     findings = []
AC8  cooled child OMITTED + second Approved queued spec w/ kind=spec dep
     ready    = ['docs/specs/second/spec.md']
     findings = []
AC9  brief EXECUTING body=Executing, child Approved entry OMITTED
     ready    = []
     findings = [('impossible_transition', brief), ('unsatisfied_dependency', brief)]
AC9  CONTROL same, entry+body=brief
     ready    = []
     findings = [('unsatisfied_dependency', brief)]
AC10 brief EXECUTING body=Executing, attributed cooled Approved child + queued Approved second
     ready    = ['docs/specs/second/spec.md']
     findings = []
AC10 CONTROL no record
     ready    = ['docs/specs/second/spec.md']
     findings = [('impossible_transition', brief), ('impossible_transition', 'docs/specs/child/spec.md')]
AC11 cooled child OMITTED + cooled BRIEF, brief-dep
     ready    = ['docs/specs/dependant/spec.md']
     findings = []
AC12 UNCOOLED, body=brief, entry OMITTED
     ready    = []
     findings = [('provenance_mismatch', 'docs/specs/child/spec.md')]
AC12 UNCOOLED, body=brief, entry='none'
     ready    = []
     findings = [('provenance_mismatch', 'docs/specs/child/spec.md')]
AC13 UNCOOLED, body='none', entry='none'
     ready    = []
     findings = []
```

### What the matrix fixed in the criteria

- **A brief body status other than the collection's own vocabulary adds a second
  `impossible_transition` on the brief.** AC9 and AC10 assert brief-path counts,
  so both state `Status: Executing` for a `brief_queue.executing` brief.
- **AC1's control reads the uncooled child body.** It holds only at
  `Status: Shipped`, so AC1 states it.
- **AC8's observable is its second spec's dispatchability**, which needs
  `Status: Approved` and a sibling plan; its row prints that path, so the
  criterion and the row agree.
- **AC10's no-record control carries two `impossible_transition` entries**, on
  the brief and on the `Approved` child in `work.shipped`; only the brief-scoped
  count is one.
- **AC5 and AC7 assert no `ready` membership.** Neither fixture has a
  dispatchable spec, so `ready` is `[]` before and after and discriminates
  nothing.
- **Declaring `source.parent` on an entry whose body says `none` emits
  `provenance_mismatch`.** Every attributed fixture sets both, so the noise never
  reaches a criterion's observable.

## Probe 15 — the corpus and the gap, re-derived after the Wave 7c merge

Wave 7c added a fourth cooling pair, `("retain-exception", "Reclassified")`, to
`_COOLING_PAIRS`. A new pair admits artifacts that could not cool before, so
probe 3's corpus figures and probe 5's zero population are re-derived here
rather than carried across the base change.

Run from the repository root at base `9ab376dcc`:

```python
import pathlib, sys, tomllib

REPO = pathlib.Path.cwd()
sys.path.insert(0, str(REPO / "packs/core/.apm/skills/workspace-status/scripts"))
import workspace_status_engine as E

print("_COOLING_PAIRS =", sorted(E._COOLING_PAIRS))

data = tomllib.loads((REPO / "workspace.toml").read_text())
entries = []
for key, section in data.items():
    if not isinstance(section, dict):
        continue
    work = section.get("work")
    if not isinstance(work, dict):
        continue
    for collection, items in work.items():
        if isinstance(items, list):
            for it in items:
                if isinstance(it, dict):
                    entries.append((key, collection, it))

specs = [(k, c, e) for k, c, e in entries if e.get("kind") == "spec"]
declared = [e for _, _, e in specs if "parent" in (e.get("source") or {})]
print(f"spec entries: {len(specs)}   declaring source.parent: {len(declared)}"
      f"   omitting: {len(specs) - len(declared)}")

module = E._load_cooling_module()
cooled, _ = E._cooled_locators(REPO, module)
print(f"cooled locators: {len(cooled)} -> {sorted(cooled)}")

gap = [e["path"] for _, _, e in specs
       if e.get("path") in {str(p) for p in cooled}
       and "parent" not in (e.get("source") or {})]
print(f"LIVE POPULATION of the gap: {len(gap)} -> {gap}")
```

Printed:

```
_COOLING_PAIRS = [('cool-30-days', 'Cooling'), ('cool-30-days', 'Retired'), ('retain-exception', 'Reclassified'), ('retain-exception', 'Retired')]
spec entries: 118   declaring source.parent: 17   omitting: 101
cooled locators: 0 -> []
LIVE POPULATION of the gap: 0 -> []
```

**What moved.** The corpus grew from 115 spec entries to 118, and the entries
omitting `source.parent` from 99 to 101. The proportion is unchanged in
substance: declaring a parent stays the exception, so the adopter-documentation
obligation this delivery carries is not narrowed by the base change.

**What the zero now rests on.** `_cooled_locators` reads accepted lifecycle
records from `docs/lifecycle/`, and that directory holds a `README.md` and no
records at all. So no artifact in this repository is cooled, and the refusal
this delivery adds has **no live subject** — the population is prospective, not
suppressed.

This corrects the basis probe 5 recorded. Probe 5 attributed the zero to
`provenance_mismatch` holding declared values honest; that mechanism is real and
probe 4 establishes it, but it is not what makes the count zero today. Nothing
is cooled. Both readings agree on the number and disagree on why, and the
distinction is load-bearing in one direction: because the refusal has no live
subject, failing closed cannot block any dependency that resolves today, and
every criterion in Group 1 must therefore be carried by a constructed fixture
rather than by any repository state.

## Probe 16 — the shipped command's exit code and payload shape

*The shipped command emits the finding* asserts two things about
`workspace_status.py reconcile` that no earlier probe established: that it exits
0, and that the finding is reachable at `canonical.findings[].code`. Every probe
before this one drives `run_canonical_reconciliation` in process. The one shipped
roster helper that runs this script tolerates a return code of **0 or 1**
(`tests/roster/test_cooling_scope_closure.py`), so the precedent does not settle
the exit code, and a criterion may not rest on an unconstructed claim about what
shipped code emits.

Two arms, both driving the script as a subprocess from the repository root
against a constructed root under `tempfile.mkdtemp()`. Arm A is the **Absent**
fixture, which draws no finding on this base. Arm B is the same tree with the
dependant's sibling `plan.md` removed, which draws a fail-closed finding today —
the arm that answers whether a finding changes the exit code.

```python
def run(root):
    cp = subprocess.run([sys.executable, str(script), "reconcile", "--root", str(root)],
                        capture_output=True, text=True, cwd=str(REPO), timeout=120)
    p = json.loads(cp.stdout)
    c = p.get("canonical", {})
    return cp.returncode, [f.get("code") for f in c.get("findings", [])]
```

Printed:

```
A (no finding)        exit=0 findings=[]
B (missing_plan)      exit=0 findings=['missing_plan']
```

Arm A's full payload carries top-level keys `canonical`, `closeout`, `cooling`,
`diagnostics`, `initiatives`, `mode`, `reconciliation`, `repo_backlog`, `scan`,
`shaping`, `schema_version`, `work`, `workspace_present`, `workspace_root`, and
`canonical` carries `active`, `blocked`, `bounded`, `evaluations`, `findings`,
`input_identity`, `legacy_memberships`, `performed`, `ready`.

**What this establishes.** Exit 0 is not conditional on an empty findings list —
arm B carries a finding and still exits 0 — so the criterion's exit-code half
stays true once this delivery's finding exists. The `code` field is reachable at
`canonical.findings[].code`, which is the path the criterion reads.

**What it does not establish.** Neither arm emits `cooled_child_scope_unknown`,
because the code does not exist yet. The criterion's content half is red by
construction until T1 lands, which is the correct pre-EXECUTE state; probe 15
records why no repository state can supply it.
