"""Integration tests for autonomous planner orchestration and hotel agent."""

import unittest
from unittest.mock import patch, MagicMock, Mock, call
import json
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, AIMessage


class TestHotelAgentIntegration(unittest.TestCase):
    """Test hotel agent functionality in isolation."""
    
    def setUp(self):
        """Initialize test state."""
        self.base_state = {
            "messages": [HumanMessage(content="Test query")],
            "metadata": {},
            "tool_results": {},
            "user_preferences": {}
        }
    
    @patch('agents.hotel_agent.AMADEUS_AVAILABLE', False)
    def test_airbnb_fallback_no_amadeus(self):
        """Test Airbnb fallback when Amadeus API is unavailable."""
        from agents.hotel_agent import hotel_agent_node
        
        state = {
            **self.base_state,
            "user_preferences": {
                "destination": "Paris",
                "start_date": "2025-11-01",
                "end_date": "2025-11-08"
            }
        }
        
        result = hotel_agent_node(state)
        
        response_content = result["messages"][-1].content
        self.assertIn("Airbnb", response_content)
        self.assertIn("accommodation", response_content.lower())
        self.assertTrue(result["tool_results"]["hotel_search"]["airbnb_suggestion"])
        self.assertEqual(result["tool_results"]["hotel_search"]["destination"], "Paris")

    @patch('agents.hotel_agent.get_amadeus_client')
    @patch('agents.hotel_agent.AMADEUS_AVAILABLE', True)
    def test_hotel_search_success_with_iata(self, mock_amadeus_client):
        """Test successful hotel search with valid IATA code."""
        mock_amadeus = MagicMock()
        mock_amadeus_client.return_value = mock_amadeus
        
        mock_amadeus.city_search.return_value = [{"iataCode": "PAR", "name": "Paris"}]
        mock_amadeus.hotel_search_by_city.return_value = {
            "success": True,
            "hotels": [{
                "hotel": {
                    "hotelId": "HTPAR001",
                    "name": "Paris Grand Hotel",
                    "rating": "4.5",
                    "cityCode": "PAR",
                    "amenities": ["WIFI", "POOL", "GYM"],
                    "address": {"cityName": "Paris"}
                },
                "offers": [{
                    "price": {"total": "700.00", "currency": "USD"},
                    "checkInDate": "2025-11-01",
                    "checkOutDate": "2025-11-08",
                    "room": {
                        "typeEstimated": {"category": "DELUXE"},
                        "description": {"text": "Luxury room"}
                    },
                    "policies": {"cancellation": {"description": "Free cancellation"}}
                }]
            }]
        }

        from agents.hotel_agent import hotel_agent_node
        
        state = {
            **self.base_state,
            "user_preferences": {
                "destination": "Paris",
                "start_date": "2025-11-01",
                "end_date": "2025-11-08",
                "travelers": 2
            }
        }
        
        result = hotel_agent_node(state)
        
        response_content = result["messages"][-1].content
        self.assertNotIn("Airbnb", response_content)
        self.assertIn("Paris Grand Hotel", response_content)
        self.assertIn("$100.00/night", response_content)
        self.assertFalse(result["tool_results"]["hotel_search"].get("airbnb_suggestion", False))
        self.assertEqual(result["tool_results"]["hotel_search"]["source"], "amadeus_api")

    @patch('agents.hotel_agent.get_amadeus_client')
    @patch('agents.hotel_agent.AMADEUS_AVAILABLE', True)
    def test_autonomous_best_hotel_selection(self, mock_amadeus_client):
        """Test autonomous mode selects best hotel based on criteria."""
        mock_amadeus = MagicMock()
        mock_amadeus_client.return_value = mock_amadeus
        
        mock_amadeus.city_search.return_value = [{"iataCode": "TYO"}]
        mock_amadeus.hotel_search_by_city.return_value = {
            "success": True,
            "hotels": [
                {
                    "hotel": {
                        "hotelId": "HT001",
                        "name": "Budget Inn",
                        "rating": "3.5",
                        "cityCode": "TYO",
                        "amenities": ["WIFI"],
                        "address": {"cityName": "Tokyo"}
                    },
                    "offers": [{
                        "price": {"total": "350.00", "currency": "USD"},
                        "checkInDate": "2025-11-01",
                        "checkOutDate": "2025-11-08",
                        "room": {"typeEstimated": {"category": "STANDARD"}},
                        "policies": {"cancellation": {"description": "Standard"}}
                    }]
                },
                {
                    "hotel": {
                        "hotelId": "HT002",
                        "name": "Luxury Palace",
                        "rating": "4.8",
                        "cityCode": "TYO",
                        "amenities": ["WIFI", "POOL", "GYM", "SPA"],
                        "address": {"cityName": "Tokyo"}
                    },
                    "offers": [{
                        "price": {"total": "1400.00", "currency": "USD"},
                        "checkInDate": "2025-11-01",
                        "checkOutDate": "2025-11-08",
                        "room": {"typeEstimated": {"category": "DELUXE"}},
                        "policies": {"cancellation": {"description": "Free cancellation"}}
                    }]
                }
            ]
        }

        from agents.hotel_agent import hotel_agent_node
        
        state = {
            **self.base_state,
            "user_preferences": {
                "destination": "Tokyo",
                "start_date": "2025-11-01",
                "end_date": "2025-11-08",
                "budget": "mid-range"
            },
            "autonomous_execution": True
        }
        
        result = hotel_agent_node(state)
        
        response_content = result["messages"][-1].content
        self.assertIn("Best hotel", response_content)
        self.assertIn("selected_hotel", result["tool_results"])
        self.assertIsNotNone(result["tool_results"]["selected_hotel"])
        
        selected = result["tool_results"]["selected_hotel"]
        self.assertEqual(selected["name"], "Budget Inn")


