# How to author a browser-automation skill

**Use this when:** You are writing a skill that drives a web browser — to read, interact with, or extract data from a site that has no usable API.
**Prerequisites:** `playwright-cli` installed; a skill directory under `packs/<pack>/.apm/skills/<name>/` with a `SKILL.md`; familiarity with [how to author a skill](author-a-skill.md).
**Result:** A skill whose browser sessions survive across invocations, whose auth is robust to SSO and device-certificate policies, and whose data layer decouples expensive browser scans from reasoning steps.

---

## Persistent profile vs. storageState

Playwright's `storageState()` serialises cookies and localStorage to a JSON file — it works for cookie-based auth (most public-facing SaaS). It does **not** work when:

- The site uses Microsoft Entra SSO with **Conditional Access** (device compliance is verified against a certificate stored in the OS keychain — it cannot be exported to JSON).
- Auth state lives in the browser's **encrypted credential store** rather than plain cookies or localStorage.
- You need the **signed system Chrome binary** to access a macOS keychain entry (bundled Playwright Chromium is unsigned and cannot reach it).

In those cases, use a **persistent profile directory** instead.

| Method | When to use |
|--------|-------------|
| `storageState` | Cookie/token auth; CI-friendly; fully headless |
| Persistent profile | Entra PRT, Conditional Access, encrypted credential store, keychain-bound auth |

## Persistent-profile auth handoff

The first-run pattern: open the system Chrome browser **headed**, let the user log in manually, then close. The profile directory (including PRT, cookies, device-compliance state) persists to disk. Every subsequent run opens the same profile headless.

**Why system Chrome:** Only `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` is signed with the identity that macOS Keychain trusts for credential-store access. Playwright's bundled Chromium is unsigned.

```typescript
import { chromium } from 'playwright';
import * as path from 'path';
import * as os from 'os';

const PROFILE_DIR = path.join(os.homedir(), '.agent-commander', '<pack>', 'chrome-profile');
const CHROME_PATHS = [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  path.join(os.homedir(), 'Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
];

export function findSystemChrome(): string {
  for (const p of CHROME_PATHS) {
    if (require('fs').existsSync(p)) return p;
  }
  throw new Error('Google Chrome not found. Install it from https://www.google.com/chrome/');
}

// First-run: open headed for the user to sign in
export async function authenticateInteractive(): Promise<void> {
  const context = await chromium.launchPersistentContext(PROFILE_DIR, {
    executablePath: findSystemChrome(),
    headless: false,
    args: ['--no-first-run', '--no-default-browser-check'],
  });
  const page = await context.newPage();
  await page.goto('https://example.yourorg.com/');
  // Prompt: wait for the user to complete login
  const readline = require('readline').createInterface({ input: process.stdin, output: process.stdout });
  await new Promise<void>(resolve => readline.question(
    'Log in, wait until the main screen is fully loaded, then press Enter…\n', () => { readline.close(); resolve(); }
  ));
  await context.close();
}

// Subsequent runs: reuse profile
export async function playwrightRun<T>(
  fn: (page: import('playwright').Page) => Promise<T>,
  opts: { headed?: boolean } = {}
): Promise<T> {
  const context = await chromium.launchPersistentContext(PROFILE_DIR, {
    executablePath: findSystemChrome(),
    headless: !opts.headed,
    args: ['--no-first-run'],
  });
  const page = await context.newPage();
  try { return await fn(page); }
  finally { await context.close(); }
}
```

**Profile directory convention:** always `~/.agent-commander/<pack>/chrome-profile/`. Never inside the repo.

## Session check

Before performing work, verify the session is still valid. On a page that requires auth, a failed session redirects to a login URL:

```typescript
export async function checkSession(): Promise<'ok' | 'needs-login'> {
  return playwrightRun(async page => {
    await page.goto('https://example.yourorg.com/inbox', { waitUntil: 'domcontentloaded' });
    try {
      await page.waitForSelector('[data-app-section="main"]', { timeout: 8000 });
      return 'ok';
    } catch {
      const url = page.url();
      return url.includes('login') || url.includes('microsoftonline') ? 'needs-login' : 'ok';
    }
  });
}
```

