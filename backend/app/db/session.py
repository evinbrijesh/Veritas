"""Postgres engine + session factory (SQLAlchemy).

The connection string comes whole from settings.database_url — docker-compose
composes it once with the `postgres` container hostname. We never rebuild
URLs here (Day 3 decision: config is the single source of truth).

The engine connects lazily: importing this module does NOT touch Postgres,
so the API can boot even while the DB is unavailable.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI dependency: one session per request, always closed.

    Routes use it as `db: Session = Depends(get_db)`.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
