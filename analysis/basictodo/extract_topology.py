#!/usr/bin/env python3
"""Dependency & topology extractor for legacy/basictodo.

Re-run:  python3 analysis/basictodo/extract_topology.py
Writes:  analysis/basictodo/topology.json, call-graph.mmd, data-lineage.mmd,
         critical-path.mmd — and prints a human summary.

Leaves are production source files (tests are excluded from the graph; they are
counted per leaf as `testRefs`). FastAPI route handlers are split out of api.py
into their own leaves so the cross-tier HTTP edges land on the exact endpoint.

Edge sources, per the three map principles:
  call      static imports (Python `ast`; TS/TSX import/export-from regex; CSS side-effect imports)
  dispatch  edges whose target is a variable or a framework hop, resolved before being drawn:
              - constructor DI: an argument bound to class C2 is passed into class C1, and C1
                actually uses the attribute it stores it in (`self.x.<...>` or `self.x()`)
              - module-level singletons: `service = create_todo_service()` -> return annotation
              - FastAPI router: app module -> each @app.<verb>(path) handler
              - "module:attr" string targets (uvicorn.run("backend.app.api.api:app"))
              - HTML <script src> -> TS entry module
              - HTTP: apiClient.<verb>(path) matched to FastAPI route templates, only for
                client methods that something actually calls
  read/write  code <-> storage, joined through the ORM mapping (database.py), not by name:
              session.query/get -> read, session.add/merge/delete -> write,
              <metadata>.create_all -> write (DDL), inspector.get_table_names -> read;
              TanStack Query cache keys: useQuery/getQueryData -> read,
              setQueryData/invalidateQueries -> write
Entry points come from deployment config: frontend/index.html, Playwright webServer
commands, GitHub Actions `run:` steps, and FastAPI route decorators (HTTP).
"""
from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYSTEM = HERE.name
ROOT = HERE.parents[1] / "legacy" / SYSTEM
DISPLAY = "basicToDo"

DOMAINS = [  # (id, display name, path regexes) — domains from /modernize-assess
    ("dom:fe-shell", "F1 · App shell & shared UI", [r"^frontend/index\.html$", r"^frontend/src/(main\.tsx|App\.tsx|App\.css|index\.css)$",
                                                     r"^frontend/src/components/(Header\.tsx|errors/|common/|ui/)", r"^frontend/src/lib/",
                                                     r"^frontend/src/hooks/useToast\.ts$", r"^frontend/src/config/queryClient\.ts$"]),
    ("dom:fe-todo-ui", "F2 · Todo feature UI", [r"^frontend/src/components/todos/"]),
    ("dom:fe-hooks", "F3 · Server-state hooks", [r"^frontend/src/hooks/queries/"]),
    ("dom:fe-api", "F4 · API client & contract types", [r"^frontend/src/services/", r"^frontend/src/config/env\.ts$", r"^frontend/src/types/"]),
    ("dom:be-boot", "B1 · Bootstrap & composition root", [r"^backend/app/(main|factory)\.py$", r"^backend/scripts/"]),
    ("dom:be-api", "B2 · HTTP API", [r"^backend/app/api/", r"^route:"]),
    ("dom:be-schemas", "B3 · Schemas (DTOs)", [r"^backend/app/schemas/"]),
    ("dom:be-service", "B4 · ToDo service", [r"^backend/app/business_logic/(todo_service|decorators|exceptions)\.py$", r"^backend/app/business_logic/builders/"]),
    ("dom:be-validation", "B5 · Validation & sanitization", [r"^backend/app/business_logic/validators/"]),
    ("dom:be-persistence", "B6 · Persistence", [r"^backend/app/data_access/", r"^backend/app/models/"]),
    ("dom:be-platform", "B7 · Platform (logging, config)", [r"^backend/app/(logger|config)\.py$"]),
]

READ_OPS = {"query", "get", "execute", "scalars", "scalar"}
WRITE_OPS = {"add", "add_all", "merge", "delete", "bulk_save_objects", "bulk_insert_mappings"}
HTTP_VERBS = {"get", "post", "put", "delete", "patch"}


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


# ─────────────────────────────── discovery ───────────────────────────────
def discover():
    py_prod = sorted(p for d in ("backend/app", "backend/scripts") for p in (ROOT / d).rglob("*.py"))
    fe_prod = sorted(p for p in (ROOT / "frontend/src").rglob("*")
                     if p.suffix in {".ts", ".tsx", ".css"} and "__tests__" not in p.parts
                     and "test" not in p.relative_to(ROOT / "frontend/src").parts[:1] and not p.name.endswith(".d.ts"))
    html = [ROOT / "frontend/index.html"] if (ROOT / "frontend/index.html").exists() else []
    py_tests = sorted((ROOT / "backend/tests").rglob("*.py"))
    fe_tests = sorted([p for p in (ROOT / "frontend/src").rglob("*") if p.suffix in {".ts", ".tsx"}
                       and ("__tests__" in p.parts or p.relative_to(ROOT / "frontend/src").parts[0] == "test")]
                      + list((ROOT / "frontend/e2e").glob("*.ts")))
    return py_prod, fe_prod, html, py_tests, fe_tests


def loc_counts(files: list[Path]) -> dict[str, int]:
    """Code lines per file via cloc (same tool as /modernize-assess); fallback: non-blank non-comment."""
    out: dict[str, int] = {}
    if shutil.which("cloc"):
        res = subprocess.run(["cloc", "--by-file", "--json", "--quiet", *[rel(f) for f in files]],
                             cwd=ROOT, capture_output=True, text=True)
        try:
            data = json.loads(res.stdout or "{}")
            for k, v in data.items():
                if isinstance(v, dict) and "code" in v and k not in ("header", "SUM"):
                    out[k.lstrip("./")] = v["code"]
        except json.JSONDecodeError:
            pass
    for f in files:
        out.setdefault(rel(f), simple_loc(f.read_text(encoding="utf-8", errors="replace").splitlines()))
    return out


def simple_loc(lines) -> int:
    return sum(1 for ln in lines if ln.strip() and not re.match(r"^\s*(#|//|/\*|\*)", ln))


