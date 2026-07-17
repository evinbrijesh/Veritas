"""
SQLAlchemy engine + session factory for Postgres (auth/audit/case data).
Neo4j has its own client — see neo4j_client.py — since it's a
completely different storage model (graph, not relational).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
