"""SQLite configuration shared by the API and seed command."""

import os
from collections.abc import Generator

from fastapi import Request
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str | None = None) -> Engine:
    engine = create_engine(
        database_url or os.getenv("DATABASE_URL", "sqlite:///./claims.db"),
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def create_tables(engine: Engine) -> None:
    from claims_api import models  # noqa: F401 — register mapped tables

    Base.metadata.create_all(engine)


def get_session(request: Request) -> Generator[Session, None, None]:
    with Session(request.app.state.engine) as session:
        yield session
