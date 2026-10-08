"""Request body cap (Q8b, SEC-004): 16 KiB; anything larger gets 413."""

import json

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MAX_BODY_BYTES = 16 * 1024


class BodyLimitMiddleware:
    """Reads the whole request body before the app runs, and refuses it above max_bytes.

    A Content-Length above the limit is refused without reading anything.
    Otherwise the body is read message by message and the bytes are counted,
    so a chunked body without Content-Length is capped as well; at most the
    limit plus the one message that crosses it is held. A Content-Length that
    is not a plain decimal number is not trusted; the bytes are counted. The
    app then gets the body replayed as one message. Either way no handler
    runs for an oversized body, also not one that never reads it (DELETE),
    and both paths answer the same JSON 413.
    """

    def __init__(self, app: ASGIApp, max_bytes: int = MAX_BODY_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declared = Headers(scope=scope).get("content-length")
        if (
            declared is not None
            and declared.isascii()
            and declared.isdigit()
            and (len(declared) > 20 or int(declared) > self.max_bytes)
        ):
            await self._reject(send)
            return

        chunks: list[bytes] = []
        size = 0
        more_body = True
        while more_body:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body = message.get("body", b"")
            size += len(body)
            if size > self.max_bytes:
                await self._reject(send)
                return
            chunks.append(body)
            more_body = message.get("more_body", False)

        replayed = False

        async def replay() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {
                    "type": "http.request",
                    "body": b"".join(chunks),
                    "more_body": False,
                }
            return await receive()

        await self.app(scope, replay, send)

    async def _reject(self, send: Send) -> None:
        body = json.dumps(
            {"detail": f"Request body larger than {self.max_bytes} bytes"},
            separators=(",", ":"),
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