# ─────────────────────────────── Python model ───────────────────────────────
class PyModel:
    def __init__(self, files: list[Path]):
        self.trees: dict[str, ast.Module] = {}
        self.modname: dict[str, str] = {}      # module name -> rel path
        for f in files:
            r = rel(f)
            self.trees[r] = ast.parse(f.read_text(encoding="utf-8"), filename=r)
            mod = r[:-3].replace("/", ".")
            self.modname[mod[:-9] if mod.endswith(".__init__") else mod] = r
        self.reexport: dict[str, dict[str, str]] = {}   # package file -> {name: defining file}
        self.passive: set[str] = set()                  # empty / docstring-only / pure re-export __init__
        self.alt_root: list[tuple[str, int, str]] = []  # imports resolved only via a sys.path hack
        for r, t in self.trees.items():
            if r.endswith("__init__.py") and self._is_passive(t):
                self.passive.add(r)
        for r in self.passive:
            for node in self.trees[r].body:
                if isinstance(node, ast.ImportFrom) and node.module:
                    tgt = self.resolve_mod(node.module, r, record=False)
                    for a in node.names:
                        if tgt:
                            self.reexport.setdefault(r, {})[a.asname or a.name] = tgt

    @staticmethod
    def _is_passive(t: ast.Module) -> bool:
        for n in t.body:
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                continue
            if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id == "__all__" for x in n.targets):
                continue
            return False
        return True

    def resolve_mod(self, name: str, importer: str, record=True, lineno=0) -> str | None:
        if name in self.modname:
            return self.modname[name]
        alt = "backend." + name   # scripts/init_db.py inserts backend/ on sys.path and imports `app.*`
        if alt in self.modname:
            if record:
                self.alt_root.append((importer, lineno, name))
            return self.modname[alt]
        return None

    def through_package(self, target: str, name: str) -> str:
        return self.reexport.get(target, {}).get(name, target)


def py_symbol_index(pm: PyModel):
    classes: dict[str, dict] = {}   # class name -> info
    funcs: dict[str, str] = {}      # top-level function name -> module
    returns: dict[str, str] = {}    # "func" / "Cls.method" -> returned class name
    def ann(a):
        if isinstance(a, ast.Name):
            return a.id
        if isinstance(a, ast.Attribute):
            return a.attr
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            return a.value
        return None
    for r, t in pm.trees.items():
        for n in t.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs[n.name] = r
                if ann(n.returns):
                    returns[n.name] = ann(n.returns)
            if isinstance(n, ast.ClassDef):
                info = {"module": r, "params": [], "attr_from_param": {}, "used": set(), "line": n.lineno}
                for m in n.body:
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if ann(m.returns):
                            returns[f"{n.name}.{m.name}"] = ann(m.returns)
                        if m.name == "__init__":
                            info["params"] = [a.arg for a in m.args.args[1:]]
                            for s in ast.walk(m):
                                if isinstance(s, ast.Assign) and isinstance(s.value, ast.Name):
                                    for tg in s.targets:
                                        if isinstance(tg, ast.Attribute) and isinstance(tg.value, ast.Name) and tg.value.id == "self":
                                            info["attr_from_param"][tg.attr] = s.value.id
                for s in ast.walk(n):
                    if isinstance(s, ast.Attribute) and isinstance(s.value, ast.Attribute) \
                            and isinstance(s.value.value, ast.Name) and s.value.value.id == "self":
                        info["used"].add(s.value.attr)
                    if isinstance(s, ast.Call) and isinstance(s.func, ast.Attribute) \
                            and isinstance(s.func.value, ast.Name) and s.func.value.id == "self":
                        info["used"].add(s.func.attr)
                classes[n.name] = info
    return classes, funcs, returns


