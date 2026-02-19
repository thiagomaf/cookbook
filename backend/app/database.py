from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    # Required for SQLite to work across threads (FastAPI uses a thread pool)
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")       # better write concurrency
        cursor.execute("PRAGMA foreign_keys=ON")        # enforce FK constraints
        cursor.execute("PRAGMA synchronous=NORMAL")     # safe + faster than FULL
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
