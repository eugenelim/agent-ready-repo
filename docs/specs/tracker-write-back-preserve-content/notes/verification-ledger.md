# Verification ledger: tracker write-back preserves existing content

## T6 manual QA, 2026-11-11

Method: the real `main()` of `jira.py` and `jira_align.py`, driven end to end through recording mocked transports, fresh temporary home each run, no network. The driver is a throwaway script kept outside the repository. It was rerun after each repair task (T6a, T8, T9, T10); every rerun exited 0 with RUN A (Jira Cloud, ADF), RUN B (Jira Server/Data Center) and RUN C (Jira Align) each PASS.

Result: preview, stale refusal, write, lossy refusal, undo, refused `transition --field`, and refused `raw` writes behave as the spec states. No token and no prior-value record contents were printed.

### First-run findings and dispositions

| Finding | Disposition |
| --- | --- |
| F1: the append preview showed only the new fragment, not the label the write adds or the merged result | Fixed in T6a: the preview prints an `after write` block built by the same function the write uses. |
| F2: the dropped-type lines printed under the wrong field | Fixed in T6a: printed only for ADF fields, under the field they concern. |
| F3: `plan-undo` of a Jira Align `PUT` restores only the written fields | Not a defect. Matches the undo criterion, the full record is saved, and the guide states the limit. |
| F4: the omitted-field list named `id` | Superseded by review: AC39 requires listing every omitted field, so `id` is listed with a note (T8). |
| F5: one `httpx` INFO log line on stderr | Driver logging artifact, not caused by this change. |
| F6: refusals print `digest:`, raw refusal text names no command, argparse usage shows the full path | Not defects. |

### Review closeout

Six review rounds with an adversarial reviewer, a security reviewer and a quality engineer. Rounds 1 to 5 produced material findings, each fixed with a failing test first and a hand-run mutation check: unencoded transition names, a Jira Align `PUT` clearing fields changed or added after the preview, folder checks after the first request and missing for the plan's and the record's own folders, the record path printed twice, digest line on refusals, exact JSON comparison in the stale check, and the shipped remedy for a folder refusal. Round 6 ended with no material finding.

Deferred, non-material, disclosed in the pull request: undo of an append into an empty Jira Cloud field needs `--allow-lossy`; Jira Align `plan-undo` always uses `PATCH`; a record with an unusual field name makes `--replace-record` refuse without naming the field; a test named for undo after a `PUT` does not run the undo; two undo limits are not in the guides; guide step text understates when a `PUT` plan refuses; `update` reads the plan before the folder check so a named pipe can hang it; undo of a number-field write is refused when a tracker reads back a float; two plan-undo test honesty points; the symlink-advice sentence conflicts with the stray-file step; `~/.agentbundle` at mode 000 is not in the remedy; and the whole-pack `pytest packs/atlassian/tests` collection collision that predates this change.

### Observed transcript (first run, before T6a)

# T6 manual QA transcript

Command: `cd /tmp && <repo>/.context/venv/bin/python /tmp/twb-qa/qa.py`
Python: <repo>/.context/venv/bin/python (Python 3.14.9)
qa.py exit code: 0 (fresh temp HOME each run, httpx.MockTransport, no network, example.invalid hosts)

