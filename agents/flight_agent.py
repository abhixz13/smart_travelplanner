"""
Flight Agent: Handles flight search and booking inquiries.
Specialized agent for flight-related operations.
Integrates with Amadeus API for real flight data.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from langchain_core.messages import AIMessage

from core.state import GraphState
from utils.config import get_config
from utils.helpers import time_execution

# Try to import Amadeus client (falls back to mock if unavailable)
try:
    from utils.amadeus_client import get_amadeus_client
    AMADEUS_AVAILABLE = True
    logger_temp = logging.getLogger(__name__)
    logger_temp.info("✅ Amadeus API client available")
except Exception as e:
    AMADEUS_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"⚠️ Amadeus API unavailable, using mock data: {e}")

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


def select_best_flight(flights: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Select the best flight from a list based on user preferences and constraints.
    
    Args:
        flights: List of flight offers
        params: Search parameters
    
    Returns:
        The best flight offer
    """
    logger.info("Selecting best flight from search results...")
    
    # Define criteria for selection
    price_weight = 0.4
    duration_weight = 0.3
    stops_weight = 0.2
    cancellation_weight = 0.1
    
    # Initialize scores
    best_score = float('-inf')
    best_flight = None
    
    for flight in flights:
        # Calculate weighted score
        price_score = price_weight * (1 / flight.get('total_price', 1e9)) # Lower price is better
        duration_score = duration_weight * (1 / (flight.get('duration_outbound', 1e9) + flight.get('duration_return', 1e9))) # Shorter duration is better
        stops_score = stops_weight * (1 / flight.get('stops', 1e9)) # Fewer stops is better
        cancellation_score = cancellation_weight * (1 if flight.get('cancellation_policy') == 'Flexible' else 0) # Flexible cancellation is better
        
        total_score = price_score + duration_score + stops_score + cancellation_score
        
        # Apply user constraints
        if params.get("max_price") and flight.get('total_price') > params["max_price"]:
            total_score -= 1e9 # Penalize if price exceeds max_price
        
        if params.get("min_duration_outbound") and flight.get('duration_outbound') < params["min_duration_outbound"]:
            total_score -= 1e9 # Penalize if outbound duration is too short
        
        if params.get("max_stops") and flight.get('stops') > params["max_stops"]:
            total_score -= 1e9 # Penalize if stops exceed max_stops
        
        if params.get("cancellation_policy") and flight.get('cancellation_policy') != params["cancellation_policy"]:
            total_score -= 1e9 # Penalize if cancellation policy doesn't match
        
        if total_score > best_score:
            best_score = total_score
            best_flight = flight
    
    if best_flight:
        logger.info(f"Selected best flight: {best_flight['airline']} - ${best_flight['total_price']:.2f}")
        return best_flight
    else:
        logger.warning("No flight found that meets all criteria.")
        return None


@time_execution()
def flight_agent_node(state: GraphState) -> Dict[str, Any]:
    """
    Flight agent node for handling flight queries.
    
    Args:
        state: Current graph state
    
    Returns:
        Updated state with flight search results
    """
    logger.info("="*60)
    logger.info("FLIGHT AGENT NODE: Processing flight request")
    logger.info("="*60)
    
    try:
        # Extract parameters from last message or state
        params = extract_flight_params(state)
        
        # Execute flight search
        flight_results = execute_flight_search(state, params)
        
        # Format response
        response = format_flight_response(flight_results)
        
        # Check for autonomous execution mode
        if state.get("autonomous_execution", False):
            selected_flight = select_best_flight(flight_results["flights"], params)
            if selected_flight:
                response += f"\n\nAutonomous Selection: Selected flight - {selected_flight['airline']} - ${selected_flight['total_price']:.2f}"
                return {
                    "messages": state["messages"] + [AIMessage(content=response)],
                    "tool_results": {
                        **state.get("tool_results", {}),
                        "flight_search": flight_results,
                        "selected_flight": selected_flight
                    }
                }
            else:
                response += "\n\nAutonomous Selection: No flight found that meets all criteria."
                return {
                    "messages": state["messages"] + [AIMessage(content=response)],
                    "tool_results": {
                        **state.get("tool_results", {}),
                        "flight_search": flight_results,
                        "selected_flight": None
                    }
                }
        else:
            return {
                "messages": state["messages"] + [AIMessage(content=response)],
                "tool_results": {
                    **state.get("tool_results", {}),
                    "flight_search": flight_results
                }
            }
        
    except Exception as e:
        logger.error(f"Error in flight agent: {str(e)}", exc_info=True)
        return {
            "messages": state["messages"] + [
                AIMessage(content=f"Flight search error: {str(e)}")
            ]
        }


