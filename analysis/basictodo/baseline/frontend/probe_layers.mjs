// One-off evidence probe for D-24 (Phase 2). Lists every CSS rule that matches the
// Cancel button (variant "outline") with its cascade layer. Needs the backend on
// 127.0.0.1:8000 and frontend/dist served on localhost:5173, as in run_screens.sh.
// Usage: node probe_layers.mjs <runner-dir> > d24-cascade-probe.json
import { createRequire } from "node:module";
import path from "node:path";
const require = createRequire(path.join(process.argv[2], "package.json"));
const { chromium } = require("playwright");
const b = await chromium.launch({ args: ["--host-resolver-rules=MAP localhost 127.0.0.1"] });
const p = await b.newPage();
await fetch("http://127.0.0.1:8000/todo", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: "44444444-4444-4444-8444-444444444444", title: "Probe" }) });
await p.goto("http://localhost:5173/");
await p.getByRole("button", { name: "Edit" }).first().click();
const out = await p.evaluate(() => {
  const el = [...document.querySelectorAll("button")].find((x) => x.textContent.trim() === "Cancel");
  const hits = [];
  const walk = (rules, layer) => {
    for (const r of rules) {
      if (r.constructor.name === "CSSLayerBlockRule") walk(r.cssRules, (layer ? layer + "." : "") + r.name);
      else if (r.cssRules && !r.selectorText) walk(r.cssRules, layer);
      else if (r.selectorText) {
        let m = false; try { m = el.matches(r.selectorText); } catch {}
        if (m) {
          const props = ["border-color", "border", "border-top-color", "color", "background-color", "background"]
            .filter((k) => r.style.getPropertyValue(k)).map((k) => `${k}: ${r.style.getPropertyValue(k)}`);
          if (props.length) hits.push({ layer: layer || "(unlayered)", selector: r.selectorText.slice(0, 60), props });
        }
      }
    }
  };
  for (const s of document.styleSheets) { try { walk(s.cssRules, ""); } catch {} }
  return { variantClass: el.className.slice(0, 80), computedBorder: getComputedStyle(el).borderTopColor, hits };
});
console.log(JSON.stringify(out, null, 1));
await b.close();