```text

======================================================================
RUN A: Jira Cloud (ADF)
======================================================================

--- RUN A step: 1 plan-update (append description, replace summary)
$ jira plan-update PROJ-12 --field description=appended note --disposition description=append --field summary=new summary --disposition summary=replace
stdout:
target: PROJ-12
flavor: cloud
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: append
  current:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "existing one",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing two",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "attrs": {
    |         "panelType": "info"
    |       },
    |       "content": [
    |         {
    |           "content": [
    |             {
    |               "text": "panel body",
    |               "type": "text"
    |             }
    |           ],
    |           "type": "paragraph"
    |         }
    |       ],
    |       "type": "panel"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  proposed:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "appended note",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
field: summary
  disposition: replace
  current:
    | OLDVALUE summary
  proposed:
    | new summary
  drops node types: none
  drops mark types: none
digest: 0a0a879b27703005566c4c2b65132dcab379e7affd5fc59c21757c88e73e6f6b
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-0a0a879b2770.json
stderr:
2026-11-11 15:23:18,070 INFO httpx: HTTP Request: GET https://jira.example.invalid/rest/api/3/issue/PROJ-12?fields=description%2Csummary "HTTP/1.1 200 OK"
exit code: 0
write requests this step: 0 (total 0)
  CHECK [ok] plan-update exit 0 and zero writes
  CHECK [ok] preview shows plan file and digest

--- RUN A step: 2 person edits description; update-issue with stale plan
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-0a0a879b2770.json --approved-digest 0a0a879b27703005566c4c2b65132dcab379e7affd5fc59c21757c88e73e6f6b
stdout:
digest: 0a0a879b27703005566c4c2b65132dcab379e7affd5fc59c21757c88e73e6f6b
stderr:
refused: fields changed since the preview: description; rerun plan-update (a small race remains between this check and the write)
exit code: 10
write requests this step: 0 (total 0)
  CHECK [ok] stale refusal: exit 10, zero write requests
  CHECK [ok] fake description restored to original nodes

--- RUN A step: 3a re-plan after the edit
$ jira plan-update PROJ-12 --field description=appended note --disposition description=append --field summary=new summary --disposition summary=replace
stdout:
target: PROJ-12
flavor: cloud
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: append
  current:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "a person edited this",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing one",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing two",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "attrs": {
    |         "panelType": "info"
    |       },
    |       "content": [
    |         {
    |           "content": [
    |             {
    |               "text": "panel body",
    |               "type": "text"
    |             }
    |           ],
    |           "type": "paragraph"
    |         }
    |       ],
    |       "type": "panel"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  proposed:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "appended note",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
field: summary
  disposition: replace
  current:
    | OLDVALUE summary
  proposed:
    | new summary
  drops node types: none
  drops mark types: none
digest: f861ab7a8ea231ecb4eedc9ff80ad12f5c3084bb9804dc09d85ce62cdf55dae9
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-f861ab7a8ea2.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 0)

--- RUN A step: 3b update-issue
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-f861ab7a8ea2.json --approved-digest f861ab7a8ea231ecb4eedc9ff80ad12f5c3084bb9804dc09d85ce62cdf55dae9
stdout:
digest: f861ab7a8ea231ecb4eedc9ff80ad12f5c3084bb9804dc09d85ce62cdf55dae9
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261111T212318083771Z-PROJ-12.json
ok: updated PROJ-12
exit code: 0
write requests this step: 1 (total 1)
  PUT /rest/api/3/issue/PROJ-12 body={"fields": {"description": {"content": [{"content": [{"text": "a person edited this", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing one", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing two", "type": "text"}], "type": "paragraph"}, {"attrs": {"panelType": "info"}, "content": [{"content": [{"text": "panel body", "type": "text"}], "type": "paragraph"}], "type": "panel"}, {"content": [{"text": "Appended text:", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "appended note", "type": "text"}], "type": "paragraph"}], "type": "doc", "version": 1}, "summary": "new summary"}}
  CHECK [ok] exactly one PUT write
  CHECK [ok] record path line printed once on stderr
  CHECK [ok] existing ADF nodes unchanged and in order (prefix)
  CHECK [ok] two paragraph nodes appended (label + text)
  CHECK [ok] last node is the appended text
  CHECK [ok] body holds only planned fields

--- RUN A step: 4a plan-update replace description with plain paragraph (drops panel)
$ jira plan-update PROJ-12 --field description=replacement plain text --disposition description=replace
stdout:
target: PROJ-12
flavor: cloud
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: replace
  current:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "a person edited this",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing one",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing two",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "attrs": {
    |         "panelType": "info"
    |       },
    |       "content": [
    |         {
    |           "content": [
    |             {
    |               "text": "panel body",
    |               "type": "text"
    |             }
    |           ],
    |           "type": "paragraph"
    |         }
    |       ],
    |       "type": "panel"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "Appended text:",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "appended note",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  proposed:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "replacement plain text",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  drops node types: panel
  drops mark types: none
  lossy: needs --allow-lossy
digest: d4bb863ef426c95bf7abd2abfa8f8688cc85d220766e3e8c816f56eafe6f865b
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-d4bb863ef426.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 1)
  CHECK [ok] plan-update names the dropped node type 'panel'

--- RUN A step: 4b update-issue without --allow-lossy
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-d4bb863ef426.json --approved-digest d4bb863ef426c95bf7abd2abfa8f8688cc85d220766e3e8c816f56eafe6f865b
stdout:
digest: d4bb863ef426c95bf7abd2abfa8f8688cc85d220766e3e8c816f56eafe6f865b
stderr:
refused: field description: replace would drop panel; pass --allow-lossy to proceed
exit code: 10
write requests this step: 0 (total 1)
  CHECK [ok] lossy replace refused: exit 10, zero writes
  CHECK [ok] issue unchanged after refusal

--- RUN A step: 5a plan-undo --record
$ jira plan-undo --record /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261111T212318083771Z-PROJ-12.json
stdout:
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-d98fd3e1e063.json
digest: d98fd3e1e06341ef1cd119e3b15d0f48f239671c83211ece63b38a546b60ebe8
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 1)
  CHECK [ok] plan-undo exit 0

--- RUN A step: 5b update-issue with undo plan
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-d98fd3e1e063.json --approved-digest d98fd3e1e06341ef1cd119e3b15d0f48f239671c83211ece63b38a546b60ebe8
stdout:
digest: d98fd3e1e06341ef1cd119e3b15d0f48f239671c83211ece63b38a546b60ebe8
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261111T212318102632Z-PROJ-12.json
ok: updated PROJ-12
exit code: 0
write requests this step: 1 (total 2)
  PUT /rest/api/3/issue/PROJ-12 body={"fields": {"description": {"content": [{"content": [{"text": "a person edited this", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing one", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing two", "type": "text"}], "type": "paragraph"}, {"attrs": {"panelType": "info"}, "content": [{"content": [{"text": "panel body", "type": "text"}], "type": "paragraph"}], "type": "panel"}], "type": "doc", "version": 1}, "summary": "OLDVALUE summary"}}
  CHECK [ok] undo write: exit 0, one request
issue state after undo: {"description": {"content": [{"content": [{"text": "a person edited this", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing one", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing two", "type": "text"}], "type": "paragraph"}, {"attrs": {"panelType": "info"}, "content": [{"content": [{"text": "panel body", "type": "text"}], "type": "paragraph"}], "type": "panel"}], "type": "doc", "version": 1}, "labels": [], "summary": "OLDVALUE summary"}
  CHECK [ok] summary restored
  CHECK [ok] description restored to pre-write nodes

--- RUN A step: 6a transition with --field
$ jira transition PROJ-12 --to Done --field description=x
stdout:
(empty)
stderr:
refused: a transition with field content is always refused; use plan-update
exit code: 10
write requests this step: 0 (total 2)
  CHECK [ok] transition+field: exit 10, zero writes
  CHECK [ok] transition+field: zero requests at all

--- RUN A step: 6b raw PUT on issue path
$ jira raw PUT issue/PROJ-12 --data-file /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/body.json
stdout:
(empty)
stderr:
refused: write refused: no verified plan; run plan-update and approve it first
exit code: 10
write requests this step: 0 (total 2)
  CHECK [ok] raw PUT refused: exit 10, zero requests

======================================================================
RUN B: Jira Server/Data Center (string fields)
======================================================================

--- RUN B step: 1 plan-update
$ jira plan-update PROJ-12 --field description=
Appended line. --disposition description=append --field summary=new summary --disposition summary=replace
stdout:
target: PROJ-12
flavor: server
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: append
  current:
    | Line one of the description.
    | Line two.
  proposed:
    | 
    | Appended line.
field: summary
  disposition: replace
  current:
    | OLDVALUE summary
  proposed:
    | new summary
digest: ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-ed5a2be5f8ff.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 0)
  CHECK [ok] plan-update exit 0, zero writes

--- RUN B step: 2 stale update-issue
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-ed5a2be5f8ff.json --approved-digest ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
stdout:
digest: ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
stderr:
refused: fields changed since the preview: description; rerun plan-update (a small race remains between this check and the write)
exit code: 10
write requests this step: 0 (total 0)
  CHECK [ok] stale refusal: exit 10, zero writes

--- RUN B step: 3a re-plan
$ jira plan-update PROJ-12 --field description=
Appended line. --disposition description=append --field summary=new summary --disposition summary=replace
stdout:
target: PROJ-12
flavor: server
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: append
  current:
    | Line one of the description.
    | Line two.
  proposed:
    | 
    | Appended line.
field: summary
  disposition: replace
  current:
    | OLDVALUE summary
  proposed:
    | new summary
digest: ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-ed5a2be5f8ff-1.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 0)

--- RUN B step: 3b update-issue
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-ed5a2be5f8ff-1.json --approved-digest ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
stdout:
digest: ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261111T212318115730Z-PROJ-12.json
ok: updated PROJ-12
exit code: 0
write requests this step: 1 (total 1)
  PUT /rest/api/2/issue/PROJ-12 body={"fields": {"description": "Line one of the description.\nLine two.\n\nAppended text:\n\nAppended line.", "summary": "new summary"}}
  CHECK [ok] one write request
  CHECK [ok] record path line on stderr
  CHECK [ok] original is a byte-exact prefix of new description
  CHECK [ok] summary replaced

--- RUN B step: 4a plan-undo
$ jira plan-undo --record /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261111T212318115730Z-PROJ-12.json
stdout:
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-f8f6c7063ca4.json
digest: f8f6c7063ca4027fa2642886547fd2a92b79c46de83ab2259df70d143c0c15cd
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 1)

--- RUN B step: 4b update-issue undo plan
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-f8f6c7063ca4.json --approved-digest f8f6c7063ca4027fa2642886547fd2a92b79c46de83ab2259df70d143c0c15cd
stdout:
digest: f8f6c7063ca4027fa2642886547fd2a92b79c46de83ab2259df70d143c0c15cd
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261111T212318128868Z-PROJ-12.json
ok: updated PROJ-12
exit code: 0
write requests this step: 1 (total 2)
  PUT /rest/api/2/issue/PROJ-12 body={"fields": {"description": "Line one of the description.\nLine two.", "summary": "OLDVALUE summary"}}
issue state after undo: {"description": "Line one of the description.\nLine two.", "labels": ["a"], "summary": "OLDVALUE summary"}
  CHECK [ok] undo restores description and summary

======================================================================
RUN C: Jira Align
======================================================================

--- RUN C step: 1 plan-update (default PATCH)
$ jira_align plan-update epics 5 --field title=new title --disposition title=replace --field points=5
stdout:
target: epics/5
flavor: align
base_url: https://align.example.invalid
method: PATCH
notify: true
field: title
  disposition: replace
  current:
    | OLDVALUE title
  proposed:
    | new title
field: points
  disposition: replace
  current:
    | 3
  proposed:
    | 5
digest: 21a17dbe8e166c0519437b64db04f60d56f018faca0a10e7104e999fa7f3ab35
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-21a17dbe8e16.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 0)
  CHECK [ok] preview shows method: PATCH, zero writes

--- RUN C step: 2 update
$ jira_align update epics 5 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-21a17dbe8e16.json --approved-digest 21a17dbe8e166c0519437b64db04f60d56f018faca0a10e7104e999fa7f3ab35
stdout:
digest: 21a17dbe8e166c0519437b64db04f60d56f018faca0a10e7104e999fa7f3ab35
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/prior/20261111T212318134954Z-epics-5.json
changed outside the plan: rank: null -> 77
ok: updated epics/5
exit code: 0
write requests this step: 1 (total 1)
  PATCH /rest/align/api/2/epics/5 body={"points": 5, "title": "new title"}
  CHECK [ok] single PATCH sent
  CHECK [ok] post-write drift report on stderr names rank
  CHECK [ok] record path printed

--- RUN C step: 3 plan-update --replace-record
$ jira_align plan-update epics 5 --field title=third title --disposition title=replace --field points=8 --replace-record
stdout:
omitted from the PUT body (each would be cleared by this PUT):
  - id
  - description
  - state
  - owner
  - rank
target: epics/5
flavor: align
base_url: https://align.example.invalid
method: PUT
notify: true
field: title
  disposition: replace
  current:
    | new title
  proposed:
    | third title
field: points
  disposition: replace
  current:
    | 5
  proposed:
    | 8
digest: 559d91cb943cb4d9b0b78a4e9e89f724e021150470d006f8907e225e8d9e41e8
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-559d91cb943c.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 1)
  CHECK [ok] preview shows method: PUT
  CHECK [ok] omitted-field list names unwritten fields

--- RUN C step: 4 update from the PUT plan
$ jira_align update epics 5 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-559d91cb943c.json --approved-digest 559d91cb943cb4d9b0b78a4e9e89f724e021150470d006f8907e225e8d9e41e8
stdout:
digest: 559d91cb943cb4d9b0b78a4e9e89f724e021150470d006f8907e225e8d9e41e8
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/prior/20261111T212318139501Z-epics-5.json
changed outside the plan: description: old description -> null
changed outside the plan: state: Open -> null
changed outside the plan: owner: someone -> null
changed outside the plan: rank: 77 -> null
ok: updated epics/5
exit code: 0
write requests this step: 1 (total 2)
  PUT /rest/align/api/2/epics/5 body={"points": 8, "title": "third title"}
  CHECK [ok] PUT sent only from the approved plan
record state after PUT: {"id": 5, "points": 8, "title": "third title"}

--- RUN C step: 5 update with --method flag
$ jira_align update epics 5 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-21a17dbe8e16.json --approved-digest 21a17dbe8e166c0519437b64db04f60d56f018faca0a10e7104e999fa7f3ab35 --method PUT
stdout:
(empty)
stderr:
usage: <repo>/.context/venv/bin/python <repo>/packs/atlassian/.apm/skills/jira-align/scripts/jira_align.py
       [-h] [--verbose] [--insecure] [--format {json,jsonl,csv}]
       [--output OUTPUT] [--intake-profile INTAKE_PROFILE]
       {check,whoami,get,list,search,create,plan-update,update,plan-undo,delete,raw} ...
<repo>/.context/venv/bin/python <repo>/packs/atlassian/.apm/skills/jira-align/scripts/jira_align.py: error: unrecognized arguments: --method PUT
exit code: 2
write requests this step: 0 (total 2)
  CHECK [ok] argparse error, zero requests

--- RUN C step: 6 raw PUT refused
$ jira_align raw PUT epics/5 --data-file /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/abody.json
stdout:
(empty)
stderr:
refused: write refused: no verified plan; run plan-update and approve it first
exit code: 10
write requests this step: 0 (total 2)
  CHECK [ok] raw PUT refused: exit 10, zero requests

--- RUN C step: 7a plan-undo of the PUT record
$ jira_align plan-undo --record /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/prior/20261111T212318139501Z-epics-5.json
stdout:
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-dd7d5718708a.json
digest: dd7d5718708a385aeb73f31368de7b0b9b6d88bfbe306bb7db654017ff7be0dc
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 2)
  CHECK [ok] plan-undo exit 0

--- RUN C step: 7b update with undo plan
$ jira_align update epics 5 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-dd7d5718708a.json --approved-digest dd7d5718708a385aeb73f31368de7b0b9b6d88bfbe306bb7db654017ff7be0dc
stdout:
digest: dd7d5718708a385aeb73f31368de7b0b9b6d88bfbe306bb7db654017ff7be0dc
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-s5uvw3k4/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/prior/20261111T212318152046Z-epics-5.json
no field outside the plan changed
ok: updated epics/5
exit code: 0
write requests this step: 1 (total 3)
  PATCH /rest/align/api/2/epics/5 body={"points": 5, "title": "new title"}
record state after undo: {"id": 5, "points": 5, "title": "new title"}
  CHECK [ok] undo restores the planned fields (AC43)
NOTE: fields cleared by the PUT after undo: {"description": "<absent>", "state": "<absent>", "owner": "<absent>", "rank": "<absent>"}

RUN A: PASS
RUN B: PASS
RUN C: PASS
files written under temp HOME: 17
```

