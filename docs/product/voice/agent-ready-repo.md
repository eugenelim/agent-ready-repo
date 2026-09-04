# Voice chart: agent-ready-repo

Derived from the brand register at `docs/design/copy/brand-register.md`
(`type: tone-of-voice`, `scope: brand-level`, both validated). No prior chart
existed. This maps the register's four brand copy goals onto the UI-specific
axes; it does not re-derive the register.

- **Slug:** `agent-ready-repo`
- **Product:** UI copy across the marketing site and the documentation surface

## Voice axes

| Axis | Position | Why | Sample line |
| --- | --- | --- | --- |
| Humor | **serious**, with dry precision allowed | The reader is deciding whether to change how their team works. A joke costs a beat of comprehension the register's dominant goal cannot spare. | "Nothing found for that term." |
| Formality | **plain, slightly toward casual** | The register bars jargon the reader did not bring. Plain words next to exact technical terms — never stiff, never chummy. | "A pull request you merge" |
| Respect | **deferential to the reader's expertise** | This audience reads source when the docs disappoint. Copy that explains what they already know reads as condescension. | "Prerequisite: none." |
| Enthusiasm | **calm** | The register's dominant goal is that a line survive being repeated in a meeting. Enthusiasm does not survive that trip. | "A deployment validated off production" |

Derivation, so the mapping is checkable: *Repeatable precision* → calm and plain.
*Named limits* → serious, because a boundary stated warmly reads as hedged.
*Plain sequence* → plain formality. *Earned specificity* → deferential, because
specificity is how you respect an expert reader.

## Tone flex by context

| Context | Tone |
| --- | --- |
| Success / celebration | Matter-of-fact. State what happened and what is now true. No exclamation. |
| Routine action | The default voice. Verb and object. |
| Error / failure | Calm, plain, blame-free. Name the situation, then the next step. |
| Destructive / high-stakes confirm | Most serious. Name what will change and what cannot be undone. No wit. |
| Waiting / loading | Brief, and say what is being answered rather than that something is happening. |

The one place tone must not warm up: a human decision point. "You ratify the
production ship" is the register's voice; "Ready to ship? 🚀" is not.

## Terminology

One concept, one word, everywhere. This table is the cross-surface vocabulary
invariant — the same terms appear in the canvas, the marketing zones, and the
documentation job groups.

| Concept | Use | Avoid |
| --- | --- | --- |
| A team taking this on | **the five stations, by name** — Evaluate · Prove it on real work · Win buy-in · Roll out a cohort · Make it the default | "onboarding", "journey", "funnel" |
| A point where a person decides | **"a person decides"**, and the specific decision as a verb phrase | any gate identifier; "approval gate"; "checkpoint" |
| The human-approved engineering contract | **"a spec and plan you approved"** | "the artifact", "the contract", "G-plan" |
| The merge decision | **"a pull request you merge"** | "PR gate", "merge approval" |
| The production decision | **"you ratify the production ship"** | "prod gate", "release approval", "go-live" |
| An installable unit of workflow | **"pack"** — defined in plain words before first use | "module", "plugin", "extension" |
| An ordered set of guides ending at a handoff | **"path"** | "track", "course", "curriculum" |
| The team's tracker | **"your tracker"** | naming a specific vendor in generic copy |
| The repository's queue of work | **"workspace"** | "backlog", "board" |

**The unresolved one, carried from the register.** "Pack" is
product-specific vocabulary in navigation on both surfaces, and the plain-language
floor bars unfamiliar jargon until it is defined. Nobody owns the one-sentence
definition or its placement. Recorded as an open question, not silently used.

## Do / don't

- ✅ "A spec and plan you approved before any code was written." — plain, exact,
  repeatable, and lifted from copy that already shipped.
- ✅ "Receives a report · sends nothing back." — states the limit as the feature.
- ❌ "G4 — you merge only when adversarial review is clean." — internal notation
  in adopter copy; unrepeatable to a budget holder.
- ❌ "Unlock seamless AI-powered delivery at scale." — every warning-signal word
  in one line, and it could be pasted onto any other product.
- ❌ "Oops! Something went wrong 😅" — blames nothing but tells the reader
  nothing, and the tone is wrong for the context.
