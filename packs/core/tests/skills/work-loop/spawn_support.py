"""The canonical process-spawn set, and the AST walks that use it.

Two test files need to agree about what "spawns a process" means:
`test_loop_concurrency.py` (nothing unbounded runs while `cmd_transition` holds the
state lock) and `test_loop_engine_no_child_python.py` (no child *Python* at all).
They previously each carried their own literal — `{"run", "Popen", "check_output",
"check_call"}` in one, the same four in the other — under a docstring claiming they
were shared "so the two cannot drift". They were not shared, and both were only the
`subprocess` half: an `os.system("git gc")` added under the lock passed both.

One definition, imported by both. Extending the set here tightens both scans at once,
which is the property the old comment claimed and did not have.

Stdlib only, no pytest import — this is support code, collected by neither runner.
"""

import ast

# `subprocess.<attr>` — the constructors that actually start a process. Omits pure
# helpers such as `list2cmdline`; `getoutput`/`getstatusoutput` ARE included,
# because they do start one.
SUBPROCESS_ATTRS = frozenset({
    "run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput",
})

# `os.<attr>` — the low-level half AC21 names. `system` and `popen` shell out;
# `posix_spawn*` and `spawn*` start a child directly; `exec*` replaces the image
# (still an unbounded external program); `fork`/`forkpty` create a child that the
# lock-holding parent then has to reason about.
OS_SPAWN_ATTRS = frozenset({
    "system", "popen",
    "posix_spawn", "posix_spawnp",
    "spawnl", "spawnle", "spawnlp", "spawnlpe",
    "spawnv", "spawnve", "spawnvp", "spawnvpe",
    "execl", "execle", "execlp", "execlpe",
    "execv", "execve", "execvp", "execvpe",
    "fork", "forkpty",
})

# Modules whose mere presence in the guard layer is the finding — dispatch through
# them is indirect, so absence is the only checkable property.
SPAWN_MODULES = frozenset({"subprocess", "multiprocessing", "socket"})

# Which attribute set belongs to which module name.
_BY_MODULE = {"subprocess": SUBPROCESS_ATTRS, "os": OS_SPAWN_ATTRS}


def spawn_calls(node):
    """Yield `(label, call_node)` for every process-spawning call under `node`.

    `label` is the source-level form, e.g. `subprocess.run` or `os.system`, so a
    failure message names what it found rather than a line number alone.
    """
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        fn = child.func
        if not (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name)):
            continue
        attrs = _BY_MODULE.get(fn.value.id)
        if attrs and fn.attr in attrs:
            yield f"{fn.value.id}.{fn.attr}", child


def functions_in(tree):
    """Map name -> FunctionDef for every top-level-reachable function in `tree`.

    Nested and method definitions collapse onto their bare name. That is coarse in
    the safe direction: a collision can only make the reachable set *larger*, never
    hide a spawn that is genuinely reachable.
    """
    return {
        n.name: n
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def reachable_from(tree, roots):
    """Names of functions reachable from `roots` by direct same-module calls.

    Intentionally conservative about what it can resolve: only `name(...)` and
    `self.name(...)` edges. Indirect dispatch (a table of callables, `getattr`) is
    invisible, so a caller must not read a small reachable set as proof of absence
    without also asserting the walk traversed something — see
    `test_the_guard_path_cannot_reach_lint_spec_status_git_calls`, which pins the
    unreachable set as well as the reachable one.
    """
    funcs = functions_in(tree)
    seen, queue = set(), [r for r in roots if r in funcs]
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        for child in ast.walk(funcs[name]):
            if not isinstance(child, ast.Call):
                continue
            fn = child.func
            callee = None
            if isinstance(fn, ast.Name):
                callee = fn.id
            elif isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) \
                    and fn.value.id == "self":
                callee = fn.attr
            if callee in funcs and callee not in seen:
                queue.append(callee)
    return seen
