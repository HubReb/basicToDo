// Captures the screens of the four persona flows (brief §4) from a built
// frontend. run_screens.sh starts the servers and calls this script.
//
//   node capture_screens.mjs <runner-dir> <out-dir> <dist.sha256> <runner-lock-sha256>
//
// Playwright comes from <runner-dir> (one fixed installation for every
// capture), never from frontend/node_modules, so browser rendering cannot
// change between F0, F1 and F2. For every screen the script stores the PNG
// and the computed styles of every rendered element, keyed by DOM path.
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";

const [runnerDir, outDir, distShaFile, runnerLockSha] = process.argv.slice(2);
const require = createRequire(path.join(path.resolve(runnerDir), "package.json"));
const { chromium } = require("playwright");
// Neither file is an exported package path, so read them from disk.
const readJson = (rel) =>
  JSON.parse(fs.readFileSync(path.join(path.resolve(runnerDir), "node_modules", rel), "utf8"));
const playwrightVersion = readJson("playwright/package.json").version;
const browsers = readJson("playwright-core/browsers.json").browsers;

const BASE = "http://localhost:5173/";
const API = "http://127.0.0.1:8000";
const SEED = [
  ["11111111-1111-4111-8111-111111111111", "Water the plants"],
  ["22222222-2222-4222-8222-222222222222", "Call the bank"],
  ["33333333-3333-4333-8333-333333333333", "Book train tickets"],
];
const PROPS = [
  "display", "color-scheme", "color", "background-color", "opacity",
  "border-top-color", "border-right-color", "border-bottom-color", "border-left-color",
  "border-top-width", "border-right-width", "border-bottom-width", "border-left-width",
  "border-top-style", "border-radius", "outline-color", "outline-style", "outline-width",
  "outline-offset", "box-shadow", "font-family", "font-size", "font-weight", "line-height",
  "padding-top", "padding-right", "padding-bottom", "padding-left",
  "margin-top", "margin-right", "margin-bottom", "margin-left",
];

fs.mkdirSync(outDir, { recursive: true });
const browser = await chromium.launch({
  args: ["--host-resolver-rules=MAP localhost 127.0.0.1"],
});
const context = await browser.newContext({
  viewport: { width: 1280, height: 800 },
  deviceScaleFactor: 1,
  reducedMotion: "reduce",
  colorScheme: "light",
  locale: "en-US",
  timezoneId: "UTC",
});
const page = await context.newPage();
page.on("dialog", (dialog) => dialog.accept());
const browserLog = [];
page.on("console", (m) => browserLog.push(`console.${m.type()}: ${m.text()}`));
page.on("requestfailed", (r) => browserLog.push(`request failed: ${r.method()} ${r.url()} ${r.failure()?.errorText}`));
page.on("response", (r) => { if (r.status() >= 400) browserLog.push(`HTTP ${r.status()}: ${r.request().method()} ${r.url()}`); });
async function fail(err) {
  try {
    await page.screenshot({ path: path.join(outDir, "error.png") });
    fs.writeFileSync(path.join(outDir, "error.log"), `${err.stack}\n\n${browserLog.join("\n")}\n`);
  } finally {
    console.error(err.message);
    await browser.close();
    process.exit(1);
  }
}

async function stylesOfAllElements() {
  return page.evaluate((props) => {
    const keyOf = (el) => {
      const parts = [];
      for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
        const same = e.parentElement
          ? [...e.parentElement.children].filter((c) => c.tagName === e.tagName)
          : [e];
        parts.unshift(`${e.tagName.toLowerCase()}[${same.indexOf(e) + 1}]`);
      }
      return parts.join(">");
    };
    const out = {};
    for (const el of document.querySelectorAll("*")) {
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      const cs = getComputedStyle(el);
      if (cs.display === "none" || cs.visibility === "hidden") continue;
      const text = [...el.childNodes]
        .filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join(" ").slice(0, 40);
      const entry = { text, box: [r.x, r.y, r.width, r.height].map((v) => Math.round(v)) };
      for (const p of props) entry[p] = cs.getPropertyValue(p);
      out[keyOf(el)] = entry;
    }
    return out;
  }, PROPS);
}

async function shot(name) {
  await page.mouse.move(1279, 799);
  await page.waitForLoadState("networkidle");
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(outDir, `${name}.png`), animations: "disabled", caret: "hide" });
  fs.writeFileSync(path.join(outDir, `${name}.styles.json`),
    JSON.stringify(await stylesOfAllElements(), null, 1) + "\n");
  console.log(`captured ${name}`);
}

const input = () => page.getByRole("textbox", { name: "Add a todo item" });
// A todo title shares its element with the Edit and Delete buttons, so titles
// are matched as substrings; no title used here contains another. Toast
// titles have their own element and match exactly.
const toast = (title) => page.getByText(title, { exact: true });

try {
  // Capture a new todo
  await page.goto(BASE);
  await page.getByText("No todos yet. Add one above!").waitFor();
  await shot("01-list-empty");
  await input().click();
  await page.keyboard.type("Buy milk");
  await shot("02-create-typed");
  await page.keyboard.press("Enter");
  await page.getByText("Buy milk").waitFor();
  await toast("Todo created").waitFor();
  await shot("03-create-done");

  // Review my todo list
  for (const [id, title] of SEED) {
    const res = await fetch(`${API}/todo`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, title }),
    });
    if (!res.ok) throw new Error(`seeding ${title} failed: ${res.status}`);
  }
  await page.reload();
  for (const [, title] of SEED) await page.getByText(title).waitFor();
  await shot("04-list-several");

  // Rename a todo
  await page.getByRole("button", { name: "Edit" }).first().click();
  await page.getByPlaceholder("Edit todo").waitFor();
  await shot("05-edit-open");
  await page.getByPlaceholder("Edit todo").fill("Buy oat milk");
  await page.getByRole("button", { name: "Save" }).click();
  await page.getByText("Buy oat milk").waitFor();
  await toast("Todo updated").waitFor();
  await shot("06-edit-saved");

  // Delete a todo
  await page.reload();
  await page.getByText("Buy oat milk").waitFor();
  await page.getByRole("button", { name: "Delete" }).first().click();
  await toast("Todo deleted").waitFor();
  await page.getByText("Buy oat milk").waitFor({ state: "detached" });
  await shot("07-delete-done");

  // Validation error on create
  await page.reload();
  await input().click();
  await page.keyboard.type("   ");
  await page.keyboard.press("Enter");
  await page.getByText("Todo title cannot be empty").waitFor();
  await shot("08-validation-error");

} catch (err) {
  await fail(err);
}

const chromiumEntry = browsers.find((b) => b.name === "chromium-headless-shell") || browsers.find((b) => b.name === "chromium");
fs.writeFileSync(path.join(outDir, "capture.json"), JSON.stringify({
  playwright: playwrightVersion,
  browser: `chromium ${browser.version()}`,
  chromium_revision: chromiumEntry && chromiumEntry.revision,
  node: process.version,
  runner_lock_sha256: runnerLockSha,
  viewport: "1280x800@1x",
  reduced_motion: true,
  dist_sha256: fs.readFileSync(distShaFile, "utf8").trim().split("\n"),
}, null, 1) + "\n");
await browser.close();
