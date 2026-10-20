
  // Hand-over prompts: one fixed sentence per next-step rule, with only the
  // record's checked file path filled in.  Nothing else from a record is used.
  var HANDOVER_TEMPLATES = {
    3: ['Use the work-loop skill to continue building ', '.'],
    4: ['Use the work-loop skill to implement ', '.'],
    5: ['Use the new-spec skill to finish the spec at ', '.'],
    6: ['Use the author-delivery-brief skill in continue mode on ', '.'],
    7: ['Use the intent skill to decompose ', '.'],
    9: ['Use the close-work skill to check whether ', ' can close.'],
    10: ['Use the intent skill to keep shaping ', '.']
  };
  var PATH_PREFIXES = {
    spec: 'docs/specs/',
    brief: 'docs/product/briefs/',
    intent: 'docs/product/intents/'
  };
  var PATH_MAX_LENGTH = 200;
  var PATH_SEGMENT = /^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$/;

  // True only for a path the prompt may carry; a failing path is never repaired.
  function isSafePath(type, path) {
    if (typeof path !== 'string' || path.length > PATH_MAX_LENGTH) { return false; }
    if (typeof type !== 'string' || !Object.prototype.hasOwnProperty.call(PATH_PREFIXES, type)) {
      return false;
    }
    if (path.indexOf(PATH_PREFIXES[type]) !== 0) { return false; }
    if (path.slice(-3) !== '.md') { return false; }
    var segments = path.split('/');
    for (var i = 0; i < segments.length; i++) {
      if (!PATH_SEGMENT.test(segments[i])) { return false; }
    }
    return true;
  }

  // null: the rule has no prompt.  { refused: true }: the path failed the test.
  function handoverPrompt(type, rule, path) {
    if (!Object.prototype.hasOwnProperty.call(HANDOVER_TEMPLATES, rule)) { return null; }
    if (!isSafePath(type, path)) { return { refused: true }; }
    var parts = HANDOVER_TEMPLATES[rule];
    return { prompt: parts[0] + '`' + path + '`' + parts[1] };
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { escapeDisplay: escapeDisplay, handoverPrompt: handoverPrompt };
  }
  if (typeof document === 'undefined') { return; }

