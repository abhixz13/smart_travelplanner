"""
Itinerary Agent: Composes day-by-day itineraries.
Specialized agent for creating structured travel itineraries.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from core.state import GraphState, Itinerary, DayItinerary
from utils.config import get_config

logger = logging.getLogger(__name__)


def itinerary_agent_node(state: GraphState) -> Dict[str, Any]:
    """
    Itinerary agent node for composing day-by-day plans.
    
    Args:
        state: Current graph state
    
    Returns:
        Updated state with composed itinerary
    """
    logger.info("="*60)
    logger.info("ITINERARY AGENT NODE: Composing itinerary")
    logger.info("="*60)
    
    try:
        # Get parameters
        tool_results = state.get("tool_results", {})
        
        # Compose itinerary
        itinerary = execute_itinerary_composition(state, {}, tool_results)
        
        # Format response
        response = format_itinerary_response(itinerary)
        
        return {
            "messages": state["messages"] + [AIMessage(content=response)],
            "current_itinerary": itinerary,
            "tool_results": {
                **tool_results,
                "itinerary": itinerary
            }
        }
        
    except Exception as e:
        logger.error(f"Error in itinerary agent: {str(e)}", exc_info=True)
        return {
            "messages": state["messages"] + [
                AIMessage(content=f"Itinerary composition error: {str(e)}")
            ]
        }


def execute_itinerary_composition(state: GraphState, params: Dict[str, Any],
                                  tool_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compose a complete day-by-day itinerary using LLM reasoning.
    
    Uses available tool results (flights, hotels, activities) to create
    a coherent, optimized itinerary.
    
    Args:
        state: Current graph state
        params: Composition parameters
        tool_results: Results from previous tool calls
    
    Returns:
        Complete itinerary dictionary
    """
    logger.info("Composing itinerary from available data")
    
    try:
        config = get_config()
        llm = ChatOpenAI(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"]
        )
        
        # Extract preferences
        prefs = None
        for result in tool_results.values():
            if isinstance(result, dict) and "destination" in result and "duration_days" in result:
                prefs = result
                break
        
        if not prefs:
            prefs = {"destination": "Tokyo", "duration_days": 7, "interests": ["culture", "food"]}
        
        # Get available activities
        activities = []
        if "activity_search" in tool_results:
            activities = tool_results["activity_search"].get("activities", [])
        
        # Build composition prompt
        composition_prompt = f"""Create a detailed day-by-day itinerary for a trip.

Destination: {prefs.get('destination')}
Duration: {prefs.get('duration_days')} days
Interests: {', '.join(prefs.get('interests', []))}
Budget: {prefs.get('budget', 'mid-range')}

Available activities: {len(activities)} options

For each day, create a realistic schedule with:
- 2-4 activities per day
- Meal suggestions (breakfast, lunch, dinner)
- Transportation notes
- Timing considerations
- Estimated daily cost

Respond with JSON in this format:
{{
  "destination": "...",
  "duration_days": N,
  "days": [
    {{
      "day_number": 1,
      "date": "2025-06-01",
      "location": "...",
      "activities": [
        {{
          "time": "09:00 AM",
          "name": "Activity name",
          "description": "Brief description",
          "duration": "2 hours",
          "cost": 50
        }}
      ],
      "meals": [
        {{"time": "12:30 PM", "type": "lunch", "suggestion": "Local restaurant", "cost": 20}}
      ],
      "transportation": [
        {{"from": "Hotel", "to": "Temple", "method": "Subway", "cost": 3}}
      ],
      "notes": "Day overview",
      "estimated_cost": 150
    }}
  ],
  "total_estimated_cost": 1050,
  "summary": "Brief trip summary"
}}

Use the available activities when possible. Be realistic about timing and costs.
Respond with ONLY valid JSON.
"""
        
        # Get itinerary from LLM
        response = llm.invoke(composition_prompt)
        
        import json
        itinerary_data = json.loads(response.content.strip())
        
        logger.info(f"Composed itinerary for {len(itinerary_data.get('days', []))} days")
        
        return itinerary_data
        
    except Exception as e:
        logger.error(f"Error composing itinerary: {str(e)}")
        # Return fallback itinerary
        return create_fallback_itinerary(prefs if 'prefs' in locals() else {})


