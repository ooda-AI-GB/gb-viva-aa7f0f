from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, timedelta
from typing import Any

from app.database import get_db
from app.models import Project, Task, Milestone, TimeEntry
from app.routes import get_current_user, get_active_subscription
from app.seed import seed_data

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    # Get user projects
    projects = db.query(Project).filter(Project.user_id == str(user.id)).all()
    
    if not projects:
        seed_data(db, user.id)
        projects = db.query(Project).filter(Project.user_id == str(user.id)).all()

    user_projects_ids = [p.id for p in projects]

    # 1. Project Overview
    project_counts = {
        "planning": 0, "active": 0, "on_hold": 0, "completed": 0, "archived": 0
    }
    for p in projects:
        if p.status in project_counts:
            project_counts[p.status] += 1

    # 2. My tasks (Tasks in user projects)
    my_tasks = []
    if user_projects_ids:
        my_tasks = db.query(Task).filter(Task.project_id.in_(user_projects_ids)).all()
    
    tasks_by_status = {
        "todo": [], "in_progress": [], "review": [], "done": [], "blocked": []
    }
    for t in my_tasks:
        if t.status in tasks_by_status:
            tasks_by_status[t.status].append(t)

    # 3. Upcoming deadlines (Next 7 days)
    today = date.today()
    next_week = today + timedelta(days=7)
    
    upcoming = []
    if user_projects_ids:
        upcoming_tasks = db.query(Task).filter(
            Task.project_id.in_(user_projects_ids),
            Task.due_date >= today,
            Task.due_date <= next_week,
            Task.status != "done"
        ).all()
        
        upcoming_milestones = db.query(Milestone).filter(
            Milestone.project_id.in_(user_projects_ids),
            Milestone.due_date >= today,
            Milestone.due_date <= next_week,
            Milestone.completed == False
        ).all()

        for t in upcoming_tasks:
            upcoming.append({"type": "Task", "title": t.title, "due_date": t.due_date, "project_id": t.project_id, "id": t.id})
        for m in upcoming_milestones:
            upcoming.append({"type": "Milestone", "title": m.title, "due_date": m.due_date, "project_id": m.project_id, "id": m.id})
        
        upcoming.sort(key=lambda x: x['due_date'])

    # 4. Quick stats
    total_projects = len(projects)
    active_tasks = 0
    overdue_items = 0
    
    if user_projects_ids:
        active_tasks = db.query(Task).filter(
            Task.project_id.in_(user_projects_ids),
            Task.status.in_(["todo", "in_progress", "review", "blocked"])
        ).count()
        
        overdue_items = db.query(Task).filter(
            Task.project_id.in_(user_projects_ids),
            Task.due_date < today,
            Task.status != "done"
        ).count()

    # Hours logged this week
    start_of_week = today - timedelta(days=today.weekday())
    hours_logged = db.query(func.sum(TimeEntry.hours)).filter(
        TimeEntry.user_id == str(user.id),
        TimeEntry.date >= start_of_week
    ).scalar() or 0.0

    # 5. Recent activity
    recent_activity = db.query(TimeEntry).filter(
        TimeEntry.user_id == str(user.id)
    ).order_by(desc(TimeEntry.created_at)).limit(10).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "project_counts": project_counts,
        "tasks_by_status": tasks_by_status,
        "upcoming": upcoming,
        "stats": {
            "total_projects": total_projects,
            "active_tasks": active_tasks,
            "hours_logged": hours_logged,
            "overdue_items": overdue_items
        },
        "recent_activity": recent_activity
    })
