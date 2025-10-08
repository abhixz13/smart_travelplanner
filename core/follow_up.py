"""
Follow-up mechanism for dynamic next-step suggestions.
Enables conversational continuation after graph completion.
"""

import logging
from typing import Dict, Any, List, Callable
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

from core.state import GraphState
from utils.config import get_config

logger = logging.getLogger(__name__)


# ============================================================================
# ACTION REGISTRY: Defines all available follow-up actions and their logic
# ============================================================================

ACTION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "search_flights": {
        "agent": "FLIGHT",
        "description": "Search for flight options to {destination}",
        "available_when": lambda state: "flight_search" not in state.get("tool_results", {})
    },
    "review_flights": {
        "agent": "FLIGHT",
        "description": "Review the {count} flight options we found",
        "available_when": lambda state: "flight_search" in state.get("tool_results", {})
    },
    "search_hotels": {
        "agent": "HOTEL",
        "description": "Find accommodation in {destination}",
        "available_when": lambda state: "hotel_search" not in state.get("tool_results", {})
    },
    "review_hotels": {
        "agent": "HOTEL",
        "description": "Review the {count} hotel options we found",
        "available_when": lambda state: "hotel_search" in state.get("tool_results", {})
    },
    "search_activities": {
        "agent": "ACTIVITY",
        "description": "Find activities and attractions in {destination}",
        "available_when": lambda state: "activity_search" not in state.get("tool_results", {})
    },
    "review_activities": {
        "agent": "ACTIVITY",
        "description": "Review the {count} activity options we found",
        "available_when": lambda state: "activity_search" in state.get("tool_results", {})
    },
    "modify_itinerary": {
        "agent": "ITINERARY",
        "description": "Modify your {days}-day itinerary",
        "available_when": lambda state: state.get("current_itinerary") is not None
    },
    "create_itinerary": {
        "agent": "ITINERARY",
        "description": "Create a day-by-day itinerary from the options we found",
        "available_when": lambda state: (
            state.get("current_itinerary") is None and
            any(key in state.get("tool_results", {}) for key in ["flight_search", "hotel_search", "activity_search"])
        )
    }
}


def get_available_actions(state: GraphState) -> List[Dict[str, Any]]:
    """
    Get list of available actions based on current state.
    
    Args:
        state: Current graph state
    
    Returns:
        List of available actions with formatted descriptions
    """
    available = []
    tool_results = state.get("tool_results", {})
    
    # Extract context data for description formatting
    prefs = tool_results.get("s1", {})  # Step 1 is usually preference extraction
    destination = prefs.get("destination", "your destination") if isinstance(prefs, dict) else "your destination"
    
    for action_id, action_config in ACTION_REGISTRY.items():
        # Check if action is available
        if action_config["available_when"](state):
            # Format description with actual values
            description = action_config["description"]
            
            # Replace placeholders
            if "{destination}" in description:
                description = description.replace("{destination}", destination)
            
            if "{count}" in description:
                # Get count based on action type
                if "flight" in action_id:
                    count = len(tool_results.get("flight_search", {}).get("flights", []))
                elif "hotel" in action_id:
                    count = len(tool_results.get("hotel_search", {}).get("hotels", []))
                elif "activity" in action_id or "activities" in action_id:
                    count = len(tool_results.get("activity_search", {}).get("activities", []))
                else:
                    count = 0
                description = description.replace("{count}", str(count))
            
            if "{days}" in description:
                itinerary = state.get("current_itinerary", {})
                days = itinerary.get("duration_days", 0) if isinstance(itinerary, dict) else 0
                description = description.replace("{days}", str(days))
            
            available.append({
                "action": action_id,
                "agent": action_config["agent"],
                "description": description
            })
    
    return available