Include a session check step in the skill body. On `needs-login`, run the `office365-setup` skill (or your pack's equivalent setup skill) rather than silently failing.

## Bearer token interception

Many internal portals issue a Bearer JWT on page load that you can capture to call their REST API directly — without requiring an OAuth app registration.

**Critical:** register the handler **before** `page.goto()`. The token arrives in the first authenticated request on page load, so a handler installed after `goto` will miss it.

```typescript
export function captureToken(page: import('playwright').Page, hostname: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`Token capture timeout (${hostname})`)), 20000);
    const handler = (req: import('playwright').Request): void => {
      const auth = req.headers()['authorization'] ?? '';
      if (auth.startsWith('Bearer ') && req.url().includes(hostname)) {
        clearTimeout(timer);
        page.off('requestfinished', handler);
        resolve(auth.slice(7));
      }
    };
    page.on('requestfinished', handler);
  });
}

// Usage:
const tokenPromise = captureToken(page, 'example.yourorg.com');
await page.goto('https://example.yourorg.com/inbox');
const token = await tokenPromise;
```

**Vendor caveat — Teams:** Teams uses a `skypetoken_asm` cookie on `.asm.skype.com` rather than a standard `Authorization: Bearer` header. The cookie is set asynchronously after page load; use polling with a deadline:

```typescript
async function resolveTeamsSkypeToken(page: import('playwright').Page, timeoutMs = 10000): Promise<string> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    // do NOT filter by URL — the cookie domain is .asm.skype.com, not the Teams host
    const cookies = await page.context().cookies();
    const token = cookies.find(c => c.name === 'skypetoken_asm')?.value;
    if (token) return token;
    await page.waitForTimeout(500);
  }
  throw new Error('Teams skypetoken_asm not found within timeout');
}
```

## Two-mode Playwright usage

The `playwright-cli` tool has two interaction modes. Pick based on what you need to do.

**CLI commands** — for single actions where one command produces one result:

```bash
playwright-cli -s=<session> open "https://…"
playwright-cli -s=<session> snapshot           # returns ARIA accessibility tree with element refs
playwright-cli -s=<session> click "e42"        # ref from snapshot — valid until next page change
playwright-cli -s=<session> fill "getByLabel('Search')" "query"   # locator — stable across page changes
playwright-cli -s=<session> close
```

Use **refs** (`e42`) when you want to act on exactly the element the snapshot showed. Use **locators** (`getByLabel(…)`, `getByRole(…)`) when you want a selector that survives navigation and re-renders.

**`run-code`** — for loops, conditional logic, or structured data extraction:

```bash
playwright-cli --raw -s=<session> run-code "async page => {
  const items = await page.locator('[role=\"option\"]').evaluateAll(opts =>
    opts.slice(0, 25).map(o => ({ id: o.id, label: o.getAttribute('aria-label') || '' }))
  );
  return JSON.stringify(items);
}"
```

`--raw` returns only the return value of the async function — no metadata wrapper. Use it whenever the skill needs to parse the output as JSON.

**Rule of thumb:** if you'd write a `for` loop to drive the browser, use `run-code`. If you'd write a single line, use a CLI command.

## `ui-patterns.md` — live-probe maintenance

Browser UIs change. Selectors that work today may not work after an app update. Keep a `references/ui-patterns.md` file in the skill directory and treat it as a living document:

```markdown
## <App name> UI selectors

Last confirmed: YYYY-MM-DD against <version/build if known>

| Selector | Status | Notes |
|----------|--------|-------|
| `[role="listbox"]` | ✓ | Inbox message list |
| `[aria-label="Reply"]` | ✓ | Reply button in thread view |
| `[data-app-section="compose"]` | ✗ | Not present in current build |
| `[data-testid="send-btn"]` | [?] | Seen in dev builds; unconfirmed in prod |

## Selector update log

| Date | Change |
|------|--------|
| YYYY-MM-DD | Initial live probe (47/62 confirmed). Core inbox/toolbar confirmed. |
| YYYY-MM-DD | Post-update probe (55/62). Compose selectors changed — updated above. |
```

Status annotations:
- `✓` — confirmed working in a recent live probe
- `✗` — not present in the current build (may be org-specific or version-gated)
- `[?]` — seen in some environments but not confirmed in the canonical environment

Run a live probe (a quick `snapshot` pass through the main surfaces) whenever the app has a major update. Document the ceiling: `55/62 — practical ceiling; remaining 7 failures are org-build-absent`.

## Probe files as data layer

Browser scans are expensive — they drive a browser, navigate pages, and extract data. Decouple the scan from the reasoning step by writing scan results to timestamped JSON files:

```
~/.agent-commander/<pack>/probes/
  <timestamp>-senders.json
  <timestamp>-threads.json
  <timestamp>-queue.json
```

The skill checks probe freshness before deciding whether to re-scan:

```bash
LATEST=$(ls -t ~/.agent-commander/<pack>/probes/*-threads.json 2>/dev/null | head -1)
if [ -z "$LATEST" ]; then echo "no-probe"; exit 0; fi
AGE=$(( ($(date +%s) - $(stat -f %m "$LATEST")) / 3600 ))
[ "$AGE" -ge 4 ] && echo "stale" || echo "fresh"
```

Rules:
- One scan writes one file with a timestamp prefix — never overwrite the previous file.
- The skill reads the most recent file that meets the freshness threshold.
- The agent reasons from the structured JSON, never from raw HTML.
- Probe files live outside the repo (`~/.agent-commander/…`), never inside it.

## Config and data paths

All user-specific data lives outside the repo:

```
~/.agent-commander/<pack>/
  config.toml         # user config (API base URLs, display prefs)
  chrome-profile/     # persistent browser profile
  probes/             # timestamped scan outputs
```

Scripts resolve these paths from `os.homedir()` or `os.homedir()` equivalents — never from `__dirname` or a repo-relative path. This keeps the repo clean and the data portable.
