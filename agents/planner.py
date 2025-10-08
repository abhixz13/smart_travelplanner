"""
Planner Node: Orchestrates planning workflow and generates execution plans.
Central decision-maker that creates structured JSON plans.
"""

import logging
import json
from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from core.state import GraphState, ExecutionPlan, PlanStep, UserPreferences
from utils.config import get_config

logger = logging.getLogger(__name__)


def planner_node(state: GraphState) -> Dict[str, Any]:
    """
    Planner node that orchestrates the planning workflow.
    
    Generates a structured execution plan as JSON with specific steps
    that will be executed by the planner_execution_node.
    
    Args:
        state: Current graph state
    
    Returns:
        Updated state with execution plan
    """
    logger.info("="*60)
    logger.info("PLANNER NODE: Generating execution plan")
    logger.info("="*60)
    
    try:
        config = get_config()
        llm = ChatOpenAI(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"]
        )
        
        # Extract user query
        user_query = state["messages"][0].content if state["messages"] else ""
        
        # Build planning prompt
        planning_prompt = f"""You are an expert travel planner creating a structured execution plan.

User Query: {user_query}

Your task is to generate a JSON execution plan with specific steps.

Available actions:
- flight_search: Search for flights
- hotel_search: Search for hotels
- activity_search: Search for activities
- compose_itinerary: Create day-by-day itinerary
- extract_preferences: Parse user preferences from query

IMPORTANT: Create a deterministic, sequential plan. Each step should have:
- id: unique identifier (e.g., "s1", "s2")
- action: one of the available actions above
- params: dictionary of parameters for the action

Example output format:
{{
  "steps": [
    {{"id": "s1", "action": "extract_preferences", "params": {{}}}},
    {{"id": "s2", "action": "flight_search", "params": {{"origin": "auto", "destination": "auto"}}}},
    {{"id": "s3", "action": "hotel_search", "params": {{"destination": "auto"}}}},
    {{"id": "s4", "action": "activity_search", "params": {{"destination": "auto", "interests": "auto"}}}},
    {{"id": "s5", "action": "compose_itinerary", "params": {{"days": "auto"}}}}
  ],
  "metadata": {{
    "planning_notes": "Brief explanation of the plan"
  }}
}}

Respond with ONLY valid JSON, no other text.
"""
        
        # Get plan from LLM
        response = llm.invoke(planning_prompt)
        plan_content = response.content.strip()
        
        # Remove markdown code block fences if present
        if plan_content.startswith("```json"):
            plan_content = plan_content[7:]  # Remove ```json
        if plan_content.startswith("```"):
            plan_content = plan_content[3:]  # Remove ```
        if plan_content.endswith("```"):
            plan_content = plan_content[:-3]  # Remove trailing ```
        plan_content = plan_content.strip()
        
        plan_json = json.loads(plan_content)
        
        logger.info(f"Generated plan with {len(plan_json.get('steps', []))} steps")
        
        # Create ExecutionPlan object
        plan = ExecutionPlan.from_dict(plan_json)
        
        # Create response message
        plan_summary = f"Created execution plan with {len(plan.steps)} steps:\n"
        for step in plan.steps:
            plan_summary += f"  - {step.id}: {step.action}\n"
        
        ai_message = AIMessage(content=plan_summary)
        
        return {
            "messages": state["messages"] + [ai_message],
            "plan": plan.to_dict(),
            "metadata": {
                **state.get("metadata", {}),
                "plan_created": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error in planner node: {str(e)}", exc_info=True)
        
        # Create fallback plan
        fallback_plan = ExecutionPlan(
            steps=[
                PlanStep(id="s1", action="extract_preferences", params={}),
                PlanStep(id="s2", action="compose_itinerary", params={})
            ],
            metadata={"fallback": True, "error": str(e)}
        )
        
        return {
            "messages": state["messages"] + [
                AIMessage(content=f"Created fallback plan due to error: {str(e)}")
            ],
            "plan": fallback_plan.to_dict()
        }


def extract_user_preferences(query: str, llm: ChatOpenAI) -> UserPreferences:
    """
    Extract structured preferences from user query using LLM.
    
    Args:
        query: User query string
        llm: Language model instance
    
    Returns:
        UserPreferences object
    """
    extraction_prompt = f"""Extract travel preferences from this query:

"{query}"

Provide a JSON object with these fields (use null if not mentioned):
- destination: string
- duration_days: integer
- budget: "budget" | "mid-range" | "luxury" | null
- interests: list of strings
- start_date: string (YYYY-MM-DD) or null
- end_date: string (YYYY-MM-DD) or null
- travelers: integer (default 1)
- accommodation_type: string or null
- dietary_restrictions: list of strings
- mobility_constraints: string or null

Respond with ONLY valid JSON.
"""
    
    try:
        response = llm.invoke(extraction_prompt)
        prefs_content = response.content.strip()
        
        # Remove markdown code block fences if present
        if prefs_content.startswith("```json"):
            prefs_content = prefs_content[7:]  # Remove ```json
        if prefs_content.startswith("```"):
            prefs_content = prefs_content[3:]  # Remove ```
        if prefs_content.endswith("```"):
            prefs_content = prefs_content[:-3]  # Remove trailing ```
        prefs_content = prefs_content.strip()
        
        prefs_dict = json.loads(prefs_content)
        
        return UserPreferences(
            destination=prefs_dict.get("destination"),
            duration_days=prefs_dict.get("duration_days"),
            budget=prefs_dict.get("budget"),
            interests=prefs_dict.get("interests", []),
            start_date=prefs_dict.get("start_date"),
            end_date=prefs_dict.get("end_date"),
            travelers=prefs_dict.get("travelers", 1),
            accommodation_type=prefs_dict.get("accommodation_type"),
            dietary_restrictions=prefs_dict.get("dietary_restrictions", []),
            mobility_constraints=prefs_dict.get("mobility_constraints")
        )
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from LLM for preferences: {e}. Content: {prefs_content if 'prefs_content' in locals() else 'N/A'}")
        return UserPreferences()
    except Exception as e:
        logger.error(f"Error extracting preferences: {str(e)}")
        return UserPreferences()