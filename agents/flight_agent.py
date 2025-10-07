"""
Flight Agent: Handles flight search and booking inquiries.
Specialized agent for flight-related operations.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from langchain_core.messages import AIMessage

from core.state import GraphState
from utils.config import get_config

logger = logging.getLogger(__name__)


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
    
    NOTE: This uses MOCK DATA for MVP. In production, integrate with:
    - Amadeus Flight Search API
    - Skyscanner API
    - Google Flights API
    - Store results in Supabase for persistence
    
    Args:
        state: Current graph state
        params: Search parameters
    
    Returns:
        Flight search results
    """
    logger.info(f"Executing flight search: {params}")
    
    # MOCK DATA - Replace with real API calls
    mock_flights = generate_mock_flights(
        origin=params.get("origin", "SFO"),
        destination=params.get("destination", "NRT"),
        departure_date=params.get("departure_date"),
        return_date=params.get("return_date"),
        passengers=params.get("passengers", 1)
    )
    
    logger.info(f"Found {len(mock_flights)} flight options (MOCK DATA)")
    
    return {
        "flights": mock_flights,
        "search_params": params,
        "timestamp": datetime.now().isoformat()
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
    
    params = {
        "origin": "SFO",  # Default, should be extracted from user location
        "destination": (extracted_prefs or prefs).get("destination", "Tokyo"),
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


def generate_mock_flights(origin: str, destination: str, 
                         departure_date: str, return_date: str,
                         passengers: int) -> List[Dict[str, Any]]:
    """
    Generate mock flight data for MVP.
    
    TODO: Replace with real flight API integration.
    """
    airlines = ["United Airlines", "ANA", "Japan Airlines", "Delta"]
    
    mock_flights = []
    for i, airline in enumerate(airlines):
        mock_flights.append({
            "flight_id": f"FL{1000 + i}",
            "airline": airline,
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "outbound_departure": "10:30 AM",
            "outbound_arrival": "2:30 PM (+1 day)",
            "return_departure": "4:00 PM",
            "return_arrival": "6:00 PM",
            "duration_outbound": "11h 00m",
            "duration_return": "10h 00m",
            "stops": 0 if i < 2 else 1,
            "price_per_passenger": 850 + (i * 150),
            "total_price": (850 + (i * 150)) * passengers,
            "cabin_class": "Economy",
            "baggage": "2 checked bags included",
            "cancellation_policy": "Flexible" if i == 0 else "Standard"
        })
    
    return mock_flights


def format_flight_response(results: Dict[str, Any]) -> str:
    """Format flight results into human-readable response."""
    flights = results.get("flights", [])
    
    if not flights:
        return "No flights found for your search criteria."
    
    response_parts = [
        f"Found {len(flights)} flight options:\n"
    ]
    
    for i, flight in enumerate(flights[:3], 1):  # Show top 3
        response_parts.append(
            f"\n{i}. {flight['airline']} - ${flight['total_price']:.2f}\n"
            f"   Outbound: {flight['departure_date']} at {flight['outbound_departure']}\n"
            f"   Return: {flight['return_date']} at {flight['return_departure']}\n"
            f"   Duration: {flight['duration_outbound']} / {flight['duration_return']}\n"
            f"   Stops: {flight['stops']}\n"
        )
    
    if len(flights) > 3:
        response_parts.append(f"\n...and {len(flights) - 3} more options available.")
    
    return "".join(response_parts)