  // ----------------------------------------------------------- the lists
  var STAGES = [['spec', 'Implementing'], ['spec', 'Approved'], ['brief', 'Executing'],
    ['brief', 'Ready'], ['intent', 'Accepted']];

  function hasNothingBeneath(id) {
    var r = rec(id);
    return r !== null && arr(r.children).length === 0 && arr(r.briefs).length === 0 &&
      arr(r.specs).length === 0;
  }
  function stageOf(id) {
    var type = typeOf(id);
    var word = statusWord(id);
    for (var i = 0; i < STAGES.length; i++) {
      if (STAGES[i][0] === type && STAGES[i][1] === word) {
        return (type !== 'intent' || hasNothingBeneath(id)) ? i : -1;
      }
    }
    return -1;
  }
  function startableIds() {
    var ids = [];
    openById.forEach(function (_it, id) { if (stageOf(id) >= 0) { ids.push(id); } });
    return ids.sort(function (a, b) { return (stageOf(a) - stageOf(b)) || byName(a, b); });
  }
  function openCount(id) { return (beneath.get(id) || []).length; }
  function capabilityIds() {
    return recordIds.filter(function (id) {
      return (rec(id).level || '') === 'capability' && openCount(id) > 0;
    }).sort(function (a, b) { return (openCount(b) - openCount(a)) || byName(a, b); });
  }
  function noParentIds() {
    if (deliveryUnavailable()) { return []; }
    return arr(data.outstanding.no_parent).filter(function (it) {
      return isObj(it) && isStr(it.id) && nodes.has(it.id);
    }).map(function (it) { return it.id; });
  }
  function brokenEntries() {
    var list = [];
    data.edges.forEach(function (e) {
      if (e.state) { list.push({ holder: e.from, edge: e }); }
    });
    if (!deliveryUnavailable()) {
      recordIds.forEach(function (id) {
        arr(rec(id).delivery_diagnostics).forEach(function (d) {
          if (isObj(d)) { list.push({ holder: id, diag: d }); }
        });
      });
    }
    // Dependency entries follow a holder's inherited ones; the stable sort keeps that order.
    recordIds.forEach(function (id) {
      depEntriesOf(id).forEach(function (entry) { list.push(entry); });
    });
    return list.sort(function (a, b) { return byName(a.holder, b.holder); });
  }
  // A dependency fault is held by its source, a cycle by each member; only an intent with a
  // record (so, in scope) holds one, and outstanding availability does not matter.
  function depEntriesOf(id) {
    if (rec(id) === null) { return []; }
    var list = [];
    (depPointers.get(id) || []).forEach(function (d) {
      if (d.state !== 'outside_scope') { list.push({ holder: id, dep: d }); }
    });
    (depCycles.get(id) || []).forEach(function (c) { list.push({ holder: id, cycle: c }); });
    return list;
  }

  function questionCount(key) {
    if (key === 'browse') { return recordIds.length; }
    if (key === 'broken') { return brokenEntries().length; }
    if (deliveryUnavailable()) { return null; }
    if (key === 'next') { return startableIds().length; }
    if (key === 'capabilities') { return capabilityIds().length; }
    return noParentIds().length;
  }

