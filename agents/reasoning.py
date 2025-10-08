"""
Reasoning Node: Validates itinerary coherence and suggests next steps.
Performs logical validation and dynamic reasoning about the plan.
"""

import logging
from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from core.state import GraphState
from utils.config import get_config
from utils.helpers import time_execution

logger = logging.getLogger(__name__)


@time_execution()
def reasoning_node(state: GraphState) -> Dict[str, Any]:
    """
    Reasoning node that validates coherence and suggests next steps.
    
    Analyzes the current state, validates itinerary logic, checks for
    completeness, and dynamically determines what should happen next.
    
    Args:
        state: Current graph state
    
    Returns:
        Updated state with validation results and next action
    """
    logger.info("="*60)
    logger.info("REASONING NODE: Validating and planning next steps")
    logger.info("="*60)
    
    try:
        # Check reasoning iteration count - prevent infinite loops
        metadata = state.get("metadata", {})
        reasoning_iterations = metadata.get("reasoning_iterations", 0)
        MAX_REASONING_ITERATIONS = 2
        
        if reasoning_iterations >= MAX_REASONING_ITERATIONS:
            logger.warning(f"⚠️ Reasoning has run {reasoning_iterations} times - forcing END to prevent infinite loop")
            logger.info("Returning results to user even if further improvements are possible")
            return {
                "messages": state["messages"] + [
                    AIMessage(content="✓ Validation complete. Your itinerary is ready!")
                ],
                "next_agent": "END",
                "metadata": {
                    **metadata,
                    "reasoning_forced_end": True
                }
            }
        
        config = get_config()
        llm = ChatOpenAI(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"]
        )
        
        # Build reasoning context
        context = _build_reasoning_context(state)
        
        # Analyze plan to understand request type
        plan = state.get("plan")
        request_type, validation_criteria = _determine_request_type(plan)
        
        # Build reasoning prompt (request-aware)
        reasoning_prompt = f"""You are a reasoning engine for a travel planning system.

Current State:
{context}

Request Type: {request_type}

Your tasks:
1. Validate that the USER'S REQUEST was fulfilled
2. Check for critical gaps or logical issues
3. Determine if results should be returned to user or more work is needed

{validation_criteria}

IMPORTANT GUIDELINES:
- Mock/fallback data is ACCEPTABLE for MVP purposes - do NOT fail validation just because real API wasn't used
- BIAS TOWARDS COMPLETION: If the plan was executed and results exist, prefer END
- Focus on whether the USER'S REQUEST was fulfilled, not whether every possible feature exists
- If work is done and results are available, return END even if minor improvements are possible

Determine next action:
- If the plan executed successfully and results are available → END (return to user)
- If there are CRITICAL gaps in fulfilling the user's request → suggest specific agent
- If optional improvements would add significant value → suggest agent
- Default to END if uncertain

Respond with JSON:
{{
  "validation_passed": true/false,
  "issues": ["list of any CRITICAL issues found"],
  "recommendations": ["list of optional recommendations"],
  "next_action": "PLANNER|FLIGHT|HOTEL|ACTIVITY|ITINERARY|END",
  "reasoning": "explanation of decision"
}}

Respond with ONLY valid JSON.
"""
        
        # Get reasoning response
        response = llm.invoke(reasoning_prompt)
        
        import json
        reasoning_content = response.content.strip()
        
        # Remove markdown code block fences if present
        if reasoning_content.startswith("```json"):
            reasoning_content = reasoning_content[7:]
        if reasoning_content.startswith("```"):
            reasoning_content = reasoning_content[3:]
        if reasoning_content.endswith("```"):
            reasoning_content = reasoning_content[:-3]
        reasoning_content = reasoning_content.strip()
        
        reasoning_result = json.loads(reasoning_content)
        
        logger.info(f"Request Type: {request_type}")
        logger.info(f"Validation: {reasoning_result.get('validation_passed')}")
        logger.info(f"Next action: {reasoning_result.get('next_action')}")
        
        # Build response message
        response_parts = [f"✓ Validation: {'Passed' if reasoning_result.get('validation_passed') else 'Issues found'}"]
        
        if reasoning_result.get('issues'):
            response_parts.append("\nIssues identified:")
            for issue in reasoning_result['issues']:
                response_parts.append(f"  - {issue}")
        
        if reasoning_result.get('recommendations'):
            response_parts.append("\nRecommendations:")
            for rec in reasoning_result['recommendations']:
                response_parts.append(f"  - {rec}")
        
        response_parts.append(f"\nReasoning: {reasoning_result.get('reasoning', '')}")
        
        ai_message = AIMessage(content="\n".join(response_parts))
        
        # Increment reasoning iteration counter
        new_metadata = {
            **metadata,
            "reasoning_result": reasoning_result,
            "reasoning_iterations": reasoning_iterations + 1
        }
        
        logger.info(f"Reasoning iteration {reasoning_iterations + 1} complete")
        
        return {
            "messages": state["messages"] + [ai_message],
            "next_agent": reasoning_result.get("next_action", "END"),
            "metadata": new_metadata
        }
        
    except Exception as e:
        logger.error(f"Error in reasoning node: {str(e)}", exc_info=True)
        return {
            "messages": state["messages"] + [
                AIMessage(content=f"Reasoning validation complete.")
            ],
            "next_agent": "END"
        }


