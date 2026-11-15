+++
schema = 1
id = "a65d5ec4-7a9d-4d6e-af6e-0fdbd859bf89"
anchor = "release-engineering030--2026-11-13-a65d5ec47a9d4d6eaf6e0fdbd859bf89"
date = 2026-11-13
[[packages]]
name = "release-engineering"
version = "0.3.0"
+++
## Highlights
- Prepare release candidates from existing evidence, pin admission records, and check focused reliability and security reviews before each release stage.

## Added

- `prepare-release-handoff` skill and stdlib evidence collector with named gaps and no implicit execution.
- `release_admission.py` for admission, byte verification, focused review, stage checks and bounded repair handoffs.
- `release-reliability-reviewer` and `release-security-reviewer` agents with canonical reliability and security reference checklists.
- Release admission reference, guide recipe and eval cases for refusals and optional Core additions.

## Changed

- Release loop accepts direct evidence without a Core workflow event; installation dependencies remain unchanged. Preparation results grant no execution or production authority.
