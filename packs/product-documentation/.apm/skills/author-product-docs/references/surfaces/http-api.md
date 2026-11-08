# HTTP or RPC API documentation

Evidence narrow: two large vendors in one cohort (Stripe for payments, Twilio for messaging), two OpenAPI rendering tools, and style guides. Small internal APIs, single-language APIs, and APIs with no sandbox are not covered. **No verified, named public product with spec-only docs was found.** Read each rule as a default plus its condition.

Load this file only when surface discovery names an HTTP or RPC API.

## First screen

**Default:** name the task and say what the reader will have at the end.[^1][^3] Ask for the reader's language only when the API supports more than one; a single-language API has nothing to ask.

## First reader action

**Default:** a quickstart that ends in one real request. Stripe ends with a test payment visible in its Dashboard; Twilio ends with one sent SMS.[^1][^3]

**Option:** run that request against a sandbox. APIs that touch real money, devices, or data may have none; then end on a request the reader can inspect without side effects. Do not state a time target.

## Sample style

**Default:** include examples on every operation.[^2][^6] Show a real-looking response object, use placeholders for secrets, and say what each placeholder is.[^2][^3]

## Reference shape

**Default:** the same entry shape for every endpoint. Stripe object pages open with a sample object, then an attribute list; Twilio resource pages list operations, a properties table, then one section per operation with parameters, examples, and a sample response.[^2][^6]

**Default:** auth, errors, limits, and pagination are documented, on one page that endpoint entries link to.

**Option:** collapse nested fields behind links and give each field a deep link (Stripe).[^2] Collapsed content is hidden from search and print, so keep the field names visible.

**Do not resolve:** generated versus hand-written reference. Generate when a contract file exists and is annotated; hand-write when it is not. Add hand-written guides either way.

## Troubleshooting

**Default:** an error catalogue with one entry per stable code, worded as cause and next step, linked from the error payload. Stripe's failed requests carry a `doc_url`; Twilio gives each code a page with Description, Possible causes, and Possible solutions.[^4][^5] Stripe's table is two columns with cause and action in one sentence, and some rows state no action, so write the next step for every row.

## Failures to refuse

Stale or missing examples, errors, auth steps, or limits, per the style guides and a 2015 survey of developers (read as a search summary only).[^7]

**Named example:** Kubernetes issue 41956 asks for examples in the auto-generated API reference; it was closed "not planned" on 2024-03-24.[^8] One person's complaint, not a verdict on the product. Do not use this as proof that generated reference fails.

## Sources

[^1]: Stripe, Build a custom checkout page, https://docs.stripe.com/payments/quickstart, accessed 2026-11-06. Confidence: medium (vendor cohort with Twilio).
[^2]: Stripe, The Charge object, https://docs.stripe.com/api/charges/object, accessed 2026-11-06. Confidence: medium.
[^3]: Twilio, SMS developer quickstart, https://www.twilio.com/docs/messaging/quickstart, accessed 2026-11-06 (summarising fetch). Confidence: medium; its per-language drift is cosmetic (a mislabelled code fence and uneven step numbers).
[^4]: Stripe, Error codes, https://docs.stripe.com/error-codes, accessed 2026-11-06 and re-opened. Confidence: high for the `doc_url` link and two-column table.
[^5]: Twilio, 30007: Message filtered, https://www.twilio.com/docs/api/errors/30007, accessed 2026-11-06 and re-opened. Confidence: high for the entry layout.
[^6]: Twilio, Message resource, https://www.twilio.com/docs/messaging/api/message-resource, accessed 2026-11-06 (first 100,000 of 160,156 characters). Confidence: medium.
[^7]: Google developer documentation style guide, API reference comments, https://developers.google.com/style/api-reference-comments, accessed 2026-11-06. Confidence: medium. Failure survey: Uddin and Robillard, How API Documentation Fails, IEEE Software 2015, https://www.cs.mcgill.ca/~martin/papers/ieeesw2015.pdf (PDF unreadable; figures from indexed records). Confidence: low.
[^8]: Kubernetes website issue 41956, https://github.com/kubernetes/website/issues/41956, accessed 2026-11-06. Confidence: low (one issue).
