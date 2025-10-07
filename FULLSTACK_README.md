# AI-First Smart Travel Planner - Full-Stack Application

## 🎯 Overview

This is a complete, production-ready AI-first travel planning web application that combines a powerful multi-agent backend (LangGraph + OpenAI) with a modern React frontend. The system provides intelligent, conversational trip planning with dynamic itinerary generation, flight searches, hotel recommendations, and activity suggestions.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  - Chat Interface                                            │
│  - Itinerary Display                                         │
│  - Flight/Hotel/Activity Results                             │
│  - Suggestion Buttons (A1, A2, A3...)                        │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP/REST API
                   │
┌──────────────────▼──────────────────────────────────────────┐
│              Backend API (FastAPI)                           │
│  - REST endpoints (/api/chat, /api/suggestion)               │
│  - Session management (in-memory)                            │
│  - CORS configuration                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│         Multi-Agent System (LangGraph)                       │
│  - Router → Planner → Execution → Reasoning                 │
│  - Specialized Agents: Flight, Hotel, Activity, Itinerary   │
│  - State Management & Conversation Continuity                │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
/app/
├── backend/                    # FastAPI backend wrapper
│   ├── server.py               # API endpoints
│   ├── requirements.txt        # Backend dependencies
│   └── .env                    # Environment variables
│
├── frontend/                   # React frontend application
│   ├── src/
│   │   ├── App.js              # Main application component
│   │   ├── App.css             # Application styles
│   │   ├── index.js            # Entry point
│   │   ├── index.css           # Global styles (Tailwind)
│   │   └── components/
│   │       ├── ChatInterface.js        # Main chat UI
│   │       ├── SuggestionButtons.js    # Tokenized suggestions
│   │       ├── ItineraryCard.js        # Day-by-day itinerary
│   │       ├── FlightResults.js        # Flight options display
│   │       ├── HotelResults.js         # Hotel listings
│   │       └── ActivityResults.js      # Activity recommendations
│   ├── public/
│   │   └── index.html          # HTML template
│   ├── package.json            # Frontend dependencies
│   ├── tailwind.config.js      # Tailwind CSS configuration
│   ├── postcss.config.js       # PostCSS configuration
│   └── .env                    # Frontend environment variables
│
├── agents/                     # Specialized AI agents
│   ├── planner.py              # Planning orchestrator
│   ├── planner_execution.py   # Plan execution engine
│   ├── reasoning.py            # Validation & reasoning
│   ├── flight_agent.py         # Flight search agent
│   ├── hotel_agent.py          # Hotel search agent
│   ├── activity_agent.py       # Activity recommendation agent
│   └── itinerary_agent.py      # Itinerary composition agent
│
├── core/                       # Core orchestration components
│   ├── state.py                # State definitions
│   ├── graph.py                # StateGraph construction
│   ├── router.py               # Intent classification
│   └── follow_up.py            # Follow-up suggestions
│
├── utils/                      # Utilities and helpers
│   ├── config.py               # Configuration management
│   ├── config.yaml             # System configuration
│   ├── logging_config.py       # Logging setup
│   └── helpers.py              # Helper functions
│
├── main.py                     # Core system orchestrator
├── requirements.txt            # Python dependencies
└── README.md                   # Original backend documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 16+ and Yarn
- OpenAI API key

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd /app
   ```

2. **Backend Setup:**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   cd backend
   pip install -r requirements.txt
   
   # Set up environment variables
   # Edit backend/.env and add your OpenAI API key
   ```

3. **Frontend Setup:**
   ```bash
   cd /app/frontend
   
   # Install Node dependencies
   yarn install
   
   # Environment is already configured in .env
   ```

4. **Start the Application:**
   ```bash
   # The application is managed by supervisor
   sudo supervisorctl status
   
   # Restart services if needed
   sudo supervisorctl restart backend
   sudo supervisorctl restart frontend
   ```

5. **Access the Application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - API Documentation: http://localhost:8001/docs

## 🎨 Features

### Core Features

✅ **AI-Powered Chat Interface**
- Natural language trip planning
- Conversational continuity across sessions
- Real-time AI responses

✅ **Dynamic Itinerary Generation**
- Day-by-day travel plans
- Budget-aware recommendations
- Customizable preferences

✅ **Tokenized Suggestion System**
- Click [A1], [A2], [A3] buttons for next steps
- Context-aware suggestions
- Seamless workflow continuation

✅ **Multi-Component Search**
- Flight options display
- Hotel recommendations
- Activity suggestions
- All with mock data (MVP)

✅ **Session Management**
- Multiple conversation threads
- Session history sidebar
- Resume past planning sessions

✅ **Responsive Design**
- Mobile-friendly interface
- Adaptive layouts
- Modern UI with Tailwind CSS

### Example User Flow

1. User: "Plan a 7-day trip to Japan, budget-friendly, interested in culture and food"
2. AI generates comprehensive itinerary with day-by-day breakdown
3. System suggests: [A1] Search for flights | [A2] Find hotels | [A3] Browse activities
4. User clicks [A1]
5. AI searches and displays flight options
6. Process continues with dynamic suggestions

## 🔌 API Endpoints

### POST /api/chat
Process a user query through the AI planning system.

**Request:**
```json
{
  "query": "Plan a 7-day trip to Japan",
  "thread_id": "user_session_123",
  "user_preferences": {}
}
```

