"""Alembic environment for the toDo schema.

The application still creates its schema with Base.metadata.create_all
(backend/app/main.py, backend/scripts/init_db.py). The revisions under
versions/ are run by hand; an existing database is stamped only after
check_baseline.py has accepted its schema.

Configuration lives in pyproject.toml ([tool.alembic]); there is no
alembic.ini, so this file reads no logging configuration and no
sqlalchemy.url. The database is the application's: DATABASE_URL, or
backend/todo.db under the working directory. A caller that already holds a
connection passes it as config.attributes["connection"].
"""

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Connection

from backend.app.models.todo import Base

config = context.config
target_metadata = Base.metadata


def database_url() -> str:
    """The application's database URL, resolved when the command runs."""
    # Imported here: the module creates the application's engine on import,
    # which a run with a passed-in connection never needs.
    from backend.app.data_access.database import get_safe_database_url

    return get_safe_database_url()


def run_migrations_offline() -> None:
    """Emit the SQL instead of running it (alembic ... --sql)."""
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=target_metadata, render_as_batch=True
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        run_migrations(connection)
        return
    engine = create_engine(database_url(), poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            run_migrations(connection)
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
