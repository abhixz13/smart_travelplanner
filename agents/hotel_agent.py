"""Hotel Agent: Handles accommodation search via Amadeus API."""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from langchain_core.messages import AIMessage
from core.state import GraphState

try:
    from utils.amadeus_client import get_amadeus_client
    AMADEUS_AVAILABLE = True
except Exception as e:
    AMADEUS_AVAILABLE = False
    logging.getLogger(__name__).warning(f"Amadeus API unavailable: {e}")

logger = logging.getLogger(__name__)


def hotel_agent_node(state: GraphState) -> Dict[str, Any]:
    """Process accommodation requests."""
    logger.info("Processing hotel search request")
    
    try:
        params = extract_hotel_params(state)
        results = execute_hotel_search(state, params)
        
        # Handle Airbnb suggestions
        if results.get("airbnb_suggestion"):
            return _update_state(state, results["message"], results)
        
        # Autonomous mode: select best hotel
        if state.get("autonomous_execution"):
            best = select_best_hotel(results["hotels"], params)
            response = format_best_hotel(best) if best else "No hotels found matching criteria."
            results["selected_hotel"] = best
            return _update_state(state, response, results, best)
        
        # Standard mode: show all options
        return _update_state(state, format_hotel_response(results), results)
            
    except Exception as e:
        logger.error(f"Hotel agent error: {e}", exc_info=True)
        return _update_state(state, f"Accommodation search error: {e}")


