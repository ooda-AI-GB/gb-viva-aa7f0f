from fastapi import APIRouter, Depends, Request, Form, HTTPException, status as fastapi_status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Any, List
from datetime import date, datetime

from app.database import get_db
from app.models import Project, Task, Milestone, TimeEntry, ProjectInsight
from app.routes import get_current_user, get_active_subscription

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/projects", response_class=HTMLResponse)
async def list_projects(
    request: Request,
    status_filter: str = None,
    sort_by: str = "due_date",
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    query = db.query(Project).filter(Project.user_id == str(user.id))
    
    if status_filter:
        query = query.filter(Project.status == status_filter)
    
    projects = query.all()
    
    if sort_by == "priority":
        priority_map = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        projects.sort(key=lambda x: priority_map.get(x.priority, 4))
    else:
        # Default due_date
        # Handle None due dates by putting them at the end or beginning?
        projects.sort(key=lambda x: x.due_date if x.due_date else date.max)

    project_data = []
    for p in projects:
        total_tasks = len(p.tasks)
        done_tasks = len([t for t in p.tasks if t.status == "done"])
        progress = 0
        if total_tasks > 0:
            progress = int((done_tasks / total_tasks) * 100)
        project_data.append({
            "project": p,
            "progress": progress
        })

    return templates.TemplateResponse("projects/list.html", {
        "request": request, 
        "user": user, 
        "projects": project_data,
        "status_filter": status_filter,
        "sort_by": sort_by
    })

@router.get("/projects/new", response_class=HTMLResponse)
async def new_project_form(request: Request, user: Any = Depends(get_current_user), _ : Any = Depends(get_active_subscription)):
    return templates.TemplateResponse("projects/form.html", {"request": request, "user": user})

@router.post("/projects/new")
async def create_project(
    request: Request,
    name: str = Form(...),
    description: str = Form(None),
    status: str = Form("planning"),
    priority: str = Form("medium"),
    start_date: str = Form(None),
    due_date: str = Form(None),
    budget: float = Form(None),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    s_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    d_date = datetime.strptime(due_date, "%Y-%m-%d").date() if due_date else None
    
    new_project = Project(
        user_id=str(user.id),
        name=name,
        description=description,
        status=status,
        priority=priority,
        start_date=s_date,
        due_date=d_date,
        budget=budget
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return RedirectResponse(url=f"/projects/{new_project.id}", status_code=fastapi_status.HTTP_303_SEE_OTHER)

@router.get("/projects/{id}", response_class=HTMLResponse)
async def project_detail(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    project = db.query(Project).filter(Project.id == id, Project.user_id == str(user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    total_tasks = len(project.tasks)
    done_tasks = len([t for t in project.tasks if t.status == "done"])
    progress = 0
    if total_tasks > 0:
        progress = int((done_tasks / total_tasks) * 100)
    
    total_hours_est = sum([t.estimated_hours for t in project.tasks if t.estimated_hours])
    total_hours_act = sum([t.actual_hours for t in project.tasks if t.actual_hours])
    
    return templates.TemplateResponse("projects/detail.html", {
        "request": request, 
        "user": user, 
        "project": project,
        "progress": progress,
        "total_hours_est": total_hours_est,
        "total_hours_act": total_hours_act
    })

@router.get("/projects/{id}/edit", response_class=HTMLResponse)
async def edit_project_form(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    project = db.query(Project).filter(Project.id == id, Project.user_id == str(user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return templates.TemplateResponse("projects/form.html", {"request": request, "user": user, "project": project})

@router.post("/projects/{id}/edit")
async def update_project(
    request: Request,
    id: int,
    name: str = Form(...),
    description: str = Form(None),
    status: str = Form(...),
    priority: str = Form(...),
    start_date: str = Form(None),
    due_date: str = Form(None),
    budget: float = Form(None),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    project = db.query(Project).filter(Project.id == id, Project.user_id == str(user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    project.name = name
    project.description = description
    project.status = status
    project.priority = priority
    project.start_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    project.due_date = datetime.strptime(due_date, "%Y-%m-%d").date() if due_date else None
    
    if budget:
        project.budget = float(budget)
    else:
        project.budget = None
    
    db.commit()
    return RedirectResponse(url=f"/projects/{id}", status_code=fastapi_status.HTTP_303_SEE_OTHER)

@router.post("/projects/{id}/delete")
async def delete_project(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    project = db.query(Project).filter(Project.id == id, Project.user_id == str(user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return RedirectResponse(url="/projects", status_code=fastapi_status.HTTP_303_SEE_OTHER)
