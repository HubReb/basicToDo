"""The access and tables for the database"""

import datetime
import os
import uuid
from contextlib import contextmanager

from sqlalchemy import Boolean, Column, String, TIMESTAMP, Table, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import registry, sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import func
from sqlalchemy_utils import UUIDType

from backend.app.models.todo import ToDoEntryData

Base = declarative_base()


class ToDoORM(Base):
    __tablename__ = "toDo"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    description = Column(String(255), nullable=True, index=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.datetime.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted = Column(Boolean, nullable=False, default=False)
    done = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<ToDo(id={self.id}, title='{self.title}')>"

try:
    DATABASE_URL = os.environ["DATABASE_URL"]
except KeyError as err:
    DATABASE_URL = "/home/rebekka/projects/basicToDo/backend/todo.db"
SQLITE_DATABASE_URL = f"sqlite:///{DATABASE_URL}"

engine = create_engine(
    SQLITE_DATABASE_URL, echo=True, connect_args={"check_same_thread": False}, poolclass=QueuePool, pool_size=10, max_overflow=20, pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

Base = declarative_base()


@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

db = get_db_session()
mapper_registry = registry()
to_do_table = Table(
    "toDo",
    mapper_registry.metadata,
    Column(
        "id", UUIDType(binary=False), primary_key=True, index=True, default=uuid.uuid4
    ),
    Column("title", String(255), nullable=False, index=True),
    Column("description", String(255), nullable=True, index=False),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False, default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), nullable=True, default=func.now()),
    Column("deleted", Boolean, nullable=False, default=False),
    Column("done", Boolean, nullable=False, default=False),
)
mapper_registry.map_imperatively(ToDoEntryData, to_do_table)