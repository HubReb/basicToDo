"""Revision 0002 (Q6.6, Q6.7): created_at from local time to UTC, the placeholder removed.

The legacy code wrote created_at as the server's local wall clock, and
updated_at as the database's UTC clock in whole seconds (RULE-034, RULE-035).
0002 converts each created_at on its own with the zoneinfo rules of the zone
the rows were written in, so a database written across a daylight-saving
change gets both offsets; Europe/Berlin rows on both sides of the March and
the October change, the hour that does not exist and the hour that occurs
twice pin that. An exact "not implemented yet" description becomes NULL.

The migrations run as at startup, through prepare_database, on a database
made before Alembic: back up, stamp 0001, upgrade.
"""

import datetime
import importlib.util
import logging
import re
import shutil
import sqlite3
import zoneinfo
from pathlib import Path

import pytest
from alembic import command
from sqlalchemy import create_engine

from backend.app.data_access.database import Base
from backend.app.data_access.schema import (
    BASELINE_SCHEMA,
    alembic_config,
    head_revision,
    prepare_database,
)
from backend.app.logger import ROOT

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATION = REPO_ROOT / "backend" / "migrations" / "versions" / "0002_utc_timestamps.py"
SAMPLE_DIR = REPO_ROOT / "analysis" / "basictodo" / "baseline" / "db"
# The zone make_sample_db.sh writes the sample databases in.
SAMPLE_ZONE = "Etc/GMT-5"
STORED_FORMAT = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}$")
PLACEHOLDER = "not implemented yet"


