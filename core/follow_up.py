"""
Follow-up mechanism for dynamic next-step suggestions.
Enables conversational continuation after graph completion.
"""

import logging
from typing import Dict, Any, List
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

from core.state import GraphState
from utils.config import get_config

logger = logging.getLogger(__name__)


def generate_follow_up_suggestions(state: GraphState) -> Dict[str, Any]:
    """
    Generate dynamic follow-up suggestions based on current state.
    
    Uses LLM to reason about what the user might want next and creates
    tokenized suggestions (A1, A2, A3, etc.) for unambiguous selection.
    
    Args:
        state: Current graph state
    
    Returns:
        Dict with suggestions list and AI message
    """
    logger.info("Generating follow-up suggestions")
    
    try:
        config = get_config()
        llm = ChatOpenAI(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"]
        )
        
        # Build context
        context = _build_follow_up_context(state)
        
        # Build prompt
        follow_up_prompt = f"""You are analyzing a travel planning session to suggest helpful next steps.

Current State:
{context}

Your task: Suggest 3-5 logical next actions the user might want to take.

Available actions:
- search_flights: Find flight options
- search_hotels: Find accommodation
- search_activities: Find things to do
- modify_itinerary: Change the current itinerary
- get_recommendations: Get specific recommendations
- check_budget: Review and optimize budget
- explore_destination: Learn more about the destination
- finalize_plan: Review and finalize the trip

Consider:
- What has been done already?
- What is missing from a complete trip plan?
- What would add value to the user's planning?
- What logical next steps follow from current state?

Respond with JSON:
{{
  "suggestions": [
    {{
      "action": "search_flights",
      "description": "Find the best flight options for your dates",
      "priority": 1
    }},
    {{
      "action": "search_hotels",
      "description": "Browse accommodation options in Tokyo",
      "priority": 2
    }}
  ],
  "reasoning": "Explanation of why these suggestions make sense"
}}

Prioritize suggestions (1 = highest priority).
Respond with ONLY valid JSON.
"""
        
        # Get suggestions
        response = llm.invoke(follow_up_prompt)
        
        import json
        result = json.loads(response.content.strip())
        
        suggestions = result.get("suggestions", [])
        reasoning = result.get("reasoning", "")
        
        # Add tokens to suggestions
        tokenized_suggestions = []
        for i, suggestion in enumerate(suggestions):
            tokenized_suggestions.append({
                "token": f"A{i + 1}",
                "action": suggestion["action"],
                "description": suggestion["description"],
                "priority": suggestion.get("priority", i + 1)
            })
        
        # Create user-friendly message
        message_parts = ["\n💡 What would you like to do next?\n"]
        for sug in tokenized_suggestions:
            message_parts.append(f"  [{sug['token']}] {sug['description']}")
        
        message_parts.append("\n\nSelect an option or ask me anything!")
        
        ai_message = AIMessage(
            content="".join(message_parts),
            additional_kwargs={
                "suggestions": tokenized_suggestions,
                "reasoning": reasoning
            }
        )
        
        logger.info(f"Generated {len(tokenized_suggestions)} follow-up suggestions")
        
        return {
            "suggestions": tokenized_suggestions,
            "message": ai_message,
            "reasoning": reasoning
        }
        
    except Exception as e:
        logger.error(f"Error generating follow-up: {str(e)}", exc_info=True)
        
        # Return default suggestions
        default_suggestions = [
            {
                "token": "A1",
                "action": "search_flights",
                "description": "Search for flight options",
                "priority": 1
            },
            {
                "token": "A2",
                "action": "search_hotels",
                "description": "Find accommodation",
                "priority": 2
            },
            {
                "token": "A3",
                "action": "modify_itinerary",
                "description": "Modify the itinerary",
                "priority": 3
            }
        ]
        
        return {
            "suggestions": default_suggestions,
            "message": AIMessage(content="What would you like to do next?"),
            "reasoning": "Default suggestions"
        }


def handle_user_selection(state: GraphState, token: str) -> GraphState:
    """
    Handle user selection of a tokenized suggestion.
    
    Maps the token to an action and updates state to trigger
    the appropriate agent.
    
    Args:
        state: Current graph state
        token: Selected suggestion token (e.g., "A1")
    
    Returns:
        Updated state ready for graph re-invocation
    """
    logger.info(f"Handling user selection: {token}")
    
    # Get suggestions from last AI message
    suggestions = []
    for msg in reversed(state["messages"]):
        if hasattr(msg, "additional_kwargs") and "suggestions" in msg.additional_kwargs:
            suggestions = msg.additional_kwargs["suggestions"]
            break
    
    # Find matching suggestion
    selected_suggestion = None
    for sug in suggestions:
        if sug["token"] == token:
            selected_suggestion = sug
            break
    
    if not selected_suggestion:
        logger.warning(f"Token not found: {token}")
        return state
    
    # Map action to agent
    action_to_agent = {
        "search_flights": "FLIGHT",
        "search_hotels": "HOTEL",
        "search_activities": "ACTIVITY",
        "modify_itinerary": "ITINERARY",
        "get_recommendations": "ACTIVITY",
        "check_budget": "REASONING",
        "explore_destination": "ACTIVITY",
        "finalize_plan": "REASONING"
    }
    
    agent = action_to_agent.get(selected_suggestion["action"], "PLANNER")
    
    # Create user message simulating the selection
    user_message = HumanMessage(
        content=f"I'd like to: {selected_suggestion['description']}",
        additional_kwargs={"selected_token": token}
    )
    
    # Update state
    updated_state = GraphState(
        messages=state["messages"] + [user_message],
        plan=state.get("plan"),
        current_itinerary=state.get("current_itinerary"),
        user_preferences=state.get("user_preferences", {}),
        next_agent="",  # Will be determined by router
        tool_results=state.get("tool_results", {}),
        metadata=state.get("metadata", {})
    )
    
    logger.info(f"Mapped token {token} to action: {selected_suggestion['action']}")
    
    return updated_state


def _build_follow_up_context(state: GraphState) -> str:
    """Build context string for follow-up prompt."""
    context_parts = []
    
    # Plan status
    plan = state.get("plan")
    if plan:
        executed = len([s for s in plan.get("steps", []) if s.get("executed", False)])
        total = len(plan.get("steps", []))
        context_parts.append(f"✓ Plan executed: {executed}/{total} steps completed")
    
    # Itinerary status
    itinerary = state.get("current_itinerary")
    if itinerary:
        context_parts.append(f"✓ Itinerary created: {itinerary.get('duration_days', 0)} days")
    else:
        context_parts.append("✗ No itinerary yet")
    
    # Tool results
    tool_results = state.get("tool_results", {})
    if "flight_search" in tool_results:
        context_parts.append("✓ Flights searched")
    else:
        context_parts.append("✗ No flight search yet")
    
    if "hotel_search" in tool_results:
        context_parts.append("✓ Hotels searched")
    else:
        context_parts.append("✗ No hotel search yet")
    
    if "activity_search" in tool_results:
        context_parts.append("✓ Activities searched")
    else:
        context_parts.append("✗ No activity search yet")
    
    # User preferences
    prefs = tool_results.get("s1", {})  # Step 1 is usually preference extraction
    if prefs and isinstance(prefs, dict):
        context_parts.append(f"\nDestination: {prefs.get('destination', 'Not set')}")
        context_parts.append(f"Duration: {prefs.get('duration_days', 'Not set')} days")
        context_parts.append(f"Budget: {prefs.get('budget', 'Not set')}")
        context_parts.append(f"Interests: {', '.join(prefs.get('interests', []))}")
    
    return "\n".join(context_parts)