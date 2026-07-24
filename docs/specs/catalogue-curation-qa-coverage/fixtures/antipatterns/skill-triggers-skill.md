---
name: daily-report-with-review
description: Generates a daily activity summary from the git log and open issues, then automatically routes it through the team's review workflow to produce a scored feedback document.
metadata:
  boundaries: [filesystem_read, filesystem_write, shell_exec]
---

# Skill: daily-report-with-review

Produce a daily activity summary covering today's commits, opened and closed issues,
and outstanding pull requests. After generating the report, the companion review
script runs automatically to score the report against the team's quality rubric.

## Steps

1. Query the git log for today's commits:
   ```
   git log --since="24 hours ago" --oneline --no-merges
   ```
2. Fetch the open and recently closed issues using `scripts/fetch_issues.py`.
3. Assemble the report from the daily template (`references/report-template.md`).
4. Save the report to `reports/YYYY-MM-DD.md`.
5. Run the automated review script to score the finished report:
   ```
   python scripts/run_review.py reports/YYYY-MM-DD.md
   ```

## Output

- `reports/YYYY-MM-DD.md` — the daily activity report
- `reports/YYYY-MM-DD-review.json` — scored feedback from the review workflow

## scripts/run_review.py

```python
#!/usr/bin/env python3
"""Submit the generated report to the review-report skill for automated grading."""
import subprocess
import sys
from pathlib import Path


def run_review(report_path: str) -> None:
    """Invoke the review-report skill via the agent CLI to score the report."""
    result = subprocess.run(
        ["claude", "/review-report", "--target", report_path, "--output-format", "json"],
        capture_output=True,
        text=True,
        check=True,
    )
    output_path = Path(report_path).with_suffix(".review.json")
    output_path.write_text(result.stdout)
    print(f"Review complete. Feedback written to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: run_review.py <report_path>", file=sys.stderr)
        sys.exit(1)
    run_review(sys.argv[1])
```

## Notes

- The review script runs unconditionally after the report is generated. If the
  agent CLI is unavailable, the step fails and the report will not be scored.
- Review feedback is JSON; parse it with `scripts/parse_review.py` for a
  human-readable summary.
