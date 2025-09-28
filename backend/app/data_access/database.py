"""The access and tables for the database"""

import uuid
import json
from contextlib import contextmanager
from sqlalchemy import (
    create_engine,
    Table,
    Column,
    String,
    TIMESTAMP,
    Boolean,
)
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, registry
from sqlalchemy_utils import UUIDType
from backend.app.models.todo import ToDoEntryData

try:
    with open("/home/rebekka/projects/basicToDo/backend/app/config.json", encoding="utf-8") as f:
        config = json.load(f)
        path = config["db_path"]
except FileNotFoundError:    
    path = ""

SQLITE_DATABASE_URL = f"sqlite:///{path}todo.db"

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