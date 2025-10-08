from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from src.db.models import Base
from src.db.database import SQLALCHEMY_DATABASE_URL
import logging

logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with tables"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Create database if it doesn't exist
    if not database_exists(engine.url):
        create_database(engine.url)
        logger.info(f"Created database: {SQLALCHEMY_DATABASE_URL}")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    
    # Create SessionLocal class for database sessions
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database session factory
SessionLocal = init_db()