# Extraction real-world message sample evidence

This packet preserves the deferred fidelity check identified by
`extraction-msg-realworld-sample`. Generated corpora exercise the declared
contract but cannot expose every assumption shared by the generator and
writer.

## Sample and evidence request

An authorized contributor must provide one PII-free, numbered real-world `.msg`
artifact and one PII-free, numbered real-world `.eml` artifact through the
repository's approved test-data process. Do not use production mail or sanitize
a message in a way that leaves recoverable personal, credential, or confidential
content.

Run the shipped converter at the tested repository revision and record:

- the sample identifier and provenance class without personal information;
- the converter command, version or revision, exit status, and output path;
- a manual comparison of headers, body structure, attachments, and ordering;
- any unsupported or lossy fields; and
- the reviewer and review date in the approved evidence record.

The packet is complete when the manual fidelity checks pass for both approved
samples, or when each observed mismatch has a separately owned canonical defect.
