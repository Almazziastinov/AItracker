from datetime import datetime, timedelta
from db.schema import Task, Event

def parse_duration(duration_str: str) -> timedelta:
    """
    Parses a human-readable duration string (e.g., "3 hours", "30 минут") into a timedelta object.
    This is a simplified version and can be expanded.
    """
    if not duration_str:
        return timedelta(hours=1) # Default to 1 hour if no duration is specified

    duration_str = duration_str.lower()
    if "час" in duration_str:
        try:
            hours = int(duration_str.split("час")[0].strip())
            return timedelta(hours=hours)
        except ValueError:
            return timedelta(hours=1)
    elif "минут" in duration_str:
        try:
            minutes = int(duration_str.split("минут")[0].strip())
            return timedelta(minutes=minutes)
        except ValueError:
            return timedelta(minutes=30)
    else:
        return timedelta(hours=1) # Default

def schedule_task(task: Task, existing_events: list[Event]) -> Event:
    """
    Finds a free slot to schedule a new task and returns it as an Event.
    
    Args:
        task: The task to be scheduled.
        existing_events: A list of the user's already scheduled events.

    Returns:
        An Event object representing the scheduled task, or None if no slot is found.
    """
    task_duration = parse_duration(task.duration)
    
    # --- Define search window ---
    # Start searching from now
    search_start = datetime.now()
    # End searching at the task's deadline, or 7 days from now if no deadline
    search_end = task.deadline or search_start + timedelta(days=7)

    # Sort existing events by start time
    existing_events.sort(key=lambda e: e.start_time)

    # --- Find the first available slot ---
    current_time = search_start

    # Case 1: No existing events
    if not existing_events:
        if current_time + task_duration <= search_end:
            return Event(
                user_id=task.user_id,
                title=task.title,
                start_time=current_time,
                end_time=current_time + task_duration
            )
        else:
            return None # Not enough time even with an empty calendar

    # Case 2: Check for a slot before the first event
    first_event_start = existing_events[0].start_time
    if current_time + task_duration <= first_event_start:
        return Event(
            user_id=task.user_id,
            title=task.title,
            start_time=current_time,
            end_time=current_time + task_duration
        )

    # Case 3: Check for slots between events
    for i in range(len(existing_events) - 1):
        slot_start = existing_events[i].end_time
        slot_end = existing_events[i+1].start_time
        
        if slot_start + task_duration <= slot_end:
            return Event(
                user_id=task.user_id,
                title=task.title,
                start_time=slot_start,
                end_time=slot_start + task_duration
            )

    # Case 4: Check for a slot after the last event
    last_event_end = existing_events[-1].end_time
    if last_event_end + task_duration <= search_end:
        return Event(
            user_id=task.user_id,
            title=task.title,
            start_time=last_event_end,
            end_time=last_event_end + task_duration
        )

    return None # No suitable slot found
