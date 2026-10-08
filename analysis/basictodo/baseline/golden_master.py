#!/usr/bin/env python3
"""HTTP golden master for the basicToDo backend.

    golden_master.py capture <base-url> <out.json> [provenance.json ...]
    golden_master.py diff <a.json> <b.json>

capture replays one fixed request sequence against a running server (start
it with run_golden_master.sh) and records every response: status, reason,
all headers and the raw body. diff compares two captures and exits 1 on any
difference.

The client is stdlib-only, so it is byte-for-byte the same whichever lock
the server runs on. The sequence writes to the database, so every capture
needs a fresh one.

Only timestamp values are normalized. Their digits become format letters,
while separators, the fraction length and the UTC offset stay literal:
    2026-10-05T13:40:21.123456        -> YYYY-MM-DDThh:mm:ss.ffffff
    2026-10-05T13:40:21.123456+00:00  -> YYYY-MM-DDThh:mm:ss.ffffff+00:00
    Sun, 05 Oct 2026 13:40:21 GMT     -> Www, DD Mmm YYYY hh:mm:ss GMT
A change of format, precision or offset therefore still shows up as a diff.

Zero microseconds: Python omits the fraction when the microsecond is
exactly 0. A JSON field value without a fraction is masked as .ffffff when
every other distinct value of the same field in the capture has 6 digits.
The rule is per field, so a field that is always second-precision (such as
updated_at, which SQLite fills) keeps showing no fraction.

Timestamp basis: masking hides which clock a naive timestamp came from. So,
before masking, every naive timestamp in a JSON body is compared with the
capture's time window, read from the local clock and from the UTC clock,
with a tolerance of TOLERANCE_S seconds. The record keeps the result per
JSON path as "local", "utc", "local=utc" (the machine's offset was 0) or
"neither", never the offset itself, so captures on both sides of a DST
change stay comparable. A timestamp that carries an offset is converted to
UTC and compared with the UTC window: "utc" or "neither".

Requests may override the Host header, and a request given as chunks is
sent with Transfer-Encoding: chunked and no Content-Length (http.client
does this for an iterable body). The record stores the joined bytes.

Headers are compared as a sorted list of [lowercased name, value]; their
order on the wire is not compared.

Provenance: run_golden_master.sh passes the records provenance.py wrote
inside init_db and inside the server process. They are stored next to the
responses and printed by diff, but never compared.
"""

import datetime
import difflib
import http.client
import json
import re
import sys
import urllib.parse

ID = "11111111-2222-3333-4444-555555555555"
ID2 = "11111111-2222-3333-4444-666666666666"
ID_LONG_TITLE = "11111111-2222-3333-4444-777777777777"
ID_EXTRA_FIELD = "11111111-2222-3333-4444-888888888888"
ID_UPPER = "AAAAAAAA-2222-3333-4444-555555555555"
UNKNOWN = "99999999-2222-3333-4444-555555555555"
ALLOWED_ORIGIN = "http://localhost:5173"
OTHER_ORIGIN = "http://evil.example"
JSON = {"Content-Type": "application/json"}


