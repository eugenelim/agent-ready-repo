# Lifecycle records

This directory owns one lifecycle record for each delivered artifact. Each record
is stored as `<delivery_id>.json`.

`close-work` is the only writer. Records are Git-tracked and leave this directory
only through the confirmed deletion workflow established in Wave 4.
