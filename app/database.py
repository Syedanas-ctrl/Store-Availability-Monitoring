from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database URL - replace with your actual database URL
SQLALCHEMY_DATABASE_URL = "postgresql://loop:loop@db:5432/loop_db"

# Create the SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