def execute_flight_search(state: GraphState, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute flight search with given parameters.
    
    Now integrated with Amadeus API for real flight data!
    Falls back to mock data if Amadeus API fails.
    
    Args:
        state: Current graph state
        params: Search parameters
    
    Returns:
        Flight search results
    """
    logger.info(f"Executing flight search: {params}")
    
    origin = params.get("origin", "SFO")
    destination = params.get("destination", "NRT")
    departure_date = params.get("departure_date")
    return_date = params.get("return_date")
    passengers = params.get("passengers", 1)
    
    # Convert country names to cities (e.g., "Japan" → "Tokyo")
    destination = convert_country_to_city(destination)
    
    # Generate dates if not provided (required for Amadeus API)
    if not departure_date:
        departure_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        logger.info(f"Generated default departure date: {departure_date}")
    
    if not return_date:
        departure_obj = datetime.strptime(departure_date, "%Y-%m-%d")
        return_date = (departure_obj + timedelta(days=7)).strftime("%Y-%m-%d")
        logger.info(f"Generated default return date: {return_date}")
    
    # Try Amadeus API first
    if AMADEUS_AVAILABLE:
        try:
            amadeus = get_amadeus_client(use_production=False)  # Use test API
            
            # Resolve origin and destination to IATA codes
            origin_code = origin
            destination_code = destination
            
            # Check if origin is not already an IATA code (3 letters)
            if not (isinstance(origin, str) and len(origin) == 3 and origin.isupper()):
                logger.info(f"Resolving origin: {origin}")
                # Try CITY first, then AIRPORT
                resolved_origin = amadeus.search_airport_city(keyword=origin, subtype=["CITY"], max_results=1)
                if not resolved_origin:
                    resolved_origin = amadeus.search_airport_city(keyword=origin, subtype=["AIRPORT"], max_results=1)
                
                if resolved_origin and len(resolved_origin) > 0:
                    origin_code = resolved_origin[0].get("iataCode", origin)
                    logger.info(f"✅ Resolved origin '{origin}' to IATA code: {origin_code}")
                else:
                    logger.warning(f"⚠️ Could not resolve origin '{origin}', using as-is")
            
            # Check if destination is not already an IATA code
            if not (isinstance(destination, str) and len(destination) == 3 and destination.isupper()):
                logger.info(f"Resolving destination city: {destination}")
                # Extract just the city name from the destination string (e.g., "Tokyo, Japan" -> "Tokyo")
                city_name = destination.split(',')[0].strip() if ',' in destination else destination.strip()
                logger.info(f"Searching cities: {city_name}")
                # Step 1: Use city_search to get city IATA code
                cities = amadeus.city_search(keyword=city_name, max_results=1)
                
                if cities and len(cities) > 0:
                    destination_code = cities[0].get("iataCode", destination)
                    logger.info(f"✅ Resolved destination '{destination}' to city code: {destination_code}")
                else:
                    logger.warning(f"⚠️ City search failed for '{destination}', using as-is")
                    # Could not resolve - will use original value (may cause 400 error)
            
            logger.info(f"🔍 Searching Amadeus API: {origin_code} → {destination_code} on {departure_date}")
            
            result = amadeus.search_flights(
                origin=origin_code,
                destination=destination_code,
                departure_date=departure_date,
                return_date=return_date,
                adults=passengers,
                max_results=10
            )
            
            if result.get("success") and result.get("offers"):
                # Format Amadeus offers
                formatted_flights = []
                dictionaries = result.get("dictionaries", {})
                
                for offer in result["offers"][:10]:  # Limit to 10
                    formatted = amadeus.format_flight_offer(offer, dictionaries)
                    if formatted:
                        formatted_flights.append(formatted)
                
                logger.info(f"✅ Found {len(formatted_flights)} real flights from Amadeus")
                
                return {
                    "flights": formatted_flights,
                    "source": "amadeus_api",
                    "search_params": params,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning(f"Amadeus API returned no results: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Amadeus API error: {e}, cannot search flights.")
            return {
                "flights": [],
                "source": "amadeus_api_error",
                "search_params": params,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    # If Amadeus is not available or failed, return empty results
    logger.warning("Amadeus API unavailable or failed to find flights. Returning no flight options.")
    return {
        "flights": [],
        "source": "no_flights_available",
        "search_params": params,
        "timestamp": datetime.now().isoformat(),
        "error": "No flight options available due to API issue or no results."
    }


def extract_flight_params(state: GraphState) -> Dict[str, Any]:
    """Extract flight search parameters from state."""
    # Try to get from user preferences first
    prefs = state.get("user_preferences", {})
    
    # Check tool results for extracted preferences
    tool_results = state.get("tool_results", {})
    extracted_prefs = None
    for result in tool_results.values():
        if isinstance(result, dict) and "destination" in result:
            extracted_prefs = result
            break
    
    # Check metadata for flight parameters
    metadata = state.get("metadata", {})
    if metadata.get("flight_params"):
        extracted_prefs = metadata["flight_params"]
    
    destination = (extracted_prefs or prefs).get("destination", "Tokyo")
    
    # Convert country names to major city names
    destination = convert_country_to_city(destination)
    
    params = {
        "origin": "SFO",  # Default, should be extracted from user location
        "destination": destination,
        "departure_date": (extracted_prefs or prefs).get("start_date"),
        "return_date": (extracted_prefs or prefs).get("end_date"),
        "passengers": (extracted_prefs or prefs).get("travelers", 1),
        "cabin_class": "economy"  # Can be extracted from budget
    }
    
    # Generate dates if not provided
    if not params["departure_date"]:
        params["departure_date"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    if not params["return_date"] and extracted_prefs:
        duration = extracted_prefs.get("duration_days", 7)
        departure = datetime.strptime(params["departure_date"], "%Y-%m-%d")
        params["return_date"] = (departure + timedelta(days=duration)).strftime("%Y-%m-%d")
    
    return params


def format_flight_response(results: Dict[str, Any]) -> str:
    """Format flight results into human-readable response."""
    flights = results.get("flights", [])
    
    if not flights:
        return "No flights found for your search criteria."
    
    response_parts = [
        f"Found {len(flights)} flight options:\n"
    ]
    
    for i, flight in enumerate(flights[:3], 1):  # Show top 3
        # Handle both mock data format and Amadeus API format
        if 'total_price' in flight:
            # Mock data format
            response_parts.append(
                f"\n{i}. {flight['airline']} - ${flight['total_price']:.2f}\n"
                f"   Outbound: {flight['departure_date']} at {flight['outbound_departure']}\n"
                f"   Return: {flight['return_date']} at {flight['return_departure']}\n"
                f"   Duration: {flight['duration_outbound']} / {flight['duration_return']}\n"
                f"   Stops: {flight['stops']}\n"
            )
        else:
            # Amadeus API format
            price = flight.get('price', 0)
            airline = flight.get('airline', 'Unknown')
            outbound = flight.get('outbound', {})
            return_flight = flight.get('return', {})
            
            response_parts.append(
                f"\n{i}. {airline} - ${price:.2f} {flight.get('currency', 'USD')}\n"
                f"   Outbound: {outbound.get('departure_time', 'N/A')}\n"
                f"   Duration: {outbound.get('duration', 'N/A')}\n"
                f"   Stops: {outbound.get('stops', 0)}\n"
            )
            if return_flight:
                response_parts.append(f"   Return: {return_flight.get('departure_time', 'N/A')}\n")
    
    if len(flights) > 3:
        response_parts.append(f"\n...and {len(flights) - 3} more options available.")
    
    return "".join(response_parts)