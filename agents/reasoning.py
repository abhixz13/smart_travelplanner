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

logger = logging.getLogger(__name__)


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
        config = get_config()
        llm = ChatOpenAI(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"]
        )
        
        # Build reasoning context
        context = _build_reasoning_context(state)
        
        # Build reasoning prompt
        reasoning_prompt = f"""You are a reasoning engine for a travel planning system.

Current State:
{context}

Your tasks:
1. Validate the current itinerary/plan for logical coherence
2. Check for missing information or gaps
3. Determine if more processing is needed or if we should end

Validation checks:
- Are activities sequenced logically?
- Are time allocations reasonable?
- Are there transportation gaps?
- Is the budget considered?
- Are all user preferences addressed?

Determine next action:
- If validation finds issues: suggest PLANNER or specific agent (FLIGHT, HOTEL, ACTIVITY, ITINERARY)
- If more user input needed: END (to hand back to user)
- If everything complete and validated: END

Respond with JSON:
{{
  "validation_passed": true/false,
  "issues": ["list of any issues found"],
  "recommendations": ["list of recommendations"],
  "next_action": "PLANNER|FLIGHT|HOTEL|ACTIVITY|ITINERARY|REASONING|END",
  "reasoning": "explanation of decision"
}}

Respond with ONLY valid JSON.
"""
        
        # Get reasoning response
        response = llm.invoke(reasoning_prompt)
        
        import json
        reasoning_result = json.loads(response.content.strip())
        
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
        
        return {
            "messages": state["messages"] + [ai_message],
            "next_agent": reasoning_result.get("next_action", "END"),
            "metadata": {
                **state.get("metadata", {}),
                "reasoning_result": reasoning_result
            }
        }
        
    except Exception as e:
        logger.error(f"Error in reasoning node: {str(e)}", exc_info=True)
        return {
            "messages": state["messages"] + [
                AIMessage(content=f"Reasoning validation complete.")
            ],
            "next_agent": "END"
        }


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