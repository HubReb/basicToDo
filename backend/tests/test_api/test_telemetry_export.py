"""D-09: the app must not export OpenTelemetry data (brief Q3).

FastAPI 0.142 adds OTLP exporters at startup as soon as
OTEL_EXPORTER_OTLP_ENDPOINT is set. The app opts out with
telemetry={"auto_configure": False}, which keeps the legacy behaviour.

Each case runs in a subprocess, because OpenTelemetry providers are
process-global, with the exporter pointed at a local sink that records
every request it receives. The control case shows that a plain FastAPI()
does export in the same setup, so an empty sink means something.
"""
import http.server
import importlib.util
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

APP_UNDER_TEST = """
from fastapi.testclient import TestClient
from backend.app.api.api import app
"""

PLAIN_FASTAPI = """
from fastapi import FastAPI
from fastapi.testclient import TestClient
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}
"""

EXERCISE = """
with TestClient(app) as client:
    client.get("/")
    client.get("/todo/not-a-uuid")
try:
    from opentelemetry import _logs, metrics, trace
except ImportError:
    pass
else:
    for provider in (trace.get_tracer_provider(), metrics.get_meter_provider(),
                     _logs.get_logger_provider()):
        flush = getattr(provider, "force_flush", None)
        if flush:
            flush()
"""


class _RecordingHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.server.received.append(self.path)
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


@pytest.fixture
def otlp_sink():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _RecordingHandler)
    server.received = []
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server
    server.shutdown()
    server.server_close()


def run_with_otlp_endpoint(code, sink, tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith("OTEL_")}
    env["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"http://127.0.0.1:{sink.server_address[1]}"
    env["DATABASE_URL"] = f"sqlite:///{tmp_path / 'telemetry.db'}"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr


def test_app_exports_nothing_when_an_otlp_endpoint_is_set(otlp_sink, tmp_path):
    run_with_otlp_endpoint(APP_UNDER_TEST + EXERCISE, otlp_sink, tmp_path)

    assert otlp_sink.received == []


@pytest.mark.skipif(
    importlib.util.find_spec("fastapi.telemetry") is None,
    reason="FastAPI < 0.142 has no native telemetry, so there is nothing to control",
)
def test_control_plain_fastapi_does_export(otlp_sink, tmp_path):
    run_with_otlp_endpoint(PLAIN_FASTAPI + EXERCISE, otlp_sink, tmp_path)

    assert "/v1/traces" in otlp_sink.received
