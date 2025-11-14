from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.core import Base
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    max_user_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    home_address = Column(String, nullable=True)
    preferences = Column(Text, nullable=True)  # JSON строка с предпочтениями
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    events = relationship("Event", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    health_metrics = relationship("HealthMetric", back_populates="user")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    location = Column(String, nullable=True)
    event_type = Column(String, nullable=False)  # meeting, travel, work, etc.
    is_travel_event = Column(Boolean, default=False)
    travel_duration = Column(Integer, nullable=True)  # в минутах
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    user = relationship("User", back_populates="events")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # в минутах
    actual_duration = Column(Integer, nullable=True)     # в минутах
    priority = Column(String, default="medium")  # low, medium, high
    status = Column(String, default="pending")   # pending, in_progress, completed, cancelled
    category = Column(String, nullable=True)     # учеба, работа, здоровье, отдых
    location = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    user = relationship("User", back_populates="tasks")

class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    metric_type = Column(String, nullable=False)  # sleep, energy, stress, mood
    value = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    user = relationship("User", back_populates="health_metrics")

# Pydantic модели для валидации и сериализации
class UserCreate(BaseModel):
    max_user_id: str
    username: Optional[str] = None
    home_address: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    max_user_id: str
    username: Optional[str]
    home_address: Optional[str]
    
    class Config:
        from_attributes = True

class EventCreate(BaseModel):
    user_id: int
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    event_type: str
    is_travel_event: bool = False
    travel_duration: Optional[int] = None

class EventResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    event_type: str
    is_travel_event: bool
    travel_duration: Optional[int]
    
    class Config:
        from_attributes = True

class TaskCreate(BaseModel):
    user_id: int
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    estimated_duration: Optional[int] = None
    priority: str = "medium"
    category: Optional[str] = None
    location: Optional[str] = None

class TaskResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    deadline: Optional[datetime]
    estimated_duration: Optional[int]
    actual_duration: Optional[int]
    priority: str
    status: str
    category: Optional[str]
    location: Optional[str]
    
    class Config:
        from_attributes = True

class HealthMetricCreate(BaseModel):
    user_id: int
    metric_type: str
    value: float
    notes: Optional[str] = None
    recorded_at: datetime

class HealthMetricResponse(BaseModel):
    id: int
    user_id: int
    metric_type: str
    value: float
    notes: Optional[str]
    recorded_at: datetime
    
    class Config:
        from_attributes = True