# Bound every value the repo_backlog projection emits

- **Status:** Draft
- **Level:** feature

## Outcome

`workspace-status` bounds every value it projects from `[backlog].open`, so an
entry in `workspace.toml` cannot place unbounded free text or an unvalidated
dependency record into agent context. Today `summary` and `needs` reach the
consumer exactly as written, on the one emitter the public-safety pass never
covered.

## Boundary

- Admits `extract_repo_backlog` in `workspace_status_engine.py` and
  `_repo_backlog_entry_dict` in `workspace_status.py`, and the two values they
  pass through unbounded: `summary` and `needs`.
- Admits the design of a free-text filter, since no filter for display prose
  exists anywhere in the file. Charset, length bound, and what a failing value
  degrades to are all open and belong to the spec.
- Admits a filter for the typed dependency record. The existing `_public_need`
  accepts only strings, so reusing it directly would redact every dict-shaped
  record to the sentinel and destroy the dependency data the skill contract
  depends on. The semantics may be reused; the inputs may not.
- Excludes the initiative `name` and `milestone` redaction. That behaviour is
  deliberate, test-pinned, and already correct; the skill contract describing
  it was corrected separately.
- Excludes any change to the `workspace.toml` schema itself. This bounds what
  the projection emits, not what an author may write.
- Excludes two adjacent gaps in the same projection: no pack, profile, adapter
  or skill inventory in the output, and no declared workspace version marker
  read anywhere.
- Determinism is a property of this tool. Same input, same output, before and
  after.

## Owner

eugenelim

## Unresolved questions

- Is `workspace.toml` in the threat model as attacker-influenced content, or
  only as review-gated repository content? This decides how much hardening is
  warranted and should be settled before the filter is designed, not after.
- The schema guide documents `summary` as 1-500 characters. `extract_repo_backlog`
  enforces no bound, and this repository currently projects a 785-character
  summary. Does the fix enforce the documented limit, or is the documented
  limit the thing that is wrong?
- Does a failing value degrade to the `workspace.toml` sentinel, or does the
  whole entry fail closed with a finding, as the canonical work-entry path does
  for an invalid `summary`? The two paths currently answer this differently.
- Does the dependency filter cover the receipt-bearing and cross-repository
  record shapes now, or only the local shape the corpus exercises, with the
  others failing closed until a real case appears? The corpus holds nine
  records, all `{type, kind, path}` with `type = "local"`.

## Projection

- A spec under `docs/specs/`, carrying a `security-reviewer` pass at spec stage
  because the change alters a trust boundary.
- No RFC. This corrects one emitter against a convention the repository already
  applies everywhere else; it proposes no new convention.

## Opportunity

The public-safety pass and the backlog projection landed two days apart, in
that order, and never met. `_repo_backlog_entry_dict` was added on 2026-08-10
by "render complete repository backlog" (#913). The sanitization pass arrived
on 2026-08-12 as "enforce canonical routing invariants" (#928), which wrapped
`slug`, `path`, `ini_slug`, `needs` and the finding fields of every other
emitter in a `_public_*` filter and replaced the initiative display fields with
a redaction sentinel. In that commit's diff the backlog emitter appears only as
unchanged context. The sweep reached the emitters its seed contained, and the
newest one was not among them.

What that leaves, measured against the current main:

- 156 open backlog entries project `summary` verbatim. The longest is 785
  characters. `extract_repo_backlog` takes the value with no type check, no
  length bound, and no charset rule.
- 11 entries project `needs`. Nine are dictionaries emitted raw from the file;
  five sibling emitters in the same module run their needs through
  `_public_needs` first.

The consequence is not hypothetical for the reader: these strings are rendered
into agent context by a skill whose stated job is cold-start orientation, which
is the first thing a session reads.

## Assumptions

The riskiest assumption is that bounding the projection is the control that
matters. The repository already requires loaded prose to be treated as
instruction-inert, and every shipped skill carries an output-rendering block
restating it. If that instruction-level rule is sufficient, then filtering
these two values buys defence in depth at best, and the initiative redaction
that prompted this intent was itself over-built.

What would have to be true for the work to be warranted: an instruction
addressed to a model is not a control, because nothing fails when the model
does not follow it. This repository has already acted on exactly that
reasoning once. The cognitive-load rules were moved inline into `AGENTS.md`
because routing to them was a model-directed read with no error, no log and no
failed gate when it did not happen — and it did not happen for a whole session
while the rule it routed to was breached throughout. If that argument holds
for guidance the agent is asked to read, it holds for prose the agent is
handed.

The cheapest way to settle this before designing anything is to answer the
threat-model question under unresolved questions. If `workspace.toml` is only
ever review-gated repository content, the assumption is probably false and
this intent should close rather than proceed.

## Source

- Mode: repo-origin
- Locator: packs/core/.apm/skills/workspace-status/scripts/workspace_status.py
- Revision: commit:003709805ae14ac5f349cac72e7e544037c14033
- Authority: repo-origin
