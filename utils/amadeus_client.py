"""
Amadeus API Client for Flight Search Integration
Handles OAuth2 authentication and flight search operations
"""

import os
import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)


class AmadeusClient:
    """
    Amadeus API client with OAuth2 authentication and token caching.
    
    Uses Amadeus Test API for development. Switch to production API when ready:
    - Test: https://test.api.amadeus.com
    - Production: https://api.amadeus.com
    """
    
    # API Endpoints
    TEST_BASE_URL = "https://test.api.amadeus.com"
    PROD_BASE_URL = "https://api.amadeus.com"
    
    def __init__(self, use_production: bool = False):
        """
        Initialize Amadeus client.
        
        Args:
            use_production: If True, use production API; otherwise use test API
        """
        self.api_key = os.getenv("AMADEUS_API_KEY")
        self.api_secret = os.getenv("AMADEUS_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("AMADEUS_API_KEY and AMADEUS_API_SECRET must be set")
        
        self.base_url = self.PROD_BASE_URL if use_production else self.TEST_BASE_URL
        self.access_token = None
        self.token_expires_at = None
        
        logger.info(f"AmadeusClient initialized (mode: {'PROD' if use_production else 'TEST'})")
    
    def _get_access_token(self) -> str:
        """
        Get OAuth2 access token. Reuses cached token if still valid.
        
        Returns:
            Access token string
        """
        # Check if cached token is still valid
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                logger.debug("Using cached Amadeus access token")
                return self.access_token
        
        # Request new token
        logger.info("Requesting new Amadeus access token...")
        
        token_url = f"{self.base_url}/v1/security/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 1799)  # Default 30 min
            
            # Set expiration time with 5 minute buffer
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
            
            logger.info(f"✅ New access token obtained (expires in {expires_in}s)")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get Amadeus access token: {e}")
            raise
    
    def search_flights(self, 
                       origin: str,
                       destination: str,
                       departure_date: str,
                       return_date: Optional[str] = None,
                       adults: int = 1,
                       max_results: int = 10,
                       currency: str = "USD") -> Dict[str, Any]:
        """
        Search for flight offers using Amadeus Flight Offers Search API.
        
        Args:
            origin: IATA airport code (e.g., "LAX")
            destination: IATA airport code (e.g., "NRT")
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date in YYYY-MM-DD format (for round trip)
            adults: Number of adult passengers
            max_results: Maximum number of results to return
            currency: Currency code for prices
        
        Returns:
            Dict containing flight offers and metadata
        """
        logger.info(f"Searching flights: {origin} → {destination} on {departure_date}")
        
        try:
            token = self._get_access_token()
            
            # Build API request
            endpoint = f"{self.base_url}/v2/shopping/flight-offers"
            headers = {"Authorization": f"Bearer {token}"}
            
            params = {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDate": departure_date,
                "adults": adults,
                "max": max_results,
                "currencyCode": currency
            }
            
            if return_date:
                params["returnDate"] = return_date
            
            # Make request (increased timeout for slow API responses)
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            flight_offers = data.get("data", [])
            
            logger.info(f"✅ Found {len(flight_offers)} flight offers from Amadeus")
            
            return {
                "success": True,
                "source": "amadeus_api",
                "offers": flight_offers,
                "meta": data.get("meta", {}),
                "dictionaries": data.get("dictionaries", {}),
                "count": len(flight_offers)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Amadeus flight search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "offers": []
            }
    
    def search_airport_city(self, keyword: str, subtype: List[str] = None, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Airport & City Search API - Search for airports and cities by keyword.
        https://developers.amadeus.com/self-service/category/air/api-doc/airport-and-city-search
        
        Args:
            keyword: Search term (city name, airport name, or code)
            subtype: List of location types to search for (e.g., ["CITY"], ["AIRPORT"], ["CITY", "AIRPORT"])
            max_results: Maximum number of results
        
        Returns:
            List of matching airports/cities
        """
        logger.info(f"Searching locations for: {keyword}")
        
        try:
            token = self._get_access_token()
            
            endpoint = f"{self.base_url}/v1/reference-data/locations"
            headers = {"Authorization": f"Bearer {token}"}
            
            # Build subType parameter
            if subtype:
                subtype_str = ",".join(subtype)
            else:
                subtype_str = "AIRPORT,CITY"
            
            params = {
                "keyword": keyword,
                "subType": subtype_str,
                "page[limit]": max_results
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            locations = data.get("data", [])
            
            logger.info(f"✅ Found {len(locations)} locations for '{keyword}' (subType: {subtype_str})")
            return locations
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Location search failed for '{keyword}': {e}")
            return []
    
    def flight_inspiration_search(self,
                                   origin: str,
                                   max_price: Optional[int] = None,
                                   departure_date_from: Optional[str] = None,
                                   departure_date_to: Optional[str] = None,
                                   duration: Optional[str] = None,
                                   max_results: int = 10) -> Dict[str, Any]:
        """
        Flight Inspiration Search API - Find cheapest destinations from origin.
        https://developers.amadeus.com/self-service/category/air/api-doc/flight-inspiration-search
        
        Perfect for "Where can I go?" queries.
        
        Args:
            origin: IATA airport code (e.g., "LAX")
            max_price: Maximum price per traveler
            departure_date_from: Start of date range (YYYY-MM-DD)
            departure_date_to: End of date range (YYYY-MM-DD)
            duration: Trip duration (e.g., "1,7" for 1-7 days)
            max_results: Maximum number of destinations
        
        Returns:
            Dict containing cheapest destinations
        """
        logger.info(f"Searching flight inspiration from: {origin}")
        
        try:
            token = self._get_access_token()
            
            endpoint = f"{self.base_url}/v1/shopping/flight-destinations"
            headers = {"Authorization": f"Bearer {token}"}
            
            params = {"origin": origin.upper()}
            if max_price:
                params["maxPrice"] = max_price
            if departure_date_from:
                params["departureDate"] = f"{departure_date_from},{departure_date_to or departure_date_from}"
            if duration:
                params["duration"] = duration
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            
            data = response.json()
            destinations = data.get("data", [])[:max_results]
            
            logger.info(f"✅ Found {len(destinations)} destinations")
            return {
                "success": True,
                "destinations": destinations,
                "meta": data.get("meta", {})
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Flight inspiration search failed: {e}")
            return {"success": False, "error": str(e), "destinations": []}
    
    def flight_cheapest_date_search(self,
                                     origin: str,
                                     destination: str,
                                     departure_date: Optional[str] = None,
                                     one_way: bool = False,
                                     duration: Optional[str] = None,
                                     max_price: Optional[int] = None) -> Dict[str, Any]:
        """
        Flight Cheapest Date Search API - Find cheapest dates to fly.
        https://developers.amadeus.com/self-service/category/air/api-doc/flight-cheapest-date-search
        
        Perfect for flexible date searches.
        
        Args:
            origin: IATA airport code
            destination: IATA airport code
            departure_date: Preferred departure date (YYYY-MM-DD) or date range
            one_way: True for one-way, False for round-trip
            duration: Trip duration in days or range (e.g., "7" or "5,10")
            max_price: Maximum price per traveler
        
        Returns:
            Dict containing cheapest dates
        """
        logger.info(f"Searching cheapest dates: {origin} → {destination}")
        
        try:
            token = self._get_access_token()
            
            endpoint = f"{self.base_url}/v1/shopping/flight-dates"
            headers = {"Authorization": f"Bearer {token}"}
            
            params = {
                "origin": origin.upper(),
                "destination": destination.upper()
            }
            
            if departure_date:
                params["departureDate"] = departure_date
            if one_way:
                params["oneWay"] = "true"
            if duration:
                params["duration"] = duration
            if max_price:
                params["maxPrice"] = max_price
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            
            data = response.json()
            dates = data.get("data", [])
            
            logger.info(f"✅ Found {len(dates)} date options")
            return {
                "success": True,
                "dates": dates,
                "meta": data.get("meta", {})
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Cheapest date search failed: {e}")
            return {"success": False, "error": str(e), "dates": []}
    
    def tours_and_activities(self,
                             latitude: float,
                             longitude: float,
                             radius: int = 1) -> Dict[str, Any]:
        """
        Tours and Activities API - Find activities and tours near location.
        https://developers.amadeus.com/self-service/category/destination-content/api-doc/tours-and-activities
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius: Search radius in km (max 20)
        
        Returns:
            Dict containing activities
        """
        logger.info(f"Searching activities at: ({latitude}, {longitude})")
        
        try:
            token = self._get_access_token()
            
            endpoint = f"{self.base_url}/v1/shopping/activities"
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "radius": min(radius, 20)  # Max 20km
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            
            data = response.json()
            activities = data.get("data", [])
            
            logger.info(f"✅ Found {len(activities)} activities")
            return {
                "success": True,
                "activities": activities,
                "meta": data.get("meta", {})
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Activities search failed: {e}")
            return {"success": False, "error": str(e), "activities": []}
    
    def airline_code_lookup(self, airline_codes: List[str]) -> Dict[str, str]:
        """
        Airline Code Lookup API - Get airline names from codes.
        https://developers.amadeus.com/self-service/category/air/api-doc/airline-code-lookup
        
        Args:
            airline_codes: List of IATA airline codes (e.g., ["AA", "UA"])
        
        Returns:
            Dict mapping codes to airline names
        """
        logger.info(f"Looking up airline codes: {airline_codes}")
        
        try:
            token = self._get_access_token()
            
            endpoint = f"{self.base_url}/v1/reference-data/airlines"
            headers = {"Authorization": f"Bearer {token}"}
            params = {"airlineCodes": ",".join(airline_codes)}
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            airlines = data.get("data", [])
            
            # Create mapping
            airline_map = {
                airline.get("iataCode"): airline.get("businessName", airline.get("commonName", ""))
                for airline in airlines
            }
            
            logger.info(f"✅ Found {len(airline_map)} airlines")
            return airline_map
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Airline lookup failed: {e}")
            return {}
    
    def hotel_list_by_city(self, city_code: str, max_results: int = 20) -> Dict[str, Any]:
        """
        Hotel List API - Get list of hotels in a city.
        https://developers.amadeus.com/self-service/category/hotel/api-doc/hotel-list
        
        Note: Use this to get hotel IDs, then use hotel_offers_search for pricing.
        
        Args:
            city_code: IATA city code (e.g., "NYC", "PAR", "LON")
            max_results: Maximum number of results
        
        Returns:
            Dict containing hotel list
        """
        logger.info(f"Searching hotels in: {city_code}")
        
        try:
            token = self._get_access_token()
            
            endpoint = f"{self.base_url}/v1/reference-data/locations/hotels/by-city"
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "cityCode": city_code.upper(),
                "radius": 50,  # km
                "radiusUnit": "KM"
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            hotels = data.get("data", [])[:max_results]
            
            logger.info(f"✅ Found {len(hotels)} hotels")
            return {
                "success": True,
                "hotels": hotels,
                "meta": data.get("meta", {})
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Hotel list search failed: {e}")
            return {"success": False, "error": str(e), "hotels": []}
    
    def hotel_offers_search(self,
                           hotel_ids: List[str],
                           check_in_date: str,
                           check_out_date: str,
                           adults: int = 1,
                           room_quantity: int = 1,
                           currency: str = "USD") -> Dict[str, Any]:
        """
        Hotel Offers Search API - Get pricing for specific hotels.
        https://developers.amadeus.com/self-service/category/hotel/api-doc/hotel-search
        
        Args:
            hotel_ids: List of Amadeus hotel IDs (max 100)
            check_in_date: Check-in date (YYYY-MM-DD)
            check_out_date: Check-out date (YYYY-MM-DD)
            adults: Number of adults per room
            room_quantity: Number of rooms
            currency: Currency code
        
        Returns:
            Dict containing hotel offers with pricing
        """
        logger.info(f"Getting offers for {len(hotel_ids)} hotels")
        
        try:
            token = self._get_access_token()
            
            endpoint = f"{self.base_url}/v3/shopping/hotel-offers"
            headers = {"Authorization": f"Bearer {token}"}
            
            # Amadeus API accepts comma-separated hotel IDs
            params = {
                "hotelIds": ",".join(hotel_ids[:100]),  # Max 100 hotels
                "checkInDate": check_in_date,
                "checkOutDate": check_out_date,
                "adults": adults,
                "roomQuantity": room_quantity,
                "currency": currency,
                "bestRateOnly": "true"
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            offers = data.get("data", [])
            
            logger.info(f"✅ Found {len(offers)} hotel offers")
            return {
                "success": True,
                "offers": offers,
                "meta": data.get("meta", {})
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Hotel offers search failed: {e}")
            return {"success": False, "error": str(e), "offers": []}
    
    def hotel_search_by_city(self,
                            city_code: str,
                            check_in_date: str,
                            check_out_date: str,
                            adults: int = 1,
                            room_quantity: int = 1,
                            currency: str = "USD",
                            max_results: int = 20) -> Dict[str, Any]:
        """
        Combined Hotel Search - Get hotels in city with pricing (2-step process).
        
        This is a convenience method that combines hotel_list_by_city and hotel_offers_search.
        
        Args:
            city_code: IATA city code (e.g., "NYC", "PAR", "LON")
            check_in_date: Check-in date (YYYY-MM-DD)
            check_out_date: Check-out date (YYYY-MM-DD)
            adults: Number of adults per room
            room_quantity: Number of rooms
            currency: Currency code
            max_results: Maximum number of results
        
        Returns:
            Dict containing hotels with offers
        """
        logger.info(f"Searching hotels with pricing in: {city_code}")
        
        # Step 1: Get hotel list
        hotels_result = self.hotel_list_by_city(city_code, max_results=50)
        
        if not hotels_result.get("success") or not hotels_result.get("hotels"):
            return {
                "success": False,
                "error": "No hotels found in city",
                "hotels": []
            }
        
        # Extract hotel IDs
        hotel_ids = [hotel.get("hotelId") for hotel in hotels_result["hotels"] if hotel.get("hotelId")]
        
        if not hotel_ids:
            return {
                "success": False,
                "error": "No valid hotel IDs found",
                "hotels": []
            }
        
        logger.info(f"Found {len(hotel_ids)} hotel IDs, getting offers...")
        
        # Step 2: Get pricing for hotels
        offers_result = self.hotel_offers_search(
            hotel_ids=hotel_ids[:max_results],  # Limit for performance
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adults=adults,
            room_quantity=room_quantity,
            currency=currency
        )
        
        if not offers_result.get("success"):
            return {
                "success": False,
                "error": offers_result.get("error"),
                "hotels": []
            }
        
        return {
            "success": True,
            "hotels": offers_result.get("offers", [])[:max_results],
            "meta": offers_result.get("meta", {})
        }
    
    def city_search(self, keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        City Search API - Search for cities by keyword.
        https://developers.amadeus.com/self-service/category/trip/api-doc/city-search
        
        Args:
            keyword: City name or keyword
            max_results: Maximum number of results
        
        Returns:
            List of matching cities
        """
        logger.info(f"Searching cities: {keyword}")
        
        try:
            token = self._get_access_token()
            
            endpoint = f"{self.base_url}/v1/reference-data/locations/cities"
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "keyword": keyword,
                "max": max_results
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            cities = data.get("data", [])
            
            logger.info(f"✅ Found {len(cities)} cities")
            return cities
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ City search failed: {e}")
            return []
    
    def format_flight_offer(self, offer: Dict[str, Any], dictionaries: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format Amadeus flight offer into simplified structure.
        
        Args:
            offer: Raw flight offer from Amadeus API
            dictionaries: Carrier and aircraft dictionaries
        
        Returns:
            Formatted flight offer
        """
        try:
            # Extract basic info
            price = offer.get("price", {})
            itineraries = offer.get("itineraries", [])
            
            # Get carrier info
            validating_airline = offer.get("validatingAirlineCodes", [""])[0]
            carriers = dictionaries.get("carriers", {})
            airline_name = carriers.get(validating_airline, validating_airline)
            
            # Format outbound flight
            outbound = itineraries[0] if len(itineraries) > 0 else {}
            outbound_segments = outbound.get("segments", [])
            
            # Format return flight (if exists)
            return_flight = None
            if len(itineraries) > 1:
                return_segments = itineraries[1].get("segments", [])
                if return_segments:
                    return_flight = {
                        "departure_time": return_segments[0]["departure"]["at"],
                        "arrival_time": return_segments[-1]["arrival"]["at"],
                        "duration": itineraries[1].get("duration", "")
                    }
            
            formatted = {
                "flight_id": offer.get("id"),
                "airline": airline_name,
                "airline_code": validating_airline,
                "price": float(price.get("total", 0)),
                "currency": price.get("currency", "USD"),
                "outbound": {
                    "departure_time": outbound_segments[0]["departure"]["at"] if outbound_segments else None,
                    "arrival_time": outbound_segments[-1]["arrival"]["at"] if outbound_segments else None,
                    "duration": outbound.get("duration", ""),
                    "stops": len(outbound_segments) - 1
                },
                "return": return_flight,
                "available_seats": offer.get("numberOfBookableSeats", 0),
                "cabin_class": "ECONOMY"  # Can be extracted from travelerPricings
            }
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting flight offer: {e}")
            return {}


# Singleton instance
_amadeus_client: Optional[AmadeusClient] = None


def get_amadeus_client(use_production: bool = False) -> AmadeusClient:
    """
    Get or create Amadeus client singleton.
    
    Args:
        use_production: If True, use production API
    
    Returns:
        AmadeusClient instance
    """
    global _amadeus_client
    
    if _amadeus_client is None:
        _amadeus_client = AmadeusClient(use_production=use_production)
    
    return _amadeus_client

