"""utc timestamps: created_at from local time to UTC; the old UI's placeholder removed

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-08 00:00:00.000000

Q6.6: the old code wrote created_at as the server's local time without an
offset (RULE-034); updated_at already holds UTC (the database clock). Each
created_at is converted on its own with the zoneinfo rules of the zone the
rows were written in, so both sides of a daylight-saving change get their
own offset; never a fixed offset. The zone: BASICTODO_LEGACY_TZ, else TZ
(both IANA names), else the system zone (/etc/localtime); without one, the
migration stops. An hour that occurs twice (autumn) is read as its first
occurrence, an hour that does not exist (spring) with the offset before the
change (fold=0, PEP 495); both are logged per row.

Safety check: the old code set updated_at to the insert time and never
changed it, so a converted created_at must lie within 30 minutes of it. If
not, the zone is wrong and the migration stops (BASICTODO_LEGACY_TZ_CHECK
=off skips the check).

Q6.7: a description that is exactly "not implemented yet", written by the
old UI, becomes NULL. The downgrade converts created_at back to local time
(exactly, except for an hour that did not exist, which comes back one hour
later) but cannot restore the placeholder.

"""

import os
from datetime import datetime, timedelta, timezone
from typing import Sequence, Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import sqlalchemy as sa
from alembic import op

from backend.app.logger import CustomLogger

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PLACEHOLDER = "not implemented yet"
ZONE_CHECK_LIMIT = timedelta(minutes=30)
SYSTEM_ZONE = "/etc/localtime"

log = CustomLogger("Migrations")


def legacy_zone() -> tuple[ZoneInfo, str]:
    """The zone the old code wrote created_at in, and its name for the log."""
    for variable in ("BASICTODO_LEGACY_TZ", "TZ"):
        name = os.environ.get(variable, "").strip().lstrip(":")
        if name:
            try:
                return ZoneInfo(name), name
            except (ZoneInfoNotFoundError, ValueError) as exc:
                raise RuntimeError(
                    f"{variable}={name!r} is not an IANA time zone name"
                ) from exc
    try:
        with open(SYSTEM_ZONE, "rb") as data:
            zone = ZoneInfo.from_file(data, key="localtime")
    except (OSError, ValueError) as exc:
        raise RuntimeError(
            "No time zone for the existing created_at values: set "
            "BASICTODO_LEGACY_TZ to the IANA zone they were written in"
        ) from exc
    real = os.path.realpath(SYSTEM_ZONE)
    return zone, real.split("zoneinfo/", 1)[1] if "zoneinfo/" in real else real


def parse(text: str) -> datetime:
    return datetime.fromisoformat(text)


def stored_text(value: datetime) -> str:
    """The text SQLAlchemy's SQLite DATETIME writes, so that text order is time order."""
    return (
        f"{value.year:04d}-{value.month:02d}-{value.day:02d} "
        f"{value.hour:02d}:{value.minute:02d}:{value.second:02d}.{value.microsecond:06d}"
    )


def local_to_utc(local: datetime, zone: ZoneInfo) -> tuple[datetime, str | None]:
    """The UTC time of a local wall clock, and a note for repeated or skipped hours."""
    first = local.replace(tzinfo=zone, fold=0)
    note = None
    if first.utcoffset() != local.replace(tzinfo=zone, fold=1).utcoffset():
        round_trip = first.astimezone(timezone.utc).astimezone(zone)
        note = "skipped" if round_trip.replace(tzinfo=None) != local else "repeated"
    return first.astimezone(timezone.utc).replace(tzinfo=None), note


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text('SELECT id, created_at, updated_at FROM "toDo"')
    ).fetchall()
    if rows:
        zone, name = legacy_zone()
        check = os.environ.get("BASICTODO_LEGACY_TZ_CHECK", "on").strip().lower()
        log.info("Converting created_at of %d todos from %s to UTC", len(rows), name)
        mismatched = 0
        for todo_id, created_at, updated_at in rows:
            utc, note = local_to_utc(parse(created_at), zone)
            if note:
                log.warning(
                    "todo %s: %s is a %s hour in %s; read with fold=0",
                    todo_id,
                    created_at,
                    note,
                    name,
                )
            if (
                updated_at is not None
                and abs(utc - parse(updated_at)) > ZONE_CHECK_LIMIT
            ):
                mismatched += 1
            bind.execute(
                sa.text('UPDATE "toDo" SET created_at = :created_at WHERE id = :id'),
                {"created_at": stored_text(utc), "id": todo_id},
            )
        if mismatched and check not in ("off", "0", "false", "no"):
            raise RuntimeError(
                f"{mismatched} of {len(rows)} todos have created_at more than 30 minutes "
                f"away from updated_at once read in {name}: they were probably written in "
                "another time zone. Set BASICTODO_LEGACY_TZ to that zone, or "
                "BASICTODO_LEGACY_TZ_CHECK=off to convert anyway."
            )
    cleared = bind.execute(
        sa.text('UPDATE "toDo" SET description = NULL WHERE description = :text'),
        {"text": PLACEHOLDER},
    ).rowcount
    if cleared:
        log.info(
            "Cleared the placeholder description of %d todos (a downgrade cannot restore it)",
            cleared,
        )


def downgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text('SELECT id, created_at FROM "toDo"')).fetchall()
    if rows:
        zone, name = legacy_zone()
        log.info("Converting created_at of %d todos from UTC to %s", len(rows), name)
        for todo_id, created_at in rows:
            local = parse(created_at).replace(tzinfo=timezone.utc).astimezone(zone)
            bind.execute(
                sa.text('UPDATE "toDo" SET created_at = :created_at WHERE id = :id'),
                {"created_at": stored_text(local.replace(tzinfo=None)), "id": todo_id},
            )
    log.warning("The placeholder descriptions removed by 0002 cannot be restored")
