"""
Activity Agent: Handles activity and attraction recommendations.
Specialized agent for activity-related operations.
Integrates with Amadeus Tours & Activities API for real data.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from langchain_core.messages import AIMessage

from core.state import GraphState
from utils.helpers import time_execution

# Try to import Amadeus client (falls back to mock if unavailable)
try:
    from utils.amadeus_client import get_amadeus_client
    AMADEUS_AVAILABLE = True
    logger_temp = logging.getLogger(__name__)
    logger_temp.info("✅ Amadeus API client available for activities")
except Exception as e:
    AMADEUS_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"⚠️ Amadeus API unavailable, using mock activity data: {e}")

logger = logging.getLogger(__name__)


def convert_country_to_city(destination: str) -> str:
    """
    Convert country names to major city names for API searches.
    
    Args:
        destination: Destination string (could be city or country)
    
    Returns:
        Major city name
    """
    # Country to major city mapping
    country_to_city = {
        "japan": "Tokyo",
        "china": "Beijing",
        "south korea": "Seoul",
        "korea": "Seoul",
        "thailand": "Bangkok",
        "singapore": "Singapore",
        "vietnam": "Hanoi",
        "indonesia": "Jakarta",
        "malaysia": "Kuala Lumpur",
        "philippines": "Manila",
        "india": "Delhi",
        "france": "Paris",
        "italy": "Rome",
        "spain": "Madrid",
        "germany": "Berlin",
        "united kingdom": "London",
        "uk": "London",
        "england": "London",
        "netherlands": "Amsterdam",
        "greece": "Athens",
        "portugal": "Lisbon",
        "switzerland": "Zurich",
        "austria": "Vienna",
        "united states": "New York",
        "usa": "New York",
        "us": "New York",
        "america": "New York",
        "canada": "Toronto",
        "mexico": "Mexico City",
        "brazil": "Sao Paulo",
        "argentina": "Buenos Aires",
        "australia": "Sydney",
        "new zealand": "Auckland",
        "egypt": "Cairo",
        "south africa": "Johannesburg",
        "uae": "Dubai",
        "united arab emirates": "Dubai",
        "turkey": "Istanbul"
    }
    
    destination_lower = destination.lower().strip()
    
    # Check if it's a known country
    if destination_lower in country_to_city:
        city = country_to_city[destination_lower]
        logger.info(f"Converted country '{destination}' to city '{city}'")
        return city
    
    # If not a known country, assume it's already a city
    return destination


@time_execution()
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
    
    Now integrated with Amadeus Tours & Activities API for real data!
    Falls back to mock data if Amadeus API fails.
    
    Args:
        state: Current graph state
        params: Search parameters
    
    Returns:
        Activity search results
    """
    logger.info(f"Executing activity search: {params}")
    
    destination = params.get("destination", "Tokyo")
    interests = params.get("interests", [])
    budget = params.get("budget", "mid-range")
    
    # Convert country names to cities (e.g., "Japan" → "Tokyo")
    destination = convert_country_to_city(destination)
    
    # Try Amadeus API first
    if AMADEUS_AVAILABLE:
        try:
            amadeus = get_amadeus_client(use_production=False)
            
            # Get city coordinates
            # Extract just the city name from the destination string (e.g., "Tokyo, Japan" -> "Tokyo")
            city_name = destination.split(',')[0].strip() if ',' in destination else destination.strip()
            logger.info(f"Searching cities: {city_name}")
            
            cities = amadeus.city_search(keyword=city_name, max_results=1)
            
            if cities and len(cities) > 0:
                city = cities[0]
                latitude = city.get("geoCode", {}).get("latitude")
                longitude = city.get("geoCode", {}).get("longitude")
                
                if latitude and longitude:
                    logger.info(f"🔍 Searching Amadeus activities in {destination} ({latitude}, {longitude})")
                    
                    result = amadeus.tours_and_activities(
                        latitude=latitude,
                        longitude=longitude,
                        radius=10  # 10km radius
                    )
                    
                    if result.get("success") and result.get("activities"):
                        # Format Amadeus activities
                        formatted_activities = []
                        
                        for activity in result["activities"]:
                            formatted = format_amadeus_activity(activity, destination, interests)
                            if formatted:
                                formatted_activities.append(formatted)
                        
                        logger.info(f"✅ Found {len(formatted_activities)} real activities from Amadeus")
                        
                        return {
                            "activities": formatted_activities,
                            "source": "amadeus_api",
                            "search_params": params,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        logger.warning(f"Amadeus returned no activities: {result.get('error')}")
                else:
                    logger.warning(f"No coordinates found for: {destination}")
            else:
                logger.warning(f"City not found: {destination}")
                
        except Exception as e:
            logger.error(f"❌ Amadeus activity search error: {e}, falling back to mock data")
    
    # Fallback to MOCK DATA
    logger.info("Using mock activity data (Amadeus unavailable or failed)")
    mock_activities = generate_mock_activities(
        destination=destination,
        interests=interests,
        budget=budget
    )
    
    return {
        "activities": mock_activities,
        "source": "mock_data",
        "search_params": params,
        "timestamp": datetime.now().isoformat()
    }


def format_amadeus_activity(activity: Dict[str, Any], destination: str, interests: List[str]) -> Dict[str, Any]:
    """
    Format Amadeus activity into simplified structure.
    
    Args:
        activity: Raw activity from Amadeus API
        destination: Destination city
        interests: User interests for categorization
    
    Returns:
        Formatted activity data
    """
    try:
        # Extract basic info
        name = activity.get("name", "Activity")
        description = activity.get("shortDescription", activity.get("description", ""))
        
        # Price information
        price_obj = activity.get("price", {})
        price_amount = float(price_obj.get("amount", 0))
        currency = price_obj.get("currencyCode", "USD")
        
        # Rating and reviews
        rating = float(activity.get("rating", 0)) if activity.get("rating") else 4.5
        
        # Pictures
        pictures = activity.get("pictures", [])
        image_url = pictures[0] if pictures else None
        
        # Category - try to match with user interests
        category = categorize_activity(name, description, interests)
        
        formatted = {
            "activity_id": activity.get("id", f"AMAD_{name[:10]}"),
            "name": name,
            "destination": destination,
            "category": category,
            "duration": extract_duration(activity),
            "price": price_amount,
            "currency": currency,
            "rating": rating,
            "reviews_count": activity.get("bookingLink") and 100 or 50,  # Amadeus doesn't provide this
            "highlights": extract_highlights(description),
            "description": description[:200] if description else "Exciting activity",
            "image_url": image_url,
            "booking_link": activity.get("bookingLink", ""),
            "available_times": ["Morning", "Afternoon", "Evening"],  # Amadeus doesn't provide specific times
            "cancellation_policy": "Check provider for details"
        }
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting Amadeus activity: {e}")
        return None


def categorize_activity(name: str, description: str, interests: List[str]) -> str:
    """Categorize activity based on name, description, and user interests."""
    text = (name + " " + description).lower()
    
    # Check if matches user interests first
    for interest in interests:
        if interest.lower() in text:
            return interest
    
    # Default categories
    if any(word in text for word in ["temple", "shrine", "museum", "historic", "cultural"]):
        return "culture"
    elif any(word in text for word in ["food", "cooking", "culinary", "restaurant", "market"]):
        return "food"
    elif any(word in text for word in ["park", "garden", "nature", "hiking", "outdoor"]):
        return "nature"
    elif any(word in text for word in ["show", "theater", "performance", "entertainment"]):
        return "entertainment"
    else:
        return "sightseeing"


def extract_duration(activity: Dict[str, Any]) -> str:
    """Extract duration from activity data."""
    # Amadeus duration is in ISO format (PT2H30M)
    duration = activity.get("duration", "")
    if duration:
        # Convert PT2H30M to "2.5 hours"
        try:
            import re
            hours = re.search(r'(\d+)H', duration)
            minutes = re.search(r'(\d+)M', duration)
            
            h = int(hours.group(1)) if hours else 0
            m = int(minutes.group(1)) if minutes else 0
            
            total_hours = h + (m / 60)
            
            if total_hours >= 1:
                return f"{total_hours:.1f} hours"
            else:
                return f"{m} minutes"
        except:
            return "2-3 hours"
    
    return "2-3 hours"


def extract_highlights(description: str) -> List[str]:
    """Extract highlights from description."""
    if not description:
        return ["Unique experience", "Expert guides"]
    
    # Simple extraction - take first 2 sentences
    sentences = description.split(". ")[:2]
    highlights = [s.strip() for s in sentences if s.strip()]
    
    if not highlights:
        return ["Unique experience", "Expert guides"]
    
    return highlights[:3]


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
    
    destination = combined_prefs.get("destination", "Tokyo")
    
    # Convert country names to major city names
    destination = convert_country_to_city(destination)
    
    return {
        "destination": destination,
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