"""Runtime settings from BASICTODO_* environment variables.

Safe defaults (SEC-002, SEC-003, SEC-008): the server binds to 127.0.0.1
without auto-reload, answers only the Host names localhost and 127.0.0.1,
and allows cross-origin calls from the Vite dev server only. The names are
prefixed because generic ones such as HOST are set by some shells.
"""

import os
import re
from dataclasses import dataclass

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_TRUSTED_HOSTS = ("localhost", "127.0.0.1")
DEFAULT_CORS_ORIGINS = ("http://localhost:5173",)
# scheme://host[:port], nothing after it; the form a browser sends as Origin.
ORIGIN = re.compile(
    r"https?://[A-Za-z0-9.\-]+(:[0-9]{1,5})?|https?://\[[0-9A-Fa-f:]+\](:[0-9]{1,5})?"
)


class SettingsError(ValueError):
    """A BASICTODO_* variable holds a value the application refuses to run with."""


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    reload: bool
    trusted_hosts: tuple[str, ...]
    cors_origins: tuple[str, ...]


def _value(name: str, default: str) -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip()
    if not value:
        raise SettingsError(f"{name} is set but empty")
    return value


def _list(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.environ.get(name)
    if raw is None:
        return default
    items = tuple(item.strip() for item in raw.split(","))
    if any(not item for item in items):
        raise SettingsError(
            f"{name} must be a comma-separated list without empty entries"
        )
    if any("*" in item for item in items):
        raise SettingsError(f"{name} must not contain wildcards")
    return items


def _flag(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    if value in ("", "0", "false", "no", "off"):
        return False
    if value in ("1", "true", "yes", "on"):
        return True
    raise SettingsError(f"{name} must be true or false")


def load_settings() -> Settings:
    host = _value("BASICTODO_HOST", DEFAULT_HOST)
    if "*" in host:
        raise SettingsError("BASICTODO_HOST must name an address")
    port_text = _value("BASICTODO_PORT", str(DEFAULT_PORT))
    # The length first: int() refuses more than 4,300 digits with ValueError.
    if (
        not (port_text.isascii() and port_text.isdigit())
        or len(port_text) > 5
        or not 1 <= int(port_text) <= 65535
    ):
        raise SettingsError("BASICTODO_PORT must be a port number")
    return Settings(
        host=host,
        port=int(port_text),
        reload=_flag("BASICTODO_RELOAD"),
        trusted_hosts=_list("BASICTODO_TRUSTED_HOSTS", DEFAULT_TRUSTED_HOSTS),
        cors_origins=_origins(),
    )


def _origins() -> tuple[str, ...]:
    origins = _list("BASICTODO_CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    for origin in origins:
        if not ORIGIN.fullmatch(origin):
            raise SettingsError(
                f"BASICTODO_CORS_ORIGINS: {origin!r} is not an origin (scheme://host[:port])"
            )
    return origins
