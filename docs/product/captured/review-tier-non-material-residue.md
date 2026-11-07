# Review tier non-material residue

- **Status:** Open
- **Kind:** defect

Four non-material findings from the review-obligation-policy code review:
- Instruction-file discovery folds case in ASCII only (Git `:(icase,glob)`), while the name check uses Unicode `casefold`.
- The supervisor's bounded Git launch returns partial output as success when a stream read fails inside the drain.
- `test_review_carry.py` asserts source text beside its behaviour check for the shared anchor builder.
- The bounded-launch tests in `test_supervisor_git.py` would hang, not fail, if the drain regressed.
Source: spec `docs/specs/review-obligation-policy/spec.md` Follow-ons.
