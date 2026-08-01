---
name: generate-release-notes
description: Scan shipped specs and write a formatted release-notes entry for the current version. Use after marking a milestone complete.
metadata:
  boundaries: [filesystem_write]
---

# Skill: generate-release-notes

Generate a release notes entry for the current version by scanning all shipped
specifications and producing a formatted changelog entry.

## IMPORTANT: Read this section first

Before generating release notes, read all of the instructions below carefully.
Do not start until you have read every step. It is essential that you understand
the complete procedure. Following these instructions exactly is important for
producing correct output.

## Step 1: Collect the version number

Ask the operator for the version number. The version number must follow semantic
versioning (MAJOR.MINOR.PATCH). Do not proceed without a valid version number.
If the version number does not follow semantic versioning, stop and ask again.
The version number must not have a leading "v". The version number must not
include pre-release identifiers unless the operator explicitly specifies one.
Do not guess the version number. Do not derive it from git tags. Do not use
the current date as a version number.

## Step 2: Read all shipped specs

Read every file matching `docs/specs/*/spec.md`. For each file:
- Check if the spec status is `Shipped`. If the status is not `Shipped`, skip
  the file. Do not include non-Shipped specs in the release notes. Do not
  include Approved specs. Do not include Implementing specs. Do not include
  Draft specs. Only include Shipped specs.
- Read the Objective section. The Objective section starts after the
  `## Objective` heading. Read it carefully.
- Read the Acceptance Criteria section. The Acceptance Criteria section starts
  after the `## Acceptance Criteria` heading. Read each item.
- Note the spec name. The spec name is the directory name under `docs/specs/`.
  The spec name is not the first heading in the file. The spec name is the
  directory name.

## Step 3: Determine which specs are new in this release

A spec is new in this release if it was shipped since the previous release:
- Read `docs/product/changelog.md` to find the previous release version.
- Compare the previous release's shipped specs to the current shipped specs.
- Any spec in the current set that was not in the previous set is new in this
  release.
- If you cannot determine the previous release, include all Shipped specs and
  note that this may include previously released items.
- Do not include specs that appeared in previous releases. Do not duplicate
  items from previous releases. Do not include specs that were already in the
  last release notes. Only include new specs.

## Step 4: Write the release notes entry

Format the release notes entry exactly as follows:
- Start with `## v<version> — <date>` where `<version>` is the version from
  Step 1 and `<date>` is today's date in `YYYY-MM-DD` format.
- For each new spec, write a bullet: `- **<spec-name>:** <one-sentence summary>`.
- The summary must be one sentence. Do not write two sentences. Do not use more
  than 25 words. Do not include technical implementation details. Do not
  reference acceptance criteria by number. Do not include the word "spec" in
  the summary. Do not include the spec directory name verbatim — paraphrase it.
  The summary must be written from the user's perspective.
- After the spec bullets, write a `### Fixes` subsection if any specs closed
  deferred items from previous releases.
- After `### Fixes`, write a `### Deferred` subsection listing ACs from this
  release deferred with `(deferred: <slug>)` annotations.
- After `### Deferred`, write a `### Notes` subsection. Ask the operator for
  notes content before writing this subsection.

## Step 5: Write the file

Prepend the release notes entry to `docs/product/changelog.md`. Do not replace
the existing content. Do not overwrite the existing changelog. Prepend the new
entry before the first existing `## v` heading. If there is no existing
`## v` heading, add the entry at the end of the file. If the file does not
exist, create it with the new entry only.

After writing, read back the first 50 lines of the file to verify the entry
was prepended correctly. If the entry was not prepended correctly, write the
file again. Do not stop until the entry is verified as correctly prepended.

## REMINDER: Important notes

Remember: only include Shipped specs. Remember: the version number must follow
semantic versioning. Remember: summaries must be one sentence and under 25
words. Remember: prepend, do not replace. Remember: verify by reading back
after writing. Remember: ask the operator for notes content before the Notes
subsection. Remember: do not derive the version number from git tags.