## Findings (product behaviour, nothing hidden; QA checks all pass)

F1. Append preview does not show what will be written. For `--disposition description=append` the preview's `proposed:` shows only the new fragment, while the write adds a separator label.
  - Server (Run B step 1) preview: `proposed:` / `|` (empty line) / `| Appended line.`
  - Server (Run B step 3b) write body: `"description": "Line one of the description.\nLine two.\n\nAppended text:\n\nAppended line."`
  - Cloud (Run A step 1) `proposed:` is a doc holding one paragraph `appended note`; the PUT body (step 3b) holds the whole existing doc plus two new paragraphs: `Appended text:` and `appended note`.
  A person approving the preview never sees the `Appended text:` label or the merged result. (Digest binds the fields, so approval is still of the stored plan, but the preview understates the write.)

F2. `drops node types: none` / `drops mark types: none` lines are printed under the `summary` (plain string) field in Run A step 1, after `proposed: | new summary`. They read as belonging to summary, but the ADF check concerns description. Under a replace of description (step 4a) the same lines follow description, so the placement depends on field order and is ambiguous.

F3. `plan-undo` of a Jira Align PUT does not restore fields the PUT cleared. Run C step 4 PUT cleared description, state, owner, rank (drift lines: `changed outside the plan: description: old description -> null`, etc.; the record file holds the full prior record). The undo plan (step 7b) is a PATCH of only title and points; afterwards the record is `{"id": 5, "points": 5, "title": "new title"}`. This matches AC43 (per-field restore) but a person may expect undo to bring back the cleared data. Neither the plan-undo output (`plan_file:` and `digest:` only) nor update output warns that cleared fields stay cleared, though the data is in the record.

F4. Run C step 3: the `--replace-record` omitted list names `id` ("each would be cleared by this PUT"). Real Align servers keep `id`; listing it may alarm. Minor. (Also, the `current:` of title in step 3 reflects the earlier PATCH, correct.)

F5. Run A step 1 stderr carried one `INFO httpx: HTTP Request: GET https://jira.example.invalid/rest/api/3/issue/PROJ-12?fields=description%2Csummary "HTTP/1.1 200 OK"` line (logging is bound to the first captured stderr, so only that step shows it). A terminal user would likely see one such line per request. It prints the URL but no secrets or record contents.

F6. Observations that are not defects: a stale or lossy refusal still prints `digest:` on stdout (AC5 requires exactly one digest line per invocation); `raw PUT` refusal text says "no verified plan; run plan-update and approve it first" for both skills (it does not name `update-issue`/`update`); argparse's usage line uses the full interpreter and script path as prog.

