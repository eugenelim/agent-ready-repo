# Lifecycle records

This directory owns one lifecycle record for each delivered artifact. Each record
is stored as `<delivery_id>.json`.

`close-work` is the only writer. Records are Git-tracked and leave this directory
only through the confirmed deletion workflow established in Wave 4.

A record may carry an optional `parent`, which is one of two forms: the string
`none`, meaning the delivered spec has no brief, or the path of its brief file,
`docs/product/briefs/<slug>.md`. Enrolment derives it from the spec's `Brief:`
header before the spec cools. When `parent` is absent, the spec's parent is
unknown and any check that depends on it fails closed. The field is preserved
unchanged whenever a record is renamed, updated, reviewed, or reclassified.