def create_fallback_itinerary(prefs: Dict[str, Any]) -> Dict[str, Any]:
    """Create a simple fallback itinerary if LLM composition fails."""
    destination = prefs.get("destination", "Tokyo")
    duration = prefs.get("duration_days", 7)
    
    days = []
    base_date = datetime.now() + timedelta(days=30)
    
    for day_num in range(1, duration + 1):
        current_date = base_date + timedelta(days=day_num - 1)
        
        days.append({
            "day_number": day_num,
            "date": current_date.strftime("%Y-%m-%d"),
            "location": destination,
            "activities": [
                {
                    "time": "09:00 AM",
                    "name": f"Morning Exploration - Day {day_num}",
                    "description": "Explore local attractions",
                    "duration": "3 hours",
                    "cost": 30
                },
                {
                    "time": "02:00 PM",
                    "name": f"Afternoon Activity - Day {day_num}",
                    "description": "Cultural experience",
                    "duration": "2 hours",
                    "cost": 40
                }
            ],
            "meals": [
                {"time": "12:30 PM", "type": "lunch", "suggestion": "Local cuisine", "cost": 20},
                {"time": "07:00 PM", "type": "dinner", "suggestion": "Restaurant", "cost": 35}
            ],
            "transportation": [
                {"from": "Hotel", "to": "Activities", "method": "Public transport", "cost": 10}
            ],
            "notes": f"Day {day_num} in {destination}",
            "estimated_cost": 135
        })
    
    return {
        "destination": destination,
        "duration_days": duration,
        "days": days,
        "total_estimated_cost": 135 * duration,
        "summary": f"A {duration}-day exploration of {destination}"
    }


def format_itinerary_response(itinerary: Dict[str, Any]) -> str:
    """Format itinerary into human-readable response."""
    if not itinerary:
        return "Unable to create itinerary."
    
    response_parts = [
        f"🗺️ {itinerary.get('destination')} Itinerary - {itinerary.get('duration_days')} Days\n",
        f"📊 Estimated Total Cost: ${itinerary.get('total_estimated_cost', 0):.2f}\n",
        f"\n{itinerary.get('summary', '')}\n"
    ]
    
    days = itinerary.get("days", [])
    for day in days[:3]:  # Show first 3 days in detail
        response_parts.append(f"\n{'='*50}")
        response_parts.append(f"\n📅 Day {day['day_number']}: {day.get('date', 'TBD')}")
        response_parts.append(f"\n📍 {day.get('location', '')}")
        
        # Activities
        activities = day.get("activities", [])
        if activities:
            response_parts.append("\n\n🎯 Activities:")
            for activity in activities[:3]:
                response_parts.append(
                    f"\n  {activity.get('time', '')} - {activity.get('name', '')} "
                    f"({activity.get('duration', '')}) - ${activity.get('cost', 0)}"
                )
        
        # Meals
        meals = day.get("meals", [])
        if meals:
            response_parts.append("\n\n🍽️ Meals:")
            for meal in meals:
                response_parts.append(
                    f"\n  {meal.get('time', '')} - {meal.get('type', '').title()}: "
                    f"{meal.get('suggestion', '')} - ${meal.get('cost', 0)}"
                )
        
        response_parts.append(f"\n\n💵 Day {day['day_number']} Total: ${day.get('estimated_cost', 0):.2f}")
    
    if len(days) > 3:
        response_parts.append(f"\n\n...and {len(days) - 3} more days planned!")
    
    response_parts.append("\n\n✨ Your complete itinerary is ready!")
    
    return "".join(response_parts)