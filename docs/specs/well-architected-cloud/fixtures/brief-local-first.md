# Dogfood brief — founder starting local-first

> **Fixture for `well-architected-cloud` manual QA.** Exercises the local-first
> provider-class on-ramp. Referenced by path so the gesture is replayable.

## The brief

I'm a solo founder building a **scheduling app**. Right now everything runs on my
laptop: a single web process, a local Postgres, uploaded files saved to a folder,
secrets in a `.env`, and I test against `http://localhost`. It works for me and
two design-partner customers I onboarded manually.

I want to **get it in front of real users** without over-building. What does my
architecture need to look like to go from "runs on my laptop" to "real people can
sign up", and how do I get there without boiling the ocean?

Constraints: solo, limited time, limited money, don't want to prematurely adopt a
big cloud platform.

---

## Expected observables (QA scaffolding — not part of the brief)

- `architect-design` treats **local-first as a legitimate starting topology**,
  not a mistake to scold.
- Names the **local→production delta** (`local-dev.md`): what localhost fakes
  that production must supply — **TLS + real domain**, **real secrets store**, a
  **durable data tier** (backups + restore), **object storage** for uploads,
  **observability**, and a **scaling/availability** story.
- Names a **graduation path** to a chosen provider class (hyperscaler or
  primitives) and **what becomes real first** (usually TLS + secrets + durable
  data before CDN/multi-region).
- Prescribes **no local toolchain** — no docker-compose recipe, no specific
  images, no named dev dependency. Stays at architecture altitude.
- The graduation *order* (how much availability before launch) is surfaced as a
  **judgment** call, not baked into a number.
