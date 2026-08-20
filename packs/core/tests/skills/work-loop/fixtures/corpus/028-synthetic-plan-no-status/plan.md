# Plan: synthetic plan with no Status line

Hand-authored. `_read_md_status` returns None for a file with no `**Status:**`
line, and `_assert_status_legal` legitimately *skips* that case. Several real plan
fixtures have no status line, and AC14 turns only an unloadable parser into a
refusal — an absent token stays a skip. This fixture pins that distinction.

## T1: Do the thing

**Depends on:** none

- [ ] a progress checkbox, normalized file-wide because this is a plan