No secrets (token `fixture`) or record file contents were printed by update-issue, update or plan-undo. Prior-value records are written to the temp HOME only.

### Observed transcript (final rerun, after T10)


======================================================================
RUN A: Jira Cloud (ADF)
======================================================================

--- RUN A step: 1 plan-update (append description, replace summary)
$ jira plan-update PROJ-12 --field description=appended note --disposition description=append --field summary=new summary --disposition summary=replace
stdout:
target: PROJ-12
flavor: cloud
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: append
  current:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "existing one",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing two",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "attrs": {
    |         "panelType": "info"
    |       },
    |       "content": [
    |         {
    |           "content": [
    |             {
    |               "text": "panel body",
    |               "type": "text"
    |             }
    |           ],
    |           "type": "paragraph"
    |         }
    |       ],
    |       "type": "panel"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  proposed:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "appended note",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  after write (lines marked + are added; others already exist):
    |   existing one
    |   existing two
    |   panel body
    | + Appended text:
    | + appended note
field: summary
  disposition: replace
  current:
    | OLDVALUE summary
  proposed:
    | new summary
digest: 0a0a879b27703005566c4c2b65132dcab379e7affd5fc59c21757c88e73e6f6b
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-0a0a879b2770.json
stderr:
2026-11-11 19:09:36,623 INFO httpx: HTTP Request: GET https://jira.example.invalid/rest/api/3/issue/PROJ-12?fields=description%2Csummary "HTTP/1.1 200 OK"
exit code: 0
write requests this step: 0 (total 0)
  CHECK [ok] plan-update exit 0 and zero writes
  CHECK [ok] preview shows plan file and digest

--- RUN A step: 2 person edits description; update-issue with stale plan
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-0a0a879b2770.json --approved-digest 0a0a879b27703005566c4c2b65132dcab379e7affd5fc59c21757c88e73e6f6b
stdout:
digest: 0a0a879b27703005566c4c2b65132dcab379e7affd5fc59c21757c88e73e6f6b
stderr:
refused: fields changed since the preview: description; rerun plan-update (a small race remains between this check and the write)
exit code: 10
write requests this step: 0 (total 0)
  CHECK [ok] stale refusal: exit 10, zero write requests
  CHECK [ok] fake description restored to original nodes

--- RUN A step: 3a re-plan after the edit
$ jira plan-update PROJ-12 --field description=appended note --disposition description=append --field summary=new summary --disposition summary=replace
stdout:
target: PROJ-12
flavor: cloud
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: append
  current:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "a person edited this",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing one",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing two",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "attrs": {
    |         "panelType": "info"
    |       },
    |       "content": [
    |         {
    |           "content": [
    |             {
    |               "text": "panel body",
    |               "type": "text"
    |             }
    |           ],
    |           "type": "paragraph"
    |         }
    |       ],
    |       "type": "panel"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  proposed:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "appended note",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  after write (lines marked + are added; others already exist):
    |   a person edited this
    |   existing one
    |   existing two
    |   panel body
    | + Appended text:
    | + appended note
field: summary
  disposition: replace
  current:
    | OLDVALUE summary
  proposed:
    | new summary
digest: f861ab7a8ea231ecb4eedc9ff80ad12f5c3084bb9804dc09d85ce62cdf55dae9
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-f861ab7a8ea2.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 0)

--- RUN A step: 3b update-issue
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-f861ab7a8ea2.json --approved-digest f861ab7a8ea231ecb4eedc9ff80ad12f5c3084bb9804dc09d85ce62cdf55dae9
stdout:
digest: f861ab7a8ea231ecb4eedc9ff80ad12f5c3084bb9804dc09d85ce62cdf55dae9
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261112T010936643576Z-PROJ-12.json
ok: updated PROJ-12
exit code: 0
write requests this step: 1 (total 1)
  PUT /rest/api/3/issue/PROJ-12 body={"fields": {"description": {"content": [{"content": [{"text": "a person edited this", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing one", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing two", "type": "text"}], "type": "paragraph"}, {"attrs": {"panelType": "info"}, "content": [{"content": [{"text": "panel body", "type": "text"}], "type": "paragraph"}], "type": "panel"}, {"content": [{"text": "Appended text:", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "appended note", "type": "text"}], "type": "paragraph"}], "type": "doc", "version": 1}, "summary": "new summary"}}
  CHECK [ok] exactly one PUT write
  CHECK [ok] record path line printed once on stderr
  CHECK [ok] existing ADF nodes unchanged and in order (prefix)
  CHECK [ok] two paragraph nodes appended (label + text)
  CHECK [ok] last node is the appended text
  CHECK [ok] body holds only planned fields

--- RUN A step: 4a plan-update replace description with plain paragraph (drops panel)
$ jira plan-update PROJ-12 --field description=replacement plain text --disposition description=replace
stdout:
target: PROJ-12
flavor: cloud
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: replace
  current:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "a person edited this",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing one",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing two",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "attrs": {
    |         "panelType": "info"
    |       },
    |       "content": [
    |         {
    |           "content": [
    |             {
    |               "text": "panel body",
    |               "type": "text"
    |             }
    |           ],
    |           "type": "paragraph"
    |         }
    |       ],
    |       "type": "panel"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "Appended text:",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "appended note",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  proposed:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "replacement plain text",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  drops node types: panel
  drops mark types: none
  lossy: needs --allow-lossy
digest: d4bb863ef426c95bf7abd2abfa8f8688cc85d220766e3e8c816f56eafe6f865b
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-d4bb863ef426.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 1)
  CHECK [ok] plan-update names the dropped node type 'panel'

--- RUN A step: 4b update-issue without --allow-lossy
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-d4bb863ef426.json --approved-digest d4bb863ef426c95bf7abd2abfa8f8688cc85d220766e3e8c816f56eafe6f865b
stdout:
digest: d4bb863ef426c95bf7abd2abfa8f8688cc85d220766e3e8c816f56eafe6f865b
stderr:
refused: field description: replace would drop panel; pass --allow-lossy to proceed
exit code: 10
write requests this step: 0 (total 1)
  CHECK [ok] lossy replace refused: exit 10, zero writes
  CHECK [ok] issue unchanged after refusal

--- RUN A step: 5a plan-undo --record
$ jira plan-undo --record /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261112T010936643576Z-PROJ-12.json
stdout:
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-d98fd3e1e063.json
digest: d98fd3e1e06341ef1cd119e3b15d0f48f239671c83211ece63b38a546b60ebe8
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 1)
  CHECK [ok] plan-undo exit 0

--- RUN A step: 5b update-issue with undo plan
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-d98fd3e1e063.json --approved-digest d98fd3e1e06341ef1cd119e3b15d0f48f239671c83211ece63b38a546b60ebe8
stdout:
digest: d98fd3e1e06341ef1cd119e3b15d0f48f239671c83211ece63b38a546b60ebe8
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261112T010936659217Z-PROJ-12.json
ok: updated PROJ-12
exit code: 0
write requests this step: 1 (total 2)
  PUT /rest/api/3/issue/PROJ-12 body={"fields": {"description": {"content": [{"content": [{"text": "a person edited this", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing one", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing two", "type": "text"}], "type": "paragraph"}, {"attrs": {"panelType": "info"}, "content": [{"content": [{"text": "panel body", "type": "text"}], "type": "paragraph"}], "type": "panel"}], "type": "doc", "version": 1}, "summary": "OLDVALUE summary"}}
  CHECK [ok] undo write: exit 0, one request
