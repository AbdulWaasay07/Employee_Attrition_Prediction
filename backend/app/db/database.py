import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

def ensure_database_exists():
    """
    Automatically creates the MySQL database schema if it doesn't already exist.
    """
    try:
        connection = pymysql.connect(
            host=settings.MYSQL_SERVER,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD
        )
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        connection.close()
    except Exception as e:
        print(f"Notice: Automated database schema creation check skipped: {e}")

# Ensure database exists before creating SQLAlchemy engine
ensure_database_exists()

# Create the SQLAlchemy engine
# pool_pre_ping=True helps prevent "MySQL server has gone away" errors
engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a declarative base class for our models
Base = declarative_base()

# Dependency function to get a DB session for FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
