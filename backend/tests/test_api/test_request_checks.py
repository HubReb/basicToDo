"""Checks on every request before a route runs: Q8b, SEC-003, SEC-008.

Q8b (the owner's decision): "cap the request body in middleware at 16 KiB,
answer 413. Count streamed bytes so chunked requests without Content-Length
are capped too. Tests: Content-Length over the limit, chunked body over the
limit, and a maximal valid request (255-char title and description, 4-byte
UTF-8) passes."

TestClient hands a chunked body to the app as one message, so counting
across messages is tested on the middleware with a hand-written ASGI
receive, and end to end against a real uvicorn server.
"""

import http.client
import json
import os
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Iterator
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import text

from backend.app.api.body_limit import MAX_BODY_BYTES, BodyLimitMiddleware
from backend.app.data_access.schema import prepare_database

REPO_ROOT = Path(__file__).resolve().parents[3]
ALLOWED_ORIGIN = "http://localhost:5173"
LIMIT_DETAIL = {"detail": f"Request body larger than {MAX_BODY_BYTES} bytes"}
# U+1F600, four bytes in UTF-8; twelve as a JSON escape (😀).
EMOJI = "\U0001f600"


def padded(payload: dict, size: int) -> bytes:
    """The payload as JSON, padded with spaces to exactly size bytes."""
    body = json.dumps(payload).encode()
    assert len(body) <= size
    return body + b" " * (size - len(body))


def maximal(todo_id: uuid.UUID) -> dict:
    return {"id": str(todo_id), "title": EMOJI * 255, "description": EMOJI * 255}


def count_todos(engine) -> int:
    with engine.connect() as conn:
        return conn.execute(text('SELECT COUNT(*) FROM "toDo"')).scalar()


def post_json(client, body: bytes, **headers):
    return client.post(
        "/todo", content=body, headers={"Content-Type": "application/json", **headers}
    )


class Recorder:
    """An inner ASGI app that records what it received."""

    def __init__(self) -> None:
        self.messages: list[dict] = []
        self.called = False

    async def __call__(self, scope, receive, send) -> None:
        self.called = True
        self.messages.append(await receive())
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


async def run_middleware(messages: list[dict], headers: list[tuple] | None = None):
    """Run BodyLimitMiddleware on the messages; returns (inner app, sent, receive calls)."""
    inner = Recorder()
    pending = list(messages)
    calls = 0
    sent: list[dict] = []

    async def receive() -> dict:
        nonlocal calls
        calls += 1
        return pending.pop(0) if pending else {"type": "http.disconnect"}

    async def send(message: dict) -> None:
        sent.append(message)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/todo",
        "headers": headers or [],
    }
    await BodyLimitMiddleware(inner, max_bytes=MAX_BODY_BYTES)(scope, receive, send)
    return inner, sent, calls


def chunks(*sizes: int) -> list[dict]:
    return [
        {
            "type": "http.request",
            "body": b"x" * size,
            "more_body": index < len(sizes) - 1,
        }
        for index, size in enumerate(sizes)
    ]


class TestBodyLimitMiddleware:
    @pytest.mark.asyncio
    async def test_a_content_length_over_the_limit_is_refused_unread(self):
        inner, sent, calls = await run_middleware(
            chunks(10), headers=[(b"content-length", b"16385")]
        )

        assert (inner.called, calls) == (False, 0)
        assert sent[0]["status"] == 413
        assert dict(sent[0]["headers"])[b"content-type"] == b"application/json"
        assert json.loads(sent[1]["body"]) == LIMIT_DETAIL

    @pytest.mark.asyncio
    async def test_streamed_messages_are_counted_until_the_limit_is_crossed(self):
        inner, sent, calls = await run_middleware(chunks(8000, 8000, 8000, 8000))

        assert inner.called is False
        assert calls == 3  # the third message crosses 16384; the fourth is not read
        assert sent[0]["status"] == 413
        assert json.loads(sent[1]["body"]) == LIMIT_DETAIL

    @pytest.mark.asyncio
    async def test_exactly_the_limit_in_several_messages_is_replayed_as_one(self):
        inner, sent, _ = await run_middleware(chunks(8000, 8000, 384))

        assert inner.messages == [
            {"type": "http.request", "body": b"x" * MAX_BODY_BYTES, "more_body": False}
        ]
        assert sent[0]["status"] == 200

    @pytest.mark.asyncio
    @pytest.mark.parametrize("declared", [b"abc", b"+5", b"1e9", "１".encode()])
    async def test_a_content_length_that_is_no_plain_number_is_not_trusted(
        self, declared
    ):
        inner, _, _ = await run_middleware(
            chunks(10), headers=[(b"content-length", declared)]
        )
        refused, sent, _ = await run_middleware(
            chunks(MAX_BODY_BYTES + 1), headers=[(b"content-length", declared)]
        )

        assert inner.called is True
        assert (refused.called, sent[0]["status"]) == (False, 413)

    @pytest.mark.asyncio
    async def test_a_disconnect_while_reading_ends_the_request(self):
        inner, sent, _ = await run_middleware(
            [{"type": "http.request", "body": b"x", "more_body": True}]
        )

        assert (inner.called, sent) == (False, [])

    @pytest.mark.asyncio
    async def test_other_scopes_pass_through(self):
        called = []

        async def app(scope, receive, send):
            called.append(scope["type"])

        await BodyLimitMiddleware(app)({"type": "lifespan"}, None, None)

        assert called == ["lifespan"]


class TestBodyLimitThroughTheApp:
    def test_content_length_over_the_limit_is_a_413(self, real_client, real_db_engine):
        response = post_json(
            real_client, padded({"id": str(uuid.uuid4()), "title": "x"}, 16385)
        )

        assert response.status_code == 413
        assert response.headers["content-type"] == "application/json"
        assert response.json() == LIMIT_DETAIL
        assert count_todos(real_db_engine) == 0

    def test_a_chunked_body_over_the_limit_is_a_413(self, real_client, real_db_engine):
        body = padded({"id": str(uuid.uuid4()), "title": "x"}, 20000)

        def stream() -> Iterator[bytes]:
            for start in range(0, len(body), 4096):
                yield body[start : start + 4096]

        response = real_client.post(
            "/todo", content=stream(), headers={"Content-Type": "application/json"}
        )

        assert response.request.headers.get("transfer-encoding") == "chunked"
        assert "content-length" not in response.request.headers
        assert response.status_code == 413
        assert count_todos(real_db_engine) == 0

    def test_exactly_the_limit_passes(self, real_client, real_db_engine):
        response = post_json(
            real_client, padded({"id": str(uuid.uuid4()), "title": "x"}, 16384)
        )

        assert response.status_code == 200
        assert count_todos(real_db_engine) == 1

    @pytest.mark.parametrize(
        "ensure_ascii", [True, False], ids=["escaped", "raw UTF-8"]
    )
    def test_a_maximal_valid_request_passes(
        self, real_client, real_db_engine, ensure_ascii
    ):
        todo_id = uuid.uuid4()
        body = json.dumps(maximal(todo_id), ensure_ascii=ensure_ascii).encode()
        assert len(body) == (6198 if ensure_ascii else 2118)

        response = post_json(real_client, body)

        assert response.status_code == 200
        with real_db_engine.connect() as conn:
            stored = conn.execute(
                text('SELECT title, description FROM "toDo" WHERE id = :id'),
                {"id": todo_id.hex},
            ).one()
        assert tuple(stored) == (EMOJI * 255, EMOJI * 255)

    def test_no_handler_runs_for_an_oversized_delete(self, real_client):
        with patch(
            "backend.app.api.api.service.delete_todo", new=AsyncMock()
        ) as delete:
            response = real_client.request(
                "DELETE", f"/todo/{uuid.uuid4()}", content=b" " * 20000
            )

        assert response.status_code == 413
        delete.assert_not_called()

    def test_a_413_carries_cors_headers(self, real_client):
        response = post_json(real_client, b" " * 16385, Origin=ALLOWED_ORIGIN)

        assert response.status_code == 413
        assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