def req(label, method, path, body=None, headers=None, raw=None, chunks=None):
    """One request. body is JSON-encoded; raw is sent as-is; chunks are sent chunked."""
    hdrs = dict(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        hdrs = {**JSON, **hdrs}
    elif raw is not None:
        data = raw
    return {
        "label": label,
        "method": method,
        "path": path,
        "headers": hdrs,
        "body": data,
        "chunks": chunks,
    }


def padded(todo_id, size):
    """A valid create body, padded with JSON whitespace to exactly size bytes."""
    data = json.dumps({"id": todo_id, "title": "Padded"}).encode()
    return data + b" " * (size - len(data))


def sequence():
    s = []
    add = s.append
    # Health
    add(req("GET root", "GET", "/"))
    add(req("HEAD root", "HEAD", "/"))
    # Create (RULE-008 and the input validators)
    add(
        req(
            "POST create ok",
            "POST",
            "/todo",
            {"id": ID, "title": " Wash ", "description": "d"},
        )
    )
    add(req("POST create ok 2", "POST", "/todo", {"id": ID2, "title": "Second"}))
    add(req("POST duplicate id", "POST", "/todo", {"id": ID, "title": "Dup"}))
    add(req("POST missing id", "POST", "/todo", {"title": "x"}))
    add(req("POST malformed id", "POST", "/todo", {"id": "nope", "title": "x"}))
    add(req("POST empty id", "POST", "/todo", {"id": "", "title": "x"}))
    add(req("POST null id", "POST", "/todo", {"id": None, "title": "x"}))
    add(
        req(
            "POST whitespace title",
            "POST",
            "/todo",
            {"id": "22222222-2222-3333-4444-555555555555", "title": "   "},
        )
    )
    add(
        req(
            "POST title int",
            "POST",
            "/todo",
            {"id": "33333333-2222-3333-4444-555555555555", "title": 123},
        )
    )
    add(
        req(
            "POST title missing",
            "POST",
            "/todo",
            {"id": "33333333-2222-3333-4444-666666666666"},
        )
    )
    add(
        req(
            "POST title 255 chars",
            "POST",
            "/todo",
            {"id": ID_LONG_TITLE, "title": "t" * 255},
        )
    )
    add(
        req(
            "POST title 256 chars",
            "POST",
            "/todo",
            {"id": "33333333-2222-3333-4444-777777777777", "title": "t" * 256},
        )
    )
    add(
        req(
            "POST description 256 chars",
            "POST",
            "/todo",
            {
                "id": "33333333-2222-3333-4444-888888888888",
                "title": "ok",
                "description": "d" * 256,
            },
        )
    )
    add(req("POST invalid json", "POST", "/todo", raw=b"{bad", headers=JSON))
    add(
        req(
            "POST text/plain body",
            "POST",
            "/todo",
            raw=b'{"id":"44444444-2222-3333-4444-555555555555","title":"x"}',
            headers={"Content-Type": "text/plain"},
        )
    )
    add(req("POST no body", "POST", "/todo"))
    add(
        req(
            "POST SQL keyword title",
            "POST",
            "/todo",
            {"id": "55555555-2222-3333-4444-555555555555", "title": "a; drop table"},
        )
    )
    add(
        req(
            "POST quirk 'Todo to delete' (blocklist)",
            "POST",
            "/todo",
            {"id": "55555555-2222-3333-4444-666666666666", "title": "Todo to delete"},
        )
    )
    add(
        req(
            "POST unknown extra field",
            "POST",
            "/todo",
            {"id": ID_EXTRA_FIELD, "title": "Extra", "foo": 1},
        )
    )
    add(req("POST uppercase id", "POST", "/todo", {"id": ID_UPPER, "title": "Upper"}))
    # Update, including lax bool coercion and the done=null quirk (500)
    for v in [
        "yes",
        "on",
        "1",
        1,
        "true",
        "TRUE",
        "y",
        "t",
        1.0,
        "false",
        0,
        "off",
        "no",
        "maybe",
        2,
        None,
        [],
        {},
    ]:
        add(req(f"PUT done={v!r}", "PUT", f"/todo/{ID2}", {"done": v}))
    add(
        req(
            "PUT title update",
            "PUT",
            f"/todo/{ID}",
            {"title": "New", "description": "x"},
        )
    )
    add(req("PUT empty object", "PUT", f"/todo/{ID}", {}))
    add(req("PUT whitespace title", "PUT", f"/todo/{ID}", {"title": "   "}))
    add(req("PUT unknown id", "PUT", f"/todo/{UNKNOWN}", {"title": "New"}))
    add(req("PUT malformed path id", "PUT", "/todo/xyz", {"title": "New"}))
    # Read one
    add(req("GET one", "GET", f"/todo/{ID}"))
    add(req("GET one uppercase id", "GET", f"/todo/{ID.upper()}"))
    add(req("GET one urn id", "GET", f"/todo/urn:uuid:{ID}"))
    add(req("GET one hex id without dashes", "GET", f"/todo/{ID.replace('-', '')}"))
    add(req("GET one unknown id", "GET", f"/todo/{UNKNOWN}"))
    add(req("GET one malformed id", "GET", "/todo/not-a-uuid"))
    # List and paging
    add(req("GET list", "GET", "/todo"))
    add(req("GET list limit=abc", "GET", "/todo?limit=abc"))
    add(req("GET list limit=-1", "GET", "/todo?limit=-1&page=1"))
    add(req("GET list page=0", "GET", "/todo?limit=10&page=0"))
    add(req("GET list limit=1.5", "GET", "/todo?limit=1.5"))
    add(req("GET list limit=' 2 '", "GET", "/todo?limit=%202%20"))
    add(req("GET list limit=2 page=2", "GET", "/todo?limit=2&page=2"))
    add(req("GET list trailing slash (307)", "GET", "/todo/"))
    # Methods and routes
    add(req("PATCH todo (405)", "PATCH", f"/todo/{ID}", {}))
    add(req("DELETE collection (405)", "DELETE", "/todo"))
    add(req("GET unknown route", "GET", "/nope"))
    # CORS
    add(
        req(
            "OPTIONS preflight allowed",
            "OPTIONS",
            "/todo",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "PUT",
                "Access-Control-Request-Headers": "content-type",
            },
        )
    )
    add(
        req(
            "OPTIONS preflight allowed DELETE",
            "OPTIONS",
            f"/todo/{ID}",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "DELETE",
            },
        )
    )
    add(
        req(
            "OPTIONS preflight disallowed origin",
            "OPTIONS",
            "/todo",
            headers={"Origin": OTHER_ORIGIN, "Access-Control-Request-Method": "PUT"},
        )
    )
    add(
        req(
            "OPTIONS preflight 127.0.0.1 origin",
            "OPTIONS",
            "/todo",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
    )
    add(
        req("GET list CORS allowed", "GET", "/todo", headers={"Origin": ALLOWED_ORIGIN})
    )
    add(
        req(
            "GET list CORS disallowed", "GET", "/todo", headers={"Origin": OTHER_ORIGIN}
        )
    )
    add(
        req(
            "GET 404 CORS allowed",
            "GET",
            f"/todo/{UNKNOWN}",
            headers={"Origin": ALLOWED_ORIGIN},
        )
    )
    add(
        req(
            "POST 422 CORS allowed",
            "POST",
            "/todo",
            {"title": "x"},
            headers={"Origin": ALLOWED_ORIGIN},
        )
    )
    # Delete (RULE-031) and re-create (RULE-008)
    add(req("DELETE ok", "DELETE", f"/todo/{ID}"))
    add(req("DELETE again (404)", "DELETE", f"/todo/{ID}"))
    add(req("DELETE malformed id", "DELETE", "/todo/zzz"))
    add(req("DELETE unknown id", "DELETE", f"/todo/{UNKNOWN}"))
    add(req("GET deleted", "GET", f"/todo/{ID}"))
    add(req("PUT deleted", "PUT", f"/todo/{ID}", {"title": "Back"}))
    add(req("PUT deleted restore attempt", "PUT", f"/todo/{ID}", {"deleted": False}))
    add(
        req(
            "POST re-create deleted id (409)",
            "POST",
            "/todo",
            {"id": ID, "title": "Again"},
        )
    )
    add(req("GET list after delete", "GET", "/todo?limit=100"))
    # API documentation
    add(req("GET openapi.json", "GET", "/openapi.json"))
    add(req("GET docs", "GET", "/docs"))
    add(req("GET redoc", "GET", "/redoc"))
    add(req("GET docs oauth2-redirect", "GET", "/docs/oauth2-redirect"))
    # Phase 5 additions (appended, so the requests above keep their state)
    emoji = "\U0001f600" * 255
    add(req("GET root bad Host", "GET", "/", headers={"Host": "evil.example"}))
    add(
        req(
            "POST body 16384 bytes",
            "POST",
            "/todo",
            raw=padded("66666666-2222-3333-4444-000000000001", 16384),
            headers=JSON,
        )
    )
    add(
        req(
            "POST body 16385 bytes",
            "POST",
            "/todo",
            raw=padded("66666666-2222-3333-4444-000000000002", 16385),
            headers=JSON,
        )
    )
    add(
        req(
            "POST body 16385 bytes CORS allowed",
            "POST",
            "/todo",
            raw=padded("66666666-2222-3333-4444-000000000003", 16385),
            headers={**JSON, "Origin": ALLOWED_ORIGIN},
        )
    )
    big = padded("66666666-2222-3333-4444-000000000004", 20000)
    add(
        req(
            "POST body 20000 bytes chunked",
            "POST",
            "/todo",
            chunks=[big[i : i + 4096] for i in range(0, len(big), 4096)],
            headers=JSON,
        )
    )
    add(
        req(
            "POST create for big DELETE",
            "POST",
            "/todo",
            {"id": "66666666-2222-3333-4444-000000000005", "title": "Remove me"},
        )
    )
    add(
        req(
            "DELETE with 20000-byte body",
            "DELETE",
            "/todo/66666666-2222-3333-4444-000000000005",
            raw=b" " * 20000,
            headers=JSON,
        )
    )
    add(
        req(
            "POST maximal valid request (4-byte UTF-8, ensure_ascii)",
            "POST",
            "/todo",
            raw=json.dumps(
                {
                    "id": "66666666-2222-3333-4444-000000000006",
                    "title": emoji,
                    "description": emoji,
                }
            ).encode(),
            headers=JSON,
        )
    )
    add(
        req(
            "POST maximal valid request (4-byte UTF-8, raw)",
            "POST",
            "/todo",
            raw=json.dumps(
                {
                    "id": "66666666-2222-3333-4444-000000000007",
                    "title": emoji,
                    "description": emoji,
                },
                ensure_ascii=False,
            ).encode(),
            headers=JSON,
        )
    )
    add(
        req(
            "POST JSON body without Content-Type",
            "POST",
            "/todo",
            raw=b'{"id":"66666666-2222-3333-4444-000000000008","title":"x"}',
        )
    )
    add(
        req(
            "PUT text/plain body",
            "PUT",
            f"/todo/{ID2}",
            raw=b'{"title":"Plain"}',
            headers={"Content-Type": "text/plain"},
        )
    )
    add(req("PUT title null", "PUT", f"/todo/{ID2}", {"title": None}))
    add(
        req(
            "PUT done and title",
            "PUT",
            f"/todo/{ID_EXTRA_FIELD}",
            {"done": True, "title": "Done and renamed"},
        )
    )
    add(
        req(
            "POST NUL in title",
            "POST",
            "/todo",
            {"id": "66666666-2222-3333-4444-000000000009", "title": "a\u0000bc"},
        )
    )
    add(
        req(
            "POST lone surrogate title",
            "POST",
            "/todo",
            raw=b'{"id":"66666666-2222-3333-4444-000000000010","title":"\\ud800"}',
            headers=JSON,
        )
    )
    add(
        req(
            "POST tab in title",
            "POST",
            "/todo",
            {"id": "66666666-2222-3333-4444-000000000011", "title": "a\tb"},
        )
    )
    add(
        req(
            "POST U+001C at the end of the title",
            "POST",
            "/todo",
            {"id": "66666666-2222-3333-4444-000000000012", "title": "ab\u001c"},
        )
    )
    add(
        req(
            "POST multiline description",
            "POST",
            "/todo",
            {
                "id": "66666666-2222-3333-4444-000000000013",
                "title": "Lines",
                "description": "one\ntwo\tthree\r\n",
            },
        )
    )
    add(
        req(
            "POST title 255 chars between spaces",
            "POST",
            "/todo",
            {
                "id": "66666666-2222-3333-4444-000000000014",
                "title": " " + "s" * 255 + " ",
            },
        )
    )
    add(req("GET list limit=100", "GET", "/todo?limit=100"))
    add(req("GET list limit=101", "GET", "/todo?limit=101"))
    return s


TOLERANCE_S = 5
ISO_CORE = (
    r"\b(?P<date>\d{4}-\d{2}-\d{2})(?P<sep>[T ])(?P<time>\d{2}:\d{2}:\d{2})"
    r"(?P<frac>\.\d+)?(?P<off>Z|[+-]\d{2}:?\d{2})?"
)
# An optional JSON key in front of the value tells the zero-microsecond rule
# which field the timestamp belongs to.
ISO = re.compile(r'(?P<prefix>"(?P<key>[A-Za-z0-9_]+)"\s*:\s*")?' + ISO_CORE)
ISO_FULL = re.compile(r"^" + ISO_CORE + r"$")
HTTP_DATE = re.compile(
    r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun), \d{2} "
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4} \d{2}:\d{2}:\d{2} GMT\b"
)