# ─────────────────────────────── main extraction ───────────────────────────────
def main() -> int:
    if not ROOT.exists():
        print(f"error: {ROOT} not found", file=sys.stderr)
        return 1
    py_prod, fe_prod, html, py_tests, fe_tests = discover()
    pm = PyModel(py_prod)
    classes, funcs, returns = py_symbol_index(pm)
    locs = loc_counts(py_prod + fe_prod + html)

    leaves: dict[str, dict] = {}
    edges: dict[tuple[str, str, str], str] = {}     # (src, tgt, kind) -> via
    notes = defaultdict(list)                       # summary sections
    entry: dict[str, str] = {}                      # id -> provenance
    unresolved_dynamic: list[str] = []

    def add_edge(s, t, kind, via):
        if s and t and s != t:
            edges.setdefault((s, t, kind), via)

    # ── Python leaves (passive __init__ files are package markers, not modules) ──
    for f in py_prod:
        r = rel(f)
        if r in pm.passive:
            continue
        leaves[r] = {"id": r, "name": f.name, "kind": "module", "language": "python", "loc": locs.get(r, 0), "file": r}

    # ── FastAPI routes: split handlers out of the app module ──
    routes: dict[str, dict] = {}    # route id -> {method, path, func, module, line, regex}
    route_of_func: dict[tuple[str, str], str] = {}
    for r, t in pm.trees.items():
        apps = {tg.id for n in t.body if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
                and getattr(n.value.func, "id", None) == "FastAPI" for tg in n.targets if isinstance(tg, ast.Name)}
        if not apps:
            continue
        src_lines = (ROOT / r).read_text(encoding="utf-8").splitlines()
        handler_loc = 0
        for n in t.body:
            if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for d in n.decorator_list:
                if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr in HTTP_VERBS \
                        and getattr(d.func.value, "id", None) in apps and d.args and isinstance(d.args[0], ast.Constant):
                    method, path = d.func.attr.upper(), d.args[0].value
                    rid = f"route:{method} {path}"
                    start = min(x.lineno for x in n.decorator_list)
                    n_loc = simple_loc(src_lines[start - 1:n.end_lineno])
                    handler_loc += n_loc
                    regex = "^" + re.sub(r"\\\{[^}]+\\\}", r"[^/]+", re.escape(path)) + "$"
                    routes[rid] = {"method": method, "path": path, "func": n.name, "module": r, "line": n.lineno, "regex": regex}
                    route_of_func[(r, n.name)] = rid
                    leaves[rid] = {"id": rid, "name": f"{method} {path}", "kind": "module", "language": "python",
                                   "loc": n_loc, "file": f"{r}:{n.lineno}"}
                    entry[rid] = f"HTTP route decorator @{d.func.value.id}.{d.func.attr}(\"{path}\") at {r}:{d.lineno}"
                    add_edge(r, rid, "dispatch", f"FastAPI router: {r} registers {n.name}() for {method} {path}")
        if r in leaves:
            leaves[r]["name"] = f"{Path(r).name} (FastAPI app)"
            leaves[r]["loc"] = max(1, leaves[r]["loc"] - handler_loc)

    # ── Python import edges (attributed to the route leaf when a handler uses the name) ──
    for r, t in pm.trees.items():
        if r in pm.passive:
            continue
        imported: dict[str, str] = {}   # local name -> target file
        for n in ast.walk(t):
            if isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                tgt = pm.resolve_mod(n.module, r, lineno=n.lineno)
                if not tgt:
                    continue
                for a in n.names:
                    sub = pm.modname.get(f"{n.module}.{a.name}") or pm.modname.get(f"backend.{n.module}.{a.name}")
                    imported[a.asname or a.name] = sub or pm.through_package(tgt, a.name)
            elif isinstance(n, ast.Import):
                for a in n.names:
                    tgt = pm.resolve_mod(a.name, r, lineno=n.lineno)
                    if tgt:
                        imported[(a.asname or a.name).split(".")[0]] = tgt
        used_by_route = defaultdict(set)
        for n in t.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and (r, n.name) in route_of_func:
                for s in ast.walk(n):
                    if isinstance(s, ast.Name) and s.id in imported:
                        used_by_route[s.id].add(route_of_func[(r, n.name)])
        for name, tgt in imported.items():
            if tgt in pm.passive:
                continue
            srcs = used_by_route.get(name)
            module_level_use = any(isinstance(s, ast.Name) and s.id == name for n in t.body
                                   if not (isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and (r, n.name) in route_of_func)
                                   and not isinstance(n, (ast.Import, ast.ImportFrom)) for s in ast.walk(n))
            for s in (srcs or []):
                add_edge(s, tgt, "call", f"import {name}")
            if module_level_use or not srcs:
                add_edge(r, tgt, "call", f"import {name}")

    # ── Python dispatch: constructor DI, module singletons, "module:attr" strings, dynamic imports ──
    def value_type(expr, local):
        if isinstance(expr, ast.Call):
            f = expr.func
            if isinstance(f, ast.Name):
                if f.id in classes:
                    return ("class", f.id)
                if f.id in returns and returns[f.id] in classes:
                    return ("class", returns[f.id])
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                q = f"{f.value.id}.{f.attr}"
                if q in returns and returns[q] in classes:
                    return ("class", returns[q])
        if isinstance(expr, ast.Name):
            if expr.id in local:
                return local[expr.id]
            if expr.id in funcs:
                return ("func", expr.id)
        return None

    def target_module(vt):
        return classes[vt[1]]["module"] if vt[0] == "class" else funcs[vt[1]]

    injected_unused = []
    for r, t in pm.trees.items():
        scopes = [t] + [n for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for scope in scopes:
            body = scope.body if isinstance(scope, ast.Module) else list(ast.walk(scope))
            local = {}
            for s in (ast.walk(scope) if not isinstance(scope, ast.Module) else scope.body):
                if isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name):
                    vt = value_type(s.value, local)
                    if vt:
                        local[s.targets[0].id] = vt
            calls = [c for c in (ast.walk(scope) if not isinstance(scope, ast.Module) else
                                 [x for st in scope.body if not isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                                  for x in ast.walk(st)]) if isinstance(c, ast.Call)]
            for c in calls:
                if not (isinstance(c.func, ast.Name) and c.func.id in classes):
                    continue
                c1 = classes[c.func.id]
                bound = list(zip(c1["params"], c.args)) + [(k.arg, k.value) for k in c.keywords if k.arg]
                for param, arg in bound:
                    vt = value_type(arg, local)
                    if not vt:
                        continue
                    attrs = [a for a, p in c1["attr_from_param"].items() if p == param]
                    tm = target_module(vt)
                    site = f"{r}:{c.lineno}"
                    if any(a in c1["used"] for a in attrs):
                        add_edge(c1["module"], tm, "dispatch", f"DI: {c.func.id}({param}={vt[1]}) wired at {site}")
                        notes["di"].append(f"{c.func.id}.{param} <- {vt[1]} ({Path(tm).name})  [wired at {site}]")
                    elif attrs:
                        injected_unused.append(f"{c.func.id}.{param} <- {vt[1]} wired at {site}, but self.{attrs[0]} is never used")
        # module-level singletons used inside functions
        singletons = {}
        for n in t.body:
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                vt = value_type(n.value, {})
                if vt and vt[0] == "class":
                    singletons[n.targets[0].id] = (vt, n.lineno)
        for n in t.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for s in ast.walk(n):
                    if isinstance(s, ast.Attribute) and isinstance(s.value, ast.Name) and s.value.id in singletons:
                        (vt, line) = singletons[s.value.id]
                        src = route_of_func.get((r, n.name), r)
                        add_edge(src, target_module(vt), "dispatch",
                                 f"module singleton {s.value.id} = {vt[1]} instance ({r}:{line}) -> .{s.attr}()")
        # string targets "pkg.mod:attr" and dynamic imports
        for s in ast.walk(t):
            if isinstance(s, ast.Constant) and isinstance(s.value, str) and re.fullmatch(r"[A-Za-z_][\w.]*:[A-Za-z_]\w*", s.value):
                tgt = pm.resolve_mod(s.value.split(":")[0], r, record=False)
                if tgt:
                    add_edge(r, tgt, "dispatch", f"string target \"{s.value}\" at {r}:{s.lineno}")
                else:
                    unresolved_dynamic.append(f"{r}:{s.lineno} string target {s.value!r}")
            if isinstance(s, ast.Call):
                fn = s.func
                name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
                if name in ("import_module", "__import__") or (name == "getattr" and len(s.args) > 1 and not isinstance(s.args[1], ast.Constant)):
                    unresolved_dynamic.append(f"{r}:{s.lineno} {name}(...) with non-literal target")

    # ── ORM join: classes/tables -> datastore; session ops and DDL -> read/write ──
    table_of_class: dict[str, str] = {}
    table_vars: dict[str, str] = {}
    metadata_tables = defaultdict(set)
    defined_at = defaultdict(list)
    for r, t in pm.trees.items():
        for n in ast.walk(t):
            if isinstance(n, ast.ClassDef):
                for b in n.body:
                    if isinstance(b, ast.Assign) and any(getattr(x, "id", "") == "__tablename__" for x in b.targets):
                        table_of_class[n.name] = b.value.value
                        base = n.bases[0].id if n.bases and isinstance(n.bases[0], ast.Name) else "?"
                        metadata_tables[f"{base}.metadata"].add(b.value.value)
                        defined_at[b.value.value].append(f"declarative class {n.name} ({r}:{n.lineno}) on {base}.metadata")
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and getattr(n.value.func, "id", "") == "Table" \
                    and n.value.args and isinstance(n.value.args[0], ast.Constant):
                tname = n.value.args[0].value
                table_vars[n.targets[0].id] = tname
                md = ast.unparse(n.value.args[1]) if len(n.value.args) > 1 else "?"
                metadata_tables[md].add(tname)
                defined_at[tname].append(f"Table({tname!r}) var {n.targets[0].id} ({r}:{n.lineno}) on {md}")
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "map_imperatively" and len(n.args) == 2:
                cls, var = ast.unparse(n.args[0]), ast.unparse(n.args[1])
                if var in table_vars:
                    table_of_class[cls] = table_vars[var]
                    notes["orm"].append(f"{cls} -> {table_vars[var]} (imperative mapping, {r}:{n.lineno})")
    for c, tb in table_of_class.items():
        if not any(c in x for x in notes["orm"]):
            notes["orm"].append(f"{c} -> {tb} (declarative __tablename__)")
    for tname in set(table_of_class.values()):
        leaves[f"ds:{tname}"] = {"id": f"ds:{tname}", "name": f"{tname} (SQLite table)", "kind": "datastore"}
    for r, t in pm.trees.items():
        if r in pm.passive:
            continue
        names = {x.id for x in ast.walk(t) if isinstance(x, ast.Name)}
        mapped = {table_of_class[c] for c in table_of_class if c in names}
        for n in ast.walk(t):
            if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
                continue
            recv = ast.unparse(n.func.value)
            if n.func.attr in READ_OPS | WRITE_OPS and re.search(r"\bsession\b", recv):
                kind = "read" if n.func.attr in READ_OPS else "write"
                for tb in mapped:
                    add_edge(r, f"ds:{tb}", kind, f"ORM session.{n.func.attr}() on mapped class -> {tb}")
            if n.func.attr == "create_all" and recv in metadata_tables:
                for tb in metadata_tables[recv]:
                    add_edge(r, f"ds:{tb}", "write", f"DDL {recv}.create_all() at {r}:{n.lineno}")
            if n.func.attr == "get_table_names":
                for tb in set(table_of_class.values()):
                    add_edge(r, f"ds:{tb}", "read", f"schema introspection get_table_names() at {r}:{n.lineno}")

    # ── Frontend leaves & import edges ──
    fe_text = {rel(f): f.read_text(encoding="utf-8") for f in fe_prod + html}
    for r in fe_text:
        p = Path(r)
        kind = "screen" if p.suffix in {".tsx", ".html"} else "module"
        lang = {".ts": "typescript", ".tsx": "typescript", ".css": "css", ".html": "html"}[p.suffix]
        leaves[r] = {"id": r, "name": p.name, "kind": kind, "language": lang, "loc": locs.get(r, 0), "file": r}

    def resolve_ts(spec: str, importer: str) -> str | None:
        if spec.startswith("@/"):
            base = Path("frontend/src") / spec[2:]
        elif spec.startswith("."):
            base = Path(importer).parent / spec
        elif spec.startswith("/"):
            base = Path("frontend") / spec.lstrip("/")
        else:
            return None
        base = Path(*[x for x in base.parts])  # normalise
        norm = (ROOT / base).resolve()
        for cand in (norm, *[norm.with_name(norm.name + ext) for ext in (".ts", ".tsx", ".css")],
                     norm / "index.ts", norm / "index.tsx"):
            if cand.is_file():
                return rel(cand)
        return None

    IMPORT_RE = re.compile(r"""^\s*(?:import|export)\b[^;'"]*?\bfrom\s+['"]([^'"]+)['"]|^\s*import\s+['"]([^'"]+)['"]""", re.M)
    unresolved_ts = []
    for r, txt in fe_text.items():
        if r.endswith(".html"):
            for m in re.finditer(r"<script[^>]*\bsrc=[\"']([^\"']+)[\"']", txt):
                tgt = resolve_ts(m.group(1), r)
                if tgt:
                    add_edge(r, tgt, "dispatch", f"<script src=\"{m.group(1)}\"> in {r}")
            entry[r] = "HTML document served by Vite (frontend/index.html is the app root)"
            continue
        for m in IMPORT_RE.finditer(txt):
            spec = m.group(1) or m.group(2)
            tgt = resolve_ts(spec, r)
            if tgt:
                add_edge(r, tgt, "call", f"import '{spec}'")
            elif spec.startswith((".", "@/")):
                unresolved_ts.append(f"{r}: {spec}")
        for m in re.finditer(r"\bimport\s*\(\s*([^)]*)\)|React\.lazy|\blazy\s*\(", txt):
            unresolved_dynamic.append(f"{r}: dynamic import/lazy {m.group(0)[:40]!r}")

    # ── HTTP dispatch: client calls -> FastAPI routes (only for methods something calls) ──
    instances = {}
    for r, txt in fe_text.items():
        for m in re.finditer(r"export\s+const\s+(\w+)\s*=\s*new\s+(\w+)", txt):
            instances[m.group(1)] = (m.group(2), r)
    fe_all_src = {r: t for r, t in fe_text.items()}
    http_rows = []
    for r, txt in fe_text.items():
        for m in re.finditer(r"\bapiClient\.(get|post|put|delete|patch)\s*(?:<[^>]*>)?\s*\(\s*(['\"`])(.*?)\2", txt):
            verb, raw = m.group(1).upper(), m.group(3)
            path = re.sub(r"\$\{[^}]*\}", "x", raw).split("?")[0]
            before = txt[:m.start()]
            meth = (re.findall(r"^\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*:\s*Promise", before, re.M) or ["?"])[-1]
            inst = next((i for i, (_, f) in instances.items() if f == r), None)
            callers = sorted(f for f, t in fe_all_src.items() if f != r and inst and re.search(rf"\b{inst}\.{meth}\b", t))
            rid = next((k for k, v in routes.items() if v["method"] == verb and re.match(v["regex"], path)), None)
            http_rows.append((verb, raw, f"{inst}.{meth}" if inst else meth, rid, callers))
            if rid is None:
                unresolved_dynamic.append(f"{r}: {verb} {raw} matches no FastAPI route")
            elif callers:
                add_edge(r, rid, "dispatch", f"HTTP {verb} {raw} via {inst}.{meth}() (called by {', '.join(Path(c).name for c in callers)})")
            else:
                notes["uncalled"].append(f"{inst}.{meth}() -> {verb} {raw} is defined in {r} but never called; edge not drawn")

    # ── Client-side cache (TanStack Query keys) as a shared in-memory store ──
    for r, txt in fe_text.items():
        for m in re.finditer(r"(useQuery\s*\(\s*\{\s*queryKey|getQueryData\s*(?:<[^>]*>)?\s*\(|setQueryData\s*(?:<[^>]*>)?\s*\(|invalidateQueries\s*\(\s*\{\s*queryKey)\s*:?\s*\[\s*'(\w+)'", txt):
            op, key = m.group(1), m.group(2)
            dsid = f"ds:qc:{key}"
            leaves.setdefault(dsid, {"id": dsid, "name": f"'{key}' query cache (browser memory)", "kind": "datastore"})
            kind = "read" if op.startswith(("useQuery", "getQueryData")) else "write"
            add_edge(r, dsid, kind, f"TanStack Query {op.split('(')[0].split('<')[0].strip()} key '{key}'")

    # ── Entry points from deployment config (CI workflows, Playwright webServer) ──
    cfg_files = sorted((ROOT / ".github/workflows").glob("*.yml")) + [ROOT / "frontend/playwright.config.ts"]
    for cf in cfg_files:
        if not cf.exists():
            continue
        for i, line in enumerate(cf.read_text(encoding="utf-8").splitlines(), 1):
            for m in re.finditer(r"python\s+-m\s+([\w.]+)", line):
                tgt = pm.resolve_mod(m.group(1), rel(cf), record=False)
                if tgt in leaves:
                    entry.setdefault(tgt, f"`python -m {m.group(1)}` in {rel(cf)}:{i}")
            for m in re.finditer(r"python\s+([\w/.-]+\.py)", line):
                if m.group(1) in leaves:
                    entry.setdefault(m.group(1), f"`python {m.group(1)}` in {rel(cf)}:{i}")

    # ── Test references (tests are not graph nodes; they are counted per leaf) ──
    test_refs = defaultdict(set)
    for f in py_tests:
        r = rel(f)
        txt = f.read_text(encoding="utf-8")
        try:
            t = ast.parse(txt)
        except SyntaxError:
            continue
        for n in ast.walk(t):
            if isinstance(n, ast.ImportFrom) and n.module:
                tgt = pm.resolve_mod(n.module, r, record=False)
                for a in n.names:
                    if tgt:
                        test_refs[pm.through_package(tgt, a.name)].add(r)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith("backend.app."):
                parts = n.value.split(".")
                for k in range(len(parts), 1, -1):
                    if ".".join(parts[:k]) in pm.modname:
                        test_refs[pm.modname[".".join(parts[:k])]].add(r)
                        break
        for m in re.finditer(r"\.(get|post|put|delete)\(\s*f?[\"']([^\"']+)[\"']", txt):
            p = re.sub(r"\{[^}]*\}", "x", m.group(2)).split("?")[0]
            for rid, v in routes.items():
                if v["method"] == m.group(1).upper() and re.match(v["regex"], p):
                    test_refs[rid].add(r)
    for f in fe_tests:
        r = rel(f)
        txt = f.read_text(encoding="utf-8")
        for m in re.finditer(r"""(?:from|vi\.mock\()\s*['"]([^'"]+)['"]""", txt):
            tgt = resolve_ts(m.group(1), r)
            if tgt:
                test_refs[tgt].add(r)
        for m in re.finditer(r"\.(get|post|put|delete)\(\s*[`'\"]https?://[^/]+(/[^`'\"]*)", txt):
            p = re.sub(r"\$\{[^}]*\}", "x", m.group(2)).split("?")[0]
            for rid, v in routes.items():
                if v["method"] == m.group(1).upper() and re.match(v["regex"], p):
                    test_refs[rid].add(r)
        if "page.goto" in txt and html:
            test_refs[rel(html[0])].add(r)
    for lid, leaf in leaves.items():
        if leaf["kind"] != "datastore":
            leaf["testRefs"] = len(test_refs.get(lid, ()))

    # ── Edge cleanup: a dispatch duplicating a static call between the same pair adds nothing ──
    for (s, t, k) in list(edges):
        if k == "dispatch" and (s, t, "call") in edges:
            del edges[(s, t, k)]
    bad = [(s, t) for (s, t, _) in edges if s not in leaves or t not in leaves]
    assert not bad, f"edge endpoints missing from tree: {bad}"

    # ── Dead-end candidates (after all entry-point and edge types are in) ──
    inbound = Counter(t for (_, t, _) in edges)
    tiers_with_unresolved = {("frontend" if u.startswith("frontend") else "backend") for u in unresolved_dynamic}
    dead, suppressed = [], []
    for lid, leaf in leaves.items():
        if leaf["kind"] == "datastore" or lid in entry or inbound[lid]:
            continue
        tier = "frontend" if lid.startswith("frontend") else "backend"
        (suppressed if tier in tiers_with_unresolved else dead).append(lid)

    # ── Domain tree ──
    def domain_of(lid: str) -> str:
        for did, _, pats in DOMAINS:
            if any(re.search(p, lid) for p in pats):
                return did
        return "dom:other"
    tree_children = []
    by_dom = defaultdict(list)
    for lid, leaf in leaves.items():
        if leaf["kind"] != "datastore":
            by_dom[domain_of(lid)].append(leaf)
    for did, dname, _ in DOMAINS + [("dom:other", "Unassigned", [])]:
        if by_dom.get(did):
            tree_children.append({"id": did, "name": dname, "kind": "domain",
                                  "children": sorted(by_dom[did], key=lambda x: x["id"])})
    tree_children.append({"id": "dom:data", "name": "Data stores", "kind": "domain",
                          "children": sorted([l for l in leaves.values() if l["kind"] == "datastore"], key=lambda x: x["id"])})

    # ── Facts for observations ──
    fan_in = Counter(t for (s, t, k) in edges if k in ("call", "dispatch"))
    fan_out = Counter(s for (s, t, k) in edges if k in ("call", "dispatch"))
    svc = "backend/app/business_logic/todo_service.py"
    route_to_svc = sorted(s for (s, t, k) in edges if t == svc and s.startswith("route:"))
    writers = defaultdict(set)
    readers = defaultdict(set)
    for (s, t, k) in edges:
        if k == "write":
            writers[t].add(s)
        if k == "read":
            readers[t].add(s)
    ddl_writers = sorted({s for (s, t, k), via in edges.items() if k == "write" and via.startswith("DDL")})
    dml_writers = sorted({s for (s, t, k), via in edges.items() if k == "write" and via.startswith("ORM")})
    routes_with_fe = sorted({t for (s, t, k) in edges if t.startswith("route:") and s.startswith("frontend/")})
    routes_without = sorted(set(routes) - set(routes_with_fe))
    qc = "ds:qc:todos"
    two_defs = {tb: d for tb, d in defined_at.items() if len(d) > 1}

    observations = [
        f"Single hub: {len(route_to_svc)} of {len(routes)} HTTP routes (all except {', '.join(sorted(set(routes) - set(route_to_svc))) or 'none'}) "
        f"dispatch into one ToDoService singleton (todo_service.py, fan-out {fan_out[svc]}), "
        f"built at import time in api.py via the hand-written composition root factory.py. There is no FastAPI Depends(); "
        f"tests reach the service by patching the module global.",
        (f"toDo has exactly one DML writer ({', '.join(Path(x).name for x in dml_writers)}), a clean persistence choke point. "
         f"But the schema has two authorities: DDL comes from {len(ddl_writers)} create_all() callers "
         f"({', '.join(Path(x).name for x in ddl_writers)}) on the declarative Base, while reads and writes go through a separately "
         f"defined Table on another MetaData ({len(two_defs.get('toDo', []))} definitions of the same table). Consolidate before any port.")
        if dml_writers else "No ORM writers detected.",
        (f"Client-cache coupling: the 'todos' query cache has {len(writers[qc])} writers (the mutation hooks) and "
         f"{len(readers[qc])} readers, all keyed to a hardcoded page 1 / limit 10 that matches TodoList. Any pagination change touches "
         f"{len(writers[qc] | readers[qc]) + 1} modules at once.") if qc in leaves else "No client-side cache keys detected.",
        f"Cross-tier seam: {len(routes_with_fe)} of {len(routes)} routes have a frontend caller. No frontend caller for "
        f"{', '.join(routes_without)} (the e2e readiness check polls /docs; todoApi.getById exists but is never called). "
        f"TS contract types are hand-mirrored in types/todo.ts. The REST contract is the natural migration seam, and generating "
        f"types from OpenAPI would remove the drift risk.",
        ("DI resolution: " + "; ".join(injected_unused) + ". So the keyword sanitizer is reached only through FieldValidator's own instance."
         + (" repository.py reaches database.py only through the injected safe_session_scope (no import)."
            if ("backend/app/data_access/repository.py", "backend/app/data_access/database.py", "dispatch") in edges else ""))
        if injected_unused else "DI resolution: every injected dependency is used.",
        (f"Dead-end candidates: {', '.join(dead) if dead else 'none'}. No unresolved dynamic dispatch was found "
         f"(the uvicorn string target and every HTTP call resolved), so these are not suppressed.")
        if not unresolved_dynamic else
        f"Dead-end claims suppressed in {', '.join(sorted(tiers_with_unresolved))}: {len(unresolved_dynamic)} unresolved dynamic targets.",
    ]
    if pm.alt_root:
        observations.append(f"Import-root split: {', '.join(sorted({Path(a).name for a, _, _ in pm.alt_root}))} imports through `app.*` after a "
                            f"sys.path hack while everything else uses `backend.app.*`. The same module can then load twice "
                            f"under two names; normalise it before restructuring packages.")

    # ── Persona flows (curated; every node id is validated) ──
    S, F = "backend/app/business_logic/", "frontend/src/"
    flows = [
        {"name": "Capture a new todo", "persona": "Todo user",
         "description": "Someone types a task and presses Enter; it appears at once and is saved on the server.",
         "steps": [
             {"label": "Types a title and presses Enter (checked: not empty, at most 255 characters)", "nodes": [F + "components/todos/TodoForm.tsx"]},
             {"label": "Shown in the list instantly, before the server answers", "nodes": [F + "hooks/queries/useCreateTodo.ts", "ds:qc:todos"]},
             {"label": "Sent to the server with a browser-generated ID", "nodes": [F + "services/api/todoApi.ts", F + "services/api/client.ts", "route:POST /todo"]},
             {"label": "Server checks the text; titles with words like 'or' or 'update' are rejected", "nodes": [S + "todo_service.py", S + "builders/todo_entry_builder.py", S + "validators/uuid_validator.py", S + "validators/field_validator.py", S + "validators/input_sanitizer.py"]},
             {"label": "Saved to the database", "nodes": ["backend/app/data_access/repository.py", "backend/app/data_access/database.py", "ds:toDo"]},
             {"label": "List refreshes from the server (or the instant entry is rolled back on error)", "nodes": [F + "hooks/queries/useCreateTodo.ts", "ds:qc:todos", F + "hooks/queries/useTodoList.ts"]},
         ]},
        {"name": "Review my todo list", "persona": "Todo user",
         "description": "Someone opens the app and sees their todos; only the first 10 are ever shown.",
         "steps": [
             {"label": "Opens the app in the browser", "nodes": ["frontend/index.html", F + "main.tsx", F + "App.tsx"]},
             {"label": "List asks for page 1, 10 items", "nodes": [F + "components/todos/TodoList.tsx", F + "hooks/queries/useTodoList.ts", "ds:qc:todos"]},
             {"label": "Request goes to the server", "nodes": [F + "services/api/todoApi.ts", F + "services/api/client.ts", "route:GET /todo"]},
             {"label": "Server loads todos not marked deleted (no sort order)", "nodes": [S + "todo_service.py", "backend/app/data_access/repository.py", "ds:toDo"]},
             {"label": "Each todo is shown with Edit and Delete buttons", "nodes": [F + "components/todos/TodoItem.tsx", F + "components/todos/TodoDeleteButton.tsx"]},
         ]},
        {"name": "Rename a todo", "persona": "Todo user",
         "description": "Someone edits a todo's title; the change shows at once and is saved.",
         "steps": [
             {"label": "Clicks Edit and types a new title", "nodes": [F + "components/todos/TodoItem.tsx", F + "components/todos/TodoEditForm.tsx"]},
             {"label": "Change shown instantly", "nodes": [F + "hooks/queries/useUpdateTodo.ts", "ds:qc:todos"]},
             {"label": "Sent to the server", "nodes": [F + "services/api/todoApi.ts", F + "services/api/client.ts", "route:PUT /todo/{todo_id}"]},
             {"label": "Server re-checks the text (same keyword rules)", "nodes": [S + "todo_service.py", S + "validators/field_validator.py", S + "validators/input_sanitizer.py"]},
             {"label": "Saved; the 'updated' timestamp is not refreshed", "nodes": ["backend/app/data_access/repository.py", "backend/app/data_access/database.py", "ds:toDo"]},
             {"label": "List refreshes from the server", "nodes": [F + "hooks/queries/useUpdateTodo.ts", F + "hooks/queries/useTodoList.ts"]},
         ]},
        {"name": "Delete a todo", "persona": "Todo user",
         "description": "Someone deletes a todo after confirming; it disappears but is only flagged as deleted in the database.",
         "steps": [
             {"label": "Clicks Delete and confirms the prompt", "nodes": [F + "components/todos/TodoDeleteButton.tsx"]},
             {"label": "Removed from view instantly", "nodes": [F + "hooks/queries/useDeleteTodo.ts", "ds:qc:todos"]},
             {"label": "Sent to the server", "nodes": [F + "services/api/todoApi.ts", F + "services/api/client.ts", "route:DELETE /todo/{todo_id}"]},
             {"label": "Server checks the ID is a valid UUID", "nodes": [S + "todo_service.py", S + "validators/uuid_validator.py"]},
             {"label": "Row flagged as deleted and kept forever (no purge)", "nodes": ["backend/app/data_access/repository.py", "backend/app/data_access/database.py", "ds:toDo"]},
         ]},
    ]
    missing = [n for fl in flows for st in fl["steps"] for n in st["nodes"] if n not in leaves]
    assert not missing, f"flow nodes missing from tree: {missing}"

    topo = {
        "system": DISPLAY,
        "root": {"id": "sys", "name": DISPLAY, "kind": "system", "children": tree_children},
        "edges": [{"source": s, "target": t, "kind": k, "via": v} for (s, t, k), v in sorted(edges.items())],
        "entryPoints": sorted(entry),
        "deadEnds": sorted(dead),
        "observations": observations,
        "flows": flows,
    }
    (HERE / "topology.json").write_text(json.dumps(topo, indent=2) + "\n", encoding="utf-8")

    # ── Mermaid exports ──
    write_mermaid(topo, leaves, edges, entry, domain_of, flows)

    # ── Human summary ──
    P = print
    kinds = Counter(l["kind"] for l in leaves.values())
    ek = Counter(k for (_, _, k) in edges)
    P(f"== {DISPLAY} topology  ({ROOT})")
    P(f"leaves: {len(leaves)}  ({', '.join(f'{v} {k}' for k, v in kinds.most_common())})  ·  "
      f"edges: {len(edges)}  ({', '.join(f'{v} {k}' for k, v in ek.most_common())})")
    P(f"package markers / re-export __init__ folded away: {', '.join(sorted(pm.passive)) or 'none'}")
    P("\n-- domains")
    for c in tree_children:
        P(f"  {c['name']:<36} {len(c['children']):>3} leaves  {sum(x.get('loc', 0) for x in c['children']):>5} LOC")
    P("\n-- entry points (from deployment config)")
    for e in sorted(entry):
        P(f"  {e:<44} <- {entry[e]}")
    P("\n-- HTTP: route -> handler -> frontend caller")
    for rid, v in sorted(routes.items(), key=lambda kv: kv[1]["line"]):
        callers = [row for row in http_rows if row[3] == rid]
        cs = "; ".join(f"{row[2]}() <- {', '.join(Path(c).name for c in row[4]) or 'NO CALLER'}" for row in callers) or "no frontend client method"
        P(f"  {rid:<28} {v['module']}:{v['line']} {v['func']}()  |  {cs}")
    P("\n-- dispatch edges resolved (DI / singleton / router / string / HTML / HTTP)")
    for (s, t, k), via in sorted(edges.items()):
        if k == "dispatch" and not via.startswith("FastAPI router"):
            P(f"  {Path(s).name if not s.startswith('route:') else s} -> {Path(t).name if not t.startswith('route:') else t}   [{via}]")
    P(f"  (+ {sum(1 for (s, t, k), v in edges.items() if k == 'dispatch' and v.startswith('FastAPI router'))} FastAPI router edges api.py -> route handlers)")
    P("\n-- data lineage (ORM mapping: " + "; ".join(notes["orm"]) + ")")
    for ds in sorted(l for l in leaves if l.startswith("ds:")):
        P(f"  {leaves[ds]['name']}")
        P(f"     writers: {', '.join(sorted(Path(x).name for x in writers[ds])) or '-'}")
        P(f"     readers: {', '.join(sorted(Path(x).name for x in readers[ds])) or '-'}")
    for tb, d in two_defs.items():
        P(f"  !! table {tb} defined {len(d)}x: " + " | ".join(d))
    P("\n-- dead-end candidates (no inbound edge, not an entry point)")
    for d in dead:
        P(f"  {d}")
    if suppressed:
        P(f"  suppressed (tier has unresolved dynamic dispatch): {', '.join(suppressed)}")
    P("\n-- unresolved dynamic dispatch: " + ("none" if not unresolved_dynamic else ""))
    for u in unresolved_dynamic:
        P(f"  {u}")
    if unresolved_ts:
        P("-- unresolved TS imports: " + ", ".join(unresolved_ts))
    P("\n-- injected but unused / defined but uncalled")
    for x in injected_unused + notes["uncalled"]:
        P(f"  {x}")
    if pm.alt_root:
        P("\n-- alternate import root (sys.path hack)")
        for a, ln, n in pm.alt_root:
            P(f"  {a}:{ln} imports `{n}` -> resolved as backend.{n}")
    P("\n-- fan-in top 6 (call+dispatch)")
    for lid, c in fan_in.most_common(6):
        P(f"  {c:>3}  {lid}")
    P("-- fan-out top 6")
    for lid, c in fan_out.most_common(6):
        P(f"  {c:>3}  {lid}")
    untested = sorted(l for l, v in leaves.items() if v["kind"] != "datastore" and v.get("testRefs", 0) == 0 and not l.endswith(".css"))
    P(f"\n-- leaves with no DIRECT test reference ({len(untested)}; Playwright still exercises the frontend through index.html): " + ", ".join(Path(u).name if not u.startswith("route:") else u for u in untested))
    P(f"\nwrote {HERE / 'topology.json'}, call-graph.mmd, data-lineage.mmd, critical-path.mmd")
    return 0


