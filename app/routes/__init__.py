# Placeholders for dependency injection from main.py
User = None
require_auth = None
require_subscription = None
create_checkout = None
get_customer = None

def get_current_user():
    pass

def get_active_subscription():
    pass

# Import route modules so they can be accessed by main.py
from . import dashboard, projects, tasks, milestones, insights, billing
