"""
FastAPI Backend Server for AI Travel Planning System
Wraps the LangGraph multi-agent system with REST API endpoints
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Add parent directory to path to import main system
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import ItineraryPlannerSystem
from utils.logging_config import setup_logging

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Travel Planning API",
    description="AI-first smart itinerary planner with multi-agent orchestration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the planning system
planner_system = ItineraryPlannerSystem()

# In-memory session storage (MVP)
# TODO: Replace with Supabase/PostgreSQL for production
# - Store sessions in 'user_sessions' table with thread_id as key
# - Persist state as JSON in 'state' column
# - Add user authentication and link sessions to user_id
sessions_db: Dict[str, Dict[str, Any]] = {}


# Pydantic models for request/response validation
class ChatRequest(BaseModel):
    query: str
    thread_id: Optional[str] = "default"
    user_preferences: Optional[Dict[str, Any]] = {}


class SuggestionRequest(BaseModel):
    token: str
    thread_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    suggestions: List[Dict[str, Any]]
    state_summary: Dict[str, Any]
    thread_id: str
    timestamp: str
    current_itinerary: Optional[Dict[str, Any]] = None


class SessionInfo(BaseModel):
    thread_id: str
    created_at: str
    last_active: str
    message_count: int
    has_itinerary: bool


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "AI Travel Planning API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    """
    Process a user query through the AI planning system.
    
    This endpoint handles initial queries and follow-up questions.
    The system maintains conversation context via thread_id.
    
    TODO: Backend Integration Points
    - Replace in-memory sessions_db with Supabase query
    - Store messages in 'messages' table linked to thread_id
    - Cache tool_results in 'tool_cache' table with TTL
    - Log all queries for analytics
    """
    try:
        logger.info(f"Processing chat request for thread_id={request.thread_id}")
        
        # Process query through planner system
        result = planner_system.process_query(
            query=request.query,
            thread_id=request.thread_id,
            user_preferences=request.user_preferences
        )
        
        # Extract current itinerary from session state
        current_itinerary = None
        if request.thread_id in planner_system.sessions:
            session_state = planner_system.sessions[request.thread_id]
            current_itinerary = session_state.get("current_itinerary")
        
        # Store session metadata in mock database
        # TODO: Replace with Supabase insert/update
        # Example:
        # supabase.table('user_sessions').upsert({
        #     'thread_id': request.thread_id,
        #     'state': session_state,
        #     'last_active': datetime.now()
        # })
        sessions_db[request.thread_id] = {
            "thread_id": request.thread_id,
            "created_at": sessions_db.get(request.thread_id, {}).get(
                "created_at", datetime.now().isoformat()
            ),
            "last_active": datetime.now().isoformat(),
            "query": request.query,
            "response": result.get("response"),
            "has_itinerary": current_itinerary is not None
        }
        
        return ChatResponse(
            response=result.get("response", "No response generated"),
            suggestions=result.get("suggestions", []),
            state_summary=result.get("state_summary", {}),
            thread_id=result.get("thread_id", request.thread_id),
            timestamp=result.get("timestamp", datetime.now().isoformat()),
            current_itinerary=current_itinerary
        )
        
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggestion", response_model=ChatResponse)
async def handle_suggestion(request: SuggestionRequest):
    """
    Handle user selection of a tokenized suggestion (A1, A2, A3, etc.).
    
    This triggers the corresponding agent action and returns updated results.
    
    TODO: Backend Integration Points
    - Log suggestion selections for analytics
    - Track user behavior patterns
    - Store action results in database
    """
    try:
        logger.info(f"Handling suggestion: token={request.token}, thread_id={request.thread_id}")
        
        result = planner_system.handle_suggestion_selection(
            token=request.token,
            thread_id=request.thread_id
        )
        
        # Extract current itinerary
        current_itinerary = None
        if request.thread_id in planner_system.sessions:
            session_state = planner_system.sessions[request.thread_id]
            current_itinerary = session_state.get("current_itinerary")
        
        # Update session in mock database
        # TODO: Replace with Supabase update
        if request.thread_id in sessions_db:
            sessions_db[request.thread_id].update({
                "last_active": datetime.now().isoformat(),
                "last_action": request.token,
                "has_itinerary": current_itinerary is not None
            })
        
        return ChatResponse(
            response=result.get("response", "No response generated"),
            suggestions=result.get("suggestions", []),
            state_summary=result.get("state_summary", {}),
            thread_id=result.get("thread_id", request.thread_id),
            timestamp=result.get("timestamp", datetime.now().isoformat()),
            current_itinerary=current_itinerary
        )
        
    except Exception as e:
        logger.error(f"Error handling suggestion: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{thread_id}")
async def get_session(thread_id: str):
    """
    Retrieve session information and state.
    
    TODO: Backend Integration Points
    - Query Supabase 'user_sessions' table
    - Return full conversation history
    - Include all cached results
    """
    try:
        # Get from in-memory storage
        if thread_id in sessions_db:
            return sessions_db[thread_id]
        
        # Check if session exists in planner system
        if thread_id in planner_system.sessions:
            state = planner_system.sessions[thread_id]
            return {
                "thread_id": thread_id,
                "message_count": len(state.get("messages", [])),
                "has_itinerary": state.get("current_itinerary") is not None,
                "current_itinerary": state.get("current_itinerary")
            }
        
        raise HTTPException(status_code=404, detail="Session not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """
    List all user sessions.
    
    TODO: Backend Integration Points
    - Query all sessions from Supabase
    - Filter by user_id (requires authentication)
    - Paginate results for large datasets
    """
    try:
        sessions_list = []
        
        # Get from mock database
        for thread_id, session_data in sessions_db.items():
            sessions_list.append(SessionInfo(
                thread_id=thread_id,
                created_at=session_data.get("created_at", ""),
                last_active=session_data.get("last_active", ""),
                message_count=len(planner_system.sessions.get(thread_id, {}).get("messages", [])),
                has_itinerary=session_data.get("has_itinerary", False)
            ))
        
        # Sort by last_active (most recent first)
        sessions_list.sort(key=lambda x: x.last_active, reverse=True)
        
        return sessions_list
        
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/session/{thread_id}")
async def delete_session(thread_id: str):
    """
    Delete a session and all associated data.
    
    TODO: Backend Integration Points
    - Delete from Supabase 'user_sessions' table
    - Clean up related data (messages, cached results)
    - Verify user owns the session (authentication)
    """
    try:
        # Remove from mock database
        if thread_id in sessions_db:
            del sessions_db[thread_id]
        
        # Remove from planner system
        if thread_id in planner_system.sessions:
            del planner_system.sessions[thread_id]
        
        return {"status": "success", "message": f"Session {thread_id} deleted"}
        
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8001))
    
    logger.info(f"Starting AI Travel Planning API on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
