# Manual QA: installed-CLI happy path

> **Not yet satisfied. This record is prepared, not filled in.**
>
> The installed-CLI criterion is the one gate in this slice that no unit test
> may stand in for: it requires invoking the built skill against a **real Jira
> instance**. No Jira credential exists in the environment where this file was
> prepared, so the run has not happened and every observation below is empty on
> purpose. Nothing here is inferred, simulated or reconstructed.
>
> **Status: blocked, pending a credentialed operator run.** The criterion's
> acceptance box stays unticked until an operator fills this file in from a
> real session.

## What has to be true before the run

1. The `atlassian` pack is **installed** — not run from this checkout's source
   tree. The criterion is about the artifact an adopter gets.
2. The `jira` skill is installed and authenticated. `jira: check` exits `0`.
   A non-zero exit means running the credential setup first; do not read a
   credential file directly.
3. The `flow-metrics` skill is installed.
4. The target Jira project contains **at least two Epics**: one whose
   `description` carries a block under a top-level `Outcome` heading, and one
   that carries no such block. Both shapes are required — a session that
   renders only one of them does not close this criterion.

Record the project key and the two Epic keys below before running, so the
expected rendering is fixed in advance rather than read off the output.

- Jira deployment (Cloud, or Server/Data Center): _____
- Project key: _____
- Epic **with** a recorded outcome: _____
- Epic **without** a recorded outcome: _____

## The command to run

Run it from the installed skill's `scripts/` directory, or with that directory
on `PYTHONPATH`:

```bash
python3 -m jira_epic_outcome_view --project <PROJECT-KEY>
```

Capture stdout and the exit code from the same invocation. Do not re-run to
tidy the transcript; paste what the first run produced.

## The documented happy path this is asserted against

These are the claims the skill's own `SKILL.md` makes. The observation is
**asserted against** each one — a bare log of output does not close this.

| # | What the documented path promises | Holds? |
| --- | --- | --- |
| 1 | Exit code is `0`. | _____ |
| 2 | Output groups the project's work by Epic. | _____ |
| 3 | The Epic **with** an outcome renders that block's text **verbatim** — blank lines above and below the block dropped, nothing else changed: no re-wrapping, no Markdown rendering. | _____ |
| 4 | The rest of that Epic's description is **not** rendered as outcome text. | _____ |
| 5 | The Epic **without** an outcome renders an explicit statement that none is recorded — not a blank, not an omitted row. | _____ |
| 6 | That same Epic renders a prompt asking the team for an outcome, naming the `Outcome` heading in the Epic's `description`. | _____ |
| 7 | No paste-ready text appears for an Epic nobody answered for. | _____ |
| 8 | Each Epic carries a delivery reading: a throughput count with its window, and work in flight. | _____ |
| 9 | No duration and no percentile appears anywhere — no cycle time, no lead time, no flow efficiency. | _____ |
| 10 | No score, grade or rating of any outcome appears. | _____ |
| 11 | Two moments are stated separately — the delivery reading's and the Jira read's — with no single timestamp implying one snapshot. | _____ |
| 12 | Every run discloses that the view covers only what the calling credential can browse. | _____ |

## Observed — fill in from the real run

### Command, exactly as invoked

```text
(empty — awaiting a credentialed run)
```

### Exit code

```text
(empty — awaiting a credentialed run)
```

### stdout, verbatim

```text
(empty — awaiting a credentialed run)
```

### Rendering for the Epic **with** a recorded outcome

Paste the rendered block, then the Epic's `Outcome` block as it reads in Jira,
so verbatim reproduction can be compared side by side rather than asserted.

```text
Rendered:
(empty — awaiting a credentialed run)

Source, as written in Jira:
(empty — awaiting a credentialed run)
```

### Rendering for the Epic **without** a recorded outcome

```text
(empty — awaiting a credentialed run)
```

## Session scope — what this run does and does not exercise

State where the session ended, and what was documented but left unexercised.

- **Exercised:** _____
- **Documented but not exercised — repeat use across two sittings.** Whether a
  team opens the view a second time, and whether the outcome recorded after
  the first sitting shows up in the second, is the parent's open question. One
  sitting cannot settle it, and this slice does not gate on it.
- **Anything else not exercised:** _____

## Sign-off

- Operator: _____
- Date of run: _____
- Verdict (pass / fail, with the numbered claim any failure is against): _____
