"""
Router Node: Determines which specialized agent to invoke next.
Uses LLM to analyze intent and route appropriately.
"""

import logging
from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from core.state import GraphState
from utils.config import get_config

logger = logging.getLogger(__name__)


def router_node(state: GraphState) -> Dict[str, Any]:
    """
    Router node that determines which agent to invoke next.
    
    Analyzes the conversation history and current state to decide
    the next appropriate agent or action.
    
    Args:
        state: Current graph state
    
    Returns:
        Updated state with next_agent decision
    """
    logger.info("="*60)
    logger.info("ROUTER NODE: Analyzing intent and routing")
    logger.info("="*60)
    
    try:
        config = get_config()
        llm = ChatOpenAI(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"]
        )
        
        # Get last message
        last_message = state["messages"][-1] if state["messages"] else None
        
        if not last_message:
            logger.warning("No messages in state, defaulting to END")
            return {"next_agent": "END"}
        
        # Check if destination planner phase is active or needed
        metadata = state.get("metadata", {})
        user_prefs = state.get("user_preferences", {})
        destination = user_prefs.get("destination")
        
        # Detect if user needs destination help
        message_content = last_message.content.lower()
        needs_destination_help = (
            not destination and 
            any(phrase in message_content for phrase in [
                "don't know where", "help me choose", "suggest destination",
                "where should i go", "recommend a place", "help me decide",
                "not sure where", "uncertain about destination"
            ])
        ) or metadata.get("preplanner_phase", False)
        
        # If destination selected from preplanner, route to PLANNER
        if metadata.get("destination_selected", False):
            logger.info("Destination selected from destination_planner, routing to PLANNER")
            return {
                "next_agent": "PLANNER",
                "messages": state["messages"]
            }
        
        # If needs destination help, route to DESTINATION_PLANNER
        if needs_destination_help:
            logger.info("User needs destination help, routing to DESTINATION_PLANNER")
            return {
                "next_agent": "DESTINATION_PLANNER",
                "messages": state["messages"] + [
                    AIMessage(content="Let me help you find the perfect destination...")
                ]
            }
        
        # Build routing prompt
        routing_prompt = f"""You are a router for a travel itinerary planning system.

Analyze the user's message and determine which specialized agent should handle it.

Available agents:
- DESTINATION_PLANNER: When user is uncertain about destination or asks for destination suggestions
- PLANNER: For comprehensive trip planning, creating itineraries, orchestrating multiple components
- FLIGHT: For flight searches, airline information, booking inquiries
- HOTEL: For accommodation searches, hotel information, booking inquiries
- ACTIVITY: For activity suggestions, attraction information, tour bookings
- ITINERARY: For creating or modifying day-by-day itineraries
- REASONING: For validating plans, optimizing schedules, checking coherence
- END: If the conversation is complete or no action needed

User message: {last_message.content}

Current state:
- Has destination: {destination is not None}
- Has plan: {state.get('plan') is not None}
- Has itinerary: {state.get('current_itinerary') is not None}
- Message count: {len(state['messages'])}

Respond with ONLY the agent name (DESTINATION_PLANNER, PLANNER, FLIGHT, HOTEL, ACTIVITY, ITINERARY, REASONING, or END).

Decision rules:
- If user is uncertain about destination or provides constraints without specific destination -> DESTINATION_PLANNER
- If user asks "where should I go" or "help me choose destination" -> DESTINATION_PLANNER
- If user describes requirements (weather, family, budget) without mentioning destination -> DESTINATION_PLANNER
- For initial trip planning requests with known destination -> PLANNER
- For specific component requests after a plan exists -> use specialized agent
- For validation or optimization -> REASONING
"""
        
        # Get routing decision
        response = llm.invoke(routing_prompt)
        decision = response.content.strip().upper()
        
        # Validate decision
        valid_agents = {"DESTINATION_PLANNER", "PLANNER", "FLIGHT", "HOTEL", "ACTIVITY", "ITINERARY", "REASONING", "END"}
        if decision not in valid_agents:
            logger.warning(f"Invalid routing decision: {decision}, defaulting to PLANNER")
            decision = "PLANNER"
        
        logger.info(f"Router decision: {decision}")
        
        # Add routing message
        routing_msg = AIMessage(
            content=f"Routing to {decision} agent...",
            additional_kwargs={"route_decision": decision}
        )
        
        return {
            "messages": state["messages"] + [routing_msg],
            "next_agent": decision
        }
        
    except Exception as e:
        logger.error(f"Error in router node: {str(e)}", exc_info=True)
        return {
            "next_agent": "END",
            "messages": state["messages"] + [
                AIMessage(content=f"Router error: {str(e)}")
            ]
        }


def extract_intent_keywords(message: str) -> Dict[str, Any]:
    """
    Extract intent keywords from message for routing hints.
    
    Args:
        message: User message
    
    Returns:
        Dictionary of intent signals
    """
    message_lower = message.lower()
    
    return {
        "flight_keywords": any(kw in message_lower for kw in ["flight", "fly", "airline", "airport"]),
        "hotel_keywords": any(kw in message_lower for kw in ["hotel", "accommodation", "stay", "lodging"]),
        "activity_keywords": any(kw in message_lower for kw in ["activity", "attraction", "tour", "visit", "see"]),
        "planning_keywords": any(kw in message_lower for kw in ["plan", "itinerary", "trip", "vacation", "travel"]),
        "modify_keywords": any(kw in message_lower for kw in ["change", "modify", "update", "different"]),
    }