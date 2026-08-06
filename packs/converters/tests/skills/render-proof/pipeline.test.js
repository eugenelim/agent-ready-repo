'use strict';

// run with: node pipeline.test.js  (from packs/converters/tests/skills/render-proof/)
// Probes A2UI v0_9 imports and verifies the buildMessages shape.
// Note: A2uiSurface SSR (renderToStaticMarkup/renderToReadableStream) is confirmed
// incompatible due to useSyncExternalStore missing getServerSnapshot; the render-proof
// skill uses the Risk #1 fallback (dangerouslySetInnerHTML). This probe verifies the
// package imports and the message-pair shape that would have been used in the pipeline.
const assert = require('assert');
const fs = require('fs');
const path = require('path');

// This suite requires @a2ui/* directly, and Node resolves node_modules by
// walking up from the *requiring* file — which, since tests live outside the
// runtime payload (ADR-0071), no longer passes through the skill. Put the
// skill's node_modules on this module's resolution path, and fail loudly if
// it is absent: `module.paths.unshift` of a missing directory is a silent
// no-op, after which Node falls through to the ancestor chain, $NODE_PATH and
// $HOME/node_modules and could bind some other copy.
const SKILL_MODULES = path.resolve(
  __dirname, '../../../.apm/skills/render-proof/node_modules');
if (!fs.existsSync(SKILL_MODULES)) {
  throw new Error(
    `render-proof node_modules not found at ${SKILL_MODULES} — ` +
    'check the depth, then run `npm install` in the skill directory.');
}
module.paths.unshift(SKILL_MODULES);

async function run() {
  // Probe A2UI v0_9 import (must not throw on browser globals)
  const a2ui = require('@a2ui/react/v0_9');      // (a) no throw = pass
  const core = require('@a2ui/web_core/v0_9');   // (b) no throw = pass
  assert(typeof a2ui.A2uiSurface !== 'undefined', 'A2uiSurface not exported from @a2ui/react/v0_9');
  assert(typeof a2ui.MarkdownContext !== 'undefined', 'MarkdownContext not exported from @a2ui/react/v0_9');
  assert(typeof core.MessageProcessor === 'function', 'MessageProcessor not a function in @a2ui/web_core/v0_9');

  // Snapshot: message pair shapes — must test production-built objects, not test-local literals
  const { buildMessages } = require('../../../.apm/skills/render-proof/scripts/render-proof.js');
  const [prodCreate, prodUpdate] = buildMessages('# Hello');
  assert(Object.keys(prodCreate)[0] === 'createSurface', 'createSurface object-key shape wrong');
  assert(typeof prodCreate.createSurface.id === 'string', 'createSurface.id not a string');
  assert(Object.keys(prodUpdate)[0] === 'updateComponents', 'updateComponents object-key shape wrong');
  const comp = prodUpdate.updateComponents.components[0];
  assert(comp.component === 'Text', 'component type not Text');
  assert(typeof comp.text === 'string', 'component text not a string');
  assert(comp.text === '# Hello', 'component text must be the input markdown string');

  console.log('All pipeline tests pass');
}
run().catch(e => {
  if (e.message && e.message.includes('browser')) {
    console.error('SURFACE: A2UI SSR incompatible — browser globals at import time. Surface to human.');
  } else {
    console.error(e);
  }
  process.exit(1);
});