issue state after undo: {"description": {"content": [{"content": [{"text": "a person edited this", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing one", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing two", "type": "text"}], "type": "paragraph"}, {"attrs": {"panelType": "info"}, "content": [{"content": [{"text": "panel body", "type": "text"}], "type": "paragraph"}], "type": "panel"}], "type": "doc", "version": 1}, "labels": [], "summary": "OLDVALUE summary"}
  CHECK [ok] summary restored
  CHECK [ok] description restored to pre-write nodes

--- RUN A step: 6a transition with --field
$ jira transition PROJ-12 --to Done --field description=x
stdout:
(empty)
stderr:
refused: a transition with field content is always refused; use plan-update
exit code: 10
write requests this step: 0 (total 2)
  CHECK [ok] transition+field: exit 10, zero writes
  CHECK [ok] transition+field: zero requests at all

--- RUN A step: 6b raw PUT on issue path
$ jira raw PUT issue/PROJ-12 --data-file /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/body.json
stdout:
(empty)
stderr:
refused: write refused: no verified plan; run plan-update and approve it first
exit code: 10
write requests this step: 0 (total 2)
  CHECK [ok] raw PUT refused: exit 10, zero requests

======================================================================
RUN B: Jira Server/Data Center (string fields)
======================================================================

--- RUN B step: 1 plan-update
$ jira plan-update PROJ-12 --field description=
Appended line. --disposition description=append --field summary=new summary --disposition summary=replace
stdout:
target: PROJ-12
flavor: server
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: append
  current:
    | Line one of the description.
    | Line two.
  proposed:
    | 
    | Appended line.
  after write (existing text, then the label and added text):
    | Line one of the description.
    | Line two.
    | 
    | Appended text:
    | 
    | Appended line.
field: summary
  disposition: replace
  current:
    | OLDVALUE summary
  proposed:
    | new summary
digest: ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-ed5a2be5f8ff.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 0)
  CHECK [ok] plan-update exit 0, zero writes

--- RUN B step: 2 stale update-issue
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-ed5a2be5f8ff.json --approved-digest ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
stdout:
digest: ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
stderr:
refused: fields changed since the preview: description; rerun plan-update (a small race remains between this check and the write)
exit code: 10
write requests this step: 0 (total 0)
  CHECK [ok] stale refusal: exit 10, zero writes

--- RUN B step: 3a re-plan
$ jira plan-update PROJ-12 --field description=
Appended line. --disposition description=append --field summary=new summary --disposition summary=replace
stdout:
target: PROJ-12
flavor: server
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: append
  current:
    | Line one of the description.
    | Line two.
  proposed:
    | 
    | Appended line.
  after write (existing text, then the label and added text):
    | Line one of the description.
    | Line two.
    | 
    | Appended text:
    | 
    | Appended line.
field: summary
  disposition: replace
  current:
    | OLDVALUE summary
  proposed:
    | new summary
digest: ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-ed5a2be5f8ff-1.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 0)

--- RUN B step: 3b update-issue
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-ed5a2be5f8ff-1.json --approved-digest ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
stdout:
digest: ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261112T010936677869Z-PROJ-12.json
ok: updated PROJ-12
exit code: 0
write requests this step: 1 (total 1)
  PUT /rest/api/2/issue/PROJ-12 body={"fields": {"description": "Line one of the description.\nLine two.\n\nAppended text:\n\nAppended line.", "summary": "new summary"}}
  CHECK [ok] one write request
  CHECK [ok] record path line on stderr
  CHECK [ok] original is a byte-exact prefix of new description
  CHECK [ok] summary replaced

--- RUN B step: 4a plan-undo
$ jira plan-undo --record /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261112T010936677869Z-PROJ-12.json
stdout:
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-f8f6c7063ca4.json
digest: f8f6c7063ca4027fa2642886547fd2a92b79c46de83ab2259df70d143c0c15cd
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 1)

--- RUN B step: 4b update-issue undo plan
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-f8f6c7063ca4.json --approved-digest f8f6c7063ca4027fa2642886547fd2a92b79c46de83ab2259df70d143c0c15cd
stdout:
digest: f8f6c7063ca4027fa2642886547fd2a92b79c46de83ab2259df70d143c0c15cd
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261112T010936690081Z-PROJ-12.json
ok: updated PROJ-12
exit code: 0
write requests this step: 1 (total 2)
  PUT /rest/api/2/issue/PROJ-12 body={"fields": {"description": "Line one of the description.\nLine two.", "summary": "OLDVALUE summary"}}
issue state after undo: {"description": "Line one of the description.\nLine two.", "labels": ["a"], "summary": "OLDVALUE summary"}
  CHECK [ok] undo restores description and summary

======================================================================
RUN C: Jira Align
======================================================================

--- RUN C step: 1 plan-update (default PATCH)
$ jira_align plan-update epics 5 --field title=new title --disposition title=replace --field points=5
stdout:
target: epics/5
flavor: align
base_url: https://align.example.invalid
method: PATCH
notify: true
field: title
  disposition: replace
  current:
    | OLDVALUE title
  proposed:
    | new title
field: points
  disposition: replace
  current:
    | 3
  proposed:
    | 5
digest: 21a17dbe8e166c0519437b64db04f60d56f018faca0a10e7104e999fa7f3ab35
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-21a17dbe8e16.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 0)
  CHECK [ok] preview shows method: PATCH, zero writes

--- RUN C step: 2 update
$ jira_align update epics 5 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-21a17dbe8e16.json --approved-digest 21a17dbe8e166c0519437b64db04f60d56f018faca0a10e7104e999fa7f3ab35
stdout:
digest: 21a17dbe8e166c0519437b64db04f60d56f018faca0a10e7104e999fa7f3ab35
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/prior/20261112T010936696947Z-epics-5.json
changed outside the plan: rank: null -> 77
ok: updated epics/5
exit code: 0
write requests this step: 1 (total 1)
  PATCH /rest/align/api/2/epics/5 body={"points": 5, "title": "new title"}
  CHECK [ok] single PATCH sent
  CHECK [ok] post-write drift report on stderr names rank
  CHECK [ok] record path printed

--- RUN C step: 3 plan-update --replace-record
$ jira_align plan-update epics 5 --field title=third title --disposition title=replace --field points=8 --replace-record
stdout:
omitted from the PUT body (each would be cleared by this PUT):
  - id (the record's identifier)
  - description
  - state
  - owner
  - rank
target: epics/5
flavor: align
base_url: https://align.example.invalid
method: PUT
notify: true
field: title
  disposition: replace
  current:
    | new title
  proposed:
    | third title
field: points
  disposition: replace
  current:
    | 5
  proposed:
    | 8
digest: 1fe11b00f7aaff38ceab2d2784278cb2988e991ca49ee29dbfd1a44b9bff9f8c
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-1fe11b00f7aa.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 1)
  CHECK [ok] preview shows method: PUT
  CHECK [ok] omitted-field list names unwritten fields

--- RUN C step: 4 update from the PUT plan
$ jira_align update epics 5 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-1fe11b00f7aa.json --approved-digest 1fe11b00f7aaff38ceab2d2784278cb2988e991ca49ee29dbfd1a44b9bff9f8c
stdout:
digest: 1fe11b00f7aaff38ceab2d2784278cb2988e991ca49ee29dbfd1a44b9bff9f8c
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/prior/20261112T010936743320Z-epics-5.json
changed outside the plan: description: old description -> null
changed outside the plan: state: Open -> null
changed outside the plan: owner: someone -> null
changed outside the plan: rank: 77 -> null
ok: updated epics/5
exit code: 0
write requests this step: 1 (total 2)
  PUT /rest/align/api/2/epics/5 body={"points": 8, "title": "third title"}
  CHECK [ok] PUT sent only from the approved plan
