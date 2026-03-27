import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# ✅ FINAL FIX
DATABASE_URL = (
    os.getenv("TEST_DATABASE_URL") 
    or os.getenv("DATABASE_URL")
)

if not DATABASE_URL:
    raise ValueError("Database URL not set ❌")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()