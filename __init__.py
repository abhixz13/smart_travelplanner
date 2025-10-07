# Create these __init__.py files in your project:

# ============================================
# agents/__init__.py
# ============================================
"""
Specialized agent nodes for the itinerary planner.
Each agent handles a specific domain (flights, hotels, etc.)
"""

from agents.planner import planner_node
from agents.planner_execution import planner_execution_node
from agents.reasoning import reasoning_node
from agents.flight_agent import flight_agent_node
from agents.hotel_agent import hotel_agent_node
from agents.activity_agent import activity_agent_node
from agents.itinerary_agent import itinerary_agent_node

__all__ = [
    "planner_node",
    "planner_execution_node",
    "reasoning_node",
    "flight_agent_node",
    "hotel_agent_node",
    "activity_agent_node",
    "itinerary_agent_node",
]


# ============================================
# core/__init__.py
# ============================================
"""
Core orchestration components for the multi-agent system.
"""

from core.state import GraphState, create_initial_state
from core.graph import build_graph
from core.router import router_node
from core.follow_up import generate_follow_up_suggestions, handle_user_selection

__all__ = [
    "GraphState",
    "create_initial_state",
    "build_graph",
    "router_node",
    "generate_follow_up_suggestions",
    "handle_user_selection",
]


# ============================================
# utils/__init__.py
# ============================================
"""
Utility modules for configuration, logging, and helpers.
"""

from utils.config import load_config, get_config
from utils.logging_config import setup_logging, get_logger

__all__ = [
    "load_config",
    "get_config",
    "setup_logging",
    "get_logger",
]


# ============================================
# FOLDER STRUCTURE
# ============================================
"""
Create this complete folder structure:

itinerary-planner/
│
├── main.py
├── config.yaml
├── requirements.txt
├── README.md
├── .env                           # Create this for API keys
├── .gitignore                     # Add .env, __pycache__, *.pyc
│
├── agents/
│   ├── __init__.py
│   ├── planner.py
│   ├── planner_execution.py
│   ├── reasoning.py
│   ├── flight_agent.py
│   ├── hotel_agent.py
│   ├── activity_agent.py
│   └── itinerary_agent.py
│
├── core/
│   ├── __init__.py
│   ├── state.py
│   ├── graph.py
│   ├── router.py
│   └── follow_up.py
│
├── utils/
│   ├── __init__.py
│   ├── config.py
│   └── logging_config.py
│
├── tests/                         # For future tests
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_core.py
│   └── test_integration.py
│
└── logs/                          # Auto-created for log files
    └── .gitkeep
"""


# ============================================
# .env file (create this manually)
# ============================================
"""
# .env
# API Keys - DO NOT COMMIT THIS FILE
OPENAI_API_KEY=sk-your-key-here

# Future integrations
AMADEUS_API_KEY=your-key-here
BOOKING_API_KEY=your-key-here
VIATOR_API_KEY=your-key-here
GOOGLE_PLACES_API_KEY=your-key-here

# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# System
LOG_LEVEL=INFO
"""


# ============================================
# .gitignore file (create this manually)
# ============================================
"""
# .gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Project specific
config.local.yaml
*.db
*.sqlite
"""