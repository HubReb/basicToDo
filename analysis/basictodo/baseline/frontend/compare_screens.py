"""Compares two screenshot captures made by run_screens.sh.

    uvx --with pillow python compare_screens.py <a-dir> <b-dir> <report-dir>

Per screen: whether the PNGs are pixel-identical, the share of changed
pixels, the bounding box of the change, a diff image (changed pixels in red
over a dimmed copy of a), and every computed-style difference (element,
property, a -> b; elements only in a or only in b). It also checks that both
captures used the same Playwright, browser and runner lock. Writes
report.json and report.md to <report-dir>; exits 1 on any difference and 2
if the capture setups differ.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops

SETUP_KEYS = ("playwright", "browser", "chromium_revision", "runner_lock_sha256", "viewport")


def compare_png(a_path, b_path, diff_path):
    a, b = Image.open(a_path).convert("RGB"), Image.open(b_path).convert("RGB")
    if a.size != b.size:
        return {"identical": False, "size": [a.size, b.size]}
    diff = ImageChops.difference(a, b)
    bbox = diff.getbbox()
    if bbox is None:
        return {"identical": True, "changed_pixels": 0, "share": 0.0}
    mask = diff.convert("L").point(lambda v: 255 if v else 0)
    changed = sum(1 for v in mask.getdata() if v)
    overlay = Image.blend(a, Image.new("RGB", a.size, (255, 255, 255)), 0.6)
    overlay.paste(Image.new("RGB", a.size, (220, 0, 0)), mask=mask)
    overlay.save(diff_path)
    return {"identical": False, "changed_pixels": changed,
            "share": round(changed / (a.size[0] * a.size[1]), 6), "bbox": list(bbox)}


def compare_styles(a_path, b_path):
    a, b = json.loads(Path(a_path).read_text()), json.loads(Path(b_path).read_text())
    changes = []
    for key in sorted(set(a) & set(b)):
        for prop in sorted(set(a[key]) | set(b[key])):
            if a[key].get(prop) != b[key].get(prop):
                changes.append({"element": key, "text": a[key].get("text") or b[key].get("text"),
                                "property": prop, "a": a[key].get(prop), "b": b[key].get(prop)})
    only_a = [{"element": k, "text": a[k]["text"]} for k in sorted(set(a) - set(b))]
    only_b = [{"element": k, "text": b[k]["text"]} for k in sorted(set(b) - set(a))]
    return changes, only_a, only_b


def main(a_dir, b_dir, report_dir):
    a_dir, b_dir, report_dir = Path(a_dir), Path(b_dir), Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    cap_a = json.loads((a_dir / "capture.json").read_text())
    cap_b = json.loads((b_dir / "capture.json").read_text())
    setup = {k: [cap_a.get(k), cap_b.get(k)] for k in SETUP_KEYS}
    setup_equal = all(v[0] == v[1] for v in setup.values())
    dist_equal = cap_a["dist_sha256"] == cap_b["dist_sha256"]
    screens = {}
    for png in sorted(a_dir.glob("*.png")):
        name = png.stem
        pixels = compare_png(png, b_dir / png.name, report_dir / f"{name}.diff.png")
        changes, only_a, only_b = compare_styles(a_dir / f"{name}.styles.json",
                                                 b_dir / f"{name}.styles.json")
        screens[name] = {"pixels": pixels, "style_changes": changes,
                         "elements_only_in_a": only_a, "elements_only_in_b": only_b}
    report = {"setup": setup, "setup_equal": setup_equal, "dist_equal": dist_equal, "screens": screens}
    (report_dir / "report.json").write_text(json.dumps(report, indent=1) + "\n")

    lines = [f"setup identical: {setup_equal}", f"dist identical: {dist_equal}", ""]
    for name, s in screens.items():
        p = s["pixels"]
        state = "identical" if p["identical"] else f"{p.get('changed_pixels')} px ({p.get('share', 0):.4%}) bbox {p.get('bbox')}"
        lines.append(f"{name}: {state}; style changes {len(s['style_changes'])}, "
                     f"elements only in a {len(s['elements_only_in_a'])}, only in b {len(s['elements_only_in_b'])}")
    (report_dir / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    if not setup_equal:
        return 2
    differs = not dist_equal or any(
        not s["pixels"]["identical"] or s["style_changes"] or s["elements_only_in_a"] or s["elements_only_in_b"]
        for s in screens.values())
    return 1 if differs else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