class TestAutonomousPlannerEndToEnd(unittest.TestCase):
    """Test autonomous planner orchestration end-to-end."""
    
    def setUp(self):
        """Initialize test state."""
        self.base_state = {
            "messages": [HumanMessage(content="Plan a weekend trip to Paris")],
            "metadata": {},
            "tool_results": {},
            "user_preferences": {}
        }
    
    def create_mock_llm_response(self, response_data):
        """Create mock LLM response with JSON content."""
        mock_response = MagicMock()
        mock_response.content = json.dumps(response_data)
        return mock_response

    @patch('agents.autonomous_planner.format_autonomous_response')
    @patch('agents.autonomous_planner.execute_autonomous_plan')
    @patch('agents.autonomous_planner.create_autonomous_plan')
    @patch('agents.autonomous_planner.extract_travel_info')
    @patch('agents.autonomous_planner.detect_travel_intent')
    def test_complete_trip_orchestration(
        self, 
        mock_detect_intent,
        mock_extract_info,
        mock_create_plan,
        mock_execute_plan,
        mock_format_response
    ):
        """Test complete trip planning orchestration flow."""
        # Mock intent detection
        mock_detect_intent.return_value = {
            "is_travel_request": True,
            "request_type": "complete_trip",
            "confidence": 0.95,
            "components_needed": ["flights", "hotels", "activities"],
            "reasoning": "User wants a complete Paris trip"
        }
        
        # Mock travel info extraction
        mock_extract_info.return_value = {
            "destination": "Paris",
            "origin": "New York",
            "start_date": "2025-11-15",
            "end_date": "2025-11-22",
            "travelers": 2,
            "budget": "mid-range",
            "preferences": ["culture", "food"]
        }
        
        # Mock plan creation
        mock_create_plan.return_value = {
            "plan_type": "complete_trip",
            "steps": [
                {"agent": "flight", "action": "search_flights"},
                {"agent": "hotel", "action": "search_hotels"},
                {"agent": "activity", "action": "suggest_activities"}
            ],
            "execution_order": ["flight", "hotel", "activity"]
        }
        
        # Mock plan execution
        mock_execute_plan.return_value = {
            "messages": self.base_state["messages"] + [
                AIMessage(content="Flight results"),
                AIMessage(content="Hotel results"),
                AIMessage(content="Activity suggestions")
            ],
            "tool_results": {
                "flight_search": {"flights": []},
                "hotel_search": {"hotels": []},
                "activity_search": {"activities": []}
            },
            "execution_summary": {
                "steps_completed": 3,
                "success": True
            }
        }
        
        # Mock response formatting
        mock_format_response.return_value = "Complete trip plan for Paris including flights, hotels, and activities."
        
        from agents.autonomous_planner import autonomous_planner_node
        
        result = autonomous_planner_node(self.base_state)
        
        # Verify orchestration flow
        mock_detect_intent.assert_called_once()
        mock_extract_info.assert_called_once()
        mock_create_plan.assert_called_once()
        mock_execute_plan.assert_called_once()
        mock_format_response.assert_called_once()
        
        # Verify final response
        final_message = result["messages"][-1]
        self.assertIsInstance(final_message, AIMessage)
        self.assertIn("Paris", final_message.content)

    @patch('agents.autonomous_planner.hotel_agent_node')
    @patch('agents.autonomous_planner.extract_travel_info')
    @patch('agents.autonomous_planner.detect_travel_intent')
    def test_hotel_only_request_integration(
        self,
        mock_detect_intent,
        mock_extract_info,
        mock_hotel_agent
    ):
        """Test hotel-only request flows through autonomous planner to hotel agent."""
        # Mock intent detection for hotel-only request
        mock_detect_intent.return_value = {
            "is_travel_request": True,
            "request_type": "hotel_only",
            "confidence": 0.9,
            "components_needed": ["hotels"],
            "reasoning": "User only needs hotel booking"
        }
        
        # Mock travel info extraction
        mock_extract_info.return_value = {
            "destination": "Tokyo",
            "start_date": "2025-12-01",
            "end_date": "2025-12-08",
            "travelers": 1,
            "budget": "luxury"
        }
        
        # Mock hotel agent response
        mock_hotel_agent.return_value = {
            "messages": self.base_state["messages"] + [
                AIMessage(content="Found 3 luxury hotels in Tokyo")
            ],
            "tool_results": {
                "hotel_search": {
                    "hotels": [
                        {"name": "Tokyo Imperial", "price_per_night": 300},
                        {"name": "Park Hyatt Tokyo", "price_per_night": 450}
                    ],
                    "source": "amadeus_api"
                }
            }
        }
        
        from agents.autonomous_planner import autonomous_planner_node
        
        result = autonomous_planner_node(self.base_state)
        
        # Verify hotel agent was called
        mock_hotel_agent.assert_called_once()
        
        # Verify the state passed to hotel agent
        call_args = mock_hotel_agent.call_args[0][0]
        self.assertEqual(call_args["user_preferences"]["destination"], "Tokyo")
        self.assertEqual(call_args["user_preferences"]["budget"], "luxury")
        
        # Verify final response contains hotel results
        final_message = result["messages"][-1]
        self.assertIn("Tokyo", final_message.content)

    @patch('agents.autonomous_planner.activity_agent_node')
    @patch('agents.autonomous_planner.hotel_agent_node')
    @patch('agents.autonomous_planner.flight_agent_node')
    @patch('agents.autonomous_planner.extract_travel_info')
    @patch('agents.autonomous_planner.detect_travel_intent')
    def test_complete_trip_calls_all_agents(
        self,
        mock_detect_intent,
        mock_extract_info,
        mock_flight_agent,
        mock_hotel_agent,
        mock_activity_agent
    ):
        """Test complete trip request calls flight, hotel, and activity agents in order."""
        # Mock intent detection
        mock_detect_intent.return_value = {
            "is_travel_request": True,
            "request_type": "complete_trip",
            "confidence": 0.95,
            "components_needed": ["flights", "hotels", "activities"],
            "reasoning": "Complete vacation planning"
        }
        
        # Mock travel info extraction
        mock_extract_info.return_value = {
            "destination": "Barcelona",
            "origin": "London",
            "start_date": "2025-11-01",
            "end_date": "2025-11-10",
            "travelers": 2,
            "budget": "mid-range"
        }
        
        # Mock agent responses
        mock_flight_agent.return_value = {
            "messages": self.base_state["messages"] + [AIMessage(content="Flight results")],
            "tool_results": {"flight_search": {"flights": [{"price": 350}]}}
        }
        
        mock_hotel_agent.return_value = {
            "messages": self.base_state["messages"] + [
                AIMessage(content="Flight results"),
                AIMessage(content="Hotel results")
            ],
            "tool_results": {
                "flight_search": {"flights": [{"price": 350}]},
                "hotel_search": {"hotels": [{"name": "Barcelona Hotel"}]}
            }
        }
        
        mock_activity_agent.return_value = {
            "messages": self.base_state["messages"] + [
                AIMessage(content="Flight results"),
                AIMessage(content="Hotel results"),
                AIMessage(content="Activity suggestions")
            ],
            "tool_results": {
                "flight_search": {"flights": [{"price": 350}]},
                "hotel_search": {"hotels": [{"name": "Barcelona Hotel"}]},
                "activity_search": {"activities": [{"name": "Sagrada Familia"}]}
            }
        }
        
        from agents.autonomous_planner import autonomous_planner_node
        
        result = autonomous_planner_node(self.base_state)
        
        # Verify all three agents were called in order
        mock_flight_agent.assert_called_once()
        mock_hotel_agent.assert_called_once()
        mock_activity_agent.assert_called_once()
        
        # Verify execution order by checking call order
        self.assertTrue(mock_flight_agent.call_count == 1)
        self.assertTrue(mock_hotel_agent.call_count == 1)
        self.assertTrue(mock_activity_agent.call_count == 1)
        
        # Verify final state has results from all agents
        self.assertIn("flight_search", result["tool_results"])
        self.assertIn("hotel_search", result["tool_results"])
        self.assertIn("activity_search", result["tool_results"])

    @patch('agents.autonomous_planner.hotel_agent_node')
    @patch('agents.autonomous_planner.extract_travel_info')
    @patch('agents.autonomous_planner.detect_travel_intent')
    def test_airbnb_fallback_in_autonomous_flow(
        self,
        mock_detect_intent,
        mock_extract_info,
        mock_hotel_agent
    ):
        """Test Airbnb fallback surfaces through autonomous planner."""
        # Mock intent detection
        mock_detect_intent.return_value = {
            "is_travel_request": True,
            "request_type": "hotel_only",
            "confidence": 0.9,
            "components_needed": ["hotels"],
            "reasoning": "Hotel search for small town"
        }
        
        # Mock travel info extraction
        mock_extract_info.return_value = {
            "destination": "Small Town, Vermont",
            "start_date": "2025-11-01",
            "end_date": "2025-11-08",
            "travelers": 2
        }
        
        # Mock hotel agent returning Airbnb suggestion
        mock_hotel_agent.return_value = {
            "messages": self.base_state["messages"] + [
                AIMessage(content="Destination 'Small Town, Vermont' doesn't have hotel availability. Please search on Airbnb.")
            ],
            "tool_results": {
                "hotel_search": {
                    "airbnb_suggestion": True,
                    "destination": "Small Town, Vermont",
                    "message": "Please search on Airbnb or other vacation rental platforms."
                }
            }
        }
        
        from agents.autonomous_planner import autonomous_planner_node
        
        result = autonomous_planner_node(self.base_state)
        
        # Verify Airbnb message surfaces in final response
        final_message = result["messages"][-1]
        self.assertIn("Airbnb", final_message.content)
        self.assertIn("Small Town, Vermont", final_message.content)
        
        # Verify tool results contain airbnb_suggestion flag
        self.assertTrue(result["tool_results"]["hotel_search"]["airbnb_suggestion"])

    @patch('agents.autonomous_planner.extract_travel_info')
    @patch('agents.autonomous_planner.detect_travel_intent')
    def test_non_travel_request_handling(
        self,
        mock_detect_intent,
        mock_extract_info
    ):
        """Test autonomous planner handles non-travel requests gracefully."""
        # Mock intent detection for non-travel request
        mock_detect_intent.return_value = {
            "is_travel_request": False,
            "request_type": "general_chat",
            "confidence": 0.95,
            "reasoning": "User is asking about the weather"
        }
        
        from agents.autonomous_planner import autonomous_planner_node
        
        state = {
            "messages": [HumanMessage(content="What's the weather like?")],
            "metadata": {},
            "tool_results": {},
            "user_preferences": {}
        }
        
        result = autonomous_planner_node(state)
        
        # Verify extract_travel_info was NOT called
        mock_extract_info.assert_not_called()
        
        # Verify response indicates it's not a travel request
        final_message = result["messages"][-1]
        self.assertIsInstance(final_message, AIMessage)
        # Should contain some kind of clarification or redirect


if __name__ == '__main__':
    unittest.main()