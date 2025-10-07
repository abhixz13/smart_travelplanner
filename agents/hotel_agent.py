"""
Hotel Agent: Handles accommodation search and booking inquiries.
Specialized agent for hotel-related operations.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from langchain_core.messages import AIMessage

from core.state import GraphState

logger = logging.getLogger(__name__)


def hotel_agent_node(state: GraphState) -> Dict[str, Any]:
    """
    Hotel agent node for handling accommodation queries.
    
    Args:
        state: Current graph state
    
    Returns:
        Updated state with hotel search results
    """
    logger.info("="*60)
    logger.info("HOTEL AGENT NODE: Processing hotel request")
    logger.info("="*60)
    
    try:
        params = extract_hotel_params(state)
        hotel_results = execute_hotel_search(state, params)
        response = format_hotel_response(hotel_results)
        
        return {
            "messages": state["messages"] + [AIMessage(content=response)],
            "tool_results": {
                **state.get("tool_results", {}),
                "hotel_search": hotel_results
            }
        }
        
    except Exception as e:
        logger.error(f"Error in hotel agent: {str(e)}", exc_info=True)
        return {
            "messages": state["messages"] + [
                AIMessage(content=f"Hotel search error: {str(e)}")
            ]
        }


def execute_hotel_search(state: GraphState, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute hotel search with given parameters.
    
    NOTE: MOCK DATA for MVP. Production integration:
    - Booking.com API
    - Expedia API
    - Hotels.com API
    - Store in Supabase Postgres
    
    Args:
        state: Current graph state
        params: Search parameters
    
    Returns:
        Hotel search results
    """
    logger.info(f"Executing hotel search: {params}")
    
    mock_hotels = generate_mock_hotels(
        destination=params.get("destination", "Tokyo"),
        check_in=params.get("check_in"),
        check_out=params.get("check_out"),
        guests=params.get("guests", 1),
        budget=params.get("budget", "mid-range")
    )
    
    logger.info(f"Found {len(mock_hotels)} hotel options (MOCK DATA)")
    
    return {
        "hotels": mock_hotels,
        "search_params": params,
        "timestamp": datetime.now().isoformat()
    }


def extract_hotel_params(state: GraphState) -> Dict[str, Any]:
    """Extract hotel search parameters from state."""
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
        "check_in": combined_prefs.get("start_date"),
        "check_out": combined_prefs.get("end_date"),
        "guests": combined_prefs.get("travelers", 1),
        "budget": combined_prefs.get("budget", "mid-range"),
        "accommodation_type": combined_prefs.get("accommodation_type", "hotel")
    }


def generate_mock_hotels(destination: str, check_in: str, check_out: str,
                        guests: int, budget: str) -> List[Dict[str, Any]]:
    """Generate mock hotel data for MVP."""
    
    budget_ranges = {
        "budget": (50, 100),
        "mid-range": (100, 250),
        "luxury": (250, 800)
    }
    
    price_range = budget_ranges.get(budget, (100, 250))
    
    hotel_templates = [
        {"name": "Tokyo Grand Hotel", "rating": 4.5, "type": "Hotel"},
        {"name": "Sakura Boutique Inn", "rating": 4.2, "type": "Boutique"},
        {"name": "Imperial Palace Hotel", "rating": 4.8, "type": "Luxury"},
        {"name": "Central Business Hotel", "rating": 4.0, "type": "Business"}
    ]
    
    mock_hotels = []
    for i, template in enumerate(hotel_templates):
        price_per_night = price_range[0] + (i * (price_range[1] - price_range[0]) // len(hotel_templates))
        
        mock_hotels.append({
            "hotel_id": f"HT{2000 + i}",
            "name": template["name"],
            "destination": destination,
            "rating": template["rating"],
            "type": template["type"],
            "price_per_night": price_per_night,
            "total_price": price_per_night * 7,  # Assuming 7 nights
            "amenities": ["WiFi", "Breakfast", "Gym", "Pool"] if i > 1 else ["WiFi", "Breakfast"],
            "location": f"{destination} City Center",
            "distance_to_center": f"{0.5 + (i * 0.3):.1f} km",
            "cancellation": "Free cancellation" if i < 2 else "Non-refundable",
            "reviews_count": 500 + (i * 200),
            "description": f"A wonderful {template['type'].lower()} in the heart of {destination}"
        })
    
    return mock_hotels


def format_hotel_response(results: Dict[str, Any]) -> str:
    """Format hotel results into human-readable response."""
    hotels = results.get("hotels", [])
    
    if not hotels:
        return "No hotels found for your search criteria."
    
    response_parts = [
        f"Found {len(hotels)} accommodation options:\n"
    ]
    
    for i, hotel in enumerate(hotels[:3], 1):
        response_parts.append(
            f"\n{i}. {hotel['name']} - ${hotel['price_per_night']:.2f}/night\n"
            f"   Rating: {hotel['rating']}⭐ ({hotel['reviews_count']} reviews)\n"
            f"   Location: {hotel['location']} ({hotel['distance_to_center']} from center)\n"
            f"   Amenities: {', '.join(hotel['amenities'][:3])}\n"
            f"   Total (7 nights): ${hotel['total_price']:.2f}\n"
        )
    
    if len(hotels) > 3:
        response_parts.append(f"\n...and {len(hotels) - 3} more options available.")
    
    return "".join(response_parts)