record state after PUT: {"id": 5, "points": 8, "title": "third title"}

--- RUN C step: 5 update with --method flag
$ jira_align update epics 5 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-21a17dbe8e16.json --approved-digest 21a17dbe8e166c0519437b64db04f60d56f018faca0a10e7104e999fa7f3ab35 --method PUT
stdout:
(empty)
stderr:
usage: <repo>/.context/venv/bin/python <repo>/packs/atlassian/.apm/skills/jira-align/scripts/jira_align.py
       [-h] [--verbose] [--insecure] [--format {json,jsonl,csv}]
       [--output OUTPUT] [--intake-profile INTAKE_PROFILE]
       {check,whoami,get,list,search,create,plan-update,update,plan-undo,delete,raw} ...
<repo>/.context/venv/bin/python <repo>/packs/atlassian/.apm/skills/jira-align/scripts/jira_align.py: error: unrecognized arguments: --method PUT
exit code: 2
write requests this step: 0 (total 2)
  CHECK [ok] argparse error, zero requests

--- RUN C step: 6 raw PUT refused
$ jira_align raw PUT epics/5 --data-file /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/abody.json
stdout:
(empty)
stderr:
refused: write refused: no verified plan; run plan-update and approve it first
exit code: 10
write requests this step: 0 (total 2)
  CHECK [ok] raw PUT refused: exit 10, zero requests

--- RUN C step: 7a plan-undo of the PUT record
$ jira_align plan-undo --record /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/prior/20261112T010936743320Z-epics-5.json
stdout:
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-dd7d5718708a.json
digest: dd7d5718708a385aeb73f31368de7b0b9b6d88bfbe306bb7db654017ff7be0dc
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 2)
  CHECK [ok] plan-undo exit 0

--- RUN C step: 7b update with undo plan
$ jira_align update epics 5 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-dd7d5718708a.json --approved-digest dd7d5718708a385aeb73f31368de7b0b9b6d88bfbe306bb7db654017ff7be0dc
stdout:
digest: dd7d5718708a385aeb73f31368de7b0b9b6d88bfbe306bb7db654017ff7be0dc
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-k18knv_t/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/prior/20261112T010936927071Z-epics-5.json
no field outside the plan changed
ok: updated epics/5
exit code: 0
write requests this step: 1 (total 3)
  PATCH /rest/align/api/2/epics/5 body={"points": 5, "title": "new title"}
record state after undo: {"id": 5, "points": 5, "title": "new title"}
  CHECK [ok] undo restores the planned fields (AC43)
NOTE: fields cleared by the PUT after undo: {"description": "<absent>", "state": "<absent>", "owner": "<absent>", "rank": "<absent>"}

RUN A: PASS
RUN B: PASS
RUN C: PASS
files written under temp HOME: 17

### Amendment cycle and final review (2026-11-11)

After the first closeout, AC5 was reworded under a controlled amendment (a digest line is printed by `plan-update` and `plan-undo` when they save a plan file, and by `update-issue` and `update` when the loader accepts the plan file, whether or not a later check refuses the update; any other invocation prints none), and three more repair tasks ran against it: T13 (the loaders refuse non-finite numbers such as `1e400`; `plan-update` and `plan-undo` build their output before saving; newlines are encoded in argument errors, field names, and printed paths), T14 (lone Unicode surrogates are encoded so a value holding one can be printed; the parser's program name is encoded), and T15 (the Jira issue key is validated before any request). Each was written test-first by a worker, with a hand-run mutation check, and verified by the controller's own gate run.

Review rounds 7 to 9 used three independent read-only reviewers per round. Round 7 found the surrogate and program-name gaps; round 8 found the unvalidated issue key; round 9 was clean from all three. The final manual QA driver rerun (RUN A Jira Cloud, RUN B Jira Server/Data Center, RUN C Jira Align) passed, and its transcript follows.

### Observed transcript (final rerun, after T15)


======================================================================
RUN A: Jira Cloud (ADF)
======================================================================

--- RUN A step: 1 plan-update (append description, replace summary)
$ jira plan-update PROJ-12 --field description=appended note --disposition description=append --field summary=new summary --disposition summary=replace
stdout:
target: PROJ-12
flavor: cloud
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: append
  current:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "existing one",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing two",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "attrs": {
    |         "panelType": "info"
    |       },
    |       "content": [
    |         {
    |           "content": [
    |             {
    |               "text": "panel body",
    |               "type": "text"
    |             }
    |           ],
    |           "type": "paragraph"
    |         }
    |       ],
    |       "type": "panel"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  proposed:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "appended note",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  after write (lines marked + are added; others already exist):
    |   existing one
    |   existing two
    |   panel body
    | + Appended text:
    | + appended note
field: summary
  disposition: replace
  current:
    | OLDVALUE summary
  proposed:
    | new summary
digest: 0a0a879b27703005566c4c2b65132dcab379e7affd5fc59c21757c88e73e6f6b
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-0a0a879b2770.json
stderr:
2026-11-11 23:06:36,067 INFO httpx: HTTP Request: GET https://jira.example.invalid/rest/api/3/issue/PROJ-12?fields=description%2Csummary "HTTP/1.1 200 OK"
exit code: 0
write requests this step: 0 (total 0)
  CHECK [ok] plan-update exit 0 and zero writes
  CHECK [ok] preview shows plan file and digest

--- RUN A step: 2 person edits description; update-issue with stale plan
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-0a0a879b2770.json --approved-digest 0a0a879b27703005566c4c2b65132dcab379e7affd5fc59c21757c88e73e6f6b
stdout:
digest: 0a0a879b27703005566c4c2b65132dcab379e7affd5fc59c21757c88e73e6f6b
stderr:
refused: fields changed since the preview: description; rerun plan-update (a small race remains between this check and the write)
exit code: 10
write requests this step: 0 (total 0)
  CHECK [ok] stale refusal: exit 10, zero write requests
  CHECK [ok] fake description restored to original nodes

--- RUN A step: 3a re-plan after the edit
$ jira plan-update PROJ-12 --field description=appended note --disposition description=append --field summary=new summary --disposition summary=replace
stdout:
target: PROJ-12
flavor: cloud
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: append
  current:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "a person edited this",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing one",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing two",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "attrs": {
    |         "panelType": "info"
    |       },
    |       "content": [
    |         {
    |           "content": [
    |             {
    |               "text": "panel body",
    |               "type": "text"
    |             }
    |           ],
    |           "type": "paragraph"
    |         }
    |       ],
    |       "type": "panel"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  proposed:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "appended note",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  after write (lines marked + are added; others already exist):
    |   a person edited this
    |   existing one
    |   existing two
    |   panel body
    | + Appended text:
    | + appended note
field: summary
  disposition: replace
  current:
    | OLDVALUE summary
  proposed:
    | new summary
digest: f861ab7a8ea231ecb4eedc9ff80ad12f5c3084bb9804dc09d85ce62cdf55dae9
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-f861ab7a8ea2.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 0)

