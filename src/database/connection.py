import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use env var, fall back to local Postgres with NO password (only for dev if allowed)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres@localhost:5432/freight_rates",
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
