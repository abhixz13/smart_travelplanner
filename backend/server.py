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

from main import ItineraryPlannerSystem
from utils.logging_config import setup_logging
from utils.helpers import ExecutionTimer

# Initialize logging first
setup_logging()
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Add parent directory to path to import main system
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Initialize FastAPI app
app = FastAPI(
    title="AI Travel Planning API",
    description="AI-first smart itinerary planner with multi-agent orchestration with Supabase",
    version="2.0.0"
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

# Try to import SupabaseDB (falls back to in-memory if not configured)
try:
    from backend.database import SupabaseDB
    SUPABASE_AVAILABLE = True
    logger.info("✅ Supabase client available")
except ImportError as e:
    SUPABASE_AVAILABLE = False
    print(f"⚠️ Supabase not available, using in-memory storage: {e}")
except Exception as e:
    SUPABASE_AVAILABLE = False
    print(f"⚠️ Supabase client failed to initialize, using in-memory storage: {e}")


# Initialize Supabase client if available
db: Optional[SupabaseDB] = None
sessions_db: Dict[str, Dict[str, Any]] = {}

if SUPABASE_AVAILABLE:
    try:
        db = SupabaseDB()
        logger.info("✅ Connected to Supabase database")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Supabase: {str(e)}")
        logger.info("📝 Falling back to in-memory storage")
        SUPABASE_AVAILABLE = False


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
    """Health check endpoint with database status."""
    return {
        "status": "online",
        "service": "AI Travel Planning API",
        "version": "2.0.0 (Supabase)",
        "database": "Supabase PostgreSQL" if SUPABASE_AVAILABLE else "In-Memory (Fallback)",
        "database_status": "connected" if (SUPABASE_AVAILABLE and db) else "fallback",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "service": "itinerary-planner-backend"
    }


@app.post("/api/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    """
    Process a user query through the AI planning system.
    Now with Supabase persistent storage!
    """
    try:
        logger.info(f"Processing chat request for thread_id={request.thread_id}")
        
        # Time the entire API request processing
        with ExecutionTimer("api_chat_request", logger_name=__name__) as timer:
            # Process query through planner system
            result = planner_system.process_query(
                query=request.query,
                thread_id=request.thread_id,
                user_preferences=request.user_preferences
            )
            
            # Extract current itinerary and messages from session state
            current_itinerary = None
            messages = []
            if request.thread_id in planner_system.sessions:
                session_state = planner_system.sessions[request.thread_id]
                current_itinerary = session_state.get("current_itinerary")
                messages = [{"type": msg.type, "content": msg.content} for msg in session_state.get("messages", [])]
            
            # Store/update session in Supabase or in-memory
            if SUPABASE_AVAILABLE and db:
                try:
                    # Check if session exists
                    existing_session = db.get_session(request.thread_id)
                    
                    if existing_session:
                        # Update existing session
                        db.update_session(request.thread_id, {
                            "state": session_state if request.thread_id in planner_system.sessions else {},
                            "messages": messages,
                            "current_itinerary": current_itinerary,
                            "metadata": {"last_query": request.query}
                        })
                        logger.info(f"✅ Session updated in Supabase: {request.thread_id}")
                    else:
                        # Create new session
                        db.create_session(request.thread_id, session_state if request.thread_id in planner_system.sessions else {})
                        logger.info(f"✅ New session created in Supabase: {request.thread_id}")
                    
                    # Save itinerary if one was generated
                    if current_itinerary:
                        db.save_itinerary(request.thread_id, current_itinerary)
                        logger.info(f"✅ Itinerary saved to Supabase")
                        
                except Exception as db_error:
                    logger.error(f"⚠️  Supabase error (non-fatal): {str(db_error)}")
                    # Continue with in-memory fallback
            
            # Fallback: Store in in-memory dict
            if not SUPABASE_AVAILABLE or not db:
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
    Now with Supabase persistent storage!
    """
    try:
        logger.info(f"Handling suggestion: token={request.token}, thread_id={request.thread_id}")
        
        result = planner_system.handle_suggestion_selection(
            token=request.token,
            thread_id=request.thread_id
        )
        
        # Extract current itinerary and messages
        current_itinerary = None
        messages = []
        if request.thread_id in planner_system.sessions:
            session_state = planner_system.sessions[request.thread_id]
            current_itinerary = session_state.get("current_itinerary")
            messages = [{"type": msg.type, "content": msg.content} for msg in session_state.get("messages", [])]
        
        # Update session in Supabase or in-memory
        if SUPABASE_AVAILABLE and db:
            try:
                db.update_session(request.thread_id, {
                    "messages": messages,
                    "current_itinerary": current_itinerary,
                    "metadata": {"last_action": request.token}
                })
                logger.info(f"✅ Session updated in Supabase: {request.thread_id}")
                
                # Save itinerary if updated
                if current_itinerary:
                    db.save_itinerary(request.thread_id, current_itinerary)
                    
            except Exception as db_error:
                logger.error(f"⚠️  Supabase error (non-fatal): {str(db_error)}")
        
        # Fallback: Update in-memory dict
        if not SUPABASE_AVAILABLE or not db:
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
    List all user sessions from Supabase.
    """
    try:
        sessions_list = []
        
        # Get from Supabase if available
        if SUPABASE_AVAILABLE and db:
            try:
                db_sessions = db.list_sessions(limit=100)
                
                for session in db_sessions:
                    # Parse metadata if it's a string
                    metadata = session.get('metadata', {})
                    if isinstance(metadata, str):
                        import json
                        metadata = json.loads(metadata)
                    
                    sessions_list.append(SessionInfo(
                        thread_id=session.get('thread_id', ''),
                        created_at=session.get('created_at', ''),
                        last_active=session.get('last_active', ''),
                        message_count=len(session.get('messages', [])),
                        has_itinerary=session.get('current_itinerary') is not None
                    ))
                
                logger.info(f"✅ Retrieved {len(sessions_list)} sessions from Supabase")
                return sessions_list
                
            except Exception as db_error:
                logger.error(f"⚠️  Supabase error: {str(db_error)}")
                # Fall through to in-memory fallback
        
        # Fallback: Get from in-memory database
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
        reload=True,  # Auto-reload for development
        timeout_keep_alive=180,  # Keep-alive timeout in seconds
        timeout_graceful_shutdown=180  # Graceful shutdown timeout in seconds
    )
