# AC5 manual-QA record — observable episodic run

AC5 requires a real standard-mode `/research` run through the documented happy
path to write a `<topic-slug>-survey.md` file and **no** `research.md`. The
source change (the renamed skill body) is not installed into the implementing
session's skill loader, so the run was performed by following the **updated**
`research` SKILL.md body directly (this is how a prompt-only skill executes).

- **Probe prompt:** `research with citations: what are the established
  conventions for HTTP Cache-Control directives for immutable assets`
- **Mode selected:** `standard` (academic/citations cue).
- **Topic slug derived (per the SKILL.md rule):** `http-cache-immutable`.
- **Retrieval:** real `WebSearch` + `WebFetch` over RFC 8246 (primary), MDN
  Cache-Control (primary), and a practitioner caching refresher (secondary) —
  ≥3 independent sources, per the triangulation rail.
- **Working directory:** `.context/research-qa/` (gitignored scratch — no repo
  pollution).
- **Produced file:** `http-cache-immutable-survey.md` (topic slug +
  `survey` type stem), with `## Findings` (confidence-tagged), `## Known
  unknowns`, and `## Sources`.
- **`research.md` written:** none — `ls .context/research-qa/research.md`
  returned "No such file or directory".

Observed working-directory listing:

```
$ ls -1 .context/research-qa/
http-cache-immutable-survey.md
```

The file on disk (not a model self-report) is the signal: the renamed typed
artifact lands, and no `research.md` is written.