def load_migration():
    spec = importlib.util.spec_from_file_location("migration_0002", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


migration = load_migration()

# (label, created_at as the legacy code wrote it in Europe/Berlin, the UTC value 0002 writes)
BERLIN_ROWS = [
    ("winter", "2026-01-15 12:00:00.000001", "2026-01-15 11:00:00.000001"),
    ("new year", "2026-01-01 00:30:00.000000", "2025-12-31 23:30:00.000000"),
    (
        "before the March change",
        "2026-03-29 01:59:59.999999",
        "2026-03-29 00:59:59.999999",
    ),
    # 02:00 to 02:59 did not exist on 29 March: read with the offset before the change.
    ("skipped hour", "2026-03-29 02:30:00.000000", "2026-03-29 01:30:00.000000"),
    (
        "after the March change",
        "2026-03-29 03:00:00.000000",
        "2026-03-29 01:00:00.000000",
    ),
    ("summer", "2026-07-15 12:00:00.500000", "2026-07-15 10:00:00.500000"),
    (
        "before the October change",
        "2026-10-25 01:59:59.999999",
        "2026-10-24 23:59:59.999999",
    ),
    # 02:00 to 02:59 occurred twice on 25 October: read as the first occurrence (CEST).
    ("repeated hour", "2026-10-25 02:30:00.000000", "2026-10-25 00:30:00.000000"),
    (
        "after the October change",
        "2026-10-25 03:00:00.000000",
        "2026-10-25 02:00:00.000000",
    ),
]


def legacy_updated_at(utc_text: str) -> str:
    """updated_at as the legacy database clock wrote it: UTC, whole seconds."""
    return utc_text[:19]


def todo_id(number: int) -> str:
    return f"5a3e0000000040008000{number:012d}"


def make_legacy_db(path: Path, rows: list[tuple]) -> Path:
    """A database made before Alembic: create_all, then rows as the legacy code stored them.

    rows: (created_at, updated_at, description) per todo.
    """
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(bind=engine)
    engine.dispose()
    connection = sqlite3.connect(path)
    try:
        connection.executemany(
            'INSERT INTO "toDo" (id, title, description, created_at, updated_at, deleted, done) '
            "VALUES (?, ?, ?, ?, ?, 0, 0)",
            [
                (todo_id(number), f"Todo {number}", description, created, updated)
                for number, (created, updated, description) in enumerate(rows, 1)
            ],
        )
        connection.commit()
    finally:
        connection.close()
    return path


def berlin_db(path: Path) -> Path:
    return make_legacy_db(
        path,
        [(local, legacy_updated_at(utc), None) for _, local, utc in BERLIN_ROWS],
    )


def query(path: Path, sql: str) -> list[tuple]:
    connection = sqlite3.connect(path)
    try:
        return connection.execute(sql).fetchall()
    finally:
        connection.close()


def todos(path: Path) -> list[tuple]:
    return query(path, 'SELECT * FROM "toDo" ORDER BY id')


def created_at(path: Path) -> list[str]:
    return [row[0] for row in query(path, 'SELECT created_at FROM "toDo" ORDER BY id')]


def url(path: Path) -> str:
    return f"sqlite:///{path}"


def downgrade_to_baseline(path: Path) -> None:
    engine = create_engine(url(path))
    try:
        with engine.begin() as connection:
            command.downgrade(alembic_config(connection), "0001")
    finally:
        engine.dispose()


@pytest.fixture
def berlin(monkeypatch):
    monkeypatch.setenv("BASICTODO_LEGACY_TZ", "Europe/Berlin")


@pytest.fixture
def records():
    """The records of the "basictodo" loggers, the migration's included."""
    captured: list[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(record)

    handler = Capture()
    logging.getLogger(ROOT).addHandler(handler)
    yield captured
    logging.getLogger(ROOT).removeHandler(handler)


class TestLocalToUtc:
    @pytest.mark.parametrize(
        "label, local, utc", BERLIN_ROWS, ids=[row[0] for row in BERLIN_ROWS]
    )
    def test_each_value_gets_the_offset_of_its_own_date(self, label, local, utc):
        converted, _ = migration.local_to_utc(
            datetime.datetime.fromisoformat(local), zoneinfo.ZoneInfo("Europe/Berlin")
        )

        assert migration.stored_text(converted) == utc

    def test_winter_and_summer_get_different_offsets_never_a_fixed_one(self):
        zone = zoneinfo.ZoneInfo("Europe/Berlin")
        winter, _ = migration.local_to_utc(datetime.datetime(2026, 1, 15, 12), zone)
        summer, _ = migration.local_to_utc(datetime.datetime(2026, 7, 15, 12), zone)

        assert (winter.hour, summer.hour) == (11, 10)

    @pytest.mark.parametrize(
        "local, note",
        [
            ("2026-03-29 02:30:00", "skipped"),
            ("2026-10-25 02:30:00", "repeated"),
            ("2026-03-29 01:59:59.999999", None),
            ("2026-03-29 03:00:00", None),
            ("2026-10-25 01:59:59.999999", None),
            ("2026-10-25 03:00:00", None),
        ],
    )
    def test_skipped_and_repeated_hours_are_noted(self, local, note):
        _, found = migration.local_to_utc(
            datetime.datetime.fromisoformat(local), zoneinfo.ZoneInfo("Europe/Berlin")
        )

        assert found == note

    def test_stored_text_has_microseconds_and_four_digit_years(self):
        assert migration.stored_text(datetime.datetime(5, 1, 2, 3, 4, 5)) == (
            "0005-01-02 03:04:05.000000"
        )


class TestUpgrade:
    def test_berlin_rows_on_both_sides_of_both_changes(self, tmp_path, berlin):
        path = berlin_db(tmp_path / "berlin.db")
        updated_before = query(path, 'SELECT updated_at FROM "toDo" ORDER BY id')

        prepare_database(url(path))

        assert created_at(path) == [utc for _, _, utc in BERLIN_ROWS]
        assert all(STORED_FORMAT.match(value) for value in created_at(path))
        assert (
            query(path, 'SELECT updated_at FROM "toDo" ORDER BY id') == updated_before
        )
        assert query(path, "SELECT version_num FROM alembic_version") == [
            (head_revision(),)
        ]
        assert (
            query(
                path,
                "SELECT type, name, tbl_name, sql FROM sqlite_master "
                "WHERE tbl_name != 'alembic_version' ORDER BY type, name",
            )
            == BASELINE_SCHEMA
        )

    def test_the_zone_and_the_skipped_and_repeated_hours_are_logged(
        self, tmp_path, berlin, records
    ):
        prepare_database(url(berlin_db(tmp_path / "berlin.db")))

        messages = [record.getMessage() for record in records]
        assert "Converting created_at of 9 todos from Europe/Berlin to UTC" in messages
        warnings = [r.getMessage() for r in records if r.levelno == logging.WARNING]
        assert warnings == [
            f"todo {todo_id(4)}: 2026-03-29 02:30:00.000000 is a skipped hour in "
            "Europe/Berlin; read with fold=0",
            f"todo {todo_id(8)}: 2026-10-25 02:30:00.000000 is a repeated hour in "
            "Europe/Berlin; read with fold=0",
        ]

    def test_an_empty_table_needs_no_zone(self, tmp_path, monkeypatch):
        # A zone the migration would refuse: it is never looked up.
        monkeypatch.setenv("BASICTODO_LEGACY_TZ", "No/Such_Zone")
        path = make_legacy_db(tmp_path / "empty.db", [])

        prepare_database(url(path))

        assert query(path, "SELECT version_num FROM alembic_version") == [
            (head_revision(),)
        ]


class TestZoneSafetyNet:
    def test_rows_read_in_the_wrong_zone_stop_the_migration(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("BASICTODO_LEGACY_TZ", "Asia/Tokyo")
        path = berlin_db(tmp_path / "berlin.db")
        rows_before = todos(path)

        with pytest.raises(RuntimeError, match="9 of 9 todos .* Asia/Tokyo"):
            prepare_database(url(path))

        assert todos(path) == rows_before
        assert (
            query(path, "SELECT name FROM sqlite_master WHERE name = 'alembic_version'")
            == []
        )

    def test_check_off_converts_in_the_given_zone_anyway(self, tmp_path, monkeypatch):
        monkeypatch.setenv("BASICTODO_LEGACY_TZ", "Asia/Tokyo")
        monkeypatch.setenv("BASICTODO_LEGACY_TZ_CHECK", "off")
        path = make_legacy_db(
            tmp_path / "tokyo.db",
            [("2026-01-15 12:00:00.000000", "2026-01-15 11:00:00", None)],
        )

        prepare_database(url(path))

        assert created_at(path) == ["2026-01-15 03:00:00.000000"]

    def test_a_row_within_30_minutes_passes(self, tmp_path, berlin):
        path = make_legacy_db(
            tmp_path / "late.db",
            [("2026-01-15 12:00:00.000000", "2026-01-15 11:29:59", None)],
        )

        prepare_database(url(path))

        assert created_at(path) == ["2026-01-15 11:00:00.000000"]

    def test_a_row_more_than_30_minutes_away_stops_it(self, tmp_path, berlin):
        path = make_legacy_db(
            tmp_path / "off.db",
            [("2026-01-15 12:00:00.000000", "2026-01-15 11:30:01", None)],
        )

        with pytest.raises(RuntimeError, match="1 of 1 todos"):
            prepare_database(url(path))


class TestPlaceholder:
    DESCRIPTIONS = [
        PLACEHOLDER,
        "not implemented yet, see the notes",
        "Not implemented yet",
        "",
        None,
        "two litres",
    ]

    @pytest.fixture
    def path(self, tmp_path, berlin):
        return make_legacy_db(
            tmp_path / "placeholder.db",
            [
                ("2026-01-15 12:00:00.000000", "2026-01-15 11:00:00", description)
                for description in self.DESCRIPTIONS
            ],
        )

    def test_only_the_exact_placeholder_becomes_null(self, path, records):
        prepare_database(url(path))

        assert query(path, 'SELECT description FROM "toDo" ORDER BY id') == [
            (None,),
            ("not implemented yet, see the notes",),
            ("Not implemented yet",),
            ("",),
            (None,),
            ("two litres",),
        ]
        assert (
            "Cleared the placeholder description of 1 todos (a downgrade cannot restore it)"
            in [record.getMessage() for record in records]
        )

    def test_the_downgrade_cannot_restore_it(self, path, records):
        prepare_database(url(path))

        downgrade_to_baseline(path)

        assert query(path, 'SELECT description FROM "toDo" ORDER BY id')[0] == (None,)
        assert "The placeholder descriptions removed by 0002 cannot be restored" in [
            record.getMessage() for record in records
        ]


class TestDowngrade:
    def test_every_value_comes_back_except_the_skipped_hour(self, tmp_path, berlin):
        path = berlin_db(tmp_path / "berlin.db")
        rows_before = todos(path)
        prepare_database(url(path))

        downgrade_to_baseline(path)

        restored = [
            "2026-03-29 03:30:00.000000" if label == "skipped hour" else local
            for label, local, _ in BERLIN_ROWS
        ]
        assert created_at(path) == restored
        assert [row[:3] + row[4:] for row in todos(path)] == [
            row[:3] + row[4:] for row in rows_before
        ]
        assert query(path, "SELECT version_num FROM alembic_version") == [("0001",)]


class TestLegacyZone:
    @pytest.fixture(autouse=True)
    def no_zone_variables(self, monkeypatch):
        monkeypatch.delenv("BASICTODO_LEGACY_TZ", raising=False)
        monkeypatch.delenv("TZ", raising=False)

    def test_basictodo_legacy_tz_comes_first(self, monkeypatch):
        monkeypatch.setenv("BASICTODO_LEGACY_TZ", "Europe/Berlin")
        monkeypatch.setenv("TZ", "Asia/Tokyo")

        zone, name = migration.legacy_zone()

        assert (zone.key, name) == ("Europe/Berlin", "Europe/Berlin")

    def test_then_tz_with_or_without_a_leading_colon(self, monkeypatch):
        monkeypatch.setenv("BASICTODO_LEGACY_TZ", "  ")
        monkeypatch.setenv("TZ", ":Asia/Tokyo")

        zone, name = migration.legacy_zone()

        assert (zone.key, name) == ("Asia/Tokyo", "Asia/Tokyo")

    @pytest.mark.parametrize("variable", ["BASICTODO_LEGACY_TZ", "TZ"])
    def test_a_name_that_is_no_zone_is_refused(self, monkeypatch, variable):
        monkeypatch.setenv(variable, "CET-1CEST")

        with pytest.raises(
            RuntimeError, match=f"{variable}='CET-1CEST' is not an IANA"
        ):
            migration.legacy_zone()

    def test_then_the_system_zone(self, monkeypatch, tmp_path):
        source = next(
            (
                Path(base) / "Europe" / "Berlin"
                for base in zoneinfo.TZPATH
                if (Path(base) / "Europe" / "Berlin").is_file()
            ),
            None,
        )
        if source is None:
            pytest.skip("no system time zone database")
        link = tmp_path / "localtime"
        link.symlink_to(source)
        monkeypatch.setattr(migration, "SYSTEM_ZONE", str(link))

        zone, name = migration.legacy_zone()

        assert name == "Europe/Berlin"
        summer = datetime.datetime(2026, 7, 1, tzinfo=zone)
        assert summer.utcoffset() == datetime.timedelta(hours=2)

    def test_without_any_zone_it_stops(self, monkeypatch, tmp_path):
        monkeypatch.setattr(migration, "SYSTEM_ZONE", str(tmp_path / "missing"))

        with pytest.raises(RuntimeError, match="set BASICTODO_LEGACY_TZ"):
            migration.legacy_zone()


class TestSampleDatabases:
    @pytest.mark.parametrize("name", ["sample-legacy.db", "sample-legacy-p5.db"])
    def test_converted_row_by_row(self, tmp_path, monkeypatch, name):
        monkeypatch.setenv("BASICTODO_LEGACY_TZ", SAMPLE_ZONE)
        copy = tmp_path / name
        shutil.copyfile(SAMPLE_DIR / name, copy)
        rows_before = todos(copy)

        prepare_database(url(copy))

        five_hours = datetime.timedelta(hours=5)
        expected = [
            (
                todo,
                title,
                None if description == PLACEHOLDER else description,
                migration.stored_text(
                    datetime.datetime.fromisoformat(created) - five_hours
                ),
                updated,
                deleted,
                done,
            )
            for todo, title, description, created, updated, deleted, done in rows_before
        ]
        assert todos(copy) == expected
        placeholders = [row for row in rows_before if row[2] and PLACEHOLDER in row[2]]
        assert len(placeholders) == (2 if name == "sample-legacy-p5.db" else 0)

    @pytest.mark.parametrize("name", ["sample-legacy.db", "sample-legacy-p5.db"])
    def test_read_in_utc_instead_the_safety_net_stops_it(
        self, tmp_path, monkeypatch, name
    ):
        monkeypatch.setenv("BASICTODO_LEGACY_TZ", "UTC")
        copy = tmp_path / name
        shutil.copyfile(SAMPLE_DIR / name, copy)
        rows_before = todos(copy)

        with pytest.raises(RuntimeError, match="written in another time zone"):
            prepare_database(url(copy))

        assert todos(copy) == rows_before
