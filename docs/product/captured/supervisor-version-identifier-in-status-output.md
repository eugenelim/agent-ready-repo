# Give the supervisor a version identifier in its status output

- **Status:** Open
- **Kind:** design

## Summary

No supervisor verb reports a version, so a controller cannot tell from the running script which behaviour it has. Priority is low and nothing depends on it today. Owner: `eugenelim`.

## Observed

- `status --json` carries no version field, and no other verb output names a version.
- A controller that selects a descriptor reads the skill version from the install state or the pack manifest, not from the script it runs.
- Adding a field means editing the pinned supervisor script, which is a core pack release and voids in-flight runs on upgrade like any change to that script.

## Intended

- `status --json` reports a supervisor version identifier, so a controller can match its descriptor to the script that answered.
- The request waits as a fallback: the design first relies on the pack manifest and a comparison of the supervisor's file hashes with the install state's per-file record, and raises this only if that comparison proves too weak.
- The change ships with a core version bump, a changelog fragment and a test that the field is present and stable.
