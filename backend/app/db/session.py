import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# Synchronous SQLAlchemy 2.0 engine - explicitly NO async SQLAlchemy
engine = None
SessionLocal = None

if DATABASE_URL:
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args={"connect_timeout": 5}
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        # Safe log without password
        safe_host = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "local"
        logger.info("SQLAlchemy engine initialized for %s", safe_host)
    except Exception as e:
        logger.warning("Database engine could not be initialized: %s", str(e))
else:
    logger.warning("DATABASE_URL environment variable is not set. Database operations will be unavailable.")

Base = declarative_base()


def get_db():
    """FastAPI dependency for obtaining a synchronous database session with graceful handling."""
    if SessionLocal is None:
        raise RuntimeError("Database is not configured or engine failed to initialize.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Verifies active connectivity to the PostgreSQL database."""
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.debug("Database health check ping failed: %s", str(e))
        return False
