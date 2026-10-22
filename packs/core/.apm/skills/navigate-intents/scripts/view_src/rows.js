  // ------------------------------------------------------------------ rows
  var contexts = new Map();
  function contextText(id) {
    var known = contexts.get(id);
    if (known === undefined) { known = buildContext(id); contexts.set(id, known); }
    return known;
  }
  function buildContext(id) {
    var type = typeOf(id);
    var label = own(TYPE_NAMES, type) || type;
    var r = rec(id);
    if (r) { label += ' \u00B7 ' + (r.level || 'unrecorded'); }
    var lists = ancestorLists(id);
    if (lists.length && lists[0].length && isObj(lists[0][0]) && isStr(lists[0][0].id)) {
      var up = lists[0][0].id;
      label += ' \u00B7 under ' + (nodes.has(up) ? displayName(up) : up + ' outside this export');
    }
    if (r && isObj(r.parent_edge) && r.parent_edge.state) {
      var st = r.parent_edge.state;
      label += ' \u00B7 refused parent: ' + (own(STATE_HELP, st) !== undefined ? st : 'unrecognised');
    }
    return label;
  }

  // The context is a string, or a node when part of it needs its own element (a diagnostic code).
  // A non-empty tag sits inside the name's cell, so it wraps under the name and stays in the link.
  function rowLink(id, mark, context, tag) {
    var a = el('a', 'row-link');
    a.setAttribute('href', hashFor({ node: id }));
    a.setAttribute('data-node', id);
    var name = add(a, el('span', 'c-name', displayName(id)));
    if (tag) { add(name, el('span', 'note-inline c-tag', tag)); }
    var state = add(a, el('span', 'c-state'));
    add(state, mark);
    if (isStr(context)) {
      add(a, el('span', 'c-context', context));
    } else {
      add(add(a, el('span', 'c-context')), context);
    }
    if (current !== null && current.node === id) { a.setAttribute('aria-current', 'true'); }
    return a;
  }
  function itemRow(id) {
    var li = el('li', 'row');
    add(li, rowLink(id, stateMark(id), contextText(id)));
    return li;
  }
  // A long list renders its first rows at once and the rest in later batches, so typing stays
  // responsive. Rows append below within their own list; a later group can shift down while
  // earlier batches land.
  var ROW_BATCH = 150;
  var listGeneration = 0;
  function rows(ids, build) {
    var make = build || itemRow;
    var ul = el('ul', 'rows');
    var generation = listGeneration;
    function fill(from) {
      if (generation !== listGeneration) { return; }
      var end = Math.min(ids.length, from + ROW_BATCH);
      for (var i = from; i < end; i++) { add(ul, make(ids[i])); }
      if (end < ids.length) { setTimeout(function () { fill(end); }, 0); }
    }
    fill(0);
    return ul;
  }

