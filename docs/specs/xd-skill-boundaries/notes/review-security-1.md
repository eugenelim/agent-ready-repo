# Security implementation review — round 1

## Concerns

**1. Boundary metadata is missing from the changed read/write-capable skill contracts.** `packs/experience-design/.apm/skills/journey-mapping/SKILL.md:1`

The reviewer proposed adding `metadata.boundaries` so policy and projection
consumers can distinguish file-capable skills from prompt-only skills.

Disposition: deferred. The diff changes only routing descriptions in canonical
skill frontmatter; the read/write behavior and absence of this metadata predate
the change. Adding a new security-metadata contract across the pack would
violate AC11 and requires its own schema, projection, and workflow review. The
new reference describes existing behavior rather than granting new capability.

**2. `experience-status` reads configured artifact files without the repo's read-side confinement and instruction/data controls.** `packs/experience-design/.apm/skills/experience-status/SKILL.md:37`

The existing workflow reads matching Markdown from configured design output
without the stronger realpath-prefix, origin-confirmation, and embedded-
directive controls used by newer write paths.

Disposition: deferred as a pre-existing workflow-security concern. The only
change to this skill is its description line; the body and effective authority
are unchanged. Fixing the read contract is explicitly Ask-first work outside
this routing-boundary release and should be handled in a dedicated security
spec rather than silently bundled here.

## Review limits

The reviewer did not run SAST/SCA or live skill invocations. No dependency or
runtime code changed; repository validation and build gates cover this release.