--- RUN A step: 3b update-issue
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-f861ab7a8ea2.json --approved-digest f861ab7a8ea231ecb4eedc9ff80ad12f5c3084bb9804dc09d85ce62cdf55dae9
stdout:
digest: f861ab7a8ea231ecb4eedc9ff80ad12f5c3084bb9804dc09d85ce62cdf55dae9
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261112T050636088605Z-PROJ-12.json
ok: updated PROJ-12
exit code: 0
write requests this step: 1 (total 1)
  PUT /rest/api/3/issue/PROJ-12 body={"fields": {"description": {"content": [{"content": [{"text": "a person edited this", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing one", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing two", "type": "text"}], "type": "paragraph"}, {"attrs": {"panelType": "info"}, "content": [{"content": [{"text": "panel body", "type": "text"}], "type": "paragraph"}], "type": "panel"}, {"content": [{"text": "Appended text:", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "appended note", "type": "text"}], "type": "paragraph"}], "type": "doc", "version": 1}, "summary": "new summary"}}
  CHECK [ok] exactly one PUT write
  CHECK [ok] record path line printed once on stderr
  CHECK [ok] existing ADF nodes unchanged and in order (prefix)
  CHECK [ok] two paragraph nodes appended (label + text)
  CHECK [ok] last node is the appended text
  CHECK [ok] body holds only planned fields

