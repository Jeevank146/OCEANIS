import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://oceanis:oceanis_dev_2026@localhost:5432/oceanis"
)

# Normalize database URL for driver compatibility (Render, Supabase, Neon, Railway)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_database_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT PostGIS_Version();"))
            return result.scalar()
    except Exception as e:
        # Fallback to standard PostgreSQL version check if PostGIS function not yet loaded
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT version();"))
                return f"PostgreSQL Active ({str(result.scalar())[:35]}...)"
        except Exception:
            raise e


def init_db():
    from models import Base
    Base.metadata.create_all(bind=engine)
