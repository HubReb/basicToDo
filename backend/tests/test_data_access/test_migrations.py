"""The Alembic baseline revision and the check that guards stamping.

The application creates its schema with Base.metadata.create_all; revision
0001 must create exactly the same schema, so that a database stamped at 0001
and one upgraded to it are interchangeable for every later revision. Only a
database whose schema check_baseline.py accepts may be stamped.

Alembic's autogenerate comparison does not see CHECK constraints, so the
schemas are compared byte for byte through sqlite_master instead.
"""

import importlib.util
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine

from backend.app.data_access.database import Base
from backend.tests.test_data_access.test_storage_characterization import (
    BASELINE_SCHEMA,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CHECK_BASELINE = REPO_ROOT / "backend" / "migrations" / "check_baseline.py"
SAMPLE_DB = (
    REPO_ROOT / "analysis" / "basictodo" / "baseline" / "db" / "sample-legacy.db"
)
VERSION_TABLE = "alembic_version"


def load_check_baseline():
    spec = importlib.util.spec_from_file_location("check_baseline", CHECK_BASELINE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_baseline = load_check_baseline()


def alembic_config(connection=None) -> Config:
    """The [tool.alembic] configuration from pyproject.toml, as the CLI reads it."""
    config = Config(toml_file=str(REPO_ROOT / "pyproject.toml"))
    if connection is not None:
        config.attributes["connection"] = connection
    return config


def head_revision() -> str:
    head = ScriptDirectory.from_config(alembic_config()).get_current_head()
    assert head is not None
    return head


def run_alembic(path: Path, operation, revision: str) -> None:
    """Run an Alembic command on the file, on a connection committed at the end."""
    engine = create_engine(f"sqlite:///{path}")
    try:
        with engine.begin() as connection:
            operation(alembic_config(connection), revision)
    finally:
        engine.dispose()


def create_all(path: Path) -> None:
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(bind=engine)
    engine.dispose()


def schema(path: Path) -> list[tuple]:
    """sqlite_master without Alembic's version table (and its index)."""
    connection = sqlite3.connect(path)
    try:
        return connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master "
            "WHERE tbl_name != ? ORDER BY type, name",
            (VERSION_TABLE,),
        ).fetchall()
    finally:
        connection.close()


def query(path: Path, sql: str) -> list[tuple]:
    connection = sqlite3.connect(path)
    try:
        return connection.execute(sql).fetchall()
    finally:
        connection.close()


@pytest.fixture
def sample_copy(tmp_path) -> Path:
    """A copy of the legacy sample database; the committed file is never opened for writing."""
    copy = tmp_path / "sample-legacy.db"
    shutil.copyfile(SAMPLE_DB, copy)
    return copy


class TestBaselineRevision:
    def test_upgrade_head_creates_the_same_schema_as_create_all(self, tmp_path):
        create_all(tmp_path / "create_all.db")
        run_alembic(tmp_path / "upgraded.db", command.upgrade, "head")

        assert schema(tmp_path / "upgraded.db") == schema(tmp_path / "create_all.db")
        assert schema(tmp_path / "upgraded.db") == BASELINE_SCHEMA
        assert query(
            tmp_path / "upgraded.db", f"SELECT version_num FROM {VERSION_TABLE}"
        ) == [(head_revision(),)]

    def test_downgrade_base_leaves_no_application_schema(self, tmp_path):
        path = tmp_path / "downgraded.db"
        run_alembic(path, command.upgrade, "head")
        run_alembic(path, command.downgrade, "base")

        assert schema(path) == []
        assert query(path, f"SELECT version_num FROM {VERSION_TABLE}") == []

    def test_stamping_the_sample_database_makes_upgrade_head_a_no_op(self, sample_copy):
        rows_before = query(sample_copy, 'SELECT * FROM "toDo" ORDER BY id')
        assert check_baseline.main(["check_baseline.py", str(sample_copy)]) == 0

        run_alembic(sample_copy, command.stamp, "head")
        run_alembic(sample_copy, command.upgrade, "head")

        assert schema(sample_copy) == BASELINE_SCHEMA
        assert query(sample_copy, 'SELECT * FROM "toDo" ORDER BY id') == rows_before
        assert query(sample_copy, f"SELECT version_num FROM {VERSION_TABLE}") == [
            (head_revision(),)
        ]

    def test_the_alembic_cli_upgrades_the_configured_database(self, tmp_path):
        path = tmp_path / "cli.db"
        env = {**os.environ, "DATABASE_URL": f"sqlite:///{path}"}

        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert schema(path) == BASELINE_SCHEMA


class TestCheckBaseline:
    def test_its_snapshot_is_the_characterization_snapshot(self):
        assert check_baseline.BASELINE_SCHEMA == BASELINE_SCHEMA

    def test_accepts_a_fresh_create_all_database(self, tmp_path):
        create_all(tmp_path / "fresh.db")

        assert (
            check_baseline.main(["check_baseline.py", str(tmp_path / "fresh.db")]) == 0
        )

    def test_its_snapshot_is_what_the_baseline_revision_creates(self, tmp_path):
        run_alembic(tmp_path / "upgraded.db", command.upgrade, "head")

        assert (
            check_baseline.read_schema(tmp_path / "upgraded.db")
            == check_baseline.BASELINE_SCHEMA
        )

    def test_accepts_the_legacy_sample_database(self, sample_copy):
        assert check_baseline.main(["check_baseline.py", str(sample_copy)]) == 0

    def test_refuses_a_database_already_under_alembic(self, tmp_path):
        run_alembic(tmp_path / "upgraded.db", command.upgrade, "head")

        assert (
            check_baseline.main(["check_baseline.py", str(tmp_path / "upgraded.db")])
            == 2
        )

    def test_refuses_a_missing_file(self, tmp_path):
        assert (
            check_baseline.main(["check_baseline.py", str(tmp_path / "missing.db")])
            == 2
        )

    def test_rejects_the_sample_database_with_one_check_constraint_dropped(
        self, sample_copy
    ):
        rows_before = query(sample_copy, 'SELECT * FROM "toDo" ORDER BY id')
        table_sql = query(
            sample_copy, "SELECT sql FROM sqlite_master WHERE name = 'toDo'"
        )[0][0]
        without_check = table_sql.replace(
            ", \n\tCONSTRAINT description_length_check CHECK (length(description) <= 255)",
            "",
        )
        assert without_check != table_sql
        connection = sqlite3.connect(sample_copy)
        try:
            connection.executescript(
                'ALTER TABLE "toDo" RENAME TO "toDo_old";\n'
                f"{without_check};\n"
                'INSERT INTO "toDo" SELECT * FROM "toDo_old";\n'
                'DROP TABLE "toDo_old";\n'
                'CREATE INDEX "ix_toDo_title" ON "toDo" (title);\n'
            )
        finally:
            connection.close()
        assert query(sample_copy, 'SELECT * FROM "toDo" ORDER BY id') == rows_before

        result = subprocess.run(
            [sys.executable, str(CHECK_BASELINE), str(sample_copy)],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 1
        assert "-\tCONSTRAINT description_length_check" in result.stdout
        assert "do not stamp" in result.stderr
