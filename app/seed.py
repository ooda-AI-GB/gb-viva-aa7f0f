from sqlalchemy.orm import Session
from app.models import Project, Task, Milestone, TimeEntry, ProjectInsight
from datetime import datetime

def seed_data(db: Session, user_id):
    # Projects
    p1 = Project(user_id=str(user_id), name="Website Redesign", description="Complete overhaul of company website with modern UI/UX.", status="active", priority="high", start_date=datetime(2026,1,15).date(), due_date=datetime(2026,3,30).date(), budget=45000.00)
    p2 = Project(user_id=str(user_id), name="Mobile App v2", description="Second major release of the mobile application.", status="active", priority="critical", start_date=datetime(2026,2,1).date(), due_date=datetime(2026,5,15).date(), budget=120000.00)
    p3 = Project(user_id=str(user_id), name="Data Migration", description="Migrate legacy database to new cloud infrastructure.", status="planning", priority="medium", start_date=datetime(2026,3,1).date(), due_date=datetime(2026,4,15).date(), budget=30000.00)
    p4 = Project(user_id=str(user_id), name="API Integration Hub", description="Build centralized API gateway for third-party integrations.", status="on_hold", priority="medium", start_date=datetime(2026,1,10).date(), due_date=datetime(2026,6,1).date(), budget=65000.00)
    p5 = Project(user_id=str(user_id), name="Q1 Marketing Campaign", description="Digital marketing campaign for Q1 product launch.", status="completed", priority="high", start_date=datetime(2026,1,1).date(), due_date=datetime(2026,2,14).date(), budget=25000.00)
    
    db.add_all([p1, p2, p3, p4, p5])
    db.commit()
    db.refresh(p1)
    db.refresh(p2)
    db.refresh(p3)
    db.refresh(p4)
    db.refresh(p5)
    
    # Tasks
    tasks = [
        Task(project_id=p1.id, title="Design wireframes", description="Create wireframes for all major pages.", status="done", priority="high", assigned_to="Design Team", due_date=datetime(2026,2,1).date(), estimated_hours=40, actual_hours=35),
        Task(project_id=p1.id, title="Implement responsive layout", description="Build mobile-first responsive CSS framework.", status="in_progress", priority="high", assigned_to="Frontend Team", due_date=datetime(2026,2,28).date(), estimated_hours=60, actual_hours=25),
        Task(project_id=p1.id, title="Backend API endpoints", description="Build REST API for new site features.", status="in_progress", priority="medium", assigned_to="Backend Team", due_date=datetime(2026,3,10).date(), estimated_hours=80, actual_hours=30),
        Task(project_id=p1.id, title="Content migration", description="Migrate existing content to new CMS.", status="todo", priority="medium", assigned_to="Content Team", due_date=datetime(2026,3,15).date(), estimated_hours=20, actual_hours=0),
        Task(project_id=p1.id, title="QA testing", description="Full regression testing before launch.", status="todo", priority="high", assigned_to="QA Team", due_date=datetime(2026,3,25).date(), estimated_hours=30, actual_hours=0),
        Task(project_id=p2.id, title="User authentication revamp", description="Implement biometric login and SSO.", status="in_progress", priority="critical", assigned_to="Mobile Team", due_date=datetime(2026,3,1).date(), estimated_hours=50, actual_hours=20),
        Task(project_id=p2.id, title="Offline mode", description="Enable app functionality without internet connection.", status="todo", priority="high", assigned_to="Mobile Team", due_date=datetime(2026,4,1).date(), estimated_hours=100, actual_hours=0),
        Task(project_id=p2.id, title="Push notification system", description="Real-time push notifications for updates.", status="review", priority="medium", assigned_to="Backend Team", due_date=datetime(2026,2,20).date(), estimated_hours=30, actual_hours=28),
        Task(project_id=p2.id, title="Performance optimization", description="Reduce app load time by 50%.", status="blocked", priority="high", assigned_to="Mobile Team", due_date=datetime(2026,4,15).date(), estimated_hours=40, actual_hours=5),
        Task(project_id=p3.id, title="Schema mapping", description="Map legacy database schema to new cloud models.", status="todo", priority="high", assigned_to="Data Team", due_date=datetime(2026,3,10).date(), estimated_hours=25, actual_hours=0),
        Task(project_id=p5.id, title="Social media content calendar", description="Plan and schedule all social posts.", status="done", priority="high", assigned_to="Marketing Team", due_date=datetime(2026,1,15).date(), estimated_hours=15, actual_hours=12),
        Task(project_id=p5.id, title="Email campaign sequence", description="Design 5-email drip campaign.", status="done", priority="medium", assigned_to="Marketing Team", due_date=datetime(2026,2,1).date(), estimated_hours=10, actual_hours=8)
    ]
    db.add_all(tasks)
    db.commit()
    
    for t in tasks:
        db.refresh(t)

    # Milestones
    milestones = [
        Milestone(project_id=p1.id, title="Design Approval", description="Client signs off on final designs.", due_date=datetime(2026,2,10).date(), completed=True, completed_at=datetime(2026,2,8)),
        Milestone(project_id=p1.id, title="Beta Launch", description="Internal beta with stakeholders.", due_date=datetime(2026,3,15).date(), completed=False),
        Milestone(project_id=p1.id, title="Go Live", description="Public launch of redesigned website.", due_date=datetime(2026,3,30).date(), completed=False),
        Milestone(project_id=p2.id, title="Alpha Release", description="Internal testing build.", due_date=datetime(2026,3,15).date(), completed=False),
        Milestone(project_id=p2.id, title="Beta Release", description="Limited public beta.", due_date=datetime(2026,4,15).date(), completed=False),
        Milestone(project_id=p2.id, title="Production Release", description="App store submission.", due_date=datetime(2026,5,15).date(), completed=False),
        Milestone(project_id=p5.id, title="Campaign Launch", description="All channels go live.", due_date=datetime(2026,1,20).date(), completed=True, completed_at=datetime(2026,1,20)),
        Milestone(project_id=p5.id, title="Campaign Wrap", description="Final analysis and report.", due_date=datetime(2026,2,14).date(), completed=True, completed_at=datetime(2026,2,14))
    ]
    db.add_all(milestones)
    
    # Time Entries
    time_entries = [
        TimeEntry(task_id=tasks[0].id, user_id=str(user_id), hours=8, description="Initial wireframe concepts for homepage and product pages.", date=datetime(2026,1,20).date()),
        TimeEntry(task_id=tasks[0].id, user_id=str(user_id), hours=6, description="Revised wireframes based on stakeholder feedback.", date=datetime(2026,1,22).date()),
        TimeEntry(task_id=tasks[1].id, user_id=str(user_id), hours=10, description="Set up CSS grid system and breakpoints.", date=datetime(2026,2,5).date()),
        TimeEntry(task_id=tasks[1].id, user_id=str(user_id), hours=8, description="Mobile navigation and header components.", date=datetime(2026,2,7).date()),
        TimeEntry(task_id=tasks[2].id, user_id=str(user_id), hours=12, description="User and product API endpoints.", date=datetime(2026,2,10).date()),
        TimeEntry(task_id=tasks[5].id, user_id=str(user_id), hours=8, description="Research biometric auth SDKs.", date=datetime(2026,2,8).date()),
        TimeEntry(task_id=tasks[5].id, user_id=str(user_id), hours=12, description="Implement fingerprint and face ID login.", date=datetime(2026,2,12).date()),
        TimeEntry(task_id=tasks[7].id, user_id=str(user_id), hours=15, description="Firebase push notification integration.", date=datetime(2026,2,14).date()),
        TimeEntry(task_id=tasks[10].id, user_id=str(user_id), hours=6, description="Planned 4 weeks of social content.", date=datetime(2026,1,10).date()),
        TimeEntry(task_id=tasks[11].id, user_id=str(user_id), hours=4, description="Wrote email copy for all 5 sequences.", date=datetime(2026,1,25).date())
    ]
    db.add_all(time_entries)
    
    # Insights
    insights = [
        ProjectInsight(project_id=p1.id, insight_type="risk_assessment", content="RISKS: Content migration depends on legacy CMS access which has intermittent outages. Backend API is 20% behind schedule. MITIGATIONS: Start content export early. Add one more developer to API team for 2 weeks. Overall project health: AMBER — on track if mitigations are applied this week.", model_used="seed_data", requested_by="system"),
        ProjectInsight(project_id=p2.id, insight_type="progress_summary", content="Mobile App v2 is 35% complete. Authentication revamp is ahead of schedule. Push notifications in review. BLOCKER: Performance optimization blocked pending new profiling tools. 3 of 4 tasks on track. Budget utilization at 28% ($33,600 of $120,000). Recommend unblocking performance task as priority.", model_used="seed_data", requested_by="system")
    ]
    db.add_all(insights)
    
    db.commit()
