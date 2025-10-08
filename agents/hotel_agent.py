"""
Hotel Agent: Handles accommodation search and booking inquiries.
Specialized agent for hotel-related operations.
Integrates with Amadeus API for real hotel data.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from langchain_core.messages import AIMessage

from core.state import GraphState

# Try to import Amadeus client (falls back to mock if unavailable)
try:
    from utils.amadeus_client import get_amadeus_client
    AMADEUS_AVAILABLE = True
    logger_temp = logging.getLogger(__name__)
    logger_temp.info("✅ Amadeus API client available for hotels")
except Exception as e:
    AMADEUS_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"⚠️ Amadeus API unavailable, using mock hotel data: {e}")

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
    
    Now integrated with Amadeus API for real hotel data!
    Falls back to mock data if Amadeus API fails.
    
    Args:
        state: Current graph state
        params: Search parameters
    
    Returns:
        Hotel search results
    """
    logger.info(f"Executing hotel search: {params}")
    
    destination = params.get("destination", "Tokyo")
    check_in = params.get("check_in")
    check_out = params.get("check_out")
    guests = params.get("guests", 1)
    budget = params.get("budget", "mid-range")
    
    # Import convert_country_to_city from flight_agent
    from agents.flight_agent import convert_country_to_city
    destination = convert_country_to_city(destination)
    
    # Try Amadeus API first
    if AMADEUS_AVAILABLE and check_in and check_out:
        try:
            amadeus = get_amadeus_client(use_production=False)
            
            # Try to get city code from destination
            # First, search for the city to get IATA code
            cities = amadeus.city_search(destination, max_results=1)
            
            if cities and len(cities) > 0:
                city_code = cities[0].get("iataCode")
                
                if city_code:
                    logger.info(f"🔍 Searching Amadeus hotels in: {city_code} ({destination})")
                    
                    result = amadeus.hotel_search_by_city(
                        city_code=city_code,
                        check_in_date=check_in,
                        check_out_date=check_out,
                        adults=guests,
                        room_quantity=1,
                        max_results=10
                    )
                    
                    if result.get("success") and result.get("hotels"):
                        # Format Amadeus hotel offers
                        formatted_hotels = []
                        
                        for hotel_offer in result["hotels"]:
                            formatted = format_amadeus_hotel(hotel_offer)
                            if formatted:
                                formatted_hotels.append(formatted)
                        
                        logger.info(f"✅ Found {len(formatted_hotels)} real hotels from Amadeus")
                        
                        return {
                            "hotels": formatted_hotels,
                            "source": "amadeus_api",
                            "search_params": params,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        logger.warning(f"Amadeus returned no hotel results: {result.get('error')}")
                else:
                    logger.warning(f"No city code found for: {destination}")
            else:
                logger.warning(f"City not found: {destination}")
                
        except Exception as e:
            logger.error(f"❌ Amadeus hotel search error: {e}, falling back to mock data")
    
    # Fallback to MOCK DATA
    logger.info("Using mock hotel data (Amadeus unavailable or failed)")
    mock_hotels = generate_mock_hotels(
        destination=destination,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        budget=budget
    )
    
    return {
        "hotels": mock_hotels,
        "source": "mock_data",
        "search_params": params,
        "timestamp": datetime.now().isoformat()
    }


def format_amadeus_hotel(hotel_offer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format Amadeus hotel offer into simplified structure.
    
    Args:
        hotel_offer: Raw hotel offer from Amadeus API
    
    Returns:
        Formatted hotel data
    """
    try:
        hotel = hotel_offer.get("hotel", {})
        offers = hotel_offer.get("offers", [])
        
        if not offers:
            return None
        
        # Get best offer (first one, as we requested bestRateOnly)
        best_offer = offers[0]
        price = best_offer.get("price", {})
        room = best_offer.get("room", {})
        
        # Calculate total price and nights
        total = float(price.get("total", 0))
        
        # Calculate nights from check-in/check-out dates
        try:
            check_in_date = best_offer.get("checkInDate", "")
            check_out_date = best_offer.get("checkOutDate", "")
            
            if check_in_date and check_out_date:
                from datetime import datetime
                check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
                check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
                nights = (check_out - check_in).days
            else:
                nights = 1
        except:
            nights = 1
        
        price_per_night = total / nights if nights > 0 else total
        
        formatted = {
            "hotel_id": hotel.get("hotelId"),
            "name": hotel.get("name", "Hotel"),
            "destination": hotel.get("cityCode", ""),
            "rating": float(hotel.get("rating", 0)) if hotel.get("rating") else 4.0,
            "type": hotel.get("type", "Hotel"),
            "price_per_night": price_per_night,
            "total_price": total,
            "currency": price.get("currency", "USD"),
            "amenities": hotel.get("amenities", []),
            "location": f"{hotel.get('address', {}).get('cityName', '')}",
            "distance_to_center": "City Center",
            "cancellation": best_offer.get("policies", {}).get("cancellation", {}).get("description", "Standard"),
            "reviews_count": 0,  # Not available in Amadeus
            "description": room.get("description", {}).get("text", ""),
            "room_type": room.get("typeEstimated", {}).get("category", "Standard")
        }
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting Amadeus hotel: {e}")
        return None


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