def field_fraction_lengths(bodies):
    """{field: {distinct raw value: fraction digits}} over all JSON bodies."""
    seen = {}
    for body in bodies:
        for m in ISO.finditer(body):
            if m.group("key"):
                frac = len(m.group("frac")) - 1 if m.group("frac") else 0
                seen.setdefault(m.group("key"), {})[
                    m.group(0)[len(m.group("prefix")) :]
                ] = frac
    return seen


def mask_timestamps(text, fraction_lengths=None):
    def iso(m):
        digits = len(m.group("frac")) - 1 if m.group("frac") else 0
        key = m.group("key")
        if digits == 0 and key and fraction_lengths:
            value = m.group(0)[len(m.group("prefix")) :]
            others = [n for v, n in fraction_lengths.get(key, {}).items() if v != value]
            if others and all(n == 6 for n in others):
                digits = 6
        frac = "." + "f" * digits if digits else ""
        return f"{m.group('prefix') or ''}YYYY-MM-DD{m.group('sep')}hh:mm:ss{frac}{m.group('off') or ''}"

    text = ISO.sub(iso, text)
    return HTTP_DATE.sub("Www, DD Mmm YYYY hh:mm:ss GMT", text)


def json_strings(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from json_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from json_strings(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def timestamp_basis(body, window):
    """{json path: clock} for every naive timestamp in a JSON body."""
    try:
        parsed = json.loads(body)
    except ValueError:
        return {}
    (local_start, local_end), (utc_start, utc_end) = window
    tol = datetime.timedelta(seconds=TOLERANCE_S)
    basis = {}
    for path, value in json_strings(parsed):
        m = ISO_FULL.match(value)
        if not m:
            continue
        if m.group("off"):
            ts = datetime.datetime.fromisoformat(value).astimezone(
                datetime.timezone.utc
            )
            ts = ts.replace(tzinfo=None)
            basis[path] = "utc" if utc_start - tol <= ts <= utc_end + tol else "neither"
            continue
        ts = datetime.datetime.fromisoformat(value)
        is_local = local_start - tol <= ts <= local_end + tol
        is_utc = utc_start - tol <= ts <= utc_end + tol
        basis[path] = (
            "local=utc"
            if is_local and is_utc
            else "local" if is_local else "utc" if is_utc else "neither"
        )
    return basis


def now_pair():
    """(local naive, UTC naive) read from the system clock."""
    return (
        datetime.datetime.now(),
        datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
    )


def capture(base_url, out_path, provenance_paths=()):
    url = urllib.parse.urlsplit(base_url)
    local_start, utc_start = now_pair()
    raw = []
    for r in sequence():
        conn = http.client.HTTPConnection(url.hostname, url.port, timeout=30)
        if r["chunks"] is not None:
            conn.request(
                r["method"], r["path"], body=iter(r["chunks"]), headers=r["headers"]
            )
        else:
            conn.request(r["method"], r["path"], body=r["body"], headers=r["headers"])
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", errors="replace")
        local_now, utc_now = now_pair()
        window = ((local_start, local_now), (utc_start, utc_now))
        raw.append((r, resp.status, resp.reason, resp.getheaders(), body, window))
        conn.close()

    fraction_lengths = field_fraction_lengths(body for *_, body, _ in raw)
    records = []
    for r, status, reason, headers, body, window in raw:
        records.append(
            {
                "label": r["label"],
                "request": {
                    "method": r["method"],
                    "path": r["path"],
                    "headers": r["headers"],
                    "body": (
                        r["body"].decode()
                        if r["body"] is not None
                        else b"".join(r["chunks"]).decode() if r["chunks"] else None
                    ),
                    "chunked": r["chunks"] is not None,
                },
                "status": status,
                "reason": reason,
                "headers": sorted([k.lower(), mask_timestamps(v)] for k, v in headers),
                "timestamp_basis": timestamp_basis(body, window),
                "body": mask_timestamps(body, fraction_lengths),
            }
        )
    with open(out_path, "w", encoding="utf-8") as f:
        provenance = [
            json.load(open(path, encoding="utf-8")) for path in provenance_paths
        ]
        json.dump(
            {"provenance": provenance, "responses": records},
            f,
            indent=1,
            ensure_ascii=False,
        )
        f.write("\n")
    print(f"captured {len(records)} responses -> {out_path}")


def pretty(body):
    try:
        return json.dumps(
            json.loads(body), indent=1, sort_keys=True, ensure_ascii=False
        ).splitlines()
    except ValueError:
        return body.splitlines()


def load(path):
    """(provenance, responses). Captures made before provenance existed are a bare list."""
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, list):
        return [], data
    return data["provenance"], data["responses"]


def diff(a_path, b_path):
    """Compares responses only; provenance is printed, never compared."""
    (prov_a, a), (prov_b, b) = load(a_path), load(b_path)
    for side, prov in (("a", prov_a), ("b", prov_b)):
        for r in prov or [{"process": "(no provenance recorded)"}]:
            print(
                f"provenance {side}: [{r['process']}] tree {r.get('tree')}, venv {r.get('venv')}, "
                f"fastapi {r.get('fastapi')}, backend.app -> {r.get('backend.app')}, "
                f"outside tree: {r.get('app_modules_outside_tree') or 'none'}"
            )
    if [r["label"] for r in a] != [r["label"] for r in b]:
        print("request sequences differ; captures are not comparable")
        return 2
    n_diff = 0
    for ra, rb in zip(a, b):
        out = []
        if (ra["status"], ra["reason"]) != (rb["status"], rb["reason"]):
            out.append(
                f"  status: {ra['status']} {ra['reason']} -> {rb['status']} {rb['reason']}"
            )
        ha = {tuple(h) for h in ra["headers"]}
        hb = {tuple(h) for h in rb["headers"]}
        for k, v in sorted(ha - hb):
            out.append(f"  - header {k}: {v}")
        for k, v in sorted(hb - ha):
            out.append(f"  + header {k}: {v}")
        basis_a, basis_b = ra.get("timestamp_basis", {}), rb.get("timestamp_basis", {})
        for path in sorted(set(basis_a) | set(basis_b)):
            if basis_a.get(path) != basis_b.get(path):
                out.append(
                    f"  timestamp basis {path}: {basis_a.get(path)} -> {basis_b.get(path)}"
                )
        if ra["body"] != rb["body"]:
            if pretty(ra["body"]) == pretty(rb["body"]):
                out.append("  body: same JSON content, different serialization")
            else:
                for line in difflib.unified_diff(
                    pretty(ra["body"]), pretty(rb["body"]), "a", "b", n=1, lineterm=""
                ):
                    if not line.startswith(("---", "+++")):
                        out.append(f"  body {line}")
        if out:
            n_diff += 1
            print(
                f"### {ra['label']}  ({ra['request']['method']} {ra['request']['path']})"
            )
            print("\n".join(out))
    print(f"{n_diff} of {len(a)} responses differ")
    return 1 if n_diff else 0


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "capture":
        capture(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif len(sys.argv) == 4 and sys.argv[1] == "diff":
        sys.exit(diff(sys.argv[2], sys.argv[3]))
    else:
        sys.exit(__doc__)
