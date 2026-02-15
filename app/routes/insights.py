from fastapi import APIRouter, Depends, Request, Form, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Any, List
import os
import json
from datetime import datetime, date

from app.database import get_db
from app.models import Project, Task, Milestone, TimeEntry, ProjectInsight
from app.routes import get_current_user, get_active_subscription
from pydantic import BaseModel

try:
    from google import genai
except ImportError:
    genai = None

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

class InsightRequest(BaseModel):
    project_id: int
    insight_type: str

@router.get("/insights", response_class=HTMLResponse)
async def list_insights(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    projects = db.query(Project).filter(Project.user_id == str(user.id)).all()
    project_ids = [p.id for p in projects]
    
    insights = []
    if project_ids:
        insights = db.query(ProjectInsight).filter(ProjectInsight.project_id.in_(project_ids)).order_by(desc(ProjectInsight.generated_at)).all()
        
    return templates.TemplateResponse("insights/dashboard.html", {
        "request": request,
        "user": user,
        "insights": insights,
        "projects": projects
    })

@router.get("/insights/{id}", response_class=HTMLResponse)
async def insight_detail(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    insight = db.query(ProjectInsight).join(Project).filter(ProjectInsight.id == id, Project.user_id == str(user.id)).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
        
    return templates.TemplateResponse("insights/detail.html", {
        "request": request,
        "user": user,
        "insight": insight
    })

@router.post("/api/insights/analyze")
async def generate_insight(
    request: Request,
    insight_request: InsightRequest,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    _ : Any = Depends(get_active_subscription)
):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
         return JSONResponse(status_code=500, content={"error": "GOOGLE_API_KEY not set"})
         
    if not genai:
         return JSONResponse(status_code=500, content={"error": "google-genai library not installed"})

    project = db.query(Project).filter(Project.id == insight_request.project_id, Project.user_id == str(user.id)).first()
    if not project:
        return JSONResponse(status_code=404, content={"error": "Project not found"})
        
    # Gather context
    tasks = db.query(Task).filter(Task.project_id == project.id).all()
    milestones = db.query(Milestone).filter(Milestone.project_id == project.id).all()
    
    done_tasks = [t for t in tasks if t.status == 'done']
    overdue_tasks = [t for t in tasks if t.due_date and t.due_date < date.today() and t.status != 'done']
    
    task_summary = f"Total Tasks: {len(tasks)}. Done: {len(done_tasks)}. Overdue: {len(overdue_tasks)}."
    
    completed_milestones = [m for m in milestones if m.completed]
    milestone_summary = f"Total Milestones: {len(milestones)}. Completed: {len(completed_milestones)}."
    
    prompt = f"""
    Analyze the project "{project.name}" ({project.description or 'No description'}).
    Status: {project.status}. Priority: {project.priority}.
    Tasks Summary: {task_summary}
    Milestones Summary: {milestone_summary}
    
    Please provide a {insight_request.insight_type} (e.g. risk_assessment, progress_summary, resource_analysis).
    Focus on potential risks, progress blockers, or resource allocation issues if applicable.
    Be concise and professional.
    """
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        content = response.text
        
        # Save insight
        requested_by = "user"
        if hasattr(user, 'email'):
            requested_by = user.email
            
        new_insight = ProjectInsight(
            project_id=project.id,
            insight_type=insight_request.insight_type,
            content=content,
            model_used="gemini-2.5-flash",
            requested_by=requested_by
        )
        db.add(new_insight)
        db.commit()
        db.refresh(new_insight)
        
        return JSONResponse(content={"status": "ok", "insight_id": new_insight.id, "content": content})
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
