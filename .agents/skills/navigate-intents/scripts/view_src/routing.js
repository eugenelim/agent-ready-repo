  // --------------------------------------------------------------- routing
  function question(key) {
    for (var i = 0; i < QUESTIONS.length; i++) { if (QUESTIONS[i].key === key) { return QUESTIONS[i]; } }
    return QUESTIONS[0];
  }
  function parseRoute() {
    var p = new URLSearchParams(location.hash.replace(/^#/, ''));
    var route = {};
    ROUTE_KEYS.forEach(function (k) { route[k] = p.get(k) || ''; });
    route.q = question(route.q).key;
    // Only the non-default offered choices are kept; anything else reads as the default.
    route.dir = route.dir === 'dependents' || route.dir === 'both' ? route.dir : '';
    route.show = route.show === 'open' || route.show === 'done' ? route.show : '';
    route.group = route.group === 'capability' ? 'capability' : '';
    route.owner = ownerChoiceValid(route.owner) ? route.owner : '';
    route.steps = route.steps === '2' || route.steps === '3' || route.steps === 'all' ? route.steps : '';
    return route;
  }
  function hashFor(over) {
    var r = Object.assign({}, current, over);
    var p = new URLSearchParams();
    ROUTE_KEYS.forEach(function (k) { if (r[k]) { p.set(k, r[k]); } });
    return '#' + p.toString();
  }
  function replaceRoute(over) {
    history.replaceState(null, '', hashFor(over));
    handleRoute();
  }
  // A link to a question starts from no other choice, but keeps the owner choice it is given.
  function questionHash(key, owner) {
    var over = {};
    ROUTE_KEYS.forEach(function (k) { over[k] = ''; });
    over.q = key;
    over.owner = owner || '';
    return hashFor(over);
  }
