"""
Activity Agent: Handles activity and attraction recommendations.
Specialized agent for activity-related operations.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from langchain_core.messages import AIMessage

from core.state import GraphState

logger = logging.getLogger(__name__)


def activity_agent_node(state: GraphState) -> Dict[str, Any]:
    """
    Activity agent node for handling activity queries.
    
    Args:
        state: Current graph state
    
    Returns:
        Updated state with activity search results
    """
    logger.info("="*60)
    logger.info("ACTIVITY AGENT NODE: Processing activity request")
    logger.info("="*60)
    
    try:
        params = extract_activity_params(state)
        activity_results = execute_activity_search(state, params)
        response = format_activity_response(activity_results)
        
        return {
            "messages": state["messages"] + [AIMessage(content=response)],
            "tool_results": {
                **state.get("tool_results", {}),
                "activity_search": activity_results
            }
        }
        
    except Exception as e:
        logger.error(f"Error in activity agent: {str(e)}", exc_info=True)
        return {
            "messages": state["messages"] + [
                AIMessage(content=f"Activity search error: {str(e)}")
            ]
        }


def execute_activity_search(state: GraphState, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute activity search with given parameters.
    
    NOTE: MOCK DATA for MVP. Production integration:
    - Viator API
    - GetYourGuide API
    - TripAdvisor API
    - Google Places API
    - Store in Supabase
    
    Args:
        state: Current graph state
        params: Search parameters
    
    Returns:
        Activity search results
    """
    logger.info(f"Executing activity search: {params}")
    
    mock_activities = generate_mock_activities(
        destination=params.get("destination", "Tokyo"),
        interests=params.get("interests", []),
        budget=params.get("budget", "mid-range")
    )
    
    logger.info(f"Found {len(mock_activities)} activity options (MOCK DATA)")
    
    return {
        "activities": mock_activities,
        "search_params": params,
        "timestamp": datetime.now().isoformat()
    }


def extract_activity_params(state: GraphState) -> Dict[str, Any]:
    """Extract activity search parameters from state."""
    tool_results = state.get("tool_results", {})
    extracted_prefs = None
    
    for result in tool_results.values():
        if isinstance(result, dict) and "destination" in result:
            extracted_prefs = result
            break
    
    prefs = state.get("user_preferences", {})
    combined_prefs = extracted_prefs or prefs
    
    return {
        "destination": combined_prefs.get("destination", "Tokyo"),
        "interests": combined_prefs.get("interests", ["culture", "food"]),
        "budget": combined_prefs.get("budget", "mid-range"),
        "duration_days": combined_prefs.get("duration_days", 7)
    }


def generate_mock_activities(destination: str, interests: List[str], 
                             budget: str) -> List[Dict[str, Any]]:
    """Generate mock activity data for MVP."""
    
    activity_database = {
        "culture": [
            {"name": "Historic Temple Tour", "duration": "3 hours", "price": 45},
            {"name": "Traditional Tea Ceremony", "duration": "2 hours", "price": 65},
            {"name": "Museum of History", "duration": "2.5 hours", "price": 20}
        ],
        "food": [
            {"name": "Street Food Walking Tour", "duration": "3 hours", "price": 75},
            {"name": "Sushi Making Class", "duration": "2 hours", "price": 85},
            {"name": "Local Market Experience", "duration": "2 hours", "price": 40}
        ],
        "nature": [
            {"name": "Garden & Park Walking Tour", "duration": "3 hours", "price": 35},
            {"name": "Mountain Hiking Experience", "duration": "6 hours", "price": 90},
            {"name": "Botanical Garden Visit", "duration": "2 hours", "price": 15}
        ],
        "entertainment": [
            {"name": "Traditional Theater Show", "duration": "2 hours", "price": 60},
            {"name": "Modern Art Gallery", "duration": "2 hours", "price": 25},
            {"name": "Night Entertainment District Tour", "duration": "3 hours", "price": 70}
        ]
    }
    
    mock_activities = []
    activity_id = 3000
    
    # Select activities based on interests
    selected_interests = interests if interests else ["culture", "food"]
    
    for interest in selected_interests:
        interest_activities = activity_database.get(interest.lower(), [])
        for activity in interest_activities[:2]:  # Get 2 per interest
            mock_activities.append({
                "activity_id": f"AC{activity_id}",
                "name": activity["name"],
                "destination": destination,
                "category": interest,
                "duration": activity["duration"],
                "price": activity["price"],
                "rating": 4.3 + (activity_id % 5) * 0.1,
                "reviews_count": 150 + (activity_id % 10) * 50,
                "highlights": [
                    "Expert local guide",
                    "Small group experience",
                    "All materials included"
                ],
                "available_times": ["9:00 AM", "2:00 PM", "6:00 PM"],
                "cancellation_policy": "Free cancellation up to 24h before"
            })
            activity_id += 1
    
    # Add some general activities
    general_activities = [
        {
            "activity_id": f"AC{activity_id}",
            "name": f"{destination} City Walking Tour",
            "destination": destination,
            "category": "sightseeing",
            "duration": "4 hours",
            "price": 50,
            "rating": 4.7,
            "reviews_count": 823,
            "highlights": ["Major landmarks", "Photo opportunities", "Local insights"],
            "available_times": ["9:00 AM", "2:00 PM"],
            "cancellation_policy": "Free cancellation up to 24h before"
        }
    ]
    
    mock_activities.extend(general_activities)
    
    return mock_activities


def format_activity_response(results: Dict[str, Any]) -> str:
    """Format activity results into human-readable response."""
    activities = results.get("activities", [])
    
    if not activities:
        return "No activities found for your interests."
    
    response_parts = [
        f"Found {len(activities)} activity options:\n"
    ]
    
    for i, activity in enumerate(activities[:5], 1):  # Show top 5
        response_parts.append(
            f"\n{i}. {activity['name']} - ${activity['price']:.2f}\n"
            f"   Category: {activity['category'].title()}\n"
            f"   Duration: {activity['duration']}\n"
            f"   Rating: {activity['rating']}⭐ ({activity['reviews_count']} reviews)\n"
            f"   Highlights: {', '.join(activity['highlights'][:2])}\n"
        )
    
    if len(activities) > 5:
        response_parts.append(f"\n...and {len(activities) - 5} more activities available.")
    
    return "".join(response_parts)