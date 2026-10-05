# Verification ledger: intent delivery traceability

Execution observations and owner decisions for this delivery. Obligations stay
in `spec.md` and `plan.md`; this file records what execution and review found.

## 2026-10-04 — T1 confinement import probe

The plan's T1 kill condition asks whether the projected resolver can import
`agentbundle.catalogue_tooling.file_safety` in supported repo-scope execution.

- Observed on the maintainer workstation: `python3 -I -c "import
  agentbundle.catalogue_tooling.file_safety"` resolved from a pip-installed
  `agentbundle`, byte-identical to
  `packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py`.
- Not observed at the time: the pipx and zipapp routes that
  `guides/_shared/how-to/install-agentbundle-from-clone.md` documents as
  supported for `core`. Neither puts `agentbundle` on the interpreter that runs
  skill scripts.

## 2026-10-05 — Review round 1 outcome

Round 1 post-gates review (adversarial, security, quality, experience) found
that the import probe above did not cover every supported install route. On a
pipx- or zipapp-only install the resolver cannot import the helper, so both
consumers would fail closed on every run. The plan's kill condition therefore
holds: the plan is amended rather than the helper vendored ad hoc.

## 2026-10-05 — Owner decisions (eugenelim)

Recorded from the owner's answers in the implementing session.

1. **Confinement source.** The resolver uses a byte-identical `file_safety.py`
   co-located in `packs/core/.apm/adapter-root-bins/`, pinned to the blessed
   `agentbundle.catalogue_tooling.file_safety` by a parity test. This is the
   pattern close-work, work-intake, and work-loop already use. It replaces the
   direct `agentbundle` import.
2. **Closure policy for a broken spec reference.** When a spec's own delivery
   reference is ambiguous, malformed, unsafe, or names a missing target,
   close-work refuses closure of every feature that spec could belong to and
   names the `delivery-…` code, instead of dropping the spec from the
   descendant set.
3. **Wording.** The changelog and how-to keep per-consumer phrasing for
   delivery problem cases. Each phrasing must match what its own consumer
   checks; only statements found to be wrong are corrected.

## 2026-10-05 — Round 1 indeterminate adjudications, resolved by the owner

Three round-1 adjudications classified `invalid (indeterminate-present)`
because each held one question for the owner. Their sustained findings stand
as adjudicated; the decisions above settle the open entries:

- Experience reviewer finding 7 (one set of problem-case terms): settled by
  decision 3. No change beyond correcting inaccurate statements.
- Security reviewer finding 4 (close-work acting on partial data when a spec
  reference is broken): settled by decision 2. Becomes required work.
- Adversarial reviewer finding 5 (no evidence that a real projection was
  invoked): settled by the sustained quality-engineer finding 4, which requires
  a test against a real clean Core repo-scope projection.
