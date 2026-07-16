from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.persistence.config import ensure_sqlite_parent_directory
from app.persistence.models import Base


def create_database_engine(database_url: str) -> Engine:
    ensure_sqlite_parent_directory(database_url)
    url = make_url(database_url)
    connect_args: dict[str, object] = {}
    if url.drivername.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(
        database_url,
        connect_args=connect_args,
        future=True,
    )

    if url.drivername.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )


def create_tables(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)


SessionFactory = Callable[[], Session]
