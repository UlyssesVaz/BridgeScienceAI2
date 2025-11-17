from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

#connect to db
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")


# 2. Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    # This setting is required for SQLite
    connect_args={"check_same_thread": False}
)

# 3. Create the Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# base class that all models will inherit from
Base = declarative_base()

# 5. This is the helper you were missing!
def get_db():
    """
    This is the "dependency" that gives your API
    a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()