def mm_id(s: str) -> str:
    return re.sub(r"\W", "_", s)


def mm_label(s: str) -> str:
    return s.replace('"', "'")


def write_mermaid(topo, leaves, edges, entry, domain_of, flows):
    dom_name = {c["id"]: c["name"] for c in topo["root"]["children"]}
    # call-graph.mmd — domain level
    agg = Counter()
    disp = set()
    for (s, t, k) in edges:
        if k not in ("call", "dispatch"):
            continue
        a, b = domain_of(s), domain_of(t)
        if a != b:
            agg[(a, b)] += 1
            if k == "dispatch":
                disp.add((a, b))
    entry_doms = {domain_of(e) for e in entry}
    L = ["%% basictodo — domain-level call graph (generated by extract_topology.py)",
         "%% Edge label = number of module-level edges; dotted = includes resolved dynamic dispatch. Orange = holds entry points.",
         "graph TD",
         '  EXT_BROWSER(["Browser loads index.html"])',
         '  EXT_RUN(["python -m backend.app.main / CI init_db.py"])',
         '  EXT_HTTP(["HTTP clients (frontend, e2e, curl)"])']
    for did in dom_name:
        if did != "dom:data":
            L.append(f'  {mm_id(did)}["{mm_label(dom_name[did])}"]')
    L += ["  EXT_BROWSER --> dom_fe_shell", "  EXT_RUN --> dom_be_boot", "  EXT_HTTP --> dom_be_api"]
    for (a, b), n in sorted(agg.items()):
        arrow = "-.->" if (a, b) in disp else "-->"
        L.append(f'  {mm_id(a)} {arrow}|"{n}"| {mm_id(b)}')
    L.append("  classDef entry fill:#cc785c,stroke:#8a4a33,color:#fff")
    L.append("  classDef ext fill:#333,stroke:#999,color:#ddd")
    L.append("  class " + ",".join(mm_id(d) for d in sorted(entry_doms)) + " entry")
    L.append("  class EXT_BROWSER,EXT_RUN,EXT_HTTP ext")
    (HERE / "call-graph.mmd").write_text("\n".join(L) + "\n", encoding="utf-8")

    # data-lineage.mmd — programs -> data stores
    L = ["%% basictodo — data lineage (generated by extract_topology.py). Solid = reads, thick = writes.", "graph LR"]
    nodes = set()
    for (s, t, k), via in sorted(edges.items()):
        if k in ("read", "write"):
            nodes |= {s, t}
    for n in sorted(nodes):
        lab = leaves[n]["name"]
        L.append(f'  {mm_id(n)}[("{mm_label(lab)}")]' if n.startswith("ds:") else f'  {mm_id(n)}["{mm_label(lab)}"]')
    for (s, t, k), via in sorted(edges.items()):
        if k == "read":
            L.append(f'  {mm_id(s)} -->|"reads"| {mm_id(t)}')
        elif k == "write":
            lab = "writes (DDL)" if via.startswith("DDL") else "writes"
            L.append(f'  {mm_id(s)} ==>|"{lab}"| {mm_id(t)}')
    L.append("  classDef store fill:#3d6a5a,stroke:#2a4a3f,color:#fff")
    L.append("  class " + ",".join(mm_id(n) for n in sorted(nodes) if n.startswith("ds:")) + " store")
    (HERE / "data-lineage.mmd").write_text("\n".join(L) + "\n", encoding="utf-8")

    # critical-path.mmd — primary persona flow
    fl = flows[0]
    L = [f"%% basictodo — critical path: {fl['name']} ({fl['persona']}). Generated by extract_topology.py.",
         "%% No production telemetry available: p50/p99 wall-clock cannot be annotated (see ASSESSMENT.md).",
         "flowchart TD",
         f'  START(["{mm_label(fl["persona"])}: {mm_label(fl["description"])}"])']
    prev = "START"
    for i, st in enumerate(fl["steps"], 1):
        mods = ", ".join(leaves[n]["name"] for n in st["nodes"])
        L.append(f'  S{i}["{i}. {mm_label(st["label"])}<br/><small>{mm_label(mods)}</small>"]')
        L.append(f"  {prev} --> S{i}")
        prev = f"S{i}"
    L.append('  NOTE["p50 / p99: n/a (no telemetry)"]')
    L.append(f"  {prev} -.- NOTE")
    (HERE / "critical-path.mmd").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
