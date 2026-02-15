from fastapi import APIRouter, Depends, Request, Form, HTTPException, status as fastapi_status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Any
from datetime import date, datetime

from app.database import get_db
from app.models import Project, Milestone
from app.routes import get_current_user, get_active_subscription

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/milestones", response_class=HTMLResponse)
async def list_milestones(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    projects = db.query(Project).filter(Project.user_id == str(user.id)).all()
    project_ids = [p.id for p in projects]
    
    milestones = []
    if project_ids:
        milestones = db.query(Milestone).filter(Milestone.project_id.in_(project_ids)).order_by(Milestone.due_date).all()
        
    return templates.TemplateResponse("milestones/list.html", {
        "request": request,
        "user": user,
        "milestones": milestones,
        "projects": projects
    })

@router.post("/milestones")
async def create_milestone(
    request: Request,
    project_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    due_date: str = Form(...),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == str(user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    d_date = datetime.strptime(due_date, "%Y-%m-%d").date()
    
    milestone = Milestone(
        project_id=project_id,
        title=title,
        description=description,
        due_date=d_date,
        completed=False
    )
    db.add(milestone)
    db.commit()
    
    referer = request.headers.get("referer")
    if referer:
         return RedirectResponse(url=referer, status_code=fastapi_status.HTTP_303_SEE_OTHER)

    return RedirectResponse(url=f"/projects/{project_id}", status_code=fastapi_status.HTTP_303_SEE_OTHER)

@router.post("/milestones/{id}/complete")
async def complete_milestone(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    milestone = db.query(Milestone).join(Project).filter(Milestone.id == id, Project.user_id == str(user.id)).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
        
    milestone.completed = True
    milestone.completed_at = func.now()
    db.commit()
    
    referer = request.headers.get("referer")
    if referer:
        return RedirectResponse(url=referer, status_code=fastapi_status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/milestones", status_code=fastapi_status.HTTP_303_SEE_OTHER)
