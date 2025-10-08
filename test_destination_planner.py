"""
Test script for destination planner integration.
"""

import os
import sys
sys.path.insert(0, '/app')

# Set environment variable
os.environ['TAVILY_API_KEY'] = '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'

from main import ItineraryPlannerSystem


def test_destination_planner_basic():
    """Test 1: User uncertain about destination."""
    print("=" * 80)
    print("TEST 1: User Uncertain About Destination")
    print("=" * 80)
    
    planner = ItineraryPlannerSystem()
    
    query = "I want to travel for 7 days in the USA with my family. We have 2 kids aged 4 and 7. I prefer not extreme weather and family-friendly activities. I don't know where to go."
    
    print(f"\n👤 USER: {query}\n")
    
    try:
        result = planner.process_query(
            query=query,
            thread_id="test_destination_1"
        )
        
        print("🤖 ASSISTANT:")
        print(result.get("response", "No response"))
        print()
        
        if result.get("suggestions"):
            print("💡 SUGGESTIONS:")
            for sug in result["suggestions"]:
                print(f"  [{sug['token']}] {sug['description']}")
            print()
        
        # Check if we got destination recommendations
        session = planner.sessions.get("test_destination_1")
        if session:
            tool_results = session.get("tool_results", {})
            if "destination_recommendations" in tool_results:
                print("✅ SUCCESS: Destination recommendations generated!")
                recommendations = tool_results["destination_recommendations"].get("recommendations", [])
                print(f"   Found {len(recommendations)} destination options")
            else:
                print("⚠️  WARNING: No destination recommendations in tool_results")
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_destination_selection(planner, thread_id="test_destination_1"):
    """Test 2: User selects a destination."""
    print("\n" + "=" * 80)
    print("TEST 2: User Selects Destination (D1)")
    print("=" * 80)
    
    try:
        result = planner.handle_suggestion_selection("D1", thread_id=thread_id)
        
        print("\n🤖 ASSISTANT:")
        print(result.get("response", "No response"))
        print()
        
        # Check if destination was set
        session = planner.sessions.get(thread_id)
        if session:
            user_prefs = session.get("user_preferences", {})
            metadata = session.get("metadata", {})
            
            print(f"Selected destination: {user_prefs.get('destination', 'NOT SET')}")
            print(f"Destination selected flag: {metadata.get('destination_selected', False)}")
            
            if user_prefs.get('destination'):
                print("✅ SUCCESS: Destination was set in user preferences!")
            else:
                print("⚠️  WARNING: Destination not found in user preferences")
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_routing_logic():
    """Test 3: Router detects destination uncertainty."""
    print("\n" + "=" * 80)
    print("TEST 3: Router Detection Logic")
    print("=" * 80)
    
    planner = ItineraryPlannerSystem()
    
    test_queries = [
        "I don't know where to go for vacation",
        "Help me choose a destination for my trip",
        "Where should I go for a week?",
        "Suggest a place for family vacation"
    ]
    
    for query in test_queries:
        print(f"\n👤 Query: {query}")
        
        try:
            result = planner.process_query(query, thread_id=f"test_routing_{hash(query)}")
            
            # Check if routed to destination planner
            session = planner.sessions.get(f"test_routing_{hash(query)}")
            if session:
                metadata = session.get("metadata", {})
                if metadata.get("preplanner_phase"):
                    print("   ✅ Correctly routed to DESTINATION_PLANNER")
                else:
                    print("   ⚠️  Did not route to DESTINATION_PLANNER")
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")


if __name__ == "__main__":
    print("\n🚀 DESTINATION PLANNER INTEGRATION TESTS")
    print("=" * 80)
    
    # Test 1: Basic destination discovery
    result1 = test_destination_planner_basic()
    
    if result1 and result1.get("suggestions"):
        # Test 2: Destination selection
        planner = ItineraryPlannerSystem()
        # Re-create the session from test 1
        test_destination_planner_basic()  # Run again to create session
        test_destination_selection(planner, "test_destination_1")
    
    # Test 3: Routing logic
    test_routing_logic()
    
    print("\n" + "=" * 80)
    print("✅ INTEGRATION TESTS COMPLETED")
    print("=" * 80)
