from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.database import engine, Base, get_db
import app.routes as routes_module

# Start imports for viv-auth and viv-pay
from viv_auth import init_auth
from viv_pay import init_pay

app = FastAPI()

# Health check (must be first)
@app.get("/health")
def health_check():
    return {"status": "ok"}

# API Health (Mandatory)
@app.get("/api/health")
def api_health_check():
    return {"status": "ok"}

# Initialize Auth
User, require_auth = init_auth(app, engine, Base, get_db, app_name="Project Tracker")

# Initialize Pay
create_checkout, get_customer, require_subscription = init_pay(app, engine, Base, get_db, app_name="Project Tracker")

# Wrapper: chain auth -> subscription check so require_subscription gets user_id
# viv-auth uses encrypted session cookie (viv_session), not a user_id cookie,
# so require_subscription can't find user_id on its own.
async def require_active_subscription(request: Request, user=Depends(require_auth)):
    return await require_subscription(request, user_id=user.id)

# Inject dependencies into routes module
routes_module.User = User
routes_module.require_auth = require_auth
routes_module.require_subscription = require_subscription
routes_module.create_checkout = create_checkout
routes_module.get_customer = get_customer

# Override dependency getters
app.dependency_overrides[routes_module.get_current_user] = require_auth
app.dependency_overrides[routes_module.get_active_subscription] = require_active_subscription

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(routes_module.dashboard.router)
app.include_router(routes_module.projects.router)
app.include_router(routes_module.tasks.router)
app.include_router(routes_module.milestones.router)
app.include_router(routes_module.insights.router)
app.include_router(routes_module.billing.router)

# Startup event
@app.on_event("startup")
def startup_event():
    # Ensure all tables are created
    # This includes User (from viv-auth), Billing tables (from viv-pay), and Project/Task/etc (from app.models)
    # We must import app.models so models are registered in Base
    import app.models
    Base.metadata.create_all(bind=engine)
