# ADR-0084: Bandit suppression reasons move behind a second `#`, and its stderr becomes a gate

- **Status:** Accepted
- **Date:** 2026-08-16
- **Decision-makers:** eugenelim
- **Consulted:** security review, quality review
- **Supersedes:** the **`# nosec <ID> — <reason>` spelling** in [ADR-0017](0017-adopt-bandit-pip-audit-semgrep-sast-gate.md)'s suppression-policy sub-decision only — that ADR's three-way real-fix-first ladder, tool choices, and severity floor all stand
- **Related:** the implementing spec `docs/specs/bandit-nosec-comment-hygiene/`; `bandit.yaml` and `tools/run-bandit-gate.py` carry the operative rules

## Decision summary

- **Decision:** A Bandit suppression is written `# nosec <ID>  # <reason>` — the
  reason after a **second** `#`, never after a dash — and `make sast` fails if
  Bandit writes anything to stderr.
- **Because:** Bandit parses the text after `# nosec` as a list of test ids, so
  a prose reason is a suppression input, not a comment.
- **Applies to:** every `# nosec` in the repo's scanned roots (`SAST_DIRS`), and
  the `sast` recipe.
- **Tradeoff accepted:** ADR-0017's form is now wrong in two frozen documents we
  cannot rewrite, so a reader who starts there needs this pointer to find the
  live rule.
- **Revisit if:** Bandit changes `NOSEC_COMMENT` so the id list no longer runs
  to the next `#`, or starts emitting routine stderr chatter under `-q`.

## Context

ADR-0017 adopted Bandit and prescribed `# nosec <ID> — <reason>`: a suppression
scoped to one test id, carrying its justification on the same line. That reads
well and was implemented faithfully across five sites.

It is also, as written, a suppression input. `bandit/core/manager.py` parses a
suppression with

```python
NOSEC_COMMENT = re.compile(r"#\s*nosec:?\s*(?P<tests>[^#]+)?#?")
```

The captured id list runs to the **next `#`** — so with a dash or em dash as the
delimiter, the whole reason is captured, tokenised, and each word looked up as a
Bandit test name. Two ways that fails open:

1. **Widening.** A reason word colliding with a real test *name* (`assert_used`,
   `weak_cryptographic_key`, …) adds that test to the suppression. Nobody wrote
   it; nothing reports it.
2. **Blanket.** A `# nosec` whose id list resolves to *no* id — a bare
   `# nosec`, an id-less `# nosec  # reason`, or a prose sentence in which no
   word names a test — is treated by `core/tester.py` as "nosec without test
   number" and skips **every** test on the statement.

Neither had fired: an audit of every suppression at `origin/main` found each
resolving to exactly the one id its author wrote, and no blanket suppressions.
The exposure was latent, and the only thing standing between the repo and it was
Bandit's stderr — 39 `Test in comment: … is not a test name or id` lines on a
clean scan, which `make sast` printed and then ignored, because warnings do not
move Bandit's exit code.

That is the shape this repo has twice refused elsewhere in the same recipe:
`tools/test-audit-requirements.py` and `tools/test-semgrep-argv-boundary.py`
exist because a scanner that is silent when it works and silent when it has been
broken into a no-op is not a gate.

## Decision

**The reason goes after a second `#`.** `# nosec B603  # list argv, no shell`.
The second `#` terminates the id list, so the reason is never parsed. The id is
**mandatory** — an id-less suppression is a blanket suppression.

**`make sast` fails on non-empty Bandit stderr.** Under `-q` Bandit's stderr
carries only diagnostics about the scan's own integrity: unparsed suppressions,
suppressions that matched no finding, file-level errors. A clean repo produces
none. Treating any of them as a gate failure is what keeps the first half of
this decision true a year from now.

The wrapper is `tools/run-bandit-gate.py` — a script rather than a recipe line,
because a rule this quiet needs a test, and `tools/test-sast-stderr-gate.py`
drives it against a stub `bandit` to prove it. A gate that is silent when it
works and equally silent when it has been simplified back into a no-op is the
shape this recipe already refuses twice.

Where each rule is written: this ADR is the decision record; `bandit.yaml`'s
header comment is the instruction, sited where the next person writing a
suppression will be; `run-bandit-gate.py` is the enforcement.

## Decision drivers

- A suppression comment is a security control's audit trail. If the reader and
  the parser disagree about what it says, it is not an audit trail.
- ADR-0017's remediation ladder is real-fix-first; a suppression that quietly
  covers more than it claims corrupts the ladder's bottom rung.
- The fix had to survive the next contributor, who will read `bandit.yaml` or
  ADR-0017 and not this spec.

## Consequences

- Every existing suppression that carried a prose reason was rewritten. Two
  complementary checks confirm the rewrite changed nothing, because neither is
  sufficient alone:
  - A before/after scan at `--severity-level low --confidence-level low` gives
    an identical *reported-finding* set. That catches a suppression that
    weakened or widened onto a test which fires somewhere in the repo.
  - Running every suppression comment at both revisions through Bandit's own
    `_parse_nosec_comment` gives an identical *resolved-id* set — one id per
    directive, no blanket suppressions, at either revision. That catches the
    case the scan cannot see: a suppression widened onto a test that fires
    nowhere today.
- `make sast` is now stricter than Bandit's own exit code. A future Bandit
  release that adds routine stderr chatter under `-q` would turn the gate red on
  no real finding — that is the `Revisit if` trigger.
- ADR-0017:107 and the shipped `docs/specs/sast-sca-tooling/` spec and plan still
  spell the old form. Both are frozen. ADR-0017's Status line points here; the
  shipped spec cannot be annotated at all, which is the accepted cost.
- The form is documented and now partially self-enforcing (any malformed
  suppression Bandit *warns* about fails the gate), but an id-less suppression
  is silent to Bandit and so still invisible. A grep-shaped form lint closes
  that residue and is tracked as `bandit-nosec-form-lint`.
- **Revisit if:** Bandit changes `NOSEC_COMMENT` so the id list no longer runs to
  the next `#`, or starts emitting routine stderr chatter under `-q`.

## Confirmation

- **Mode:** gate-enforced, with a self-test
- **Signal:** `tools/run-bandit-gate.py` exits non-zero on any Bandit stderr
  line, so a suppression Bandit cannot parse fails CI rather than printing into
  a scrollback; `tools/test-sast-stderr-gate.py` proves that against a stub
  `bandit`, so the rule cannot be simplified away unnoticed.
- **Owner:** repo maintainers

## Alternatives considered

- **Leave the form and filter the warnings out of the recipe.** Rejected: it
  hides the signal rather than fixing the comments producing it, and leaves both
  fail-open paths intact.
- **Put the reason on the preceding line instead.** Works, and is what the one
  multi-line rationale in `capture-publish-control-evidence.py` does. Rejected as
  the general rule because ADR-0017's same-line requirement is worth keeping —
  a suppression and its justification should not drift apart.
- **Pin or downgrade Bandit so the warnings stop.** Rejected: the warnings are
  correct, and the parse behaviour they report predates the version that started
  reporting it.
- **Amend ADR-0017 in place.** Rejected: ADR bodies are immutable once Accepted
  (`docs/CONVENTIONS.md` § Document lifecycle). Only its Status line moves, and
  it moves to point here.
- **Ship the form with no enforcement at all.** Rejected: the new spelling is
  *quieter* than the old one when it is malformed, so documenting it without a
  gate would trade a noisy foot-gun for a silent one.

## References

- Bandit 1.9.4 `core/manager.py` (`NOSEC_COMMENT`, `_parse_nosec_comment`),
  `core/tester.py` (empty-id-set handling), `core/utils.py` (`get_nosec`, which
  matches a suppression against the whole statement's linerange).
- [ADR-0017](0017-adopt-bandit-pip-audit-semgrep-sast-gate.md) — the SAST gate
  and its suppression ladder.