def generate_destination_suggestions(state: GraphState) -> Dict[str, Any]:
    """
    Generate destination selection tokens (D1, D2, D3, etc.) for pre-planner phase.
    
    Args:
        state: Current graph state with destination recommendations
    
    Returns:
        Dict with destination selection suggestions
    """
    logger.info("Generating destination selection suggestions")
    
    try:
        # Get recommendations from tool_results
        tool_results = state.get("tool_results", {})
        recommendations_data = tool_results.get("destination_recommendations", {})
        recommendations = recommendations_data.get("recommendations", [])
        
        if not recommendations:
            # Fallback suggestions
            return {
                "suggestions": [
                    {
                        "token": "A1",
                        "action": "refine_search",
                        "description": "Refine my destination search",
                        "priority": 1
                    }
                ],
                "message": AIMessage(content="What would you like to do next?"),
                "reasoning": "No recommendations available"
            }
        
        # Create D1, D2, D3... tokens for top destinations
        tokenized_suggestions = []
        for i, dest in enumerate(recommendations[:5], 1):
            tokenized_suggestions.append({
                "token": f"D{i}",
                "action": "select_destination",
                "destination": dest.get("destination"),
                "description": f"Choose {dest.get('destination')}, {dest.get('country')}",
                "priority": i,
                "destination_data": dest
            })
        
        # Add "show more" and "refine" options
        tokenized_suggestions.append({
            "token": "D99",
            "action": "refine_search",
            "description": "Show different options or refine my search",
            "priority": 99
        })
        
        # Create user-friendly message
        message_parts = ["\n🌍 Ready to plan your trip! Select a destination:\n"]
        for sug in tokenized_suggestions[:-1]:  # Exclude the refine option from main list
            message_parts.append(f"  [{sug['token']}] {sug['description']}")
        
        message_parts.append(f"\n  [{tokenized_suggestions[-1]['token']}] {tokenized_suggestions[-1]['description']}")
        message_parts.append("\n\nSelect an option or tell me more about what you're looking for!")
        
        ai_message = AIMessage(
            content="".join(message_parts),
            additional_kwargs={
                "suggestions": tokenized_suggestions,
                "preplanner_phase": True
            }
        )
        
        logger.info(f"Generated {len(tokenized_suggestions)} destination selection tokens")
        
        return {
            "suggestions": tokenized_suggestions,
            "message": ai_message,
            "reasoning": "Destination selection phase"
        }
        
    except Exception as e:
        logger.error(f"Error generating destination suggestions: {str(e)}", exc_info=True)
        
        # Return fallback
        return {
            "suggestions": [],
            "message": AIMessage(content="Which destination interests you?"),
            "reasoning": "Error in destination suggestion generation"
        }


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
        # Check if in preplanner phase - if so, generate destination selection tokens
        metadata = state.get("metadata", {})
        if metadata.get("preplanner_phase", False):
            return generate_destination_suggestions(state)
        
        config = get_config()
        llm = ChatOpenAI(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"]
        )
        
        # Build context
        context = _build_follow_up_context(state)
        
        # Get available actions dynamically based on current state
        available_actions = get_available_actions(state)
        
        # If no actions available, return empty suggestions
        if not available_actions:
            return {
                "suggestions": [],
                "message": AIMessage(content="Your itinerary is complete! Feel free to ask me anything else."),
                "reasoning": "No further actions available"
            }
        
        # Build available actions string for prompt
        actions_list = []
        for action in available_actions:
            actions_list.append(f"- {action['action']}: {action['description']}")
        actions_string = "\n".join(actions_list)
        
        # Build prompt (token-efficient, focused)
        follow_up_prompt = f"""Suggest 3-5 next actions from these available options:

{actions_string}

Current State:
{context}

Select the most logical and valuable actions for the user.
Prioritize based on what's missing or what would add most value.

Respond with JSON:
{{
  "suggestions": [
    {{"action": "action_name", "priority": 1}},
    {{"action": "action_name", "priority": 2}}
  ]
}}

Respond with ONLY valid JSON.
"""
        
        # Get suggestions
        response = llm.invoke(follow_up_prompt)
        
        import json
        suggestion_content = response.content.strip()
        
        # Remove markdown code block fences if present
        if suggestion_content.startswith("```json"):
            suggestion_content = suggestion_content[7:]
        if suggestion_content.startswith("```"):
            suggestion_content = suggestion_content[3:]
        if suggestion_content.endswith("```"):
            suggestion_content = suggestion_content[:-3]
        suggestion_content = suggestion_content.strip()
        
        result = json.loads(suggestion_content)
        
        suggested_actions = result.get("suggestions", [])
        
        # Match suggested actions with available actions to get descriptions and agents
        tokenized_suggestions = []
        for i, suggestion in enumerate(suggested_actions):
            action_name = suggestion.get("action")
            
            # Find matching action in available_actions
            matching_action = next((a for a in available_actions if a["action"] == action_name), None)
            
            if matching_action:
                tokenized_suggestions.append({
                    "token": f"A{i + 1}",
                    "action": action_name,
                    "agent": matching_action["agent"],  # Store agent for direct routing
                    "description": matching_action["description"],
                    "priority": suggestion.get("priority", i + 1)
                })
            else:
                logger.warning(f"LLM suggested unknown action: {action_name}")
        
        # Create user-friendly message
        message_parts = ["\n💡 What would you like to do next?\n"]
        for sug in tokenized_suggestions:
            message_parts.append(f"  [{sug['token']}] {sug['description']}")
        
        message_parts.append("\n\nSelect an option or ask me anything!")
        
        ai_message = AIMessage(
            content="".join(message_parts),
            additional_kwargs={
                "suggestions": tokenized_suggestions,
                "reasoning": result.get("reasoning", "")
            }
        )
        
        logger.info(f"Generated {len(tokenized_suggestions)} follow-up suggestions")
        
        return {
            "suggestions": tokenized_suggestions,
            "message": ai_message,
            "reasoning": result.get("reasoning", "")
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
        token: Selected suggestion token (e.g., "A1", "D1")
    
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
    
    # Handle destination selection (D tokens)
    if token.startswith("D") and selected_suggestion["action"] == "select_destination":
        from core.destination_planner import handle_destination_selection
        
        destination_name = selected_suggestion.get("destination", "")
        logger.info(f"User selected destination: {destination_name}")
        
        # Create user message for the selection
        user_message = HumanMessage(
            content=f"I'd like to go to {destination_name}",
            additional_kwargs={"selected_token": token}
        )
        
        # Update state with selection
        updated_state = handle_destination_selection(state, destination_name)
        updated_state["messages"] = state["messages"] + [user_message]
        
        return updated_state
    
    # Handle refine search in preplanner phase
    if token.startswith("D") and selected_suggestion["action"] == "refine_search":
        user_message = HumanMessage(
            content="I'd like to see different destination options",
            additional_kwargs={"selected_token": token}
        )
        
        return GraphState(
            messages=state["messages"] + [user_message],
            plan=state.get("plan"),
            current_itinerary=state.get("current_itinerary"),
            user_preferences=state.get("user_preferences", {}),
            next_agent="",  # Router will decide
            tool_results=state.get("tool_results", {}),
            metadata={
                **state.get("metadata", {}),
                "preplanner_phase": True
            }
        )
    
    # Get agent from the suggestion (stored during generation)
    action_name = selected_suggestion["action"]
    target_agent = selected_suggestion.get("agent")
    
    # If agent not stored, look it up in registry
    if not target_agent and action_name in ACTION_REGISTRY:
        target_agent = ACTION_REGISTRY[action_name]["agent"]
    
    # Fallback to PLANNER if agent not found
    if not target_agent:
        logger.warning(f"No agent found for action: {action_name}, defaulting to PLANNER")
        target_agent = "PLANNER"
    
    logger.info(f"Mapped token {token} → action: {action_name} → agent: {target_agent}")
    
    # Create user message simulating the selection
    user_message = HumanMessage(
        content=f"I'd like to: {selected_suggestion['description']}",
        additional_kwargs={"selected_token": token}
    )
    
    # Update state with direct agent routing (no LLM re-evaluation needed)
    updated_state = GraphState(
        messages=state["messages"] + [user_message],
        plan=state.get("plan"),
        current_itinerary=state.get("current_itinerary"),
        user_preferences=state.get("user_preferences", {}),
        next_agent=target_agent,  # Direct routing to target agent
        tool_results=state.get("tool_results", {}),
        metadata=state.get("metadata", {})
    )
    
    return updated_state


def _build_follow_up_context(state: GraphState) -> str:
    """Build detailed context string for follow-up prompt."""
    context_parts = []
    
    # Plan status
    plan = state.get("plan")
    if plan:
        executed = len([s for s in plan.get("steps", []) if s.get("executed", False)])
        total = len(plan.get("steps", []))
        context_parts.append(f"✓ Plan: {executed}/{total} steps executed")
    
    # Itinerary status with details
    itinerary = state.get("current_itinerary")
    if itinerary:
        days = itinerary.get("days", [])
        duration = itinerary.get("duration_days", len(days))
        context_parts.append(f"✓ Itinerary: {duration}-day plan created with {len(days)} days detailed")
    else:
        context_parts.append("✗ Itinerary: Not created yet")
    
    # Tool results with details
    tool_results = state.get("tool_results", {})
    
    # Flights
    if "flight_search" in tool_results:
        flight_data = tool_results["flight_search"]
        num_flights = len(flight_data.get("flights", []))
        source = flight_data.get("source", "unknown")
        context_parts.append(f"✓ Flights: {num_flights} options found (source: {source})")
    else:
        context_parts.append("✗ Flights: Not searched yet")
    
    # Hotels
    if "hotel_search" in tool_results:
        hotel_data = tool_results["hotel_search"]
        num_hotels = len(hotel_data.get("hotels", []))
        source = hotel_data.get("source", "unknown")
        context_parts.append(f"✓ Hotels: {num_hotels} options found (source: {source})")
    else:
        context_parts.append("✗ Hotels: Not searched yet")
    
    # Activities
    if "activity_search" in tool_results:
        activity_data = tool_results["activity_search"]
        num_activities = len(activity_data.get("activities", []))
        source = activity_data.get("source", "unknown")
        context_parts.append(f"✓ Activities: {num_activities} options found (source: {source})")
    else:
        context_parts.append("✗ Activities: Not searched yet")
    
    # User preferences
    prefs = tool_results.get("s1", {})  # Step 1 is usually preference extraction
    if prefs and isinstance(prefs, dict):
        context_parts.append(f"\nUser Preferences:")
        context_parts.append(f"  Destination: {prefs.get('destination', 'Not set')}")
        context_parts.append(f"  Duration: {prefs.get('duration_days', 'Not set')} days")
        context_parts.append(f"  Budget: {prefs.get('budget', 'Not set')}")
        context_parts.append(f"  Interests: {', '.join(prefs.get('interests', []))}")
    
    return "\n".join(context_parts)