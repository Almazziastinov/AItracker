import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import json

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from db.schema import get_db
from db.postgres import get_events_for_user, get_or_create_user, get_health_metrics_for_user

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/calendar/{user_max_id}", response_class=HTMLResponse)
async def get_calendar(request: Request, user_max_id: str, db: Session = Depends(get_db)):
    """
    Renders the calendar view for a specific user.
    """
    user = get_or_create_user(db, user_max_id)
    events = get_events_for_user(db, user.id)
    
    calendar_events = []
    for event in events:
        calendar_events.append({
            "title": event.title,
            "start": event.start_time.isoformat(),
            "end": event.end_time.isoformat() if event.end_time else None,
        })

    return templates.TemplateResponse(
        "calendar.html", 
        {"request": request, "events": json.dumps(calendar_events)}
    )

@app.get("/dashboard/{user_max_id}", response_class=HTMLResponse)
async def get_dashboard(request: Request, user_max_id: str, db: Session = Depends(get_db)):
    """
    Renders the wellness dashboard for a specific user.
    """
    user = get_or_create_user(db, user_max_id)
    metrics = get_health_metrics_for_user(db, user.id)
    
    # Process metrics for Chart.js
    # We'll create separate datasets for each metric type (e.g., sleep_quality, mood)
    datasets = {}
    for metric in metrics:
        if metric.metric not in datasets:
            datasets[metric.metric] = {"labels": [], "values": []}
        datasets[metric.metric]["labels"].append(metric.created_at.strftime("%Y-%m-%d"))
        # This assumes the value is numeric. We might need more robust parsing.
        try:
            datasets[metric.metric]["values"].append(float(metric.value))
        except ValueError:
            # Handle non-numeric values if necessary
            pass

    return templates.TemplateResponse(
        "dashboard.html", 
        {"request": request, "datasets": json.dumps(datasets)}
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)