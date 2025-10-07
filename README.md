AI-First Smart Itinerary Planner
A production-grade, multi-agent AI system for intelligent travel planning using LangGraph and LLM-driven reasoning.

🎯 Overview
This system implements a state-driven, multi-agent orchestration pattern that dynamically plans travel itineraries through specialized agents. The architecture separates concerns into routing, planning, execution, reasoning, and specialized domain agents (Flight, Hotel, Activity, Itinerary).

Key Features
🤖 Multi-Agent Architecture: Specialized agents for different travel components
🧠 LLM-Driven Reasoning: Dynamic decision-making and plan generation
🔄 Conversational Continuation: Intelligent follow-up suggestions after graph completion
📊 State Management: Comprehensive state tracking across the planning workflow
🔌 Extensible Design: Easy to add new agents, tools, and capabilities
💾 Production-Ready: Designed for integration with real APIs and databases
📁 Project Structure
itinerary-planner/
├── main.py                          # System orchestrator and entry point
├── config.yaml                      # Configuration file
├── requirements.txt                 # Python dependencies
│
├── core/                            # Core orchestration components
│   ├── state.py                     # State definitions and data structures
│   ├── graph.py                     # StateGraph construction
│   ├── router.py                    # Router node for intent classification
│   └── follow_up.py                 # Follow-up suggestion engine
│
├── agents/                          # Specialized agent nodes
│   ├── planner.py                   # Central planning orchestrator
│   ├── planner_execution.py        # Plan execution engine
│   ├── reasoning.py                 # Validation and reasoning
│   ├── flight_agent.py             # Flight search agent
│   ├── hotel_agent.py              # Hotel search agent
│   ├── activity_agent.py           # Activity recommendation agent
│   └── itinerary_agent.py          # Itinerary composition agent
│
└── utils/                           # Utilities and helpers
    ├── config.py                    # Configuration management
    └── logging_config.py            # Logging setup
🚀 Quick Start
Prerequisites
Python 3.10+
OpenAI API key
Installation
Clone the repository:
bash
git clone <repository-url>
cd itinerary-planner
Install dependencies:
bash
pip install -r requirements.txt
Set up environment variables:
bash
export OPENAI_API_KEY="your-api-key-here"
Run the demo:
bash
python main.py
💡 Usage Examples
Basic Usage
python
from main import ItineraryPlannerSystem

# Initialize the system
planner = ItineraryPlannerSystem()

# Process a travel query
result = planner.process_query(
    query="Plan a 7-day trip to Japan, budget-friendly, interested in culture and food",
    thread_id="user_session_123"
)

# Display response
print(result["response"])

# Show suggestions
for suggestion in result["suggestions"]:
    print(f"[{suggestion['token']}] {suggestion['description']}")

# Handle user selection
follow_up = planner.handle_suggestion_selection(
    token="A1",
    thread_id="user_session_123"
)
Conversation Flow
User: "Plan a 7-day trip to Japan, budget-friendly"
  ↓
Router → Planner → Execution → Reasoning
  ↓
System: "Created itinerary for 7 days in Tokyo..."
  ↓
Follow-up Suggestions:
  [A1] Search for flight options
  [A2] Find accommodation
  [A3] Browse activities
  ↓
User: Selects A1
  ↓
Router → Flight Agent → Results
  ↓
System: "Found 4 flight options..."
🏗️ Architecture
State Graph Flow
Entry → Router
         ↓
    [Conditional Routing]
         ↓
    ┌────┴────┬────────┬─────────┬──────────┐
    ↓         ↓        ↓         ↓          ↓
 Planner  Flight   Hotel   Activity  Itinerary
    ↓         ↓        ↓         ↓          ↓
    └────┬────┴────────┴─────────┴──────────┘
         ↓
     Reasoning
         ↓
    [Check Next]
         ↓
    Router or END
         ↓
    Follow-up Suggestions
Node Responsibilities
Router: Analyzes intent and routes to appropriate agent
Planner: Generates structured execution plans (JSON)
Planner Execution: Executes plan steps, invokes specialized agents
Reasoning: Validates coherence, suggests next actions
Specialized Agents: Handle domain-specific tasks (flights, hotels, etc.)
Follow-up: Generates dynamic suggestions for conversation continuation
State Structure
python
GraphState = {
    "messages": List[BaseMessage],           # Conversation history
    "plan": Dict[str, Any],                  # Execution plan
    "current_itinerary": Dict[str, Any],     # Built itinerary
    "user_preferences": Dict[str, Any],      # Extracted preferences
    "next_agent": str,                       # Routing decision
    "tool_results": Dict[str, Any],          # Cached results
    "metadata": Dict[str, Any]               # Session metadata
}
🔧 Configuration
Edit config.yaml to customize:

LLM model and parameters
API keys and endpoints
Agent behavior
Budget ranges
Feature flags
Environment variables override config file settings.

🧪 MVP vs Production
Current (MVP)
✅ Mock data for flights, hotels, activities
✅ In-memory state storage
✅ Local execution
✅ Basic error handling
Production Roadmap
🔲 Real API integrations (Amadeus, Booking.com, Viator)
🔲 Supabase PostgreSQL for persistent storage
🔲 User authentication and session management
🔲 Caching layer (Redis)
🔲 Background tasks (Celery)
🔲 Payment integration (Stripe)
🔲 Booking confirmations
🔲 Real-time updates
🔲 Cost optimization algorithms
🗄️ Database Schema (Production)
Supabase Tables
users

id, email, preferences, created_at
itineraries

id, user_id, destination, dates, days (JSON), status, created_at
user_sessions

id, user_id, thread_id, state (JSON), last_active
plans

id, session_id, steps (JSON), executed_steps, created_at
tool_cache

id, tool_name, params_hash, result (JSON), expires_at
🔌 API Integrations (Production)
Flight Search
Amadeus Flight Offers Search API: Real-time flight prices
Skyscanner API: Alternative flight search
Hotel Search
Booking.com API: Hotel inventory
Expedia Rapid API: Alternative accommodation
Activities
Viator API: Tours and activities
GetYourGuide API: Alternative activities
Google Places API: POI information
📝 Logging
Logs are output to console (INFO) and optionally to file (DEBUG).

python
# In your code
import logging
logger = logging.getLogger(__name__)

logger.info("Processing query")
logger.debug("Detailed state: %s", state)
logger.error("Error occurred", exc_info=True)
🧪 Testing
bash
# Run tests (when implemented)
pytest tests/

# Run with coverage
pytest --cov=. tests/
🤝 Contributing
Fork the repository
Create a feature branch
Make your changes
Add tests
Submit a pull request
📄 License
MIT License - see LICENSE file for details

🙏 Acknowledgments
Built with LangGraph and LangChain
Uses OpenAI GPT models for reasoning
Inspired by modern agentic AI architectures
📞 Support
For issues and questions:

Open an issue on GitHub
Check the documentation
Review the code comments
Note: This is an MVP implementation with mock data. For production deployment, integrate real APIs and implement proper data persistence, authentication, and error handling as outlined in the configuration and code comments.

