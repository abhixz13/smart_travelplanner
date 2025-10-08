"""
Database helper module for Supabase integration.
Handles all database operations for sessions, itineraries, and cache.
"""

import os
import json
import hashlib
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseDB:
    """Supabase database wrapper for AI Travel Planner."""
    
    def __init__(self):
        """Initialize Supabase client."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
        
        self.client: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
    
    # ========== Session Operations ==========
    
    def create_session(self, thread_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new session in the database.
        
        Args:
            thread_id: Unique session identifier
            state: Initial session state
        
        Returns:
            Created session data
        """
        try:
            session_data = {
                "thread_id": thread_id,
                "state": json.dumps(state) if isinstance(state, dict) else state,
                "messages": json.dumps([]),
                "current_itinerary": None,
                "tool_results": json.dumps({}),
                "metadata": json.dumps({"created_at": datetime.now().isoformat()}),
                "last_active": datetime.now().isoformat()
            }
            
            response = self.client.table("user_sessions").insert(session_data).execute()
            logger.info(f"Session created: {thread_id}")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise
    
    def get_session(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a session by thread_id.
        
        Args:
            thread_id: Session identifier
        
        Returns:
            Session data or None if not found
        """
        try:
            response = self.client.table("user_sessions").select("*").eq("thread_id", thread_id).execute()
            
            if response.data and len(response.data) > 0:
                session = response.data[0]
                # Parse JSON fields
                session['state'] = json.loads(session['state']) if isinstance(session['state'], str) else session['state']
                session['messages'] = json.loads(session['messages']) if isinstance(session['messages'], str) else session['messages']
                session['tool_results'] = json.loads(session['tool_results']) if isinstance(session['tool_results'], str) else session['tool_results']
                session['metadata'] = json.loads(session['metadata']) if isinstance(session['metadata'], str) else session['metadata']
                
                if session.get('current_itinerary') and isinstance(session['current_itinerary'], str):
                    session['current_itinerary'] = json.loads(session['current_itinerary'])
                
                return session
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving session: {str(e)}")
            return None
    
    def update_session(self, thread_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing session.
        
        Args:
            thread_id: Session identifier
            updates: Dictionary of fields to update
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize JSON fields
            if 'state' in updates:
                updates['state'] = json.dumps(updates['state']) if isinstance(updates['state'], dict) else updates['state']
            if 'messages' in updates:
                converted_messages = self._convert_messages_to_dict(updates['messages'])
                updates['messages'] = json.dumps(converted_messages) if isinstance(converted_messages, list) else converted_messages
            if 'current_itinerary' in updates and updates['current_itinerary']:
                updates['current_itinerary'] = json.dumps(updates['current_itinerary']) if isinstance(updates['current_itinerary'], dict) else updates['current_itinerary']
            if 'tool_results' in updates:
                updates['tool_results'] = json.dumps(updates['tool_results']) if isinstance(updates['tool_results'], dict) else updates['tool_results']
            
            # Always update last_active
            updates['last_active'] = datetime.now().isoformat()
            
            response = self.client.table("user_sessions").update(updates).eq("thread_id", thread_id).execute()
            logger.info(f"Session updated: {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session: {str(e)}")
            return False
    
    def delete_session(self, thread_id: str) -> bool:
        """
        Delete a session and all related data.
        
        Args:
            thread_id: Session identifier
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.table("user_sessions").delete().eq("thread_id", thread_id).execute()
            logger.info(f"Session deleted: {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            return False
    
    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all sessions ordered by last_active.
        
        Args:
            limit: Maximum number of sessions to return
        
        Returns:
            List of session data
        """
        try:
            response = self.client.table("user_sessions")\
                .select("thread_id, created_at, last_active, metadata")\
                .order("last_active", desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            return []
    
    # ========== Itinerary Operations ==========
    
    def save_itinerary(self, thread_id: str, itinerary: Dict[str, Any]) -> Optional[str]:
        """
        Save an itinerary to the database.
        
        Args:
            thread_id: Associated session ID
            itinerary: Itinerary data
        
        Returns:
            Itinerary ID if successful, None otherwise
        """
        try:
            itinerary_data = {
                "thread_id": thread_id,
                "destination": itinerary.get("destination", "Unknown"),
                "start_date": itinerary.get("start_date"),
                "end_date": itinerary.get("end_date"),
                "duration_days": itinerary.get("duration_days", 0),
                "days": json.dumps(itinerary.get("days", [])),
                "total_estimated_cost": itinerary.get("total_estimated_cost"),
                "summary": itinerary.get("summary"),
                "metadata": json.dumps(itinerary.get("metadata", {})),
                "status": "active"
            }
            
            response = self.client.table("itineraries").insert(itinerary_data).execute()
            
            if response.data and len(response.data) > 0:
                itinerary_id = response.data[0]['id']
                logger.info(f"Itinerary saved: {itinerary_id}")
                return itinerary_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error saving itinerary: {str(e)}")
            return None
    
    def get_itinerary(self, itinerary_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an itinerary by ID.
        
        Args:
            itinerary_id: Itinerary UUID
        
        Returns:
            Itinerary data or None
        """
        try:
            response = self.client.table("itineraries").select("*").eq("id", itinerary_id).execute()
            
            if response.data and len(response.data) > 0:
                itinerary = response.data[0]
                # Parse JSON fields
                itinerary['days'] = json.loads(itinerary['days']) if isinstance(itinerary['days'], str) else itinerary['days']
                itinerary['metadata'] = json.loads(itinerary['metadata']) if isinstance(itinerary['metadata'], str) else itinerary['metadata']
                return itinerary
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving itinerary: {str(e)}")
            return None
    
    # ========== Cache Operations ==========
    
    def _hash_params(self, params: Dict[str, Any]) -> str:
        """Generate hash from parameters for cache key."""
        params_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(params_str.encode()).hexdigest()
    
    def get_cached_result(self, tool_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached tool result if not expired.
        
        Args:
            tool_name: Name of the tool/API
            params: Parameters used for the call
        
        Returns:
            Cached result or None
        """
        try:
            params_hash = self._hash_params(params)
            
            response = self.client.table("tool_cache")\
                .select("*")\
                .eq("tool_name", tool_name)\
                .eq("params_hash", params_hash)\
                .gt("expires_at", datetime.now().isoformat())\
                .execute()
            
            if response.data and len(response.data) > 0:
                cache_entry = response.data[0]
                result = json.loads(cache_entry['result']) if isinstance(cache_entry['result'], str) else cache_entry['result']
                logger.info(f"Cache hit: {tool_name}")
                return result
            
            logger.info(f"Cache miss: {tool_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cache: {str(e)}")
            return None
    
    def cache_result(self, tool_name: str, params: Dict[str, Any], result: Dict[str, Any], ttl_hours: int = 24) -> bool:
        """
        Cache a tool result.
        
        Args:
            tool_name: Name of the tool/API
            params: Parameters used for the call
            result: Result to cache
            ttl_hours: Time to live in hours
        
        Returns:
            True if successful, False otherwise
        """
        try:
            params_hash = self._hash_params(params)
            expires_at = datetime.now() + timedelta(hours=ttl_hours)
            
            cache_data = {
                "tool_name": tool_name,
                "params_hash": params_hash,
                "result": json.dumps(result),
                "expires_at": expires_at.isoformat()
            }
            
            # Use upsert to handle duplicates
            response = self.client.table("tool_cache").upsert(cache_data).execute()
            logger.info(f"Result cached: {tool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching result: {str(e)}")
            return False
    
    def clean_expired_cache(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of entries deleted
        """
        try:
            response = self.client.table("tool_cache")\
                .delete()\
                .lt("expires_at", datetime.now().isoformat())\
                .execute()
            
            count = len(response.data) if response.data else 0
            logger.info(f"Cleaned {count} expired cache entries")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning cache: {str(e)}")
            return 0

    def _convert_messages_to_dict(self, messages: List[Any]) -> List[Dict[str, Any]]:
        """Convert LangChain message objects to serializable dictionaries."""
        if not messages:
            return []
        
        converted_messages = []
        for msg in messages:
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                # Convert LangChain message to dict
                message_dict = {
                    "type": msg.type,
                    "content": msg.content,
                    "timestamp": getattr(msg, 'timestamp', None),
                    "metadata": getattr(msg, 'metadata', {})
                }
                converted_messages.append(message_dict)
            elif isinstance(msg, dict) and 'type' in msg and 'content' in msg:
                # Already a dictionary, use as-is
                converted_messages.append(msg)
            else:
                # Fallback: try to convert to string
                converted_messages.append({"type": "unknown", "content": str(msg)})
        
        return converted_messages


# Global database instance
_db_instance: Optional[SupabaseDB] = None


def get_db() -> SupabaseDB:
    """Get or create the global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = SupabaseDB()
    return _db_instance
