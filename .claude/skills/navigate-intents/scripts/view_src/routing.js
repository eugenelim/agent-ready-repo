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
  function questionHash(key) {
    var over = { q: key, node: '', search: '' };
    FILTER_KEYS.forEach(function (k) { over[k] = ''; });
    return hashFor(over);
  }

