"""
Semantic Router: Uses LLM for intelligent travel intent detection.
Replaces keyword matching with semantic understanding.
"""

import logging
import json
from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from core.state import GraphState
from utils.config import get_config
from utils.helpers import time_execution

logger = logging.getLogger(__name__)


def detect_travel_intent(message: str) -> Dict[str, Any]:
    """
    Use LLM to semantically analyze if this is a travel planning request.
    
    Args:
        message: User message to analyze
        
    Returns:
        Dictionary with intent analysis including type, confidence, and components needed
    """
    config = get_config()
    llm = ChatOpenAI(
        model=config["llm"]["model"],
        temperature=0.1  # Low temperature for consistent classification
    )
    
    prompt = f"""Analyze this user message and determine if it's a travel planning request:

Message: "{message}"

Respond with JSON:
{{
  "is_travel_request": true/false,
  "request_type": "flight_only|hotel_only|activity_only|complete_trip|destination_discovery|other",
  "confidence": 0.0-1.0,
  "components_needed": ["flights", "hotels", "activities", "itinerary"],
  "reasoning": "brief explanation of classification"
}}

Consider these as travel requests:
- Direct requests: "book flight", "find hotel", "plan trip"
- Indirect requests: "I need to go to Tokyo", "looking for vacation options"  
- Implied requests: "gateway outing is missing", "weekend getaway ideas"
- Partial requests: "what about accommodation?", "any activities there?"

Be liberal in interpretation - if it could be travel-related, classify as travel request.

Respond with ONLY valid JSON.
"""
    
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # Remove markdown code block fences if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        intent_analysis = json.loads(content.strip())
        logger.info(f"Semantic intent analysis: {intent_analysis}")
        return intent_analysis
        
    except Exception as e:
        logger.error(f"Error in semantic intent detection: {e}")
        # Fallback to basic detection
        return {
            "is_travel_request": any(kw in message.lower() for kw in [
                "flight", "hotel", "trip", "vacation", "travel", "book", "find", 
                "plan", "itinerary", "visit", "go to", "destination", "outing"
            ]),
            "request_type": "other",
            "confidence": 0.5,
            "components_needed": [],
            "reasoning": "fallback detection due to LLM error"
        }


def handle_ambiguous_request(message: str, intent_analysis: Dict) -> str:
    """
    Handle semantically ambiguous requests with special interpretation.
    """
    message_lower = message.lower()
    
    if "gateway outing" in message_lower or "outing" in message_lower:
        # Interpret as activity/experience planning request
        intent_analysis.update({
            "request_type": "activity_only",
            "components_needed": ["activities"],
            "reasoning": "Interpreted 'outing' as activity/experience request"
        })
        return "I'll find the best outing options and create a complete activity plan."
    
    if "weekend" in message_lower or "getaway" in message_lower:
        # Interpret as short trip planning
        intent_analysis.update({
            "request_type": "complete_trip", 
            "components_needed": ["flights", "hotels", "activities", "itinerary"],
            "reasoning": "Interpreted weekend/getaway as complete short trip planning"
        })
        return "I'll plan a perfect weekend getaway with accommodation and activities."
    
    return f"I'll handle this {intent_analysis['request_type']} request completely."


@time_execution()
def semantic_router_node(state: GraphState) -> Dict[str, Any]:
    """
    Semantic router that uses LLM to detect travel intent and route to autonomous planner.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with routing decision
    """
    logger.info("="*60)
    logger.info("SEMANTIC ROUTER: Analyzing intent with LLM")
    logger.info("="*60)
    
    try:
        # Get last message
        last_message = state["messages"][-1] if state["messages"] else None
        
        if not last_message:
            logger.warning("No messages in state, defaulting to END")
            return {"next_agent": "END"}
        
        # Use LLM for semantic intent detection
        intent_analysis = detect_travel_intent(last_message.content)
        
        # Handle ambiguous requests with special interpretation
        response_message = handle_ambiguous_request(last_message.content, intent_analysis)
        
        if intent_analysis["is_travel_request"]:
            # Route ALL travel requests to autonomous planner
            logger.info(f"Travel request detected: {intent_analysis['request_type']}")
            
            return {
                "next_agent": "AUTONOMOUS_PLANNER",
                "messages": state["messages"] + [
                    AIMessage(content=response_message)
                ],
                "metadata": {
                    **state.get("metadata", {}),
                    "intent_analysis": intent_analysis
                }
            }
        
        # Non-travel requests end conversation
        logger.info("No travel intent detected, ending conversation")
        return {
            "next_agent": "END",
            "messages": state["messages"] + [
                AIMessage(content="I'm here to help with travel planning. Let me know if you need travel assistance!")
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in semantic router: {e}", exc_info=True)
        return {
            "next_agent": "END",
            "messages": state["messages"] + [
                AIMessage(content=f"Routing error: {str(e)}")
            ]
        }
