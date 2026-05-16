#!/usr/bin/env python3
"""Mechanical termination checker for the work-loop's spec state.

Reads a spec's `state.json` and decides whether the loop's current phase
is satisfied. Caps and budgets live in the JSON, not in the SKILL's
prose — this script is what turns those numbers into a gate. The
work-loop SKILL calls it between phases.

Exit contract:
  0       — phase satisfied; continue.
  non-zero — phase not satisfied; reason on stderr. The work-loop SKILL
             treats exit-1 from `--phase plan` (with reason "plan not
             approved") as the expected first-invocation cue to run the
             spec-mode reviewer, *not* as a stop-and-surface signal. Any
             other non-zero exit terminates the loop.

Kill criteria, scoped by --phase:

  plan:      #4 plan-review pending
  implement: #1 iteration cap, #2 token cap, #3 consecutive-error,
             #4 plan-review pending
  review:    #1, #2, #3, #4, plus #5 fingerprint stasis (current ==
             previous AND non-empty)

Defaults (used when a field is absent from state.json) live in the
template at docs/_templates/state.json. The DEFAULTS dict below is the
no-template floor, used only when the field is omitted from the
caller's state.json — keep it in sync with the template.

Schema reference: docs/_templates/state.json and
docs/CONVENTIONS.md#work-loop-state.

Usage:
  tools/check-done.py docs/specs/<feature>/state.json --phase {plan,implement,review}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULTS = {
    "max_iterations": 5,
    "token_budget_cap_pct": 0.85,
    "consecutive_same_error_threshold": 3,
}

PHASES = {"plan", "implement", "review"}


def stop(reason: str) -> int:
    print(f"check-done: stop — {reason}", file=sys.stderr)
    return 1


def evaluate(state: dict, phase: str) -> int:
    if state.get("plan_review_status", "pending") == "pending":
        return stop("plan not approved (plan_review_status=pending)")
    if phase == "plan":
        return 0

    iter_count = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", DEFAULTS["max_iterations"])
    if iter_count >= max_iter:
        return stop(f"iteration cap reached ({iter_count}/{max_iter})")

    used = state.get("token_budget_used_pct", 0.0)
    cap = state.get("token_budget_cap_pct", DEFAULTS["token_budget_cap_pct"])
    if used >= cap:
        return stop(f"token budget exhausted ({used:.2%}/{cap:.2%})")

    same_err = state.get("consecutive_same_error_count", 0)
    same_err_threshold = state.get(
        "consecutive_same_error_threshold",
        DEFAULTS["consecutive_same_error_threshold"],
    )
    if same_err >= same_err_threshold:
        return stop(
            f"stuck on same error ({same_err} consecutive iterations)"
        )

    if phase == "review":
        current = sorted(state.get("finding_fingerprints", []))
        previous = sorted(state.get("previous_finding_fingerprints", []))
        if current and current == previous:
            return stop(
                f"no progress — same {len(current)} finding(s) two iterations in a row"
            )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "state_path",
        type=Path,
        help="path to docs/specs/<feature>/state.json",
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=sorted(PHASES),
        help="which phase of the loop is calling",
    )
    args = parser.parse_args()

    if not args.state_path.exists():
        return stop(f"state.json missing at {args.state_path}")

    try:
        state = json.loads(args.state_path.read_text())
    except json.JSONDecodeError as exc:
        return stop(f"state.json malformed: {exc.msg} at line {exc.lineno}")

    if not isinstance(state, dict):
        return stop("state.json root must be an object")

    return evaluate(state, args.phase)


if __name__ == "__main__":
    sys.exit(main())
