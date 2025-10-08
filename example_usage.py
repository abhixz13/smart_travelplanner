"""
Complete example demonstrating the AI-First Smart Itinerary Planner.
Shows various usage patterns and conversation flows.
"""

from main import ItineraryPlannerSystem
import json


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def print_response(result: dict):
    """Print formatted response."""
    print("🤖 ASSISTANT:")
    print(result.get("response", "No response"))
    print()


def print_suggestions(suggestions: list):
    """Print formatted suggestions."""
    if suggestions:
        print("💡 SUGGESTIONS:")
        for sug in suggestions:
            print(f"  [{sug['token']}] {sug['description']}")
        print()


def example_1_basic_planning():
    """Example 1: Basic trip planning workflow."""
    print_section("Example 1: Basic Trip Planning")
    
    planner = ItineraryPlannerSystem()
    
    # Initial query
    print("👤 USER: Plan a 7-day trip to Japan, budget-friendly, interested in culture and food")
    print()
    
    result = planner.process_query(
        query="Plan a 7-day trip to Japan, budget-friendly, interested in culture and food",
        thread_id="example_1"
    )
    
    print_response(result)
    print_suggestions(result.get("suggestions", []))
    
    # Follow up with suggestion
    if result.get("suggestions"):
        token = result["suggestions"][0]["token"]
        print(f"👤 USER: [Selects {token}]")
        print()
        
        follow_up = planner.handle_suggestion_selection(token, thread_id="example_1")
        print_response(follow_up)
        print_suggestions(follow_up.get("suggestions", []))


def example_2_specific_requests():
    """Example 2: Specific component requests."""
    print_section("Example 2: Specific Component Requests")
    
    planner = ItineraryPlannerSystem()
    
    # Flight search
    print("👤 USER: Find flights from San Francisco to Tokyo for June 1-8")
    print()
    
    result = planner.process_query(
        query="Find flights from San Francisco to Tokyo for June 1-8",
        thread_id="example_2"
    )
    
    print_response(result)
    print_suggestions(result.get("suggestions", []))
    
    # Hotel search
    print("👤 USER: Now show me hotel options in Tokyo")
    print()
    
    result = planner.process_query(
        query="Now show me hotel options in Tokyo",
        thread_id="example_2"
    )
    
    print_response(result)


def example_3_conversation_flow():
    """Example 3: Multi-turn conversation."""
    print_section("Example 3: Multi-turn Conversation")
    
    planner = ItineraryPlannerSystem()
    thread_id = "example_3"
    
    conversations = [
        "I want to visit Tokyo for a week",
        "What are the best cultural activities?",
        "Can you add a day trip to Mount Fuji?",
        "What's the estimated total cost?"
    ]
    
    for query in conversations:
        print(f"👤 USER: {query}")
        print()
        
        result = planner.process_query(query, thread_id=thread_id)
        print_response(result)
        
        if result.get("suggestions"):
            print_suggestions(result["suggestions"][:2])  # Show top 2


def example_4_state_inspection():
    """Example 4: Inspecting system state."""
    print_section("Example 4: State Inspection and Debugging")
    
    planner = ItineraryPlannerSystem()
    
    result = planner.process_query(
        query="Plan a 5-day trip to Paris for art lovers",
        thread_id="example_4"
    )
    
    print_response(result)
    
    # Inspect state
    print("📊 STATE SUMMARY:")
    state_summary = result.get("state_summary", {})
    for key, value in state_summary.items():
        print(f"  {key}: {value}")
    print()
    
    # Show full session state (for debugging)
    session = planner.sessions.get("example_4")
    if session:
        print("🔍 FULL SESSION STATE:")
        print(f"  Messages: {len(session['messages'])} total")
        print(f"  Has plan: {session.get('plan') is not None}")
        print(f"  Has itinerary: {session.get('current_itinerary') is not None}")
        print(f"  Tool results: {list(session.get('tool_results', {}).keys())}")
        print()


def example_5_error_handling():
    """Example 5: Error handling and recovery."""
    print_section("Example 5: Error Handling")
    
    planner = ItineraryPlannerSystem()
    
    # Invalid or unclear query
    print("👤 USER: asdfghjkl")
    print()
    
    result = planner.process_query(
        query="asdfghjkl",
        thread_id="example_5"
    )
    
    print_response(result)
    
    # System should handle gracefully and ask for clarification
    if result.get("suggestions"):
        print_suggestions(result["suggestions"])