--- RUN A step: 4a plan-update replace description with plain paragraph (drops panel)
$ jira plan-update PROJ-12 --field description=replacement plain text --disposition description=replace
stdout:
target: PROJ-12
flavor: cloud
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: replace
  current:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "a person edited this",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing one",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "existing two",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "attrs": {
    |         "panelType": "info"
    |       },
    |       "content": [
    |         {
    |           "content": [
    |             {
    |               "text": "panel body",
    |               "type": "text"
    |             }
    |           ],
    |           "type": "paragraph"
    |         }
    |       ],
    |       "type": "panel"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "Appended text:",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     },
    |     {
    |       "content": [
    |         {
    |           "text": "appended note",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  proposed:
    | {
    |   "content": [
    |     {
    |       "content": [
    |         {
    |           "text": "replacement plain text",
    |           "type": "text"
    |         }
    |       ],
    |       "type": "paragraph"
    |     }
    |   ],
    |   "type": "doc",
    |   "version": 1
    | }
  drops node types: panel
  drops mark types: none
  lossy: needs --allow-lossy
digest: d4bb863ef426c95bf7abd2abfa8f8688cc85d220766e3e8c816f56eafe6f865b
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-d4bb863ef426.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 1)
  CHECK [ok] plan-update names the dropped node type 'panel'

--- RUN A step: 4b update-issue without --allow-lossy
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-d4bb863ef426.json --approved-digest d4bb863ef426c95bf7abd2abfa8f8688cc85d220766e3e8c816f56eafe6f865b
stdout:
digest: d4bb863ef426c95bf7abd2abfa8f8688cc85d220766e3e8c816f56eafe6f865b
stderr:
refused: field description: replace would drop panel; pass --allow-lossy to proceed
exit code: 10
write requests this step: 0 (total 1)
  CHECK [ok] lossy replace refused: exit 10, zero writes
  CHECK [ok] issue unchanged after refusal

--- RUN A step: 5a plan-undo --record
$ jira plan-undo --record /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261112T050636088605Z-PROJ-12.json
stdout:
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-d98fd3e1e063.json
digest: d98fd3e1e06341ef1cd119e3b15d0f48f239671c83211ece63b38a546b60ebe8
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 1)
  CHECK [ok] plan-undo exit 0

--- RUN A step: 5b update-issue with undo plan
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-d98fd3e1e063.json --approved-digest d98fd3e1e06341ef1cd119e3b15d0f48f239671c83211ece63b38a546b60ebe8
stdout:
digest: d98fd3e1e06341ef1cd119e3b15d0f48f239671c83211ece63b38a546b60ebe8
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261112T050636118394Z-PROJ-12.json
ok: updated PROJ-12
exit code: 0
write requests this step: 1 (total 2)
  PUT /rest/api/3/issue/PROJ-12 body={"fields": {"description": {"content": [{"content": [{"text": "a person edited this", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing one", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing two", "type": "text"}], "type": "paragraph"}, {"attrs": {"panelType": "info"}, "content": [{"content": [{"text": "panel body", "type": "text"}], "type": "paragraph"}], "type": "panel"}], "type": "doc", "version": 1}, "summary": "OLDVALUE summary"}}
  CHECK [ok] undo write: exit 0, one request
issue state after undo: {"description": {"content": [{"content": [{"text": "a person edited this", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing one", "type": "text"}], "type": "paragraph"}, {"content": [{"text": "existing two", "type": "text"}], "type": "paragraph"}, {"attrs": {"panelType": "info"}, "content": [{"content": [{"text": "panel body", "type": "text"}], "type": "paragraph"}], "type": "panel"}], "type": "doc", "version": 1}, "labels": [], "summary": "OLDVALUE summary"}
  CHECK [ok] summary restored
  CHECK [ok] description restored to pre-write nodes

--- RUN A step: 6a transition with --field
$ jira transition PROJ-12 --to Done --field description=x
stdout:
(empty)
stderr:
refused: a transition with field content is always refused; use plan-update
exit code: 10
write requests this step: 0 (total 2)
  CHECK [ok] transition+field: exit 10, zero writes
  CHECK [ok] transition+field: zero requests at all

--- RUN A step: 6b raw PUT on issue path
$ jira raw PUT issue/PROJ-12 --data-file /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/body.json
stdout:
(empty)
stderr:
refused: write refused: no verified plan; run plan-update and approve it first
exit code: 10
write requests this step: 0 (total 2)
  CHECK [ok] raw PUT refused: exit 10, zero requests

======================================================================
RUN B: Jira Server/Data Center (string fields)
======================================================================

--- RUN B step: 1 plan-update
$ jira plan-update PROJ-12 --field description=
Appended line. --disposition description=append --field summary=new summary --disposition summary=replace
stdout:
target: PROJ-12
flavor: server
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: append
  current:
    | Line one of the description.
    | Line two.
  proposed:
    | 
    | Appended line.
  after write (existing text, then the label and added text):
    | Line one of the description.
    | Line two.
    | 
    | Appended text:
    | 
    | Appended line.
field: summary
  disposition: replace
  current:
    | OLDVALUE summary
  proposed:
    | new summary
digest: ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-ed5a2be5f8ff.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 0)
  CHECK [ok] plan-update exit 0, zero writes

--- RUN B step: 2 stale update-issue
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-ed5a2be5f8ff.json --approved-digest ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
stdout:
digest: ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
stderr:
refused: fields changed since the preview: description; rerun plan-update (a small race remains between this check and the write)
exit code: 10
write requests this step: 0 (total 0)
  CHECK [ok] stale refusal: exit 10, zero writes

--- RUN B step: 3a re-plan
$ jira plan-update PROJ-12 --field description=
Appended line. --disposition description=append --field summary=new summary --disposition summary=replace
stdout:
target: PROJ-12
flavor: server
base_url: https://jira.example.invalid
method: PUT
notify: true
field: description
  disposition: append
  current:
    | Line one of the description.
    | Line two.
  proposed:
    | 
    | Appended line.
  after write (existing text, then the label and added text):
    | Line one of the description.
    | Line two.
    | 
    | Appended text:
    | 
    | Appended line.
field: summary
  disposition: replace
  current:
    | OLDVALUE summary
  proposed:
    | new summary
digest: ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-ed5a2be5f8ff-1.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 0)

--- RUN B step: 3b update-issue
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-ed5a2be5f8ff-1.json --approved-digest ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
stdout:
digest: ed5a2be5f8ff7c10ba6a8006eb7f51d3420bcae1072193a3c8768a3528a9fdee
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261112T050636265645Z-PROJ-12.json
ok: updated PROJ-12
exit code: 0
write requests this step: 1 (total 1)
  PUT /rest/api/2/issue/PROJ-12 body={"fields": {"description": "Line one of the description.\nLine two.\n\nAppended text:\n\nAppended line.", "summary": "new summary"}}
  CHECK [ok] one write request
  CHECK [ok] record path line on stderr
  CHECK [ok] original is a byte-exact prefix of new description
  CHECK [ok] summary replaced

--- RUN B step: 4a plan-undo
$ jira plan-undo --record /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261112T050636265645Z-PROJ-12.json
stdout:
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-f8f6c7063ca4.json
digest: f8f6c7063ca4027fa2642886547fd2a92b79c46de83ab2259df70d143c0c15cd
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 1)

--- RUN B step: 4b update-issue undo plan
$ jira update-issue PROJ-12 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/plans/PROJ-12-f8f6c7063ca4.json --approved-digest f8f6c7063ca4027fa2642886547fd2a92b79c46de83ab2259df70d143c0c15cd
stdout:
digest: f8f6c7063ca4027fa2642886547fd2a92b79c46de83ab2259df70d143c0c15cd
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/jira.example.invalid-b153ffaeb8db/prior/20261112T050636292648Z-PROJ-12.json
ok: updated PROJ-12
exit code: 0
write requests this step: 1 (total 2)
  PUT /rest/api/2/issue/PROJ-12 body={"fields": {"description": "Line one of the description.\nLine two.", "summary": "OLDVALUE summary"}}
issue state after undo: {"description": "Line one of the description.\nLine two.", "labels": ["a"], "summary": "OLDVALUE summary"}
  CHECK [ok] undo restores description and summary

======================================================================
RUN C: Jira Align
======================================================================

--- RUN C step: 1 plan-update (default PATCH)
$ jira_align plan-update epics 5 --field title=new title --disposition title=replace --field points=5
stdout:
target: epics/5
flavor: align
base_url: https://align.example.invalid
method: PATCH
notify: true
field: title
  disposition: replace
  current:
    | OLDVALUE title
  proposed:
    | new title
field: points
  disposition: replace
  current:
    | 3
  proposed:
    | 5
digest: 21a17dbe8e166c0519437b64db04f60d56f018faca0a10e7104e999fa7f3ab35
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-21a17dbe8e16.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 0)
  CHECK [ok] preview shows method: PATCH, zero writes

--- RUN C step: 2 update
$ jira_align update epics 5 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-21a17dbe8e16.json --approved-digest 21a17dbe8e166c0519437b64db04f60d56f018faca0a10e7104e999fa7f3ab35
stdout:
digest: 21a17dbe8e166c0519437b64db04f60d56f018faca0a10e7104e999fa7f3ab35
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/prior/20261112T050636303728Z-epics-5.json
changed outside the plan: rank: null -> 77
ok: updated epics/5
exit code: 0
write requests this step: 1 (total 1)
  PATCH /rest/align/api/2/epics/5 body={"points": 5, "title": "new title"}
  CHECK [ok] single PATCH sent
  CHECK [ok] post-write drift report on stderr names rank
  CHECK [ok] record path printed

--- RUN C step: 3 plan-update --replace-record
$ jira_align plan-update epics 5 --field title=third title --disposition title=replace --field points=8 --replace-record
stdout:
omitted from the PUT body (each would be cleared by this PUT):
  - id (the record's identifier)
  - description
  - state
  - owner
  - rank
target: epics/5
flavor: align
base_url: https://align.example.invalid
method: PUT
notify: true
field: title
  disposition: replace
  current:
    | new title
  proposed:
    | third title
field: points
  disposition: replace
  current:
    | 5
  proposed:
    | 8
digest: 1fe11b00f7aaff38ceab2d2784278cb2988e991ca49ee29dbfd1a44b9bff9f8c
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-1fe11b00f7aa.json
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 1)
  CHECK [ok] preview shows method: PUT
  CHECK [ok] omitted-field list names unwritten fields

--- RUN C step: 4 update from the PUT plan
$ jira_align update epics 5 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-1fe11b00f7aa.json --approved-digest 1fe11b00f7aaff38ceab2d2784278cb2988e991ca49ee29dbfd1a44b9bff9f8c
stdout:
digest: 1fe11b00f7aaff38ceab2d2784278cb2988e991ca49ee29dbfd1a44b9bff9f8c
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/prior/20261112T050636317912Z-epics-5.json
changed outside the plan: description: old description -> null
changed outside the plan: state: Open -> null
changed outside the plan: owner: someone -> null
changed outside the plan: rank: 77 -> null
ok: updated epics/5
exit code: 0
write requests this step: 1 (total 2)
  PUT /rest/align/api/2/epics/5 body={"points": 8, "title": "third title"}
  CHECK [ok] PUT sent only from the approved plan
record state after PUT: {"id": 5, "points": 8, "title": "third title"}

--- RUN C step: 5 update with --method flag
$ jira_align update epics 5 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-21a17dbe8e16.json --approved-digest 21a17dbe8e166c0519437b64db04f60d56f018faca0a10e7104e999fa7f3ab35 --method PUT
stdout:
(empty)
stderr:
usage: <repo>/.context/venv/bin/python <repo>/packs/atlassian/.apm/skills/jira-align/scripts/jira_align.py
       [-h] [--verbose] [--insecure] [--format {json,jsonl,csv}]
       [--output OUTPUT] [--intake-profile INTAKE_PROFILE]
       {check,whoami,get,list,search,create,plan-update,update,plan-undo,delete,raw} ...
<repo>/.context/venv/bin/python <repo>/packs/atlassian/.apm/skills/jira-align/scripts/jira_align.py: error: unrecognized arguments: --method PUT
exit code: 2
write requests this step: 0 (total 2)
  CHECK [ok] argparse error, zero requests

--- RUN C step: 6 raw PUT refused
$ jira_align raw PUT epics/5 --data-file /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/abody.json
stdout:
(empty)
stderr:
refused: write refused: no verified plan; run plan-update and approve it first
exit code: 10
write requests this step: 0 (total 2)
  CHECK [ok] raw PUT refused: exit 10, zero requests

--- RUN C step: 7a plan-undo of the PUT record
$ jira_align plan-undo --record /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/prior/20261112T050636317912Z-epics-5.json
stdout:
plan_file: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-dd7d5718708a.json
digest: dd7d5718708a385aeb73f31368de7b0b9b6d88bfbe306bb7db654017ff7be0dc
stderr:
(empty)
exit code: 0
write requests this step: 0 (total 2)
  CHECK [ok] plan-undo exit 0

--- RUN C step: 7b update with undo plan
$ jira_align update epics 5 --plan /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/plans/epics-5-dd7d5718708a.json --approved-digest dd7d5718708a385aeb73f31368de7b0b9b6d88bfbe306bb7db654017ff7be0dc
stdout:
digest: dd7d5718708a385aeb73f31368de7b0b9b6d88bfbe306bb7db654017ff7be0dc
stderr:
prior-value record: /var/folders/vy/7bm5bhf11k32bjcg00624btm0000gp/T/twb-qa-home-696ez9rd/home/.agentbundle/tracker-write-back/align.example.invalid-a177bfd5abc1/prior/20261112T050636341769Z-epics-5.json
no field outside the plan changed
ok: updated epics/5
exit code: 0
write requests this step: 1 (total 3)
  PATCH /rest/align/api/2/epics/5 body={"points": 5, "title": "new title"}
record state after undo: {"id": 5, "points": 5, "title": "new title"}
  CHECK [ok] undo restores the planned fields (AC43)
NOTE: fields cleared by the PUT after undo: {"description": "<absent>", "state": "<absent>", "owner": "<absent>", "rank": "<absent>"}

RUN A: PASS
RUN B: PASS
RUN C: PASS
files written under temp HOME: 17