**Response:**
```json
{
  "response": "I've created a 7-day itinerary for Japan...",
  "suggestions": [
    {"token": "A1", "description": "Search for flight options"},
    {"token": "A2", "description": "Find accommodation"}
  ],
  "current_itinerary": {...},
  "state_summary": {...},
  "thread_id": "user_session_123",
  "timestamp": "2025-10-07T21:00:00.000Z"
}
```

### POST /api/suggestion
Handle user selection of a tokenized suggestion.

**Request:**
```json
{
  "token": "A1",
  "thread_id": "user_session_123"
}
```

**Response:**
Similar to /api/chat endpoint

### GET /api/session/{thread_id}
Retrieve session information and state.

### GET /api/sessions
List all user sessions.

### DELETE /api/session/{thread_id}
Delete a session and all associated data.

## 📊 Data Flow

1. **User Input** → Frontend captures message
2. **API Call** → POST to `/api/chat` with query
3. **Backend Processing** → ItineraryPlannerSystem.process_query()
4. **LangGraph Execution** → Router → Planner → Execution → Reasoning
5. **Response** → AI message + suggestions + tool results
6. **UI Update** → Display message, itinerary, results, suggestion buttons
7. **User Action** → Click suggestion button
8. **Suggestion Flow** → POST to `/api/suggestion` → Repeat from step 3

## 🛠️ Technology Stack

### Frontend
- **React 18** - UI framework
- **Tailwind CSS 3** - Styling and design system
- **Axios** - HTTP client
- **Lucide React** - Icon library
- **React Scripts** - Build tooling

### Backend
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

### AI & Multi-Agent System
- **LangGraph** - Agent orchestration framework
- **LangChain** - LLM integration
- **OpenAI GPT-4** - Language model
- **Python 3.11** - Runtime

## 🔐 Environment Variables

### Backend (.env)
```bash
OPENAI_API_KEY=your_openai_api_key_here
PORT=8001
```

### Frontend (.env)
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_NAME=AI Travel Planner
REACT_APP_VERSION=1.0.0
```

## 🧪 Testing

### Test Backend API
```bash
# Health check
curl http://localhost:8001/

# Test chat endpoint
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Plan a 5-day trip to Paris",
    "thread_id": "test_session"
  }'
```

### Test Frontend
- Open http://localhost:3000 in browser
- Try sample queries:
  - "Plan a 7-day trip to Japan"
  - "Find flights from San Francisco to Tokyo"
  - "Show me hotel options in Barcelona"

## 📝 TODO: Backend Integration Points

The application currently uses **mock data** for MVP. Here are the integration points for Phase 2 (Supabase/PostgreSQL):

### 1. Database Schema (Supabase)

**users** table:
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE,
  preferences JSONB,
  created_at TIMESTAMP
);
```

**user_sessions** table:
```sql
CREATE TABLE user_sessions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  thread_id VARCHAR(255) UNIQUE,
  state JSONB,
  last_active TIMESTAMP
);
```

**itineraries** table:
```sql
CREATE TABLE itineraries (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  destination VARCHAR(255),
  start_date DATE,
  end_date DATE,
  days JSONB,
  status VARCHAR(50),
  created_at TIMESTAMP
);
```

**tool_cache** table:
```sql
CREATE TABLE tool_cache (
  id UUID PRIMARY KEY,
  tool_name VARCHAR(100),
  params_hash VARCHAR(255),
  result JSONB,
  expires_at TIMESTAMP
);
```

### 2. API Integrations

**Flight Search:**
- Amadeus Flight Offers Search API
- Skyscanner API

**Hotel Search:**
- Booking.com API
- Expedia Rapid API

**Activities:**
- Viator API
- GetYourGuide API
- Google Places API

### 3. Code Integration Points

All TODO comments in the code are marked with:
```javascript
// TODO: Backend Integration Point
```

Key locations:
- `/app/backend/server.py` - Lines 42-56, 87-91, 134-139, 197-202, 241-246, 278-283
- `/app/frontend/src/App.js` - Lines 38-43, 73-76, 116-119, 185-187
- All result components (FlightResults.js, HotelResults.js, ActivityResults.js)

## 🎯 Next Steps (Phase 2)

1. **Authentication**
   - Implement user authentication (JWT or OAuth)
   - Link sessions to authenticated users

2. **Database Integration**
   - Set up Supabase PostgreSQL
   - Migrate from in-memory to persistent storage
   - Implement caching layer (Redis)

3. **Real API Integrations**
   - Connect to flight search APIs
   - Integrate hotel booking platforms
   - Add activity recommendation services

4. **Payment Integration**
   - Stripe for payments
   - Booking confirmations
   - Invoice generation

5. **Advanced Features**
   - Email notifications
   - Itinerary export (PDF, Email)
   - Social sharing
   - Real-time collaboration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License

## 🙏 Acknowledgments

- Built with LangGraph and LangChain
- Uses OpenAI GPT-4 for AI reasoning
- Inspired by modern agentic AI architectures
- UI designed with Tailwind CSS

## 📞 Support

For issues and questions:
- Check the inline code comments
- Review the API documentation at http://localhost:8001/docs
- Open an issue on GitHub

---

**Current Status:** MVP Phase 1 Complete ✅
- Full-stack architecture implemented
- AI chat interface working
- Mock data for all components
- Ready for Phase 2 (Supabase integration)
