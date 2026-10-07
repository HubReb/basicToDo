"""BASICTODO_* settings (SEC-002, SEC-003, SEC-008) and how main.py uses them."""

import runpy

import pytest
import uvicorn

from backend.app.settings import Settings, SettingsError, load_settings
from backend.scripts import init_db

VARIABLES = (
    "BASICTODO_HOST",
    "BASICTODO_PORT",
    "BASICTODO_RELOAD",
    "BASICTODO_TRUSTED_HOSTS",
    "BASICTODO_CORS_ORIGINS",
)


@pytest.fixture(autouse=True)
def unset(monkeypatch):
    for name in VARIABLES:
        monkeypatch.delenv(name, raising=False)


def test_the_defaults_are_local_only():
    assert load_settings() == Settings(
        host="127.0.0.1",
        port=8000,
        reload=False,
        trusted_hosts=("localhost", "127.0.0.1"),
        cors_origins=("http://localhost:5173",),
    )


def test_every_setting_can_be_given(monkeypatch):
    monkeypatch.setenv("BASICTODO_HOST", " 0.0.0.0 ")
    monkeypatch.setenv("BASICTODO_PORT", "8080")
    monkeypatch.setenv("BASICTODO_RELOAD", "On")
    monkeypatch.setenv("BASICTODO_TRUSTED_HOSTS", "todo.example, localhost")
    monkeypatch.setenv(
        "BASICTODO_CORS_ORIGINS", "https://todo.example,http://[::1]:5173"
    )

    assert load_settings() == Settings(
        host="0.0.0.0",
        port=8080,
        reload=True,
        trusted_hosts=("todo.example", "localhost"),
        cors_origins=("https://todo.example", "http://[::1]:5173"),
    )


@pytest.mark.parametrize("value", ["", "0", "false", "no", "off", "FALSE"])
def test_reload_is_off_for_false_spellings(monkeypatch, value):
    monkeypatch.setenv("BASICTODO_RELOAD", value)

    assert load_settings().reload is False


@pytest.mark.parametrize(
    "name, value, message",
    [
        ("BASICTODO_HOST", "  ", "BASICTODO_HOST is set but empty"),
        ("BASICTODO_HOST", "*", "must name an address"),
        ("BASICTODO_PORT", "", "BASICTODO_PORT is set but empty"),
        ("BASICTODO_PORT", "http", "must be a port number"),
        ("BASICTODO_PORT", "0", "must be a port number"),
        ("BASICTODO_PORT", "65536", "must be a port number"),
        ("BASICTODO_PORT", "-1", "must be a port number"),
        ("BASICTODO_PORT", "٨٠", "must be a port number"),
        ("BASICTODO_PORT", "008080", "must be a port number"),
        ("BASICTODO_PORT", "1" * 5000, "must be a port number"),
        ("BASICTODO_RELOAD", "maybe", "must be true or false"),
        ("BASICTODO_TRUSTED_HOSTS", "", "without empty entries"),
        ("BASICTODO_TRUSTED_HOSTS", "localhost,,127.0.0.1", "without empty entries"),
        ("BASICTODO_TRUSTED_HOSTS", "*", "must not contain wildcards"),
        ("BASICTODO_TRUSTED_HOSTS", "*.example", "must not contain wildcards"),
        ("BASICTODO_CORS_ORIGINS", "*", "must not contain wildcards"),
        ("BASICTODO_CORS_ORIGINS", "localhost:5173", "is not an origin"),
        ("BASICTODO_CORS_ORIGINS", "http://todo.example/", "is not an origin"),
        ("BASICTODO_CORS_ORIGINS", "http://todo.example/app", "is not an origin"),
    ],
)
def test_values_the_application_refuses(monkeypatch, name, value, message):
    monkeypatch.setenv(name, value)

    with pytest.raises(SettingsError, match=message):
        load_settings()


class TestMain:
    @pytest.fixture
    def calls(self, monkeypatch):
        calls = []
        monkeypatch.setattr(init_db, "init_database", lambda: calls.append("init"))
        monkeypatch.setattr(
            uvicorn, "run", lambda app, **options: calls.append((app, options))
        )
        return calls

    def test_main_prepares_the_database_then_serves_on_localhost(self, calls):
        runpy.run_module("backend.app.main", run_name="__main__")

        assert calls == [
            "init",
            (
                "backend.app.api.api:app",
                {"host": "127.0.0.1", "port": 8000, "reload": False},
            ),
        ]

    def test_main_uses_the_settings(self, calls, monkeypatch):
        monkeypatch.setenv("BASICTODO_HOST", "0.0.0.0")
        monkeypatch.setenv("BASICTODO_PORT", "9000")
        monkeypatch.setenv("BASICTODO_RELOAD", "true")

        runpy.run_module("backend.app.main", run_name="__main__")

        assert calls[1] == (
            "backend.app.api.api:app",
            {"host": "0.0.0.0", "port": 9000, "reload": True},
        )

    def test_main_refuses_bad_settings_before_touching_the_database(
        self, calls, monkeypatch
    ):
        monkeypatch.setenv("BASICTODO_PORT", "http")

        with pytest.raises(SettingsError):
            runpy.run_module("backend.app.main", run_name="__main__")

        assert calls == []
