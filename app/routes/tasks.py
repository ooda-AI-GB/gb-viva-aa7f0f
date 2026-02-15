from fastapi import APIRouter, Depends, Request, Form, HTTPException, status as fastapi_status, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Any, List
from datetime import date, datetime
from pydantic import BaseModel

from app.database import get_db
from app.models import Project, Task, TimeEntry
from app.routes import get_current_user, get_active_subscription

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

class TaskMove(BaseModel):
    status: str

@router.get("/tasks", response_class=HTMLResponse)
async def tasks_board(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    projects = db.query(Project).filter(Project.user_id == str(user.id)).all()
    project_ids = [p.id for p in projects]
    
    tasks = []
    if project_ids:
        tasks = db.query(Task).filter(Task.project_id.in_(project_ids)).all()
        
    tasks_by_status = {
        "todo": [],
        "in_progress": [],
        "review": [],
        "done": [],
        "blocked": []
    }
    
    for t in tasks:
        if t.status in tasks_by_status:
            tasks_by_status[t.status].append(t)
            
    return templates.TemplateResponse("tasks/board.html", {
        "request": request,
        "user": user,
        "tasks_by_status": tasks_by_status,
        "projects": projects
    })

@router.get("/tasks/{id}", response_class=HTMLResponse)
async def task_detail(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    # Join with Project to ensure user owns the project
    task = db.query(Task).join(Project).filter(Task.id == id, Project.user_id == str(user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return templates.TemplateResponse("tasks/detail.html", {
        "request": request,
        "user": user,
        "task": task
    })

@router.post("/tasks")
async def create_task(
    request: Request,
    project_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    priority: str = Form("medium"),
    assigned_to: str = Form(None),
    due_date: str = Form(None),
    estimated_hours: float = Form(None),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == str(user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    d_date = datetime.strptime(due_date, "%Y-%m-%d").date() if due_date else None
    
    new_task = Task(
        project_id=project_id,
        title=title,
        description=description,
        priority=priority,
        assigned_to=assigned_to,
        due_date=d_date,
        estimated_hours=estimated_hours,
        status="todo"
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return RedirectResponse(url=f"/projects/{project_id}", status_code=fastapi_status.HTTP_303_SEE_OTHER)

@router.post("/tasks/{id}/move")
async def move_task(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    # Expecting JSON body for drag and drop
    # Or possibly form data
    try:
        data = await request.json()
        new_status = data.get("status")
    except:
        form = await request.form()
        new_status = form.get("status")
        
    if not new_status:
        raise HTTPException(status_code=400, detail="Missing status")

    task = db.query(Task).join(Project).filter(Task.id == id, Project.user_id == str(user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task.status = new_status
    db.commit()
    
    return JSONResponse(content={"status": "ok", "new_status": task.status})

@router.post("/tasks/{id}/log-time")
async def log_time(
    request: Request,
    id: int,
    hours: float = Form(...),
    description: str = Form(None),
    date_logged: str = Form(...),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    task = db.query(Task).join(Project).filter(Task.id == id, Project.user_id == str(user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    l_date = datetime.strptime(date_logged, "%Y-%m-%d").date()
    
    entry = TimeEntry(
        task_id=id,
        user_id=str(user.id),
        hours=hours,
        description=description,
        date=l_date
    )
    db.add(entry)
    
    # Update actual hours on task
    if task.actual_hours is None:
        task.actual_hours = 0.0
    task.actual_hours += hours
    
    db.commit()
    
    return RedirectResponse(url=f"/tasks/{id}", status_code=fastapi_status.HTTP_303_SEE_OTHER)
