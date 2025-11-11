from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from max_bot import config

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    max_user_id = Column(String, unique=True, nullable=False)
    home_address = Column(String) # New field for user's home address
    
    tasks = relationship("Task", back_populates="user")
    events = relationship("Event", back_populates="user")
    health_metrics = relationship("HealthMetric", back_populates="user")

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    duration = Column(String) # e.g., "3 hours"
    deadline = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="tasks")

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String) # New field for location
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="events")

class HealthMetric(Base):
    __tablename__ = 'health_metrics'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    metric = Column(String, nullable=False) # e.g., "sleep_quality", "mood"
    value = Column(String, nullable=False) # e.g., "poor", "good"
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="health_metrics")


# --- Database Connection ---
DATABASE_URL = f"postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Creates the database tables."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Returns a new database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
