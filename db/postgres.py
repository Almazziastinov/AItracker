from sqlalchemy.orm import Session
from . import schema
from datetime import datetime

def get_or_create_user(db: Session, max_user_id: str) -> schema.User:
    """
    Retrieves a user by their MAX ID, creating them if they don't exist.
    """
    user = db.query(schema.User).filter(schema.User.max_user_id == max_user_id).first()
    if not user:
        user = schema.User(max_user_id=max_user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def save_structured_data(db: Session, user_id: int, structured_data: dict) -> list[schema.Task]:
    """
    Saves the structured data (tasks, events, health metrics) to the database.
    Returns a list of the newly created tasks.
    """
    new_tasks = []
    user = db.query(schema.User).filter(schema.User.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    for task_data in structured_data.get("tasks", []):
        task = schema.Task(
            user_id=user.id,
            title=task_data["title"],
            duration=task_data.get("duration"),
            # TODO: Parse deadline string to datetime object
        )
        db.add(task)
        new_tasks.append(task)

    for event_data in structured_data.get("events", []):
        event = schema.Event(
            user_id=user.id,
            title=event_data["title"],
            location=event_data.get("location"), # Save location
            # TODO: Parse start_time and end_time strings to datetime objects
        )
        db.add(event)

    for metric_data in structured_data.get("health_metrics", []):
        metric = schema.HealthMetric(
            user_id=user.id,
            metric=metric_data["metric"],
            value=metric_data["value"],
        )
        db.add(metric)

    db.commit()
    for task in new_tasks:
        db.refresh(task)
        
    return new_tasks

def get_events_for_user(db: Session, user_id: int) -> list[schema.Event]:
    """
    Retrieves all future events for a given user.
    """
    return db.query(schema.Event).filter(
        schema.Event.user_id == user_id,
        schema.Event.start_time >= datetime.now()
    ).all()

def save_event(db: Session, event: schema.Event):
    """Saves a new event to the database."""
    db.add(event)
    db.commit()

def get_health_metrics_for_user(db: Session, user_id: int) -> list[schema.HealthMetric]:
    """
    Retrieves all health metrics for a given user, ordered by creation date.
    """
    return db.query(schema.HealthMetric).filter(
        schema.HealthMetric.user_id == user_id
    ).order_by(schema.HealthMetric.created_at).all()

def set_user_home_address(db: Session, user_id: int, address: str):
    """
    Sets the home address for a given user.
    """
    user = db.query(schema.User).filter(schema.User.id == user_id).first()
    if user:
        user.home_address = address
        db.commit()

def get_user_home_address(db: Session, user_id: int) -> str | None:
    """
    Retrieves the home address for a given user.
    """
    user = db.query(schema.User).filter(schema.User.id == user_id).first()
    if user:
        return user.home_address
    return None

def get_task_by_id(db: Session, task_id: int, user_id: int) -> schema.Task | None:
    """
    Retrieves a task by its ID and user ID.
    """
    return db.query(schema.Task).filter(
        schema.Task.id == task_id,
        schema.Task.user_id == user_id
    ).first()