def execute_hotel_search(state: GraphState, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute hotel search with Amadeus API or suggest Airbnb."""
    from agents.flight_agent import convert_country_to_city
    
    destination = convert_country_to_city(params.get("destination", "Tokyo"))
    check_in = params.get("check_in") or (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    check_out = params.get("check_out") or (datetime.strptime(check_in, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")
    guests = params.get("guests", 1)
    
    if not AMADEUS_AVAILABLE:
        return _airbnb_fallback(destination, check_in, check_out, guests, params)
    
    try:
        amadeus = get_amadeus_client(use_production=False)
        city_name = destination.split(',')[0].strip()
        cities = amadeus.city_search(city_name, max_results=1)
        
        if not cities or not cities[0].get("iataCode"):
            return _airbnb_fallback(destination, check_in, check_out, guests, params, 
                                   "Destination lacks hotel availability in our system")
        
        city_code = cities[0]["iataCode"]
        logger.info(f"Searching hotels in {city_code} ({destination})")
        
        result = amadeus.hotel_search_by_city(
            city_code=city_code,
            check_in_date=check_in,
            check_out_date=check_out,
            adults=guests,
            room_quantity=1,
            max_results=10
        )
        
        if not result.get("success") or not result.get("hotels"):
            return _airbnb_fallback(destination, check_in, check_out, guests, params,
                                   result.get('error', 'No hotels available'))
        
        formatted = [format_amadeus_hotel(h) for h in result["hotels"]]
        formatted = [h for h in formatted if h]  # Remove None values
        
        logger.info(f"Found {len(formatted)} hotels from Amadeus")
        return {
            "hotels": formatted,
            "source": "amadeus_api",
            "search_params": params,
            "timestamp": datetime.now().isoformat()
        }
                
    except Exception as e:
        logger.error(f"Amadeus search error: {e}")
        return _airbnb_fallback(destination, check_in, check_out, guests, params, "API error")


def format_amadeus_hotel(hotel_offer: Dict[str, Any]) -> Dict[str, Any]:
    """Format Amadeus hotel offer into simplified structure."""
    try:
        hotel = hotel_offer.get("hotel", {})
        offers = hotel_offer.get("offers", [])
        if not offers:
            return None
        
        best = offers[0]
        price = best.get("price", {})
        room = best.get("room", {})
        total = float(price.get("total", 0))
        
        # Calculate nights
        nights = 1
        try:
            cin = datetime.strptime(best.get("checkInDate", ""), "%Y-%m-%d")
            cout = datetime.strptime(best.get("checkOutDate", ""), "%Y-%m-%d")
            nights = max((cout - cin).days, 1)
        except:
            pass
        
        return {
            "hotel_id": hotel.get("hotelId"),
            "name": hotel.get("name", "Hotel"),
            "destination": hotel.get("cityCode", ""),
            "rating": float(hotel.get("rating", 4.0) or 4.0),
            "type": hotel.get("type", "Hotel"),
            "price_per_night": total / nights,
            "total_price": total,
            "currency": price.get("currency", "USD"),
            "amenities": hotel.get("amenities", []),
            "location": hotel.get('address', {}).get('cityName', ''),
            "distance_to_center": "City Center",
            "cancellation": best.get("policies", {}).get("cancellation", {}).get("description", "Standard"),
            "reviews_count": 0,
            "description": room.get("description", {}).get("text", ""),
            "room_type": room.get("typeEstimated", {}).get("category", "Standard")
        }
    except Exception as e:
        logger.error(f"Format error: {e}")
        return None


def extract_hotel_params(state: GraphState) -> Dict[str, Any]:
    """Extract hotel search parameters from state."""
    # Get preferences from tool results or user_preferences
    prefs = {}
    for result in state.get("tool_results", {}).values():
        if isinstance(result, dict) and "destination" in result:
            prefs = result
            break
    
    if not prefs:
        prefs = state.get("user_preferences", {})
    
    # Override with metadata if present
    metadata = state.get("metadata", {})
    for key, meta_key in [
        ("destination", "hotel_destination"),
        ("start_date", "hotel_start_date"),
        ("end_date", "hotel_end_date"),
        ("travelers", "hotel_guests"),
        ("budget", "hotel_budget"),
        ("accommodation_type", "hotel_accommodation_type")
    ]:
        if metadata.get(meta_key):
            prefs[key] = metadata[meta_key]

    return {
        "destination": prefs.get("destination", "Tokyo"),
        "check_in": prefs.get("start_date"),
        "check_out": prefs.get("end_date"),
        "guests": prefs.get("travelers", 1),
        "budget": prefs.get("budget", "mid-range"),
        "accommodation_type": prefs.get("accommodation_type", "hotel")
    }


def format_hotel_response(results: Dict[str, Any]) -> str:
    """Format hotel results into readable response."""
    hotels = results.get("hotels", [])
    if not hotels:
        return "No hotels found for your criteria."
    
    lines = [f"Found {len(hotels)} accommodation options:\n"]
    for i, h in enumerate(hotels[:3], 1):
        lines.append(
            f"\n{i}. {h['name']} - ${h['price_per_night']:.2f}/night\n"
            f"   Rating: {h['rating']}⭐ ({h['reviews_count']} reviews)\n"
            f"   Location: {h['location']} ({h['distance_to_center']} from center)\n"
            f"   Amenities: {', '.join(h['amenities'][:3])}\n"
            f"   Total (7 nights): ${h['total_price']:.2f}\n"
        )
    
    if len(hotels) > 3:
        lines.append(f"\n...and {len(hotels) - 3} more options.")
    
    return "".join(lines)


def format_best_hotel(hotel: Dict[str, Any]) -> str:
    """Format best hotel selection."""
    return (
        f"Best hotel: {hotel['name']} - ${hotel['price_per_night']:.2f}/night\n"
        f"   Rating: {hotel['rating']}⭐ ({hotel['reviews_count']} reviews)\n"
        f"   Location: {hotel['location']} ({hotel['distance_to_center']} from center)\n"
        f"   Amenities: {', '.join(hotel['amenities'][:3])}\n"
        f"   Total (7 nights): ${hotel['total_price']:.2f}\n"
        f"   Cancellation: {hotel['cancellation']}\n"
    )


def select_best_hotel(hotels: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
    """Select best hotel based on weighted scoring."""
    if not hotels:
        return None
    
    # Weight criteria by budget level
    weights = {
        "budget": {"price": 0.6, "rating": 0.2, "amenities": 0.1, "location": 0.1},
        "luxury": {"price": 0.2, "rating": 0.4, "amenities": 0.3, "location": 0.1},
        "mid-range": {"price": 0.4, "rating": 0.3, "amenities": 0.2, "location": 0.1}
    }[params.get("budget", "mid-range")]
    
    def score_hotel(h: Dict) -> float:
        score = (
            weights["price"] * (1 / max(h.get('price_per_night', 1e9), 1)) +
            weights["rating"] * (h.get('rating', 0) / 5.0) +
            weights["amenities"] * (len(h.get('amenities', [])) / 10.0) +
            weights["location"] * (1 if 'center' in h.get('location', '').lower() else 0.5)
        )
        
        # Apply constraints
        if params.get("max_price") and h.get('price_per_night', 0) > params["max_price"]:
            score -= 1e9
        if params.get("min_rating") and h.get('rating', 0) < params["min_rating"]:
            score -= 1e9
        if params.get("must_have_amenities"):
            missing = set(params["must_have_amenities"]) - set(h.get('amenities', []))
            score -= 1e9 * len(missing)
        
        return score
    
    best = max(hotels, key=score_hotel)
    logger.info(f"Selected: {best['name']} - ${best['price_per_night']:.2f}/night")
    return best


def _airbnb_fallback(destination: str, check_in: str, check_out: str, 
                     guests: int, params: Dict, reason: str = None) -> Dict[str, Any]:
    """Generate Airbnb suggestion response."""
    msg = f"Destination '{destination}' "
    msg += f"({reason}). " if reason else "is unavailable. "
    msg += "Please search accommodations on Airbnb or other vacation rental platforms."
    
    return {
        "airbnb_suggestion": True,
        "destination": destination,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "message": msg,
        "search_params": params,
        "timestamp": datetime.now().isoformat()
    }


def _update_state(state: GraphState, response: str, 
                 tool_results: Dict = None, selected: Dict = None) -> Dict[str, Any]:
    """Helper to update state with response."""
    update = {"messages": state["messages"] + [AIMessage(content=response)]}
    
    if tool_results:
        update["tool_results"] = {
            **state.get("tool_results", {}),
            "hotel_search": tool_results
        }
        if selected is not None:
            update["tool_results"]["selected_hotel"] = selected
    
    return update