  // ------------------------------------------------------------ small parts
  function helpId(kind, key) { return 'help-' + kind + '-' + key; }
  function labelChip(table, kind, key) {
    if (!isStr(key) || own(table, key) === undefined) { return null; }
    var chip = el('span', 'chip label-' + kind, key);
    // The key stays the visible text; its plain-words sentence is the chip's description.
    chip.setAttribute('aria-describedby', helpId(kind, key));
    return chip;
  }
  function stateChip(key) { return labelChip(STATE_HELP, 'state', key); }
  function trustChip(key) { return labelChip(TRUST_HELP, 'trust', key); }
  function formChip(key) { return labelChip(FORM_HELP, 'form', key); }

  function nodeLink(id, cls) {
    var a = el('a', cls || 'node-link', displayName(id));
    a.setAttribute('href', hashFor({ node: id }));
    a.setAttribute('data-node', id);
    return a;
  }
  function outsideRef(id) {
    var s = el('span', 'outside');
    add(s, el('span', 'value', id));
    add(s, el('span', 'note-inline', 'outside this export'));
    return s;
  }
  function nodeRef(id, cls) { return nodes.has(id) ? nodeLink(id, cls) : outsideRef(id); }
  // An intent in this export is its display-name link with its state mark; any other is its
  // node id as plain text marked "outside this export".
  function namedIntent(id) {
    if (!nodes.has(id)) { return outsideRef(id); }
    var s = el('span', 'named');
    add(s, nodeLink(id, 'node-link'));
    text(s, ' ');
    add(s, stateMark(id));
    return s;
  }

  function edgeValue(e) {
    if (isStr(e.value)) { return e.value; }
    var basis = e.basis;
    if (isObj(basis) && Array.isArray(basis.values)) {
      return basis.values.map(function (v) { return isObj(v) && isStr(v.value) ? v.value : ''; })
        .join(', ');
    }
    return '';
  }

  function edgeItem(e, withSource) {
    var li = el('li', 'edge');
    var line = add(li, el('div', 'edge-line'));
    if (withSource) { add(line, nodeRef(e.from, 'node-link')); }
    add(line, el('span', 'field', isStr(e.field) ? e.field : ''));
    if (e.state) {
      add(line, el('code', 'value', edgeValue(e)));
      var sc = stateChip(e.state);
      add(line, sc || el('span', 'value', String(e.state)));
    } else if (isStr(e.to)) {
      add(line, nodeRef(e.to, 'node-link'));
    } else {
      add(line, el('code', 'value', edgeValue(e)));
    }
    var tc = trustChip(e.trust_class);
    if (tc) { add(line, tc); }
    return li;
  }

  function describe(o) {
    if (!isObj(o)) { return String(o); }
    return Object.keys(o).sort().map(function (k) {
      var v = o[k];
      return k + ': ' + (isStr(v) ? v : JSON.stringify(v));
    }).join('; ');
  }

  function relationItem(rel) {
    var li = el('li', 'edge');
    var line = add(li, el('div', 'edge-line'));
    add(line, el('span', 'field', isStr(rel.type) ? rel.type : ''));
    [['intent', 'Intent'], ['brief', 'Brief'], ['spec', 'Spec']].forEach(function (pair) {
      var id = rel[pair[0]];
      if (!isStr(id)) { return; }
      add(line, el('span', 'part-name', pair[1]));
      add(line, nodeRef(pair[0] === 'intent' ? intentNodeId(id) : id, 'node-link'));
    });
    if (isStr(rel.route)) { add(line, el('span', 'value', 'route ' + rel.route)); }
    var tc = trustChip(rel.trust_class);
    if (tc) { add(line, tc); }
    return li;
  }

  function sourceBlock(id) {
    var wrap = el('p', 'source');
    var link = own(data.source_links, id);
    var n = nodes.get(id) || {};
    var url = isObj(link) && isStr(link.url) ? link.url : '';
    var kind = isObj(link) ? link.kind : '';
    var path = isObj(link) && isStr(link.path) ? link.path : (n.path || '');
    if ((kind === 'commit' || kind === 'latest') && url.indexOf(GITHUB_PREFIX) === 0) {
      var a = add(wrap, el('a', 'source-link', 'Open on GitHub'));
      a.setAttribute('href', url);
      a.setAttribute('rel', 'noopener noreferrer');
      add(wrap, el('span', 'value', path));
      if (kind === 'latest') {
        add(wrap, markEl('stale', 'may be newer than this export'));
      } else if (isStr(data.provenance.commit)) {
        add(wrap, el('span', 'note-inline', 'at commit ' + data.provenance.commit.slice(0, 12)));
      }
    } else {
      add(wrap, el('span', 'value', path));
      add(wrap, el('span', 'note-inline', 'no link available'));
    }
    return wrap;
  }