def example_6_advanced_preferences():
    """Example 6: Advanced user preferences."""
    print_section("Example 6: Advanced Preferences")
    
    planner = ItineraryPlannerSystem()
    
    query = """
    Plan a 10-day trip to Italy for 2 people.
    Budget: mid-range ($200/day per person)
    Interests: Renaissance art, wine tasting, coastal towns
    Start date: September 15, 2025
    Dietary: vegetarian options needed
    Prefer boutique hotels over chains
    """
    
    print(f"👤 USER: {query.strip()}")
    print()
    
    result = planner.process_query(
        query=query,
        thread_id="example_6",
        user_preferences={
            "email": "user@example.com",
            "language": "en",
            "currency": "USD"
        }
    )
    
    print_response(result)
    print_suggestions(result.get("suggestions", []))


def example_7_itinerary_modification():
    """Example 7: Modifying an existing itinerary."""
    print_section("Example 7: Itinerary Modification")
    
    planner = ItineraryPlannerSystem()
    thread_id = "example_7"
    
    # Create initial itinerary
    print("👤 USER: Create a 3-day itinerary for Kyoto")
    print()
    
    result = planner.process_query(
        query="Create a 3-day itinerary for Kyoto",
        thread_id=thread_id
    )
    
    print_response(result)
    
    # Modify it
    print("👤 USER: Can you replace day 2 activities with more temple visits?")
    print()
    
    result = planner.process_query(
        query="Can you replace day 2 activities with more temple visits?",
        thread_id=thread_id
    )
    
    print_response(result)


def example_8_export_itinerary():
    """Example 8: Export itinerary to different formats."""
    print_section("Example 8: Export Itinerary")
    
    planner = ItineraryPlannerSystem()
    
    result = planner.process_query(
        query="Plan a 4-day trip to Barcelona",
        thread_id="example_8"
    )
    
    print_response(result)
    
    # Get session state
    session = planner.sessions.get("example_8")
    if session and session.get("current_itinerary"):
        itinerary = session["current_itinerary"]
        
        print("📄 ITINERARY EXPORT (JSON):")
        print(json.dumps(itinerary, indent=2)[:500] + "...")
        print()
        
        print("✉️ EMAIL-READY FORMAT:")
        print(f"Trip to {itinerary.get('destination')}")
        print(f"Duration: {itinerary.get('duration_days')} days")
        print(f"Estimated Cost: ${itinerary.get('total_estimated_cost', 0):.2f}")
        print("\nDay-by-day breakdown available in full export.")
        print()


def example_9_destination_planner():
    """Example 9: Using destination planner for uncertain travelers."""
    print_section("Example 9: Destination Planner (Uncertain Destination)")
    
    planner = ItineraryPlannerSystem()
    thread_id = "example_9"
    
    # User uncertain about destination
    print("👤 USER: I want to travel for 7 days in the USA with my family.")
    print("        We have 2 kids aged 4 and 7. I prefer not extreme weather")
    print("        and family-friendly activities. I don't know where to go.\n")
    
    result = planner.process_query(
        query="I want to travel for 7 days in the USA with my family. We have 2 kids aged 4 and 7. I prefer not extreme weather and family-friendly activities. I don't know where to go.",
        thread_id=thread_id
    )
    
    print_response(result)
    print_suggestions(result.get("suggestions", []))
    
    # Simulate user selecting first destination (D1)
    if result.get("suggestions") and any(s["token"].startswith("D") for s in result["suggestions"]):
        print("👤 USER: [Selects D1]\n")
        
        follow_up = planner.handle_suggestion_selection("D1", thread_id=thread_id)
        print_response(follow_up)
        
        # Check if destination was set
        session = planner.sessions.get(thread_id)
        if session:
            destination = session.get("user_preferences", {}).get("destination")
            print(f"📍 Destination Set: {destination}\n")
            
            # Show that planning can now proceed
            print("👤 USER: Great! Now create a detailed itinerary.\n")
            final_result = planner.process_query(
                query="Great! Now create a detailed itinerary.",
                thread_id=thread_id
            )
            print_response(final_result)


def run_all_examples():
    """Run all examples in sequence."""
    examples = [
        ("Basic Planning", example_1_basic_planning),
        ("Specific Requests", example_2_specific_requests),
        ("Conversation Flow", example_3_conversation_flow),
        ("State Inspection", example_4_state_inspection),
        ("Error Handling", example_5_error_handling),
        ("Advanced Preferences", example_6_advanced_preferences),
        ("Itinerary Modification", example_7_itinerary_modification),
        ("Export Itinerary", example_8_export_itinerary),
        ("Destination Planner", example_9_destination_planner),
    ]
    
    print("\n" + "🚀"*40)
    print("  AI-First Smart Itinerary Planner - Complete Examples")
    print("🚀"*40)
    
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {str(e)}\n")
            continue
    
    print("\n" + "✅"*40)
    print("  All examples completed!")
    print("✅"*40 + "\n")


if __name__ == "__main__":
    # Run all examples
    run_all_examples()
    
    # Or run individual examples:
    # example_1_basic_planning()
    # example_3_conversation_flow()
    # example_6_advanced_preferences()