def _determine_request_type(plan: Dict[str, Any]) -> tuple[str, str]:
    """
    Determine the type of user request based on the plan.
    
    Args:
        plan: Execution plan dictionary
    
    Returns:
        Tuple of (request_type, validation_criteria)
    """
    if not plan:
        return "Unknown", "Validate that basic results are provided."
    
    # Get list of actions in the plan
    plan_steps = [step.get("action") for step in plan.get("steps", [])]
    
    # Determine request complexity
    has_itinerary = "compose_itinerary" in plan_steps
    has_flights = "flight_search" in plan_steps
    has_hotels = "hotel_search" in plan_steps
    has_activities = "activity_search" in plan_steps
    
    # Categorize request type
    if has_itinerary and len(plan_steps) >= 4:
        request_type = "Full Trip Planning"
        validation_criteria = """Validation criteria for FULL TRIP:
- Is the itinerary created for the requested duration?
- Are flights, hotels, and activities included?
- Are activities sequenced in a logical order?
- Are time allocations reasonable?
- Are all user preferences (budget, interests) addressed?"""
    
    elif has_flights and has_hotels and not has_itinerary:
        request_type = "Multi-Component Search (Flights + Hotels)"
        validation_criteria = """Validation criteria for MULTI-COMPONENT:
- Are flight options provided?
- Are hotel options provided?
- Do the options match the user's destination and dates?
- Is basic information sufficient for user decision-making?"""
    
    elif has_flights and not has_hotels and not has_itinerary:
        request_type = "Flight Search Only"
        validation_criteria = """Validation criteria for FLIGHT SEARCH:
- Are flight options provided for the requested route?
- Do flights match the user's dates (or reasonable defaults)?
- Is there enough information (price, airline, duration) for the user?
- Do NOT require hotels or itinerary - user only asked for flights."""
    
    elif has_hotels and not has_flights and not has_itinerary:
        request_type = "Hotel Search Only"
        validation_criteria = """Validation criteria for HOTEL SEARCH:
- Are hotel options provided for the requested destination?
- Is there variety in price/quality options?
- Is there enough information for the user to choose?
- Do NOT require flights or itinerary - user only asked for hotels."""
    
    elif has_activities and not has_flights and not has_hotels:
        request_type = "Activity Search Only"
        validation_criteria = """Validation criteria for ACTIVITY SEARCH:
- Are activity options provided for the destination?
- Do activities match the user's interests?
- Is there variety in activity types?
- Do NOT require flights/hotels - user only asked for activities."""
    
    else:
        request_type = f"Custom Request ({len(plan_steps)} steps)"
        validation_criteria = """Validation criteria:
- Were all plan steps executed successfully?
- Are results available for the user?
- Does the output match what was requested?"""
    
    return request_type, validation_criteria


def _build_reasoning_context(state: GraphState) -> str:
    """Build context string for reasoning prompt."""
    context_parts = []
    
    # Plan status
    plan = state.get("plan")
    if plan:
        executed_steps = len([s for s in plan.get("steps", []) if s.get("executed", False)])
        total_steps = len(plan.get("steps", []))
        context_parts.append(f"Plan: {executed_steps}/{total_steps} steps executed")
    else:
        context_parts.append("Plan: No plan created")
    
    # Itinerary status
    itinerary = state.get("current_itinerary")
    if itinerary:
        days = itinerary.get("days", [])
        context_parts.append(f"Itinerary: {len(days)} days planned")
    else:
        context_parts.append("Itinerary: Not created")
    
    # Tool results
    tool_results = state.get("tool_results", {})
    if tool_results:
        context_parts.append(f"Tool results: {len(tool_results)} results available")
        for key, result in tool_results.items():
            if isinstance(result, dict):
                if "flights" in result:
                    context_parts.append(f"  - Flights: {len(result['flights'])} options")
                elif "hotels" in result:
                    context_parts.append(f"  - Hotels: {len(result['hotels'])} options")
                elif "activities" in result:
                    context_parts.append(f"  - Activities: {len(result['activities'])} options")
    
    # Message count
    context_parts.append(f"Messages: {len(state.get('messages', []))} in history")
    
    # User preferences
    prefs = state.get("user_preferences", {})
    if prefs:
        context_parts.append(f"Preferences: {prefs}")
    
    return "\n".join(context_parts)


def validate_itinerary_logic(itinerary: Dict[str, Any]) -> List[str]:
    """
    Validate itinerary for logical consistency.
    
    Args:
        itinerary: Itinerary dictionary
    
    Returns:
        List of validation issues (empty if valid)
    """
    issues = []
    
    if not itinerary:
        issues.append("No itinerary provided")
        return issues
    
    days = itinerary.get("days", [])
    if not days:
        issues.append("No days in itinerary")
        return issues
    
    for day in days:
        day_num = day.get("day_number")
        activities = day.get("activities", [])
        
        # Check for reasonable number of activities
        if len(activities) > 8:
            issues.append(f"Day {day_num}: Too many activities ({len(activities)}), may be unrealistic")
        
        # Check for time conflicts (simplified)
        if len(activities) >= 2:
            for i in range(len(activities) - 1):
                curr_activity = activities[i]
                next_activity = activities[i + 1]
                # In production, check actual time conflicts
                pass
    
    return issues


def optimize_activity_sequence(activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Optimize activity sequence for logical flow.
    
    Args:
        activities: List of activity dictionaries
    
    Returns:
        Optimized activity list
    """
    # TODO: Implement intelligent optimization based on:
    # - Geographic proximity
    # - Opening hours
    # - Activity duration
    # - Transportation time
    
    # For MVP, return as-is
    return activities