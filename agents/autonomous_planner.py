import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

from core.state import GraphState
from utils.config import get_config
from utils.helpers import time_execution

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Extract travel info from query and context. Infer missing details intelligently:

Query: "{query}"
Context: "{context}"

Return JSON only:
{{
  "origin": "city/country or null if not mentioned",
  "destination": "city/country or null if not mentioned",
  "departure_date": "YYYY-MM-DD or null",
  "return_date": "YYYY-MM-DD or null",
  "duration_days": int or null,
  "budget_level": "budget|mid-range|luxury or null",
  "travel_party": {{"adults": int, "children": int, "child_ages": []}},
  "interests": [],
  "constraints": {{}},
  "must_haves": [],
  "activities_to_avoid": [],
  "trip_purpose": "leisure|business|family|romantic|adventure or null"
}}

Inference rules:
- Duration without dates → calculate from context (weekend=2-3, week=7, month=30)
- "this weekend" → next Friday-Sunday
- Country only → use null for destination (let system suggest cities)
- No budget → mid-range
- No party → 2 adults
- Activity mentions → interests
- "relaxing" → interests: ["spa", "beach", "nature"]
- "adventure" → interests: ["hiking", "outdoor", "active"]
- If no destination mentioned at all → null (do NOT invent one)
- If no origin mentioned → null (must ask user)"""

DEFAULT_INFO = {
    "origin": None,
    "destination": None,
    "departure_date": None,
    "return_date": None,
    "duration_days": None,
    "budget_level": "mid-range",
    "travel_party": {"adults": 2, "children": 0, "child_ages": None},
    "interests": [],
    "constraints": {},
    "must_haves": [],
    "activities_to_avoid": [],
    "trip_purpose": "leisure"
}

CLARIFICATION_PROMPT = """Based on this travel request, determine what CRITICAL information is missing:

Extracted Info: {extracted_info}
Original Query: "{query}"

Critical information (must have):
1. Origin location (where traveling FROM)
2. Destination OR interests/preferences to suggest one
3. Approximate dates or duration

Return JSON:
{{
  "missing_critical": ["origin", "destination", "dates"],  // only truly critical ones
  "can_suggest": {{
    "destination": true/false,  // can we suggest based on interests?
    "dates": true/false  // can we infer from context?
  }},
  "clarification_needed": true/false
}}"""

DESTINATION_SUGGESTION_PROMPT = """Suggest 3 ideal destinations based on:

Origin: {origin}
Interests: {interests}
Duration: {duration} days
Budget: {budget}
Purpose: {purpose}
Constraints: {constraints}

