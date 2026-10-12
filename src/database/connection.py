from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config.settings import settings
import os
import logging

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite"):
    db_path = db_url.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from src.database.models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized.")
