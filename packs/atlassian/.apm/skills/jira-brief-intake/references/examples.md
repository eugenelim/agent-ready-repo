# Jira intake examples

## One shippable behavior

A Story with one bounded behavior emits a normalized envelope with its trusted
issue key and `updated` value, then lets `work-intake` choose the spec route.

## One coherent multi-spec outcome

An Epic may supply several behaviors. It becomes brief-shaped only when the
content states one coherent outcome; the Epic type is only a hint.

## A collection

A board, sprint, or JQL selection with unrelated outcomes stays separate or
view-only. The adapter asks when that distinction is ambiguous.

## A claimed defect

A Bug routes to defect handling only when it cites durable expected behavior.
Without that evidence, the normalized record retains the gap and does not
invent a contract.
