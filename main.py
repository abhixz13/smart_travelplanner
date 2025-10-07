"""
AI-First Smart Itinerary Planner - Main Orchestrator
Production-grade multi-agent system for dynamic travel planning
"""

import logging
from typing import Dict, Any
from datetime import datetime

from core.state import GraphState, create_initial_state
from core.graph import build_graph
from core.follow_up import generate_follow_up_suggestions, handle_user_selection
from utils.config import load_config
from utils.logging_config import setup_logging

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)


class ItineraryPlannerSystem:
    """Main orchestrator for the AI itinerary planning system."""
    
    def __init__(self):
        """Initialize the planner system."""
        self.config = load_config()
        self.graph = build_graph()
        self.sessions: Dict[str, GraphState] = {}  # Thread ID -> State mapping
        logger.info("ItineraryPlannerSystem initialized successfully")
    
    def process_query(self, 
                     query: str, 
                     thread_id: str = "default",
                     **kwargs) -> Dict[str, Any]:
        """
        Process a user query through the agent system.
        
        Args:
            query: Natural language user query
            thread_id: Session identifier for conversation continuity
            **kwargs: Additional context (user_preferences, etc.)
        
        Returns:
            Dict containing response, state, and follow-up suggestions
        """
        logger.info(f"Processing query for thread_id={thread_id}: {query[:100]}...")
        
        try:
            # Get or create state for this thread
            if thread_id in self.sessions:
                state = self.sessions[thread_id]
                logger.info(f"Resuming existing session: {thread_id}")
            else:
                state = create_initial_state(query, **kwargs)
                logger.info(f"Created new session: {thread_id}")
            
            # Add new user message to state
            from langchain_core.messages import HumanMessage
            state["messages"].append(HumanMessage(content=query))
            
            # Run the state graph with increased recursion limit
            logger.info("Invoking state graph execution")
            final_state = self.graph.invoke(state, config={"recursion_limit": 50})
            
            # Store updated state
            self.sessions[thread_id] = final_state
            
            # Generate follow-up suggestions
            logger.info("Generating follow-up suggestions")
            follow_up_result = generate_follow_up_suggestions(final_state)
            
            # Add follow-up message to state
            final_state["messages"].append(follow_up_result["message"])
            self.sessions[thread_id] = final_state
            
            # Extract response
            response_text = self._extract_response(final_state)
            
            result = {
                "response": response_text,
                "suggestions": follow_up_result["suggestions"],
                "state_summary": self._summarize_state(final_state),
                "thread_id": thread_id,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Query processed successfully. Generated {len(follow_up_result['suggestions'])} suggestions")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "response": "I encountered an error processing your request. Please try again.",
                "suggestions": [],
                "thread_id": thread_id
            }
    
    def handle_suggestion_selection(self, 
                                    token: str, 
                                    thread_id: str = "default") -> Dict[str, Any]:
        """
        Handle user selection of a tokenized suggestion.
        
        Args:
            token: Suggestion token (e.g., "A1", "A2")
            thread_id: Session identifier
        
        Returns:
            Dict containing updated response and new suggestions
        """
        logger.info(f"Handling suggestion selection: token={token}, thread_id={thread_id}")
        
        if thread_id not in self.sessions:
            logger.error(f"Thread ID not found: {thread_id}")
            return {
                "error": "Session not found. Please start a new conversation.",
                "thread_id": thread_id
            }
        
        try:
            state = self.sessions[thread_id]
            
            # Handle the selection
            updated_state = handle_user_selection(state, token)
            
            # Run graph with updated state
            logger.info("Re-invoking graph after user selection")
            final_state = self.graph.invoke(updated_state)
            
            # Store updated state
            self.sessions[thread_id] = final_state
            
            # Generate new follow-up suggestions
            follow_up_result = generate_follow_up_suggestions(final_state)
            final_state["messages"].append(follow_up_result["message"])
            self.sessions[thread_id] = final_state
            
            response_text = self._extract_response(final_state)
            
            result = {
                "response": response_text,
                "suggestions": follow_up_result["suggestions"],
                "state_summary": self._summarize_state(final_state),
                "thread_id": thread_id,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Suggestion handled successfully: {token}")
            return result
            
        except Exception as e:
            logger.error(f"Error handling suggestion: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "response": "I encountered an error processing your selection. Please try again.",
                "thread_id": thread_id
            }
    
    def _extract_response(self, state: GraphState) -> str:
        """Extract human-readable response from state."""
        if not state["messages"]:
            return "No response generated."
        
        # Get last AI message
        for msg in reversed(state["messages"]):
            if hasattr(msg, "type") and msg.type == "ai":
                return msg.content
        
        return "Processing complete. Please review the itinerary above."
    
    def _summarize_state(self, state: GraphState) -> Dict[str, Any]:
        """Create a summary of current state for debugging/UI."""
        return {
            "message_count": len(state["messages"]),
            "has_plan": state.get("plan") is not None,
            "executed_steps": len([s for s in state.get("plan", {}).get("steps", []) 
                                  if s.get("executed", False)]),
            "current_itinerary": bool(state.get("current_itinerary")),
            "last_agent": state.get("next_agent", "none")
        }


def main():
    """Example usage of the itinerary planner system."""
    print("=" * 80)
    print("AI-First Smart Itinerary Planner System")
    print("=" * 80)
    print()
    
    # Initialize system
    planner = ItineraryPlannerSystem()
    
    # Example query
    query = "Plan a 7-day trip to Japan, budget-friendly, interested in culture and food"
    print(f"User Query: {query}")
    print("-" * 80)
    
    # Process query
    result = planner.process_query(query, thread_id="demo_session_001")
    
    # Display response
    print("\n✅ SYSTEM RESPONSE:")
    print(result["response"])
    print()
    
    # Display suggestions
    if result.get("suggestions"):
        print("\n💡 SUGGESTED NEXT STEPS:")
        for suggestion in result["suggestions"]:
            print(f"  [{suggestion['token']}] {suggestion['description']}")
    print()
    
    # Display state summary
    print("\n📊 STATE SUMMARY:")
    for key, value in result["state_summary"].items():
        print(f"  {key}: {value}")
    print()
    
    # Simulate user selecting a suggestion
    if result.get("suggestions"):
        selected_token = result["suggestions"][0]["token"]
        print(f"\n🔄 USER SELECTS: {selected_token}")
        print("-" * 80)
        
        follow_up_result = planner.handle_suggestion_selection(
            selected_token, 
            thread_id="demo_session_001"
        )
        
        print("\n✅ FOLLOW-UP RESPONSE:")
        print(follow_up_result["response"])
        print()
        
        if follow_up_result.get("suggestions"):
            print("\n💡 NEW SUGGESTIONS:")
            for suggestion in follow_up_result["suggestions"]:
                print(f"  [{suggestion['token']}] {suggestion['description']}")
    
    print("\n" + "=" * 80)
    print("Demo completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()