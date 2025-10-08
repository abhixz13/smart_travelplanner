# agents/preplanner_agent.py

"""
Pre-Planner Agent: Helps users discover and choose destinations.
Handles uncertain destination scenarios with intelligent suggestions.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from tavily import TavilyClient

from core.state import GraphState
from utils.config import get_config

logger = logging.getLogger(__name__)


def preplanner_agent_node(state: GraphState) -> Dict[str, Any]:
    """
    Pre-planner agent for destination discovery and recommendation.
    
    Helps users who are unsure about their destination by:
    - Understanding requirements and constraints
    - Researching potential destinations
    - Providing ranked recommendations with reasoning
    - Facilitating destination selection
    
    Args:
        state: Current graph state
    
    Returns:
        Updated state with destination recommendations
    """
    logger.info("="*60)
    logger.info("PRE-PLANNER AGENT: Destination discovery")
    logger.info("="*60)
    
    try:
        # Extract user requirements
        requirements = extract_travel_requirements(state)
        
        # Generate destination recommendations
        recommendations = generate_destination_recommendations(requirements, state)
        
        # Format response
        response = format_preplanner_response(recommendations, requirements)
        
        return {
            "messages": state["messages"] + [AIMessage(content=response)],
            "tool_results": {
                **state.get("tool_results", {}),
                "destination_recommendations": recommendations
            },
            "metadata": {
                **state.get("metadata", {}),
                "preplanner_phase": True,
                "requirements": requirements
            }
        }
        
    except Exception as e:
        logger.error(f"Error in pre-planner agent: {str(e)}", exc_info=True)
        return {
            "messages": state["messages"] + [
                AIMessage(content="Let me help you find the perfect destination. What are you looking for in your trip?")
            ]
        }


def extract_travel_requirements(state: GraphState) -> Dict[str, Any]:
    """
    Extract travel requirements from user messages using LLM.
    
    Extracts:
    - Duration
    - Region/country preference
    - Budget
    - Travel party (solo, couple, family, kids ages)
    - Interests/activities
    - Constraints (weather, accessibility, safety, etc.)
    - Must-haves and must-avoids
    """
    config = get_config()
    llm = ChatOpenAI(
        model=config["llm"]["model"],
        temperature=0.3  # Lower temperature for extraction
    )
    
    # Get conversation history
    messages = state.get("messages", [])
    user_messages = [msg.content for msg in messages if hasattr(msg, 'type') and msg.type == "human"]
    conversation = "\n".join(user_messages)
    
    extraction_prompt = f"""Extract travel requirements from this conversation:

"{conversation}"

Extract and structure the following information (use null if not mentioned):

{{
  "duration_days": integer or null,
  "region_preference": "specific region/country" or null,
  "budget": "budget" | "mid-range" | "luxury" | null,
  "travel_party": {{
    "type": "solo" | "couple" | "family" | "group",
    "adults": integer,
    "children": integer,
    "child_ages": [list of ages] or null
  }},
  "interests": [list of strings],
  "constraints": {{
    "weather": "description of weather preferences",
    "accessibility": "any mobility/accessibility needs",
    "safety": "safety concerns or requirements",
    "activities_to_avoid": [list],
    "must_haves": [list],
    "physical_difficulty": "easy" | "moderate" | "challenging"
  }},
  "specific_attractions": [list of must-see places mentioned],
  "flexible_dates": boolean,
  "preferred_season": "spring" | "summer" | "fall" | "winter" | null
}}

Be thorough in extraction. If weather preferences mentioned (not extreme, mild, warm, etc.), capture them.
If family-friendly mentioned or kids present, note physical_difficulty as "easy".
If specific places mentioned (Niagara Falls), add to specific_attractions.

Respond with ONLY valid JSON.
"""
    
    try:
        response = llm.invoke(extraction_prompt)
        requirements = json.loads(response.content.strip())
        
        logger.info(f"Extracted requirements: {requirements}")
        return requirements
        
    except Exception as e:
        logger.error(f"Error extracting requirements: {e}")
        return {
            "duration_days": 7,
            "region_preference": None,
            "interests": [],
            "constraints": {}
        }


def generate_destination_recommendations(requirements: Dict[str, Any], 
                                        state: GraphState) -> Dict[str, Any]:
    """
    Generate destination recommendations based on requirements.
    
    Uses two-phase approach:
    1. LLM reasoning to generate candidate destinations
    2. Tavily search to validate and enrich data
    """
    config = get_config()
    llm = ChatOpenAI(
        model=config["llm"]["model"],
        temperature=0.7
    )
    
    # Phase 1: LLM generates candidate destinations
    candidates = generate_candidate_destinations(requirements, llm)
    
    # Phase 2: Research and validate with Tavily
    enriched_candidates = research_destinations(candidates, requirements, state)
    
    # Phase 3: Rank and score
    ranked_recommendations = rank_destinations(enriched_candidates, requirements)
    
    return {
        "recommendations": ranked_recommendations,
        "requirements": requirements,
        "timestamp": datetime.now().isoformat()
    }


def generate_candidate_destinations(requirements: Dict[str, Any], 
                                   llm: ChatOpenAI) -> List[Dict[str, Any]]:
    """
    Use LLM to generate candidate destinations based on requirements.
    """
    
    # Build detailed prompt
    prompt = f"""You are a travel expert. Based on these requirements, suggest 5-7 suitable destinations.

Requirements:
{json.dumps(requirements, indent=2)}

Consider:
- Duration: {requirements.get('duration_days', 'unspecified')} days
- Region: {requirements.get('region_preference', 'anywhere')}
- Budget: {requirements.get('budget', 'mid-range')}
- Travel party: {requirements.get('travel_party', {}).get('type', 'unknown')}
- Children: {requirements.get('travel_party', {}).get('children', 0)} kids
- Child ages: {requirements.get('travel_party', {}).get('child_ages', [])}
- Interests: {', '.join(requirements.get('interests', []))}
- Weather constraints: {requirements.get('constraints', {}).get('weather', 'none')}
- Physical difficulty: {requirements.get('constraints', {}).get('physical_difficulty', 'any')}
- Must avoid: {requirements.get('constraints', {}).get('activities_to_avoid', [])}
- Specific attractions: {requirements.get('specific_attractions', [])}

For each destination, provide:
1. Destination name (city or region)
2. Country
3. Why it matches requirements
4. Best for (what type of traveler)
5. Typical weather during travel period
6. Family-friendly rating (1-10)
7. Safety rating (1-10)
8. Estimated daily budget
9. Key attractions
10. Potential concerns

Respond with JSON array:
[
  {{
    "destination": "San Diego, California",
    "country": "USA",
    "region": "Southern California",
    "match_score": 9.5,
    "why_suitable": "Perfect weather year-round, beaches, kid-friendly attractions like SeaWorld and San Diego Zoo, safe, easy to navigate",
    "best_for": "Families with young children",
    "typical_weather": "Mild and sunny, 70-75°F",
    "family_friendly_score": 10,
    "safety_score": 9,
    "estimated_daily_budget": 200,
    "key_attractions": ["San Diego Zoo", "Balboa Park", "La Jolla Beaches", "USS Midway"],
    "concerns": ["Can be touristy in peak season", "Parking can be challenging"]
  }},
  ...
]

Prioritize destinations that:
- Match weather preferences exactly
- Are safe and accessible for the travel party
- Fit the budget
- Offer activities aligned with interests
- Avoid activities they want to avoid

Respond with ONLY valid JSON array.
"""
    
    try:
        response = llm.invoke(prompt)
        candidates = json.loads(response.content.strip())
        
        logger.info(f"Generated {len(candidates)} candidate destinations")
        return candidates
        
    except Exception as e:
        logger.error(f"Error generating candidates: {e}")
        return []


def research_destinations(candidates: List[Dict[str, Any]], 
                         requirements: Dict[str, Any],
                         state: GraphState) -> List[Dict[str, Any]]:
    """
    Use Tavily to research and validate destination candidates.
    Adds real-time information and current conditions.
    """
    config = get_config()
    tavily_key = config.get("api_keys", {}).get("tavily")
    
    if not tavily_key:
        logger.warning("Tavily not configured, skipping research phase")
        return candidates
    
    try:
        tavily_client = TavilyClient(api_key=tavily_key)
        
        enriched = []
        for candidate in candidates:
            destination = candidate.get("destination")
            
            # Build research query
            query = f"{destination} family travel weather attractions things to do"
            
            if requirements.get('travel_party', {}).get('children'):
                query += " kid-friendly activities"
            
            logger.info(f"Researching: {destination}")
            
            try:
                # Search for current information
                search_results = tavily_client.search(
                    query=query,
                    search_depth="basic",
                    max_results=3,
                    include_answer=True
                )
                
                # Add research data to candidate
                candidate["research"] = {
                    "answer": search_results.get("answer", ""),
                    "sources": [r.get("url") for r in search_results.get("results", [])[:2]],
                    "recent_info": search_results.get("results", [{}])[0].get("content", "")[:300]
                }
                
                enriched.append(candidate)
                
            except Exception as e:
                logger.error(f"Error researching {destination}: {e}")
                enriched.append(candidate)  # Add anyway without research
        
        return enriched
        
    except Exception as e:
        logger.error(f"Research phase error: {e}")
        return candidates


def rank_destinations(candidates: List[Dict[str, Any]], 
                     requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Rank destinations based on how well they match requirements.
    
    Scoring factors:
    - Weather match (25%)
    - Family-friendly (20% if traveling with kids)
    - Safety (20%)
    - Budget fit (15%)
    - Interest alignment (20%)
    """
    
    travel_party = requirements.get("travel_party", {})
    has_children = travel_party.get("children", 0) > 0
    child_ages = travel_party.get("child_ages", [])
    young_children = any(age < 6 for age in child_ages) if child_ages else False
    
    constraints = requirements.get("constraints", {})
    
    for candidate in candidates:
        score = 0
        score_breakdown = {}
        
        # Weather match (25 points)
        weather_pref = constraints.get("weather", "").lower()
        dest_weather = candidate.get("typical_weather", "").lower()
        
        if weather_pref:
            weather_score = 0
            if "not extreme" in weather_pref or "mild" in weather_pref:
                if any(word in dest_weather for word in ["mild", "moderate", "pleasant", "comfortable"]):
                    weather_score = 25
                elif any(word in dest_weather for word in ["extreme", "very hot", "very cold"]):
                    weather_score = 5
                else:
                    weather_score = 15
            elif "warm" in weather_pref:
                if any(word in dest_weather for word in ["warm", "hot", "sunny"]):
                    weather_score = 25
                else:
                    weather_score = 10
            elif "cold" in weather_pref or "snow" in weather_pref:
                if any(word in dest_weather for word in ["cold", "snow", "winter"]):
                    weather_score = 25
                else:
                    weather_score = 10
            
            score += weather_score
            score_breakdown["weather"] = weather_score
        else:
            score += 15  # Neutral score if no preference
            score_breakdown["weather"] = 15
        
        # Family-friendly (20 points if has kids, 10 otherwise)
        family_score = candidate.get("family_friendly_score", 5)
        if has_children:
            score += (family_score / 10) * 20
            score_breakdown["family_friendly"] = (family_score / 10) * 20
            
            # Extra penalty if young children and difficult terrain
            if young_children:
                difficulty = constraints.get("physical_difficulty", "").lower()
                if "easy" in difficulty or "accessible" in difficulty:
                    score += 5  # Bonus for easy access
        else:
            score += (family_score / 10) * 10
            score_breakdown["family_friendly"] = (family_score / 10) * 10
        
        # Safety (20 points)
        safety_score = candidate.get("safety_score", 5)
        safety_points = (safety_score / 10) * 20
        score += safety_points
        score_breakdown["safety"] = safety_points
        
        # Budget fit (15 points)
        budget_pref = requirements.get("budget", "mid-range")
        dest_budget = candidate.get("estimated_daily_budget", 150)
        
        budget_ranges = {
            "budget": (50, 100),
            "mid-range": (100, 250),
            "luxury": (250, 500)
        }
        target_range = budget_ranges.get(budget_pref, (100, 250))
        
        if target_range[0] <= dest_budget <= target_range[1]:
            budget_points = 15
        else:
            distance = min(abs(dest_budget - target_range[0]), abs(dest_budget - target_range[1]))
            budget_points = max(0, 15 - (distance / 20))
        
        score += budget_points
        score_breakdown["budget"] = budget_points
        
        # Interest alignment (20 points)
        interests = requirements.get("interests", [])
        attractions = candidate.get("key_attractions", [])
        
        if interests:
            interest_match = 0
            for interest in interests:
                interest_lower = interest.lower()
                for attraction in attractions:
                    attraction_lower = str(attraction).lower()
                    if interest_lower in attraction_lower or any(word in attraction_lower for word in interest_lower.split()):
                        interest_match += 1
                        break
            
            interest_points = min(20, (interest_match / len(interests)) * 20)
        else:
            interest_points = 15  # Neutral if no specific interests
        
        score += interest_points
        score_breakdown["interest"] = interest_points
        
        # Store scores
        candidate["final_score"] = round(score, 2)
        candidate["score_breakdown"] = score_breakdown
    
    # Sort by score
    candidates.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    
    return candidates


def format_preplanner_response(recommendations: Dict[str, Any], 
                               requirements: Dict[str, Any]) -> str:
    """
    Format pre-planner recommendations into human-readable response.
    """
    destinations = recommendations.get("recommendations", [])
    
    if not destinations:
        return "I'd love to help you find the perfect destination! Could you tell me more about what you're looking for?"
    
    response_parts = [
        "🌍 Based on your requirements, here are my top destination recommendations:\n"
    ]
    
    # Summary of requirements
    duration = requirements.get("duration_days")
    if duration:
        response_parts.append(f"\n📅 Trip Duration: {duration} days")
    
    travel_party = requirements.get("travel_party", {})
    if travel_party.get("children"):
        response_parts.append(f"\n👨‍👩‍👧‍👦 Traveling with {travel_party['children']} child(ren)")
    
    constraints = requirements.get("constraints", {})
    if constraints.get("weather"):
        response_parts.append(f"\n🌤️ Weather Preference: {constraints['weather']}")
    
    response_parts.append("\n" + "="*60)
    
    # Show top 3-5 recommendations
    for i, dest in enumerate(destinations[:5], 1):
        response_parts.append(f"\n\n**{i}. {dest['destination']}, {dest['country']}**")
        response_parts.append(f"\n   📊 Match Score: {dest['final_score']:.1f}/100")
        
        response_parts.append(f"\n\n   ✨ Why This Destination:")
        response_parts.append(f"\n   {dest['why_suitable']}")
        
        response_parts.append(f"\n\n   🌡️ Weather: {dest['typical_weather']}")
        response_parts.append(f"\n   💰 Est. Daily Budget: ${dest['estimated_daily_budget']}")
        response_parts.append(f"\n   👨‍👩‍👧 Family-Friendly: {dest['family_friendly_score']}/10")
        response_parts.append(f"\n   🛡️ Safety: {dest['safety_score']}/10")
        
        if dest.get("key_attractions"):
            response_parts.append(f"\n\n   🎯 Key Attractions:")
            for attraction in dest["key_attractions"][:4]:
                response_parts.append(f"\n      • {attraction}")
        
        if dest.get("concerns"):
            response_parts.append(f"\n\n   ⚠️ Things to Consider:")
            for concern in dest["concerns"][:2]:
                response_parts.append(f"\n      • {concern}")
        
        # Add research insights if available
        if dest.get("research", {}).get("answer"):
            response_parts.append(f"\n\n   💡 Current Info:")
            answer = dest["research"]["answer"][:200]
            response_parts.append(f"\n   {answer}...")
        
        response_parts.append("\n   " + "-"*50)
    
    response_parts.append("\n\n" + "="*60)
    response_parts.append("\n\n💬 Which destination interests you? I can create a detailed itinerary for any of these!")
    response_parts.append("\nOr let me know if you'd like different options based on other criteria.")
    
    return "".join(response_parts)


def handle_destination_selection(state: GraphState, selected_destination: str) -> GraphState:
    """
    Handle when user selects a destination from recommendations.
    Updates state to proceed with full planning.
    """
    # Extract destination details from recommendations
    tool_results = state.get("tool_results", {})
    recommendations = tool_results.get("destination_recommendations", {}).get("recommendations", [])
    
    selected = None
    for dest in recommendations:
        if selected_destination.lower() in dest.get("destination", "").lower():
            selected = dest
            break
    
    if selected:
        # Update user preferences with selected destination
        user_prefs = {
            "destination": selected["destination"],
            "budget": selected.get("estimated_daily_budget", 150),
            "family_friendly": selected.get("family_friendly_score", 5) > 7,
            **state.get("metadata", {}).get("requirements", {})
        }
        
        # Update state
        updated_state = GraphState(
            messages=state["messages"],
            plan=None,
            current_itinerary=None,
            user_preferences=user_prefs,
            next_agent="PLANNER",  # Move to full planning
            tool_results=tool_results,
            metadata={
                **state.get("metadata", {}),
                "preplanner_phase": False,
                "destination_selected": True,
                "selected_destination": selected
            }
        )
        
        return updated_state
    
    return state