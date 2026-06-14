# Microcopy formulas — the recurring UI states

Four UI states recur in almost every product. Each has a **formula** that makes
the copy do its job, and a **before → after** that shows the formula at work. The
formulas are framework-agnostic — they shape words, not widgets. The same
formula-thinking extends to confirmations, notifications, and tooltips; these four
are the load-bearing core.

Filter every string through the voice chart (`references/voice-axes.md`) for
position, and the content checklist (`references/content-checklist.md`) before it
ships.

## Error

**Formula:** *what happened, plainly* + *what to do next*. **Blame-free** — describe
the situation, never fault the user. Drop the error code and the apology; lead with
the recovery.

- ❌ **Before:** "Error: invalid input. You entered an incorrect verification code."
- ✅ **After:** "That code has expired. Request a new one and we'll send it right away."

Why: the "before" blames the user and stops at the diagnosis. The "after" states
the situation neutrally and hands the user the next action. An error the user
can't act on is a dead end.

## Empty state

**Formula:** *orient* (what belongs here, in one line) + *invite the first action*.
An empty state is the user's first impression of a feature — never a blank panel or
a lone illustration.

- ❌ **Before:** "No items." / a graphic with no words
- ✅ **After:** "No invoices yet. Create your first one to start tracking what you're owed." + a **Create invoice** button

Why: the "before" confirms emptiness and stops. The "after" tells the user what
this space is for and gives them the one action that fills it.

## Button / CTA

**Formula:** *verb + object* that names the user's goal. Avoid generic
**Submit / OK / Yes** — they make the user re-read the surrounding copy to know
what they're agreeing to. The button should make sense read on its own.

- ❌ **Before:** "Submit" / "OK"
- ✅ **After:** "Send invite" / "Delete 3 files"

Why: a specific verb-object button is self-describing and survives being read out
of context (screen readers, confirmation dialogs). For a destructive action, name
the object and the count so the consequence is unmistakable.

## Label

**Formula:** concise noun phrase, **keyword front-loaded**, scannable, **one term
per concept** (consistent with the voice chart's terminology list). Labels are
scanned, not read — the first word carries the meaning.

- ❌ **Before:** "Please enter the email address you'd like to use" / "Date that the project was created on"
- ✅ **After:** "Email" / "Created"

Why: users scan labels; a sentence-shaped label slows that scan. Front-load the
keyword and cut the framing words. Keep the term identical everywhere the concept
appears — a field called "Email" here must not be "E-mail address" two screens on.
