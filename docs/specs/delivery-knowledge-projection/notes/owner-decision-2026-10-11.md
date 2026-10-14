# Owner decision — 2026-10-11

The scope owner chose to ship Slice 3 beside the current reusable capture
gates and move their removal to a named follow-on cutover.

## Question put to the owner

Slice 3 cannot safely remove the reusable capture gates yet. The delivery facts
it would project exist only when `WORK_LOOP_SHADOW_SERVICES=1`, in the
gitignored per-spec evidence log that Slice 1 writes. Removing the
`spec-approved` and `plan-locked` capture gates now would drop capture for every
default run. Those gates also capture agent-written practice notes that no
delivery fact holds. How should the refreshed spec handle gate removal?

## Owner answer

"Ship beside gates (Recommended)". The option shown was:

> Slice 3 ships feed, projector, pull collection, and read quarantine beside the
> current gates, as Slices 1 and 2 did. Gate removal moves to a named follow-on
> cutover. Architecture §10 and the brief's Slice 3 row get amended to match.

## Evidence shown with the question

- `packs/core/.apm/skills/work-loop/scripts/_compat_facade.py` writes the only
  production evidence log at `<spec-dir>/.shadow-acceptance/shadow-evidence.log`,
  and only when `WORK_LOOP_SHADOW_SERVICES=1`. That directory ignores itself.
- `packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py`
  accepts work-loop producer captures only at the `spec-approved` and
  `plan-locked` gates, and their content is agent-authored practice.
- Slice 2 shipped its boundary beside the legacy review path under the
  2026-10-10 owner amendment, with its cutover named as FEAT-0036.

## Effect

The brief's Slice 3 row drops gate replacement, and its Slice 8
`legacy-engine-cutover` row gains reusable capture-gate removal. Architecture
§10 of `docs/architecture/work-loop-knowledge-handoff.md` is corrected by this
slice's T4. This record approves neither the refreshed spec nor its plan; both
human gates still run after pre-EXECUTE review.

## Second decision — admission model (2026-10-12)

Round 2 of pre-execute review showed that a feed candidate cannot become a
`knowledge-captured-observation.v2` capture automatically. That contract needs
a human-written `lesson` and a human `privacy_attestation`, and its
`capture_id` hashes `observed_at` and `freshness_anchor`, so a rescan on a later
day would make a new record. The owner was asked which admission model Slice 3
should use and chose "Candidates only (Recommended)":

> Collection returns checked, read-only candidates and stores nothing. A person
> or agent turns a chosen one into a normal capture through the existing path,
> writing the lesson and doing the privacy review. Rescans then cannot duplicate
> or withdraw anything, and the capture format is unchanged.

The rejected option was automatic admission through a new capture contract
version with a stable source identity, delivery provenance, an automated
privacy step, a new gate, and a withdrawal path for promoted records.

The owner also chose to record the round-2 security report, which the review
classifier could not parse, as invalid and unused, and to re-run the security
review in round 3.
