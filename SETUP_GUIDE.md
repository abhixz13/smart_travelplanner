Setup Guide - AI-First Smart Itinerary Planner
Complete installation and setup guide for running the system locally.

📋 Prerequisites
Python 3.10 or higher
pip (Python package manager)
OpenAI API Key (required for LLM functionality)
Git (for cloning the repository)
🔧 Step-by-Step Setup
1. Create Project Directory
bash
mkdir itinerary-planner
cd itinerary-planner
2. Set Up Python Virtual Environment
bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
3. Create Directory Structure
bash
# Create directories
mkdir -p agents core utils tests logs

# Create __init__.py files
touch agents/__init__.py
touch core/__init__.py
touch utils/__init__.py
touch tests/__init__.py
touch logs/.gitkeep
4. Install Dependencies
Create requirements.txt with the provided content, then:

bash
pip install -r requirements.txt
5. Configure Environment Variables
Create a .env file in the project root:

bash
# .env
OPENAI_API_KEY=your-openai-api-key-here

# Optional (for future use)
AMADEUS_API_KEY=
BOOKING_API_KEY=
VIATOR_API_KEY=
GOOGLE_PLACES_API_KEY=

# Database (Supabase - for production)
SUPABASE_URL=
SUPABASE_KEY=

# System
LOG_LEVEL=INFO
Important: Never commit .env to version control!

6. Add Files to Project
Copy all the provided code files to their respective locations:

itinerary-planner/
├── main.py
├── config.yaml
├── requirements.txt
├── .env
├── agents/
│   ├── __init__.py
│   ├── planner.py
│   ├── planner_execution.py
│   ├── reasoning.py
│   ├── flight_agent.py
│   ├── hotel_agent.py
│   ├── activity_agent.py
│   └── itinerary_agent.py
├── core/
│   ├── __init__.py
│   ├── state.py
│   ├── graph.py
│   ├── router.py
│   └── follow_up.py
└── utils/
    ├── __init__.py
    ├── config.py
    ├── logging_config.py
    └── helpers.py
7. Create .gitignore
bash
# .gitignore
__pycache__/
*.py[cod]
.env
venv/
*.log
logs/
.DS_Store
.vscode/
.idea/
8. Verify Installation
bash
# Test import
python -c "from main import ItineraryPlannerSystem; print('✅ Installation successful!')"
🚀 Running the System
Basic Run
bash
python main.py
This will execute the demo scenario from main.py.

Interactive Usage
python
from main import ItineraryPlannerSystem

# Initialize
planner = ItineraryPlannerSystem()

# Process query
result = planner.process_query(
    query="Plan a 7-day trip to Japan",
    thread_id="user_123"
)

# Display results
print(result["response"])
for sug in result["suggestions"]:
    print(f"[{sug['token']}] {sug['description']}")
Run Examples
bash
python example_usage.py
🔍 Verification Checklist
 Python 3.10+ installed
 Virtual environment activated
 All dependencies installed successfully
 .env file created with OpenAI API key
 All code files in correct directories
 python main.py runs without errors
 Demo output shows itinerary generation
🐛 Troubleshooting
Issue: ModuleNotFoundError
Solution: Ensure virtual environment is activated and dependencies installed:

bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
Issue: OpenAI API Error
Solution: Verify your API key is correct:

bash
echo $OPENAI_API_KEY  # Should display your key
If empty, add to .env and reload:

bash
export OPENAI_API_KEY=your-key-here  # Linux/macOS
set OPENAI_API_KEY=your-key-here     # Windows CMD
Issue: Import Errors
Solution: Ensure you're in the project root directory and __init__.py files exist:

bash
ls agents/__init__.py core/__init__.py utils/__init__.py
Issue: Config File Not Found
Solution: Ensure config.yaml is in the project root:

bash
ls config.yaml
Issue: Permission Errors on Logs
Solution: Create logs directory with proper permissions:

bash
mkdir -p logs
chmod 755 logs
📊 Testing Your Setup
Quick Test Script
Create test_setup.py:

python
#!/usr/bin/env python
"""Quick setup verification script."""

import sys

def test_imports():
    """Test all imports."""
    try:
        from main import ItineraryPlannerSystem
        from core.state import GraphState
        from core.graph import build_graph
        from agents.planner import planner_node
        from utils.config import load_config
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config():
    """Test configuration loading."""
    try:
        from utils.config import load_config
        config = load_config()
        assert config["llm"]["model"]
        print("✅ Configuration loaded")
        return True
    except Exception as e:
        print(f"❌ Config failed: {e}")
        return False

def test_graph():
    """Test graph construction."""
    try:
        from core.graph import build_graph
        graph = build_graph()
        print("✅ State graph built")
        return True
    except Exception as e:
        print(f"❌ Graph build failed: {e}")
        return False

def test_system():
    """Test system initialization."""
    try:
        from main import ItineraryPlannerSystem
        planner = ItineraryPlannerSystem()
        print("✅ System initialized")
        return True
    except Exception as e:
        print(f"❌ System init failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing setup...\n")
    
    tests = [
        test_imports,
        test_config,
        test_graph,
        test_system
    ]
    
    results = [test() for test in tests]
    
    print(f"\n{'='*50}")
    if all(results):
        print("✅ All tests passed! Setup is complete.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check errors above.")
        sys.exit(1)
Run it:

bash
python test_setup.py
🎯 Next Steps
Run the Demo: python main.py
Try Examples: python example_usage.py
Explore the Code: Start with main.py and follow the flow
Customize Config: Edit config.yaml for your needs
Build Your Integration: Add real API calls to replace mock data
📚 Additional Resources
LangGraph Docs: https://python.langchain.com/docs/langgraph
LangChain Docs: https://python.langchain.com/docs/
OpenAI API: https://platform.openai.com/docs/
💡 Development Tips
Enable Debug Logging
In .env:

bash
LOG_LEVEL=DEBUG
Use IPython for Interactive Development
bash
pip install ipython
ipython
Then:

python
from main import ItineraryPlannerSystem
planner = ItineraryPlannerSystem()
# Interactive exploration
Monitor State Changes
Add logging to see state updates:

python
import logging
logging.basicConfig(level=logging.DEBUG)
🚀 Production Deployment
For production deployment, see:

config.yaml - Production integration notes
README.md - Production roadmap section
Database schema comments in code
Key production tasks:

 Set up Supabase database
 Integrate real flight APIs (Amadeus)
 Integrate hotel APIs (Booking.com)
 Integrate activity APIs (Viator)
 Implement authentication
 Add caching layer (Redis)
 Set up monitoring and logging
 Deploy to cloud (AWS/GCP/Azure)
Questions? Check the README.md or review code comments for detailed explanations.

