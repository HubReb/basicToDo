"""Attributes a JS bundle difference to the modules and packages it came from.

    bundle_modules.py list <frontend-dir> <dist-with-sourcemaps> > modules.json
    bundle_modules.py diff <a-modules.json> <b-modules.json>

`list` reads every *.js.map in the dist directory and records, per source
module, the SHA-256 of its sourcesContent, the npm package it belongs to and
that package's installed version (read from <frontend-dir>/node_modules).
`diff` groups the changed, added and removed modules by package, so a bundle
change can be traced to the package versions that caused it. App modules
(outside node_modules) are reported separately.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

PKG = re.compile(r"node_modules/((?:@[^/]+/)?[^/]+)/")


def package_of(source):
    matches = PKG.findall(source)
    return matches[-1] if matches else None


def list_modules(frontend_dir, dist_dir):
    frontend_dir, dist_dir = Path(frontend_dir), Path(dist_dir)
    versions, modules = {}, {}
    for map_path in sorted(dist_dir.rglob("*.js.map")):
        data = json.loads(map_path.read_text())
        for source, content in zip(data["sources"], data.get("sourcesContent") or []):
            # Sources are relative to the map file; key them relative to the
            # frontend directory so captures from different checkouts compare.
            absolute = (map_path.parent / source).resolve()
            try:
                key = str(absolute.relative_to(frontend_dir.resolve()))
            except ValueError:
                key = re.sub(r"^(\.\./)+", "", source)
            pkg = package_of(key)
            key = key.split("node_modules/", 1)[1] if pkg else key
            if pkg and pkg not in versions:
                manifest = frontend_dir / "node_modules" / pkg / "package.json"
                versions[pkg] = json.loads(manifest.read_text())["version"] if manifest.exists() else None
            modules[key] = {
                "package": pkg or "(app)",
                "version": versions.get(pkg) if pkg else None,
                "sha256": hashlib.sha256((content or "").encode()).hexdigest(),
            }
    return modules


def diff(a_path, b_path):
    a, b = json.load(open(a_path)), json.load(open(b_path))
    by_pkg = {}
    for key in sorted(set(a) | set(b)):
        ma, mb = a.get(key), b.get(key)
        if ma and mb and ma["sha256"] == mb["sha256"]:
            continue
        pkg = (ma or mb)["package"]
        entry = by_pkg.setdefault(pkg, {"versions": set(), "changed": 0, "added": 0, "removed": 0})
        entry["versions"].add(f"{ma['version'] if ma else '-'} -> {mb['version'] if mb else '-'}")
        entry["changed" if ma and mb else "added" if mb else "removed"] += 1
    unchanged_pkgs = sorted({m["package"] for m in a.values()} - set(by_pkg))
    print(f"modules: {len(a)} -> {len(b)}; packages with module changes: {len(by_pkg)}")
    for pkg, e in sorted(by_pkg.items()):
        print(f"  {pkg:42} {', '.join(sorted(e['versions']))}: "
              f"{e['changed']} changed, {e['added']} added, {e['removed']} removed")
    print(f"packages with identical modules: {len(unchanged_pkgs)}")
    print("  " + ", ".join(unchanged_pkgs))
    return 1 if by_pkg else 0


if __name__ == "__main__":
    if sys.argv[1] == "list":
        print(json.dumps(list_modules(sys.argv[2], sys.argv[3]), indent=1, sort_keys=True))
    elif sys.argv[1] == "diff":
        sys.exit(diff(sys.argv[2], sys.argv[3]))
    else:
        sys.exit(__doc__)