Return JSON with 3 destinations optimized for this profile:
{{
  "suggestions": [
    {{
      "city": "City Name",
      "country": "Country",
      "why": "brief reason (one line)",
      "travel_time": "X hours",
      "best_for": ["interest1", "interest2"]
    }}
  ],
  "recommended": "City Name"  // your top pick
}}"""


@time_execution()
def autonomous_planner_node(state: GraphState) -> Dict[str, Any]:
    """Autonomous end-to-end travel planner with intelligent clarification."""
    logger.info("="*60 + "\nAUTONOMOUS PLANNER: Taking ownership\n" + "="*60)
    
    try:
        intent_analysis = state.get("metadata", {}).get("intent_analysis", {})
        request_type = intent_analysis.get("request_type", "complete_trip")
        components_needed = intent_analysis.get("components_needed", [])
        
        user_query = state["messages"][-1].content if state["messages"] else ""
        
        # Phase 1: Extract information
        extracted_info = extract_travel_info(user_query, state)
        logger.info(f"Extracted info: {extracted_info}")
        
        # Phase 2: Check for critical missing information
        clarification = check_missing_info(extracted_info, user_query, state)
        
        if clarification["clarification_needed"]:
            # Ask for critical information
            response = generate_clarification_request(clarification, extracted_info)
            return {
                "messages": state["messages"] + [AIMessage(content=response)],
                "metadata": {
                    **state.get("metadata", {}),
                    "awaiting_clarification": True,
                    "extracted_info": extracted_info,
                    "clarification": clarification
                }
            }
        
        # Phase 3: Suggest destination if needed
        if not extracted_info.get("destination") and extracted_info.get("origin"):
            suggested_dest = suggest_destination(extracted_info, state)
            if suggested_dest:
                extracted_info["destination"] = suggested_dest["recommended"]
                extracted_info["destination_suggestions"] = suggested_dest["suggestions"]
        
        # Phase 4: Create execution plan
        execution_plan = create_autonomous_plan(request_type, extracted_info, components_needed)
        
        # Phase 5: Execute the plan
        execution_results = execute_autonomous_plan(execution_plan, state)
        
        # Phase 6: Format complete response
        response = format_autonomous_response(execution_results, request_type, extracted_info)
        
        return {
            "messages": state["messages"] + [AIMessage(content=response)],
            "plan": execution_plan,
            "tool_results": execution_results,
            "metadata": {
                **state.get("metadata", {}),
                "autonomous_execution": True,
                "request_type": request_type,
                "extracted_info": extracted_info
            }
        }
        
    except Exception as e:
        logger.error(f"Autonomous planner error: {e}", exc_info=True)
        return {
            "messages": state["messages"] + [
                AIMessage(content=f"Planning error: {str(e)}")
            ],
            "next_agent": "END"
        }


def extract_travel_info(user_query: str, state: GraphState) -> Dict[str, Any]:
    """Extract and infer travel information using LLM."""
    config = get_config()
    llm = ChatOpenAI(model=config["llm"]["model"], temperature=0.1)
    
    messages = state.get("messages", [])
    context = "\n".join([msg.content for msg in messages[-5:] if hasattr(msg, 'content')])
    
    prompt = EXTRACTION_PROMPT.format(query=user_query, context=context)
    
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # Strip markdown code blocks
        for prefix in ["```json", "```"]:
            if content.startswith(prefix):
                content = content[len(prefix):]
        if content.endswith("```"):
            content = content[:-3]
            
        extracted = json.loads(content.strip())
        
        # Apply smart defaults only where appropriate
        if not extracted.get("budget_level"):
            extracted["budget_level"] = "mid-range"
        if not extracted.get("travel_party"):
            extracted["travel_party"] = {"adults": 2, "children": 0, "child_ages": None}
        if not extracted.get("trip_purpose"):
            extracted["trip_purpose"] = "leisure"
            
        # Infer duration from context if dates provided
        if extracted.get("departure_date") and extracted.get("return_date") and not extracted.get("duration_days"):
            try:
                start = datetime.strptime(extracted["departure_date"], "%Y-%m-%d")
                end = datetime.strptime(extracted["return_date"], "%Y-%m-%d")
                extracted["duration_days"] = (end - start).days
            except:
                pass
        
        # Infer dates from duration if provided
        if extracted.get("duration_days") and not extracted.get("departure_date"):
            start_date = datetime.now() + timedelta(days=30)  # Default 1 month out
            extracted["departure_date"] = start_date.strftime("%Y-%m-%d")
            extracted["return_date"] = (start_date + timedelta(days=extracted["duration_days"])).strftime("%Y-%m-%d")
        
        logger.info(f"Extracted: {extracted}")
        return extracted
        
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return DEFAULT_INFO.copy()


def check_missing_info(extracted_info: Dict, user_query: str, state: GraphState) -> Dict[str, Any]:
    """Determine if critical information is missing and clarification is needed."""
    config = get_config()
    llm = ChatOpenAI(model=config["llm"]["model"], temperature=0.1)
    
    prompt = CLARIFICATION_PROMPT.format(
        extracted_info=json.dumps(extracted_info, indent=2),
        query=user_query
    )
    
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        for prefix in ["```json", "```"]:
            if content.startswith(prefix):
                content = content[len(prefix):]
        if content.endswith("```"):
            content = content[:-3]
            
        clarification = json.loads(content.strip())
        logger.info(f"Clarification check: {clarification}")
        return clarification
        
    except Exception as e:
        logger.error(f"Clarification check error: {e}")
        # Default: if origin or destination missing, need clarification
        missing = []
        if not extracted_info.get("origin"):
            missing.append("origin")
        if not extracted_info.get("destination") and not extracted_info.get("interests"):
            missing.append("destination")
        
        return {
            "missing_critical": missing,
            "can_suggest": {
                "destination": bool(extracted_info.get("interests")),
                "dates": bool(extracted_info.get("duration_days"))
            },
            "clarification_needed": len(missing) > 0
        }


def generate_clarification_request(clarification: Dict, extracted_info: Dict) -> str:
    """Generate a friendly clarification request."""
    missing = clarification.get("missing_critical", [])
    
    response = "I'd love to help plan your trip! Just need a couple quick details:\n\n"
    
    if "origin" in missing:
        response += "🌍 **Where are you traveling from?** (city or airport code)\n"
    
    if "destination" in missing:
        if extracted_info.get("interests"):
            response += f"🎯 **I see you're interested in {', '.join(extracted_info['interests'][:3])}**. "
            response += "Any destination in mind, or should I suggest some options?\n"
        else:
            response += "🗺️ **Where would you like to go?** (or tell me what you're looking for and I'll suggest destinations)\n"
    
    if "dates" in missing:
        if extracted_info.get("duration_days"):
            response += f"📅 **When would you like to travel?** (I'll plan for {extracted_info['duration_days']} days)\n"
        else:
            response += "📅 **When are you thinking of traveling?** (dates or just how long)\n"
    
    response += "\nOnce I have these, I'll create your complete plan autonomously! 🚀"
    
    return response


def suggest_destination(extracted_info: Dict, state: GraphState) -> Optional[Dict]:
    """Suggest destinations based on user preferences."""
    if not extracted_info.get("origin"):
        return None
    
    config = get_config()
    llm = ChatOpenAI(model=config["llm"]["model"], temperature=0.3)
    
    prompt = DESTINATION_SUGGESTION_PROMPT.format(
        origin=extracted_info.get("origin", "unknown"),
        interests=", ".join(extracted_info.get("interests", [])) or "general travel",
        duration=extracted_info.get("duration_days", 7),
        budget=extracted_info.get("budget_level", "mid-range"),
        purpose=extracted_info.get("trip_purpose", "leisure"),
        constraints=json.dumps(extracted_info.get("constraints", {}))
    )
    
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        for prefix in ["```json", "```"]:
            if content.startswith(prefix):
                content = content[len(prefix):]
        if content.endswith("```"):
            content = content[:-3]
            
        suggestions = json.loads(content.strip())
        logger.info(f"Destination suggestions: {suggestions}")
        return suggestions
        
    except Exception as e:
        logger.error(f"Destination suggestion error: {e}")
        return None


def create_autonomous_plan(request_type: str, info: Dict, components: List[str]) -> Dict[str, Any]:
    """Create execution plan - NO HARDCODED DEFAULTS."""
    plan = {
        "request_type": request_type,
        "extracted_info": info,
        "components_needed": components,
        "steps": [],
        "timestamp": datetime.now().isoformat()
    }
    
    party = info.get("travel_party", {})
    total_guests = party.get("adults", 1) + party.get("children", 0)
    
    # Only add steps if we have required info
    origin = info.get("origin")
    destination = info.get("destination")
    
    # Flight search step - ONLY if we have origin AND destination
    if ("flights" in components or request_type in ["flight_only", "complete_trip"]) and origin and destination:
        plan["steps"].append({
            "action": "flight_search",
            "params": {
                "origin": origin,
                "destination": destination,
                "departure_date": info.get("departure_date"),
                "return_date": info.get("return_date"),
                "passengers": total_guests
            },
            "autonomous_selection": True
        })
    
    # Hotel search step - ONLY if we have destination
    if ("hotels" in components or request_type in ["hotel_only", "complete_trip"]) and destination:
        plan["steps"].append({
            "action": "hotel_search",
            "params": {
                "destination": destination,
                "check_in": info.get("departure_date"),
                "check_out": info.get("return_date"),
                "guests": total_guests,
                "budget": info.get("budget_level", "mid-range")
            },
            "autonomous_selection": True
        })
    
    # Activity search step - ONLY if we have destination
    if ("activities" in components or request_type in ["activity_only", "complete_trip"]) and destination:
        plan["steps"].append({
            "action": "activity_search",
            "params": {
                "destination": destination,
                "interests": info.get("interests", []),
                "duration_days": info.get("duration_days"),
                "budget": info.get("budget_level", "mid-range")
            },
            "autonomous_selection": True
        })
    
    # Itinerary composition - ONLY if we have destination
    if ("itinerary" in components or request_type == "complete_trip") and destination:
        plan["steps"].append({
            "action": "compose_itinerary",
            "params": {
                "destination": destination,
                "duration_days": info.get("duration_days")
            },
            "autonomous_selection": True
        })
    
    logger.info(f"Created plan with {len(plan['steps'])} steps")
    return plan


def execute_autonomous_plan(plan: Dict[str, Any], state: GraphState) -> Dict[str, Any]:
    """
    Execute autonomous plan by calling real agents.
    TODO: Replace with actual API calls to Flight_agent, Hotel_agent, Activity_agent
    """
    results = {"steps_executed": [], "selections": {}}
    
    for step in plan["steps"]:
        action = step["action"]
        params = step["params"]
        logger.info(f"Executing: {action} with params: {params}")
        
        results["steps_executed"].append({
            "action": action,
            "status": "pending_api_integration",
            "timestamp": datetime.now().isoformat()
        })
        
        # TODO: Call real agents here
        # Example:
        # if action == "flight_search":
        #     from agents.Flight_agent import FlightAgent
        #     flight_agent = FlightAgent()
        #     flight_results = flight_agent.search_flights(**params)
        #     selected_flight = flight_agent.select_best_option(flight_results, plan["extracted_info"])
        #     results["selections"]["flight"] = selected_flight
        
        if action == "flight_search":
            results["selections"]["flight"] = {
                "airline": "NA",
                "origin": params.get("origin", "NA"),
                "destination": params.get("destination", "NA"),
                "price": "NA",
                "departure": params.get("departure_date", "NA"),
                "return": params.get("return_date", "NA"),
                "passengers": params.get("passengers", "NA")
            }
        elif action == "hotel_search":
            results["selections"]["hotel"] = {
                "name": "NA",
                "destination": params.get("destination", "NA"),
                "check_in": params.get("check_in", "NA"),
                "check_out": params.get("check_out", "NA"),
                "price_per_night": "NA",
                "total_nights": "NA",
                "rating": "NA",
                "guests": params.get("guests", "NA")
            }
        elif action == "activity_search":
            results["selections"]["activities"] = [
                {
                    "name": "NA",
                    "destination": params.get("destination", "NA"),
                    "price": "NA",
                    "duration": "NA",
                    "category": "NA"
                }
            ]
        elif action == "compose_itinerary":
            results["selections"]["itinerary"] = {
                "destination": params.get("destination", "NA"),
                "duration_days": params.get("duration_days", "NA"),
                "daily_plan": "NA"
            }
    
    return results


def format_autonomous_response(results: Dict, request_type: str, info: Dict) -> str:
    """Format autonomous planning response with clear API integration status."""
    destination = info.get("destination", "NA")
    duration = info.get("duration_days", "NA")
    
    response = f"# Autonomous Travel Plan: {destination}\n\n"
    
    # Show destination selection reasoning if suggestions were made
    if info.get("destination_suggestions"):
        response += "## 🎯 Destination Selection\n"
        response += f"Based on your interests, I've selected **{destination}**\n\n"
        response += "Alternative suggestions:\n"
        for suggestion in info["destination_suggestions"][:3]:
            response += f"- {suggestion.get('city', 'NA')}: {suggestion.get('why', 'NA')}\n"
        response += "\n"
    
    response += f"**Duration**: {duration} days\n"
    response += f"**Budget Level**: {info.get('budget_level', 'NA')}\n"
    response += f"**Travel Party**: {info.get('travel_party', {}).get('adults', 'NA')} adults"
    if info.get('travel_party', {}).get('children', 0) > 0:
        response += f", {info['travel_party']['children']} children"
    response += "\n\n"
    
    # Status notice
    response += "⚠️ **Status**: API integration pending - showing plan structure\n\n"
    
    # Flight information
    if "flight" in results.get("selections", {}):
        flight = results["selections"]["flight"]
        response += f"## ✈️ Flight Search Parameters\n"
        response += f"- **Route**: {flight.get('origin', 'NA')} → {flight.get('destination', 'NA')}\n"
        response += f"- **Departure Date**: {flight.get('departure', 'NA')}\n"
        response += f"- **Return Date**: {flight.get('return', 'NA')}\n"
        response += f"- **Passengers**: {flight.get('passengers', 'NA')}\n"
        response += f"- **Airline**: {flight.get('airline', 'NA')} *(pending API)*\n"
        response += f"- **Price**: {flight.get('price', 'NA')} *(pending API)*\n\n"
    
    # Hotel information
    if "hotel" in results.get("selections", {}):
        hotel = results["selections"]["hotel"]
        response += f"## 🏨 Hotel Search Parameters\n"
        response += f"- **Location**: {hotel.get('destination', 'NA')}\n"
        response += f"- **Check-in**: {hotel.get('check_in', 'NA')}\n"
        response += f"- **Check-out**: {hotel.get('check_out', 'NA')}\n"
        response += f"- **Guests**: {hotel.get('guests', 'NA')}\n"
        response += f"- **Hotel Name**: {hotel.get('name', 'NA')} *(pending API)*\n"
        response += f"- **Price/Night**: {hotel.get('price_per_night', 'NA')} *(pending API)*\n"
        response += f"- **Rating**: {hotel.get('rating', 'NA')} *(pending API)*\n\n"
    
    # Activities information
    if "activities" in results.get("selections", {}):
        response += f"## 🎯 Activity Search Parameters\n"
        response += f"- **Destination**: {info.get('destination', 'NA')}\n"
        response += f"- **Interests**: {', '.join(info.get('interests', [])) or 'NA'}\n"
        response += f"- **Duration**: {info.get('duration_days', 'NA')} days\n"
        response += f"- **Activities**: {results['selections']['activities'][0].get('name', 'NA')} *(pending API)*\n\n"
    
    # Itinerary information
    if "itinerary" in results.get("selections", {}):
        itinerary = results["selections"]["itinerary"]
        response += f"## 📅 Itinerary Generation\n"
        response += f"- **Destination**: {itinerary.get('destination', 'NA')}\n"
        response += f"- **Duration**: {itinerary.get('duration_days', 'NA')} days\n"
        response += f"- **Daily Plan**: {itinerary.get('daily_plan', 'NA')} *(pending API)*\n\n"
    
    # Show extracted information for transparency
    response += "## 📊 Extracted Information\n"
    response += f"- **Origin**: {info.get('origin', 'NA')}\n"
    response += f"- **Destination**: {info.get('destination', 'NA')}\n"
    response += f"- **Trip Purpose**: {info.get('trip_purpose', 'NA')}\n"
    if info.get('interests'):
        response += f"- **Interests**: {', '.join(info['interests'])}\n"
    if info.get('constraints'):
        response += f"- **Constraints**: {json.dumps(info['constraints'])}\n"
    
    response += "\n---\n"
    response += "*Note: Connect Flight_agent, Hotel_agent, and Activity_agent APIs to get real results.*\n"
    response += "*You can modify any parameter by asking.*"
    
    return response