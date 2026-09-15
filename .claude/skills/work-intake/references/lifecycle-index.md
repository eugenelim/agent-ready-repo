# The workspace lifecycle index

Use `work-intake` as the front door for starting, remembering, inspecting, or
refreshing repository work. It classifies content by delivery role. Source
labels such as PRD, Feature, Story, Project, Issue, board, or Milestone are
hints; they do not select an intent, brief, spec, or defect route.

Canonical artifacts own requirements and decisions. `workspace.toml` is their
lifecycle index, not a second requirements store. A target entry contains
exactly `path`, `kind`, `source`, `summary`, and `needs`. Comments, summaries,
list order, tracker labels, and profile hints are non-semantic: they cannot
select a route, satisfy a dependency, choose a processor, or authorize
dispatch. Only an existing Approved `spec.md` with an existing sibling
`plan.md` and valid unique workspace membership may start from the queue.

Workspace prose stays terse and present-tense. A generated or materially
updated entry carries minimal provenance, one short summary of the current
outcome or next-needed condition, and hard dependencies only. It must not carry
history, rationale, procedure, review transcript, raw finding, copied source
text, soft priority, or suggested order in comments or adjacent fields. When
that context matters, write it to the resolved canonical artifact first and
index only the pointer. Settled live coordination is removed or compacted; it
is not replaced with a workspace history.

Repository-origin artifacts are locally authoritative. Tracker-origin
artifacts record source reference/revision and exactly one closed authority
record whose field map names `source` or `local` ownership. Intake acquisition
is read-only at the tracker boundary. Local refresh decisions and any supported
remote coordination action are separate effects; the latter needs its own
fresh exact confirmation.

Supported legacy workspace entries remain visible but non-dispatchable during
the compatibility window. Migration planning consumes a reviewed,
human-authored selection and remains read-only. Apply and rollback each consume
a fresh, single-use, human-authored confirmation permitted by repository
`[authorization.migration]` policy. Agents and migration tooling must never
create, edit, prefill, or choose substantive route or authorization values in
those files. Ledger-backed rollback restores the exact legacy workspace
representation and never deletes the canonical artifact.

`capture-work` is a temporary forwarding alias for `work-intake`; it must not
grow separate routing or storage semantics. New writers and workspace seeds
emit only target structured entries.