class TestJsonOnly:
    @pytest.mark.parametrize(
        "headers",
        [
            {},
            {"Content-Type": "text/plain"},
            {"Content-Type": "application/json-patch+json"},
        ],
        ids=["none", "text/plain", "json-patch"],
    )
    def test_a_body_not_declared_as_json_is_a_415(
        self, real_client, real_db_engine, headers
    ):
        body = json.dumps({"id": str(uuid.uuid4()), "title": "x"}).encode()

        response = real_client.post("/todo", content=body, headers=headers)

        assert response.status_code == 415
        assert response.json() == {"detail": "Content-Type must be application/json"}
        assert count_todos(real_db_engine) == 0

    @pytest.mark.parametrize(
        "content_type", ["application/json; charset=utf-8", "Application/JSON"]
    )
    def test_parameters_and_case_do_not_matter(self, real_client, content_type):
        body = json.dumps({"id": str(uuid.uuid4()), "title": "x"}).encode()

        response = real_client.post(
            "/todo", content=body, headers={"Content-Type": content_type}
        )

        assert response.status_code == 200

    def test_put_needs_json_too(self, real_client):
        todo_id = uuid.uuid4()
        assert (
            real_client.post(
                "/todo", json={"id": str(todo_id), "title": "Kept"}
            ).status_code
            == 200
        )

        response = real_client.put(
            f"/todo/{todo_id}",
            content=b'{"title": "Changed"}',
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 415
        assert (
            real_client.get(f"/todo/{todo_id}").json()["todo_entry"]["title"] == "Kept"
        )

    def test_requests_without_a_body_are_not_affected(self, real_client):
        todo_id = uuid.uuid4()
        real_client.post("/todo", json={"id": str(todo_id), "title": "x"})

        assert real_client.get("/todo").status_code == 200
        assert real_client.get(f"/todo/{todo_id}").status_code == 200
        assert real_client.delete(f"/todo/{todo_id}").status_code == 200


class TestHostAndCors:
    @pytest.mark.parametrize("host", ["localhost", "127.0.0.1:8000", "localhost:8000"])
    def test_configured_hosts_are_served(self, real_client, host):
        assert real_client.get("/", headers={"Host": host}).status_code == 200

    @pytest.mark.parametrize(
        "host", ["evil.example", "localhost.evil.example", "0.0.0.0:8000"]
    )
    def test_other_hosts_get_400_before_anything_runs(self, real_client, host):
        with patch(
            "backend.app.api.api.service.get_all_todos", new=AsyncMock()
        ) as listed:
            response = real_client.get("/todo", headers={"Host": host})

        assert response.status_code == 400
        listed.assert_not_called()

    def test_the_allowed_origin_gets_cors_headers_without_credentials(
        self, real_client
    ):
        response = real_client.get("/todo", headers={"Origin": ALLOWED_ORIGIN})

        assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
        assert "access-control-allow-credentials" not in response.headers

    def test_another_origin_gets_none(self, real_client):
        response = real_client.get("/todo", headers={"Origin": "https://evil.example"})

        assert "access-control-allow-origin" not in response.headers

    @pytest.mark.parametrize(
        "method, headers, allowed",
        [
            ("PUT", "content-type", True),
            ("DELETE", "accept", True),
            ("PATCH", "content-type", False),
            ("POST", "x-anything", False),
        ],
    )
    def test_preflight_allows_only_what_the_frontend_needs(
        self, real_client, method, headers, allowed
    ):
        response = real_client.options(
            "/todo",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": headers,
            },
        )

        assert (response.status_code == 200) is allowed


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture(scope="module")
def server(tmp_path_factory) -> Iterator[int]:
    """A real uvicorn server on 127.0.0.1 with a prepared database; yields its port."""
    database = tmp_path_factory.mktemp("uvicorn") / "todo.db"
    prepare_database(f"sqlite:///{database}")
    port = free_port()
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("BASICTODO_", "OTEL_"))
    }
    env["DATABASE_URL"] = f"sqlite:///{database}"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.app.api.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 30
        while True:
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                break
            except OSError:
                if process.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError(
                        process.stderr.read().decode() if process.stderr else ""
                    )
                time.sleep(0.1)
        yield port
    finally:
        process.terminate()
        process.wait(timeout=10)


def send(port: int, body, headers: dict) -> tuple[int, bytes]:
    """POST /todo; with Transfer-Encoding: chunked, http.client frames each part as a chunk."""
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        connection.request(
            "POST",
            "/todo",
            body=body,
            headers={"Content-Type": "application/json", **headers},
            encode_chunked=headers.get("Transfer-Encoding") == "chunked",
        )
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


class TestAgainstUvicorn:
    def test_content_length_over_the_limit(self, server):
        body = padded({"id": str(uuid.uuid4()), "title": "x"}, 20000)

        status, answer = send(server, body, {"Content-Length": str(len(body))})

        assert (status, json.loads(answer)) == (413, LIMIT_DETAIL)

    def test_chunked_without_content_length_over_the_limit(self, server):
        body = padded({"id": str(uuid.uuid4()), "title": "x"}, 20000)
        parts = [body[start : start + 1000] for start in range(0, len(body), 1000)]

        status, answer = send(server, iter(parts), {"Transfer-Encoding": "chunked"})

        assert (status, json.loads(answer)) == (413, LIMIT_DETAIL)

    def test_chunked_exactly_at_the_limit_passes(self, server):
        body = padded({"id": str(uuid.uuid4()), "title": "x"}, MAX_BODY_BYTES)
        parts = [body[start : start + 1000] for start in range(0, len(body), 1000)]

        status, _ = send(server, iter(parts), {"Transfer-Encoding": "chunked"})

        assert status == 200

    def test_chunked_one_byte_over_the_limit(self, server):
        body = padded({"id": str(uuid.uuid4()), "title": "x"}, MAX_BODY_BYTES + 1)
        parts = [body[start : start + 1000] for start in range(0, len(body), 1000)]

        status, _ = send(server, iter(parts), {"Transfer-Encoding": "chunked"})

        assert status == 413

    @pytest.mark.parametrize(
        "ensure_ascii", [True, False], ids=["escaped", "raw UTF-8"]
    )
    def test_a_maximal_valid_request_passes(self, server, ensure_ascii):
        todo_id = uuid.uuid4()
        body = json.dumps(maximal(todo_id), ensure_ascii=ensure_ascii).encode()

        status, answer = send(server, body, {"Content-Length": str(len(body))})

        assert status == 200
        assert json.loads(answer)["todo_entry"]["title"] == EMOJI